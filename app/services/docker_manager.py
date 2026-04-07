#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Docker操作服务"""

import gzip
import json
import shutil
import subprocess
import logging
import time
from pathlib import Path
from threading import Lock

import docker
from docker.errors import DockerException, APIError, ImageNotFound

from app.core.config import config
from app.core.logging import ICONS, get_console
from app.core.shutdown import shutdown_event

_console_lock = Lock()


class DockerManager:
    """Docker操作管理器"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            try:
                self._client = docker.from_env()
            except DockerException as e:
                self.logger.error(f"Docker 客户端初始化失败: {e}")
                raise
        return self._client
    
    def check_image_exists(self, full_image_name: str, arch: str) -> bool:
        """检查指定架构的镜像是否已存在"""
        try:
            result = subprocess.run(
                ["docker", "inspect", full_image_name],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                image_info = json.loads(result.stdout)
                if image_info and 'Architecture' in image_info[0]:
                    return image_info[0]['Architecture'] == arch
            return False
        except Exception:
            return False
    
    def pull_image(self, full_image_name: str, arch: str) -> bool:
        """拉取指定架构的镜像"""
        if shutdown_event.is_set():
            return False
        
        if self.check_image_exists(full_image_name, arch):
            self.logger.debug(f"[{arch}] 镜像已存在: {full_image_name}")
            return True
        
        for attempt in range(config.max_retries):
            if shutdown_event.is_set():
                return False
            
            try:
                self.logger.debug(f"[{arch}] 拉取镜像: {full_image_name}")
                
                pull_stream = self.client.api.pull(
                    full_image_name,
                    platform=f"linux/{arch}",
                    stream=True,
                    decode=True
                )
                
                for event in pull_stream:
                    if shutdown_event.is_set():
                        self.logger.info(f"[{arch}] 拉取被中断")
                        return False
                    
                    status = event.get('status', '')
                    error = event.get('error', '')
                    
                    if error:
                        raise APIError(error)
                    
                    if 'Pulling from' in status:
                        self.logger.debug(f"[{arch}] {status}")
                
                self.logger.debug(f"[{arch}] 拉取成功: {full_image_name}")
                return True
                
            except (DockerException, APIError, ImageNotFound) as e:
                if shutdown_event.is_set():
                    return False
                
                if attempt == config.max_retries - 1:
                    self.logger.error(f"[{arch}] 拉取失败: {full_image_name}")
                    raise
                else:
                    self.logger.warning(f"[{arch}] 重试 {attempt + 2}...")
                    time.sleep(config.retry_delay)
            
            except Exception as e:
                if shutdown_event.is_set():
                    return False
                
                if attempt == config.max_retries - 1:
                    self.logger.error(f"[{arch}] 拉取失败: {full_image_name} - {e}")
                    raise
                else:
                    self.logger.warning(f"[{arch}] 重试 {attempt + 2}...")
                    time.sleep(config.retry_delay)
        
        return False
    
    def export_image(self, full_image_name: str, image_path: Path, arch: str) -> bool:
        """导出镜像并压缩"""
        if shutdown_event.is_set():
            return False
        
        last_error = None
        
        for attempt in range(config.max_retries):
            if shutdown_event.is_set():
                return False
            
            try:
                self.logger.debug(f"[{arch}] 制作离线镜像: {image_path.name}")
                
                image_path.parent.mkdir(parents=True, exist_ok=True)
                
                if image_path.exists() and image_path.stat().st_size > config.min_file_size:
                    self.logger.debug(f"[{arch}] 镜像已存在: {image_path.name}")
                    return True
                
                if arch == 'arm64':
                    cmd = f"docker save {full_image_name} --platform=linux/{arch} | gzip > {image_path}"
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=config.timeout
                    )
                else:
                    with subprocess.Popen(
                        ["docker", "save", full_image_name],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    ) as proc:
                        if proc.stdout is None:
                            raise RuntimeError("Failed to create pipe")
                        
                        chunk_size = 1024 * 1024
                        with gzip.open(image_path, 'wb') as f:
                            while not shutdown_event.is_set():
                                chunk = proc.stdout.read(chunk_size)
                                if not chunk:
                                    break
                                f.write(chunk)
                        
                        if shutdown_event.is_set():
                            proc.terminate()
                            proc.wait()
                            self.logger.info(f"[{arch}] 导出被中断")
                            if image_path.exists():
                                try:
                                    image_path.unlink()
                                except Exception:
                                    pass
                            return False
                        
                        if proc.wait() != 0:
                            stderr = proc.stderr.read().decode('utf-8', errors='replace') if proc.stderr else ""
                            raise subprocess.CalledProcessError(proc.returncode or 1, proc.args or "docker save", stderr)
                        result = proc
                
                if shutdown_event.is_set():
                    return False
                
                if hasattr(result, 'returncode') and result.returncode != 0:
                    stderr = result.stderr if isinstance(result.stderr, str) else result.stderr.decode('utf-8', errors='replace') if result.stderr else ""
                    raise subprocess.CalledProcessError(result.returncode, str(result.args or ""), stderr)
                
                if not image_path.exists() or image_path.stat().st_size < config.min_file_size:
                    raise RuntimeError(f"文件太小: {image_path}")
                
                self.logger.debug(f"[{arch}] 制作完成: {image_path.name}")
                return True
                
            except subprocess.TimeoutExpired:
                if shutdown_event.is_set():
                    return False
                
                last_error = "导出超时"
                self.logger.error(f"[{arch}] 导出超时: {full_image_name}")
                if attempt < config.max_retries - 1:
                    wait_time = config.retry_delay * (config.retry_backoff_factor ** attempt)
                    self.logger.warning(f"[{arch}] 重试 {attempt + 2}, 等待 {wait_time}s...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                if shutdown_event.is_set():
                    return False
                
                last_error = str(e)
                self.logger.error(f"[{arch}] 导出失败: {full_image_name}")
                if attempt < config.max_retries - 1:
                    wait_time = config.retry_delay * (config.retry_backoff_factor ** attempt)
                    self.logger.warning(f"[{arch}] 重试 {attempt + 2}, 等待 {wait_time}s...")
                    time.sleep(wait_time)
            
            finally:
                if image_path.exists() and image_path.stat().st_size < config.min_file_size:
                    try:
                        image_path.unlink()
                    except Exception:
                        pass
        
        raise RuntimeError(f"导出失败，已重试 {config.max_retries} 次: {last_error}")