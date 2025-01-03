import os
import gzip
import shutil
import subprocess
import time
import json
import logging
import sys
import re
from datetime import datetime
from pathlib import Path

# 获取项目根目录和其他路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
VERSIONS_DIR = os.path.join(DATA_DIR, "versions")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# 设置默认超时和重试参数
DEFAULT_TIMEOUT = 300
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 2

def setup_logger():
    """配置日志记录器"""
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file = os.path.join(LOGS_DIR, f'image_exporter_{datetime.now().strftime("%Y%m%d")}.log')
    
    logger = logging.getLogger('ImageExporter')
    logger.setLevel(logging.DEBUG)
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 文件日志
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # 控制台日志
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()

# 文件操作相关函数
def ensure_dirs():
    """确保所有必要的目录都存在"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(VERSIONS_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

def get_version_file_path(filename=""):
    """获取版本文件的完整路径"""
    os.makedirs(VERSIONS_DIR, exist_ok=True)
    if not filename:
        return VERSIONS_DIR
    return os.path.join(VERSIONS_DIR, filename)

def get_output_path(date_str, arch):
    """获取输出路径"""
    output_path = os.path.join(IMAGES_DIR, date_str, arch)
    os.makedirs(output_path, exist_ok=True)
    return output_path

def write_versions_to_file(filename, versions):
    """将版本信息写入文件"""
    try:
        full_path = os.path.join(VERSIONS_DIR, filename)
        os.makedirs(VERSIONS_DIR, exist_ok=True)
        with open(full_path, 'w') as file:
            for component, version in sorted(versions.items()):
                file.write(f"{component}:{version}\n")
    except Exception as e:
        logger.error(f"写入版本文件出错: {str(e)}")

def read_versions_from_file(filename):
    """从文件中读取版本信息"""
    versions = {}
    full_path = os.path.join(VERSIONS_DIR, filename)
    if os.path.exists(full_path):
        try:
            with open(full_path, 'r') as file:
                for line in file:
                    if ':' in line:
                        component, version = line.strip().split(':')
                        versions[component] = version
        except Exception as e:
            logger.error(f"读取版本文件出错: {str(e)}")
    return versions

def version_key(version_str):
    """将版本号字符串转换为可比较的元组"""
    try:
        if not version_str:
            return (0, 0, 0)
            
        if version_str.startswith('RELEASE.'):
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', version_str)
            if date_match:
                return tuple(map(int, date_match.groups()))
            
        if version_str.startswith('v'):
            version_str = version_str[1:]
            
        version_parts = version_str.split('-')[0]
        parts = []
        for part in version_parts.split('.'):
            try:
                parts.append(int(part))
            except ValueError:
                parts.append(0)
        
        while len(parts) < 3:
            parts.append(0)
            
        return tuple(parts[:3])
    except Exception as e:
        logger.debug(f"版本号格式处理: {version_str} -> {str(e)}")
        return (0, 0, 0)

def pull_image(component, full_image_name, arch, timeout=DEFAULT_TIMEOUT, max_retries=DEFAULT_MAX_RETRIES, retry_delay=DEFAULT_RETRY_DELAY, verbose=True):
    """尝试拉取指定架构的镜像"""
    if check_image_exists(full_image_name, arch):
        if verbose:
            logger.info(f"[{arch}] 镜像已存在本地: {full_image_name}")
        return True

    for attempt in range(max_retries):
        try:
            if verbose:
                logger.info(f"[{arch}] 正在尝试拉取镜像: {full_image_name}")
            
            subprocess.run(
                ["docker", "pull", f"--platform=linux/{arch}", full_image_name],
                check=True,
                stdout=subprocess.DEVNULL if not verbose else None,
                stderr=subprocess.DEVNULL if not verbose else None,
                timeout=timeout
            )
            
            if verbose:
                logger.info(f"[{arch}] 成功拉取镜像: {full_image_name}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error(f"[{arch}] 拉取镜像超时: {full_image_name}")
            if attempt == max_retries - 1:
                raise
                
        except subprocess.CalledProcessError as e:
            if attempt == max_retries - 1:
                logger.error(f"[{arch}] 拉取镜像失败: {full_image_name}, 错误: {str(e)}")
                raise
            else:
                logger.warning(f"[{arch}] 拉取失败，尝试第 {attempt + 1} 次...")
                time.sleep(retry_delay)

def check_image_exists(full_image_name, arch):
    """检查指定架构的镜像是否已经存在"""
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

def export_image(full_image_name, image_path, arch, verbose=True):
    """导出镜像并直接压缩"""
    try:
        if verbose:
            rel_path = os.path.relpath(image_path, PROJECT_ROOT)
            logger.info(f"[{arch}] 正在制作离线镜像文件: {rel_path}")
        
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
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception:
                pass
        raise

# 初始化目录
ensure_dirs()