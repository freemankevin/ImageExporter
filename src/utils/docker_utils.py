import os
import gzip
import shutil
import subprocess
import time
import json
from pathlib import Path
from src.utils.logger import logger
from src.utils.paths import PROJECT_ROOT
from config import CONFIG

def check_image_exists(full_image_name, arch):
    """检查指定架构的镜像是否已经存在
    
    Args:
        full_image_name: 完整的镜像名称（包含标签）
        arch: 架构类型（amd64/arm64）
    
    Returns:
        bool: 镜像是否存在
    """
    try:
        result = subprocess.run(
            ["docker", "inspect", full_image_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            image_info = json.loads(result.stdout)
            if image_info and 'Architecture' in image_info[0]:
                image_arch = image_info[0]['Architecture']
                return image_arch == arch
        return False
    except Exception:
        return False

def pull_image(component, full_image_name, arch, verbose=True):
    """尝试拉取指定架构的镜像"""
    # 首先检查镜像是否已存在
    if check_image_exists(full_image_name, arch):
        if verbose:
            logger.info(f"[{arch}] 镜像已存在本地: {full_image_name}")
        return True

    # 如果镜像不存在，则尝试拉取
    for attempt in range(CONFIG['max_retries']):
        try:
            if verbose:
                logger.info(f"[{arch}] 正在尝试拉取镜像: {full_image_name}")
            
            subprocess.run(
                ["docker", "pull", f"--platform=linux/{arch}", full_image_name],
                check=True,
                stdout=subprocess.DEVNULL if not verbose else None,
                stderr=subprocess.DEVNULL if not verbose else None,
                timeout=CONFIG['timeout']
            )
            
            if verbose:
                logger.info(f"[{arch}] 成功拉取镜像: {full_image_name}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error(f"[{arch}] 拉取镜像超时: {full_image_name}")
            if attempt == CONFIG['max_retries'] - 1:
                raise
                
        except subprocess.CalledProcessError as e:
            if attempt == CONFIG['max_retries'] - 1:
                logger.error(f"[{arch}] 拉取镜像失败: {full_image_name}, 错误: {str(e)}")
                raise
            else:
                logger.warning(f"[{arch}] 拉取失败，尝试第 {attempt + 1} 次...")
                time.sleep(CONFIG['retry_delay'])

def export_image(full_image_name, image_path, arch, verbose=True):
    """导出镜像并直接压缩"""
    try:
        if verbose:
            # 使用相对于项目根目录的路径
            rel_path = os.path.relpath(image_path, PROJECT_ROOT)
            logger.info(f"[{arch}] 正在制作离线镜像文件: {rel_path}")
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        
        with subprocess.Popen(
            ["docker", "save", full_image_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ) as proc:
            with gzip.open(image_path, 'wb') as f:
                shutil.copyfileobj(proc.stdout, f)
            
            if proc.wait() != 0:
                error = proc.stderr.read().decode()
                raise subprocess.CalledProcessError(
                    proc.returncode,
                    proc.args,
                    error
                )
                
            if verbose:
                logger.info(f"[{arch}] 离线镜像文件制作完成: {rel_path}")
                
    except Exception as e:
        logger.error(f"[{arch}] 导出镜像失败: {full_image_name}, 错误: {str(e)}")
        # 如果导出失败，删除可能存在的不完整文件
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception:
                pass
        raise