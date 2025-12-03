#!/usr/bin/env python3
"""
Docker镜像离线导出工具
支持多架构镜像导出 (amd64/arm64)
"""

import os
import re
import json
import gzip
import shutil
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Tuple, Set

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

# ==================== 配置和常量 ====================

# 项目目录配置
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
VERSIONS_DIR = DATA_DIR / "versions"
IMAGES_DIR = DATA_DIR / "images"
LOGS_DIR = PROJECT_ROOT / "logs"

# Docker配置
DEFAULT_TIMEOUT = 300
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 2

# ANSI 颜色代码和个性化图标
COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_CYAN = "\033[96m"
COLOR_RESET = "\033[0m"
ICON_CHECK = "✅"
ICON_CROSS = "❌"
ICON_INFO = "ℹ️ "
ICON_SUCCESS = "🎉"
ICON_WARNING = "⚠️ "
ICON_COMPONENT = "🧩"
ICON_ARROW = "➡️"

# 组件配置
COMPONENTS_CONFIG = {
    'elasticsearch': {
        'name': 'elasticsearch',
        'image': 'docker.io/library/elasticsearch',
        'tag_pattern': r'^[0-9]+\.[0-9]+\.[0-9]+$',
        'latest_version': None,
        'version_type': 'single'  # 只获取最新版本
    },
    'minio': {
        'name': 'minio',
        'image': 'docker.io/derklaro/minio',
        'tag_pattern': r'^RELEASE\.[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}-[0-9]{2}-[0-9]{2}Z$',
        'latest_version': None,
        'version_type': 'single'
    },
    'nacos': {
        'name': 'nacos',
        'image': 'docker.io/nacos/nacos-server',
        'tag_pattern': r'^v[0-9]+\.[0-9]+\.[0-9]+$',
        'latest_version': None,
        'version_type': 'single'
    },
    'nginx': {
        'name': 'nginx',
        'image': 'docker.io/library/nginx',
        'tag_pattern': r'^[0-9]+\.[0-9]+\.[0-9]+(?:-alpine)?$',
        'latest_version': None,
        'version_type': 'single'
    },
    'rabbitmq': {
        'name': 'rabbitmq',
        'image': 'docker.io/library/rabbitmq',
        'tag_pattern': r'^[0-9]+\.[0-9]+\.[0-9]+-management-alpine$',
        'latest_version': None,
        'version_type': 'single'
    },
    'redis': {
        'name': 'redis',
        'image': 'docker.io/library/redis',
        'tag_pattern': r'^[0-9]+\.[0-9]+\.[0-9]+$',
        'latest_version': None,
        'version_type': 'single'
    },
    'geoserver': {
        'name': 'geoserver',
        'image': 'docker.io/kartoza/geoserver',
        'tag_pattern': r'^[0-9]+\.[0-9]+\.[0-9]+$',
        'latest_version': None,
        'version_type': 'single'
    },
    'postgresql-postgis': {
        'name': 'postgresql-postgis',
        'image': 'docker.io/freelabspace/postgresql-postgis',
        'tag_pattern': r'^[0-9]+\.[0-9]+$',
        'exclude_pattern': r'^buildcache-.*',
        'latest_version': None,
        'version_type': 'multiple'  # 获取所有版本
    }
}

# ==================== 镜像处理结果类 ====================

class ImageResult:
    """镜像处理结果"""
    def __init__(self, image_name: str, version: str, arch: str):
        self.image_name = image_name
        self.version = version
        self.arch = arch
        self.full_image_name = f"{image_name}:{version}"
        self.pull_success = False
        self.export_success = False
        self.error_message = ""
        self.file_path: Optional[Path] = None

# ==================== 日志配置 ====================

def setup_logger(debug: bool = False) -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger('ImageExporter')
    logger.handlers.clear()  # 清除现有处理器
    
    # 设置日志级别
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        f'{COLOR_CYAN}%(asctime)s{COLOR_RESET} - {COLOR_YELLOW}%(levelname)s{COLOR_RESET} - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    ensure_dirs()
    log_file = LOGS_DIR / f"image_exporter_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.propagate = False
    return logger

# ==================== 工具函数 ====================

def ensure_dirs():
    """确保所有必要的目录都存在"""
    for directory in [DATA_DIR, VERSIONS_DIR, IMAGES_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

def version_key(version_str: str) -> Tuple[int, ...]:
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
    except Exception:
        return (0, 0, 0)

def get_major_version(version: str) -> str:
    """获取主版本号（如 13.21 返回 13）"""
    if not version:
        return ""
    return version.split('.')[0]

def print_banner():
    """打印程序横幅"""
    banner = f"""
{COLOR_CYAN}╔══════════════════════════════════════════════════════════════════════════════╗
║{COLOR_GREEN}                            DOCKER IMAGES EXPOTER                             {COLOR_CYAN}║
║{COLOR_YELLOW}                         -- SUP AMD64 & ARM64 ARCH --                         {COLOR_CYAN}║
╚══════════════════════════════════════════════════════════════════════════════╝{COLOR_RESET}
"""
    print(banner)

def print_separator(title: str = ""):
    """打印分隔符"""
    if title:
        print(f"\n{COLOR_BLUE}{'='*20} {title} {'='*20}{COLOR_RESET}")
    else:
        print(f"{COLOR_BLUE}{'='*60}{COLOR_RESET}")

# 辅助函数：计算字符串的显示宽度（考虑中文字符）
def display_width(s: str) -> int:
    """计算字符串的显示宽度，中文字符算作 2 个宽度单位"""
    width = 0
    for char in s:
        # 中文字符通常占 2 个宽度单位
        if ord(char) > 127:
            width += 2
        else:
            width += 1
    return width

def pad_string(s: str, width: int) -> str:
    """按显示宽度填充字符串，中文字符占 2 个宽度单位"""
    current_width = display_width(s)
    return s + " " * (width - current_width)

def generate_manual_commands(failed_results: List[ImageResult], today: str) -> str:
    """生成手动拉取和导出命令"""
    if not failed_results:
        return ""
    
    commands = []
    commands.append("#!/bin/bash")
    commands.append("# 手动拉取和导出失败的镜像")
    commands.append(f"# 生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    commands.append("")
    
    # 按架构分组
    arch_groups = {}
    for result in failed_results:
        if result.arch not in arch_groups:
            arch_groups[result.arch] = []
        arch_groups[result.arch].append(result)
    
    for arch, results in arch_groups.items():
        commands.append(f"# {arch.upper()} 架构镜像")
        commands.append("")
        
        for result in results:
            image_name = os.path.basename(result.image_name)
            filename = f"{image_name}_{result.version}_{arch}.tar.gz"
            
            commands.append(f"# 拉取 {result.full_image_name} ({arch})")
            commands.append(f"docker pull --platform=linux/{arch} {result.full_image_name}")
            commands.append("")
            
            commands.append(f"# 导出 {result.full_image_name} ({arch})")
            if arch == 'arm64':
                commands.append(f"docker save {result.full_image_name} --platform=linux/{arch} | gzip > data/images/{today}/{arch}/{filename}")
            else:
                commands.append(f"docker save {result.full_image_name} | gzip > data/images/{today}/{arch}/{filename}")
            commands.append("")
    
    return "\n".join(commands)

# ==================== Docker Hub API ====================

class DockerHubAPI:
    """Docker Hub API 客户端"""
    
    def __init__(self):
        self.base_url = "https://registry.hub.docker.com/v2"
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """创建带重试策略的会话"""
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_redirect=False,
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retries, pool_maxsize=10)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        return session
    
    def get_versions(self, repository: str, tag_pattern: str, exclude_pattern: Optional[str], 
                    version_type: str, logger: logging.Logger) -> List[str]:
        """获取符合指定模式的所有版本或最新版本"""
        try:
            matching_tags = []
            page = 1
            
            while True:
                url = f"{self.base_url}/repositories/{repository}/tags"
                params = {
                    'page_size': 100,
                    'page': page,
                    'ordering': 'last_updated'
                }
                
                logger.debug(f"正在获取 {repository} 的标签列表，页面: {page}")
                
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                results = data.get('results', [])
                if not results:
                    break
                
                # 筛选符合模式的版本
                for tag in results:
                    tag_name = tag['name']
                    # 匹配 tag_pattern
                    if not re.match(tag_pattern, tag_name):
                        continue
                    # 排除 exclude_pattern（如果有）
                    if exclude_pattern and re.match(exclude_pattern, tag_name):
                        continue
                    matching_tags.append(tag_name)
                
                # 检查是否有下一页
                if not data.get('next'):
                    break
                
                page += 1
            
            logger.debug(f"为 {repository} 找到 {len(matching_tags)} 个匹配的标签")
            
            if not matching_tags:
                logger.error(f"未找到符合模式 {tag_pattern} 的标签: {repository}")
                return []
            
            # 根据 version_type 处理
            if version_type == 'multiple':
                # 返回所有版本，按版本号排序
                matching_tags.sort(key=version_key)
                return matching_tags
            else:
                # 只返回最新版本
                try:
                    if 'RELEASE' in tag_pattern:
                        return [matching_tags[0]]  # minio 使用时间戳，保持原始顺序
                    elif 'management-alpine' in tag_pattern:
                        matching_tags.sort(key=lambda v: version_key(v.split('-')[0]))
                    elif tag_pattern.startswith('^v'):
                        matching_tags.sort(key=lambda v: version_key(v[1:]))
                    else:
                        matching_tags.sort(key=version_key)
                    return [matching_tags[-1]]
                except Exception as e:
                    logger.error(f"版本排序错误 {repository}: {str(e)}")
                    return [matching_tags[0]]
                
        except Exception as e:
            logger.error(f"获取版本信息失败 {repository}: {str(e)}")
            return []

# ==================== Docker 操作 ====================

class DockerManager:
    """Docker 操作管理器"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def check_image_exists(self, full_image_name: str, arch: str) -> bool:
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
    
    def pull_image(self, full_image_name: str, arch: str, 
                   timeout: int = DEFAULT_TIMEOUT, 
                   max_retries: int = DEFAULT_MAX_RETRIES, 
                   retry_delay: int = DEFAULT_RETRY_DELAY) -> bool:
        """拉取指定架构的镜像"""
        if self.check_image_exists(full_image_name, arch):
            self.logger.info(f"[{arch}] 镜像已存在: {full_image_name}")
            return True
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"[{arch}] {ICON_ARROW} 正在拉取镜像: {full_image_name}")
                
                subprocess.run(
                    ["docker", "pull", f"--platform=linux/{arch}", full_image_name],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=timeout
                )
                
                self.logger.info(f"[{arch}] {ICON_CHECK} 成功拉取镜像: {full_image_name}")
                return True
                
            except subprocess.TimeoutExpired:
                self.logger.error(f"[{arch}] {ICON_CROSS} 拉取镜像超时: {full_image_name}")
                if attempt == max_retries - 1:
                    raise
                    
            except subprocess.CalledProcessError as e:
                if attempt == max_retries - 1:
                    self.logger.error(f"[{arch}] {ICON_CROSS} 拉取镜像失败: {full_image_name}, 错误: {str(e)}")
                    raise
                else:
                    self.logger.warning(f"[{arch}] {ICON_WARNING} 拉取失败，重试第 {attempt + 2} 次...")
                    import time
                    time.sleep(retry_delay)
        
        return False
    
    def export_image(self, full_image_name: str, image_path: Path, arch: str):
        """导出镜像并压缩 - 针对arm64使用新的导出方式"""
        try:
            self.logger.info(f"[{arch}] {ICON_ARROW} 正在制作离线镜像文件: {image_path.name}")
            
            # 确保输出目录存在
            image_path.parent.mkdir(parents=True, exist_ok=True)
            
            if arch == 'arm64':
                # 对于 arm64 架构，使用新的导出方式
                cmd = f"docker save {full_image_name} --platform=linux/{arch} | gzip > {image_path}"
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True
                )
            else:
                # 对于 amd64 架构，使用原来的方式
                with subprocess.Popen(
                    ["docker", "save", full_image_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                ) as proc:
                    with gzip.open(image_path, 'wb') as f:
                        shutil.copyfileobj(proc.stdout, f)
                    
                    result = proc
                    if proc.wait() != 0:
                        error = proc.stderr.read().decode()
                        raise subprocess.CalledProcessError(
                            proc.returncode,
                            proc.args,
                            error
                        )
            
            if hasattr(result, 'returncode') and result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode,
                    result.args if hasattr(result, 'args') else cmd,
                    result.stderr if hasattr(result, 'stderr') else "导出失败"
                )
            
            self.logger.info(f"[{arch}] {ICON_CHECK} 离线镜像文件制作完成: {image_path.name}")
            
        except Exception as e:
            self.logger.error(f"[{arch}] {ICON_CROSS} 导出镜像失败: {full_image_name}, 错误: {str(e)}")
            if image_path.exists():
                try:
                    image_path.unlink()
                except Exception:
                    pass
            raise

# ==================== 版本管理 ====================

class VersionManager:
    """版本管理器"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.today = datetime.now().strftime('%Y%m%d_%H%M')      # 精确到分钟
        self.today_date = datetime.now().strftime('%Y%m%d')      # 保留日期用于目录
    
    def get_latest_history_file(self) -> Optional[Path]:
        """获取最新的历史版本文件"""
        try:
            if not VERSIONS_DIR.exists():
                return None

            history_files = []
            current_timestamp = datetime.now().strftime('%Y%m%d_%H%M')

            for file in VERSIONS_DIR.iterdir():
                if file.name.startswith("latest-") and file.name.endswith(".txt"):
                    timestamp_str = file.name.replace("latest-", "").replace(".txt", "")
                    if timestamp_str != current_timestamp:          # 排除当前时间点
                        history_files.append((timestamp_str, file))

            if not history_files:
                return None

            history_files.sort(reverse=True)
            return history_files[0][1]

        except Exception as e:
            self.logger.error(f"{ICON_CROSS} 查找历史版本文件时出错: {str(e)}")
            return None
    
    def load_history_versions(self, history_file: Path) -> Dict[str, Dict[str, str]]:
        """加载历史版本信息，按主版本号分组"""
        old_versions = {}
        try:
            with open(history_file, 'r') as f:
                for line in f:
                    if line.strip():
                        image_path = line.strip()
                        image_name = os.path.basename(image_path.split(':')[0])
                        version = image_path.split(':')[1]
                        if image_name not in old_versions:
                            old_versions[image_name] = {}
                        major_version = get_major_version(version)
                        old_versions[image_name][major_version] = version
            return old_versions
        except Exception as e:
            self.logger.error(f"{ICON_CROSS} 读取历史版本文件失败: {str(e)}")
            return {}
    
    def save_latest_versions(self, components: Dict) -> Path:
        """保存最新版本列表"""
        latest_file = VERSIONS_DIR / f"latest-{self.today}.txt"
        with open(latest_file, 'w') as f:
            for component in components.values():
                if component.get('latest_version'):
                    if isinstance(component['latest_version'], list):
                        for version in component['latest_version']:
                            f.write(f"{component['image']}:{version}\n")
                    else:
                        f.write(f"{component['image']}:{component['latest_version']}\n")
        return latest_file
    
    def save_update_list(self, updates_needed: Dict) -> Path:
        """保存需要更新的镜像列表"""
        update_file = VERSIONS_DIR / f"update-{self.today}.txt"
        with open(update_file, 'w') as f:
            for component in updates_needed.values():
                if isinstance(component['latest_version'], list):
                    for version in component['latest_version']:
                        f.write(f"{component['image']}:{version}\n")
                else:
                    f.write(f"{component['image']}:{component['latest_version']}\n")
        return update_file

# ==================== 主要业务逻辑 ====================

class ImageExporter:
    """镜像导出器主类"""
    
    def __init__(self, debug: bool = False):
        self.logger = setup_logger(debug)
        self.docker_api = DockerHubAPI()
        self.docker_manager = DockerManager(self.logger)
        self.version_manager = VersionManager(self.logger)
        self.today = datetime.now().strftime('%Y%m%d_%H%M')      # 精确到分钟
        self.today_date = datetime.now().strftime('%Y%m%d')      # 用于目录
        self.image_results: List[ImageResult] = []
        ensure_dirs()
    
    def get_latest_versions(self, components: Dict) -> Dict:
        """获取所有组件的最新版本"""
        print_separator("获取最新版本信息")
        
        for name, component in components.items():
            print(f"{ICON_ARROW} 正在检查 {component['name']} 的版本...")
            
            image_path = component['image'].replace('docker.io/', '')
            exclude_pattern = component.get('exclude_pattern')
            versions = self.docker_api.get_versions(
                image_path, 
                component['tag_pattern'], 
                exclude_pattern,
                component['version_type'],
                self.logger
            )
            
            component['latest_version'] = versions
            if versions:
                if component['version_type'] == 'multiple':
                    print(f"  {ICON_CHECK} {component['name']} 可用版本: {COLOR_GREEN}{', '.join(versions)}{COLOR_RESET}")
                else:
                    print(f"  {ICON_CHECK} {component['name']}: {COLOR_GREEN}{versions[0]}{COLOR_RESET}")
            else:
                print(f"  {ICON_CROSS} {component['name']}: {COLOR_RED}获取失败{COLOR_RESET}")
        
        return components
    

    def check_updates(self, components: Dict) -> Dict:
        """检查需要更新的组件"""
        print_separator("版本比较")
        
        # 获取历史版本文件
        history_file = self.version_manager.get_latest_history_file()
        old_versions = {}
        
        if not history_file:
            print(f"{ICON_WARNING} 未找到历史版本文件")
            choice = input(f"{ICON_INFO} 是否将历史版本文件放入 data/versions 目录? (y/n): ").lower().strip()
            
            if choice == 'y':
                print(f"{ICON_INFO} 请将历史版本文件放入: {VERSIONS_DIR}")
                input(f"{ICON_INFO} 放置完成后按回车键继续...")
                history_file = self.version_manager.get_latest_history_file()
                
                if not history_file:
                    print(f"{ICON_WARNING} 未检测到历史版本文件，将获取所有组件的最新版本")
                else:
                    print(f"{ICON_INFO} 使用历史版本文件: {history_file.name}")
                    old_versions = self.version_manager.load_history_versions(history_file)
        else:
            print(f"{ICON_INFO} 使用历史版本文件: {history_file.name}")
            old_versions = self.version_manager.load_history_versions(history_file)
        
        updates_needed = {}
        # 定义表格宽度
        col_widths = {
            'component': 18,
            'old_version': 40,
            'new_version': 40,
            'status': 10
        }
        
        # 显示表格头部
        header = (
            f"{pad_string('组件', col_widths['component'])}│ "
            f"{pad_string('历史版本', col_widths['old_version'])}│ "
            f"{pad_string('最新版本', col_widths['new_version'])}│ "
            f"{pad_string('状态', col_widths['status'])}"
        )
        total_width = sum(col_widths.values()) + 11
        print(f"\n{COLOR_CYAN}{header}{COLOR_RESET}")
        print(f"{COLOR_CYAN}{'─' * total_width}{COLOR_RESET}")
        
        for name, component in components.items():
            image_name = os.path.basename(component['image'])
            old_version_map = old_versions.get(image_name, {})
            versions = component.get('latest_version', [])
            
            if not versions:
                continue
            
            if component['version_type'] == 'multiple':
                # 按主版本号分组比较
                version_groups = {}
                for version in versions:
                    major = get_major_version(version)
                    if major not in version_groups:
                        version_groups[major] = []
                    version_groups[major].append(version)
                
                selected_versions = []
                for major, group in version_groups.items():
                    group.sort(key=version_key)
                    latest_in_group = group[-1]  # 获取该主版本号下的最新版本
                    old_version = old_version_map.get(major, "无")
                    
                    if not old_version or old_version == "无" or latest_in_group != old_version:
                        status = f"{COLOR_YELLOW}需要更新{COLOR_RESET}"
                        selected_versions.append(latest_in_group)
                    else:
                        status = f"{COLOR_GREEN}无需更新{COLOR_RESET}"
                    
                    # 显示表格行，保留颜色代码
                    row = (
                        f"{pad_string(component['name'], col_widths['component'])}│ "
                        f"{pad_string(old_version, col_widths['old_version'])}│ "
                        f"{pad_string(latest_in_group, col_widths['new_version'])}│ "
                        f"{status}"
                    )
                    print(row)
                
                if selected_versions:
                    component['latest_version'] = selected_versions
                    updates_needed[name] = component
            else:
                # 对于只需要最新版本的组件
                latest_version = versions[0]
                old_version = list(old_version_map.values())[0] if old_version_map else "无"
                
                if latest_version != "获取失败":
                    if not old_version or old_version == "无" or latest_version != old_version:
                        status = f"{COLOR_YELLOW}需要更新{COLOR_RESET}"
                        updates_needed[name] = component
                    else:
                        status = f"{COLOR_GREEN}无需更新{COLOR_RESET}"
                    
                    row = (
                        f"{pad_string(component['name'], col_widths['component'])}│ "
                        f"{pad_string(old_version, col_widths['old_version'])}│ "
                        f"{pad_string(latest_version, col_widths['new_version'])}│ "
                        f"{status}"
                    )
                    print(row)
        
        # 总是保存版本文件，即使没有历史文件
        latest_file = self.version_manager.save_latest_versions(components)
        print(f"\n{ICON_CHECK} 最新版本文件已保存: {latest_file.name}")
        
        if updates_needed:
            update_file = self.version_manager.save_update_list(updates_needed)
            print(f"{ICON_CHECK} 更新列表已保存: {update_file.name}")
            print(f"\n{ICON_INFO} 找到 {len(updates_needed)} 个需要处理的组件")
        else:
            print(f"\n{ICON_INFO} 无需处理任何组件！")
        
        return updates_needed
    
    def process_images(self, updates_needed: Dict):
        """处理镜像的拉取和导出"""
        if not updates_needed:
            return
        
        print_separator("处理镜像")
        
        total_tasks = sum(len(component['latest_version']) if isinstance(component['latest_version'], list) 
                         else 1 for component in updates_needed.values()) * 2  # 两个架构
        current_task = 0
        
        # 收集预期的镜像列表
        expected_images = set()
        for name, component in updates_needed.items():
            image_name = component['image']
            versions = component['latest_version']
            
            if not versions:
                continue
            
            if not isinstance(versions, list):
                versions = [versions]
            
            for version in versions:
                for arch in ['amd64', 'arm64']:
                    expected_images.add(f"{image_name}:{version}:{arch}")
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            
            for name, component in updates_needed.items():
                image_name = component['image']
                versions = component['latest_version']
                
                if not versions:
                    continue
                
                if not isinstance(versions, list):
                    versions = [versions]
                
                for version in versions:
                    full_image_name = f"{image_name}:{version}"
                    
                    for arch in ['amd64', 'arm64']:
                        output_dir = IMAGES_DIR / self.today_date / arch
                        output_dir.mkdir(parents=True, exist_ok=True)
                        
                        image_filename = f"{os.path.basename(image_name)}_{version}_{arch}.tar.gz"
                        image_path = output_dir / image_filename
                        
                        future = executor.submit(
                            self._process_single_image,
                            full_image_name,
                            image_path,
                            arch
                        )
                        futures.append(future)
            
            # 等待所有任务完成
            for future in futures:
                try:
                    future.result()
                    current_task += 1
                    print(f"{ICON_ARROW} 进度: {current_task}/{total_tasks}")
                except Exception as e:
                    self.logger.error(f"{ICON_CROSS} 处理镜像时出错: {str(e)}")
        
        # 验证镜像文件
        self._validate_images(expected_images)
        
        # 生成统计报告和手动命令
        self._generate_summary_report()
        
        print(f"\n{ICON_CHECK} 所有镜像已保存到: {IMAGES_DIR / self.today}")
    
    def _process_single_image(self, full_image_name: str, image_path: Path, arch: str):
        """处理单个镜像的拉取和导出"""
        result = ImageResult(
            image_name=full_image_name.split(':')[0],
            version=full_image_name.split(':')[1],
            arch=arch
        )
        result.file_path = image_path
        
        try:
            # 拉取镜像
            if self.docker_manager.pull_image(full_image_name, arch):
                result.pull_success = True
                # 导出镜像
                self.docker_manager.export_image(full_image_name, image_path, arch)
                result.export_success = True
            else:
                result.error_message = "拉取镜像失败"
        except Exception as e:
            result.error_message = str(e)
            self.logger.error(f"[{arch}] {ICON_CROSS} 处理镜像失败: {full_image_name}, {str(e)}")
        
        self.image_results.append(result)
    
    def _validate_images(self, expected_images: Set[str]):
        """验证生成的镜像文件是否与预期一致"""
        print_separator("镜像文件验证")
        
        # 扫描实际生成的文件
        actual_files = set()
        for arch in ['amd64', 'arm64']:
            arch_dir = IMAGES_DIR / self.today / arch
            if arch_dir.exists():
                for file in arch_dir.glob("*.tar.gz"):
                    # 从文件名解析镜像信息
                    parts = file.stem.split('_')
                    if len(parts) >= 3:
                        # 重建镜像名和版本
                        name_parts = parts[:-2]  # 除了最后两个部分（版本和架构）
                        version = parts[-2]
                        arch_from_file = parts[-1]
                        
                        if arch_from_file == arch:
                            # 根据组件配置重建完整镜像名
                            for component in COMPONENTS_CONFIG.values():
                                if os.path.basename(component['image']) == '_'.join(name_parts):
                                    image_key = f"{component['image']}:{version}:{arch}"
                                    actual_files.add(image_key)
                                    break
        
        # 比较预期和实际
        missing_files = expected_images - actual_files
        unexpected_files = actual_files - expected_images
        
        print(f"{ICON_INFO} 预期镜像文件数量: {len(expected_images)}")
        print(f"{ICON_INFO} 实际镜像文件数量: {len(actual_files)}")
        
        if missing_files:
            print(f"\n{ICON_CROSS} 缺失的镜像文件 ({len(missing_files)} 个):")
            for missing in sorted(missing_files):
                image_name, version, arch = missing.rsplit(':', 2)
                print(f"  - {os.path.basename(image_name)}:{version} ({arch})")
        
        if unexpected_files:
            print(f"\n{ICON_WARNING} 意外的镜像文件 ({len(unexpected_files)} 个):")
            for unexpected in sorted(unexpected_files):
                image_name, version, arch = unexpected.rsplit(':', 2)
                print(f"  - {os.path.basename(image_name)}:{version} ({arch})")
        
        if not missing_files and not unexpected_files:
            print(f"{ICON_CHECK} 镜像文件验证通过，所有预期文件都已生成")
    
    def _generate_summary_report(self):
        """生成统计报告和手动命令"""
        print_separator("处理结果统计")
        
        # 统计结果
        total_results = len(self.image_results)
        successful_results = [r for r in self.image_results if r.pull_success and r.export_success]
        failed_results = [r for r in self.image_results if not (r.pull_success and r.export_success)]
        
        print(f"{ICON_INFO} 总计处理: {total_results} 个镜像")
        print(f"{ICON_CHECK} 成功处理: {COLOR_GREEN}{len(successful_results)}{COLOR_RESET} 个")
        print(f"{ICON_CROSS} 失败处理: {COLOR_RED}{len(failed_results)}{COLOR_RESET} 个")
        
        if failed_results:
            # 显示失败详情
            print(f"\n{COLOR_RED}失败的镜像详情:{COLOR_RESET}")
            for result in failed_results:
                status = ""
                if not result.pull_success:
                    status = "拉取失败"
                elif not result.export_success:
                    status = "导出失败"
                
                print(f"  {ICON_CROSS} [{result.arch}] {os.path.basename(result.image_name)}:{result.version} - {status}")
                if result.error_message:
                    print(f"    错误: {result.error_message}")
            
            # 生成手动命令文件
            manual_commands = generate_manual_commands(failed_results, self.today_date)
            if manual_commands:
                commands_file = LOGS_DIR / f"manual_commands_{self.today}.sh"
                with open(commands_file, 'w', encoding='utf-8') as f:
                    f.write(manual_commands)
                
                # 设置执行权限
                try:
                    os.chmod(commands_file, 0o755)
                except Exception:
                    pass
                
                print(f"\n{ICON_INFO} 手动拉取命令已生成: {commands_file}")
                print(f"{ICON_ARROW} 可以执行以下命令来处理失败的镜像:")
                print(f"  chmod +x {commands_file}")
                print(f"  {commands_file}")
        
        # 保存详细报告
        report_file = LOGS_DIR / f"processing_report_{self.today}.json"
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'total_processed': total_results,
            'successful_count': len(successful_results),
            'failed_count': len(failed_results),
            'successful_images': [
                {
                    'image': f"{result.image_name}:{result.version}",
                    'arch': result.arch,
                    'file_path': str(result.file_path) if result.file_path else None
                }
                for result in successful_results
            ],
            'failed_images': [
                {
                    'image': f"{result.image_name}:{result.version}",
                    'arch': result.arch,
                    'pull_success': result.pull_success,
                    'export_success': result.export_success,
                    'error_message': result.error_message
                }
                for result in failed_results
            ]
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"{ICON_INFO} 详细处理报告已保存: {report_file}")
    
    def run(self):
        """运行主程序"""
        try:
            print_banner()
            start_time = datetime.now()
            
            # 获取组件配置
            components = COMPONENTS_CONFIG.copy()
            
            print(f"{COLOR_YELLOW}配置的组件列表:{COLOR_RESET}")
            for component in components.values():
                print(f"  {ICON_COMPONENT} {component['name']} ({component['image']})")
            
            # 获取最新版本
            components = self.get_latest_versions(components)
            
            # 检查更新
            updates_needed = self.check_updates(components)
            
            # 处理镜像
            self.process_images(updates_needed)
            
            # 显示总结
            end_time = datetime.now()
            duration = end_time - start_time
            
            print_separator("执行总结")
            print(f"{ICON_INFO} 执行时间: {duration}")
            print(f"{ICON_INFO} 检查组件数: {len(components)}")
            
            if updates_needed:
                print(f"{ICON_WARNING} 需要处理: {len(updates_needed)} 个组件")
                for component in updates_needed.values():
                    versions = component['latest_version']
                    if isinstance(versions, list):
                        versions_str = ', '.join(versions)
                    else:
                        versions_str = versions
                    print(f"  {ICON_COMPONENT} {component['name']} ({versions_str})")
                print(f"{ICON_CHECK} 镜像文件保存至: data/images/{self.today_date}/")
            else:
                print(f"{ICON_INFO} 无需处理任何组件")
            
            print(f"\n{ICON_SUCCESS} 任务完成！")
            return 0
            
        except KeyboardInterrupt:
            print(f"\n{ICON_CROSS} 操作被用户中断")
            return 1
        except Exception as e:
            self.logger.error(f"{ICON_CROSS} 程序执行出错: {str(e)}")
            return 1

# ==================== 清理工具 ====================

def clean_cache():
    """清理Python缓存文件"""
    print(f"{COLOR_YELLOW}正在清理Python缓存...{COLOR_RESET}")
    for root, dirs, files in os.walk('.'):
        # 删除 __pycache__ 目录
        for dir_name in dirs:
            if dir_name == "__pycache__":
                cache_dir = Path(root) / dir_name
                shutil.rmtree(cache_dir, ignore_errors=True)
                print(f"{ICON_CHECK} 已删除: {cache_dir}")
        
        # 删除 .pyc 文件
        for file_name in files:
            if file_name.endswith('.pyc'):
                pyc_file = Path(root) / file_name
                pyc_file.unlink(missing_ok=True)
                print(f"{ICON_CHECK} 已删除: {pyc_file}")

def clean_all():
    """清理所有临时文件"""
    print(f"{COLOR_YELLOW}正在执行全面清理...{COLOR_RESET}")

    clean_cache()

    if IMAGES_DIR.exists():
        shutil.rmtree(IMAGES_DIR, ignore_errors=True)
        print(f"{ICON_CHECK} 已清理: {IMAGES_DIR}")

    # 清理今天所有时间点的版本文件
    today_date = datetime.now().strftime('%Y%m%d')
    if VERSIONS_DIR.exists():
        for file in VERSIONS_DIR.iterdir():
            if (file.name.startswith(f"latest-{today_date}") or
                file.name.startswith(f"update-{today_date}")):
                file.unlink()
                print(f"{ICON_CHECK} 已删除: {file}")

    if LOGS_DIR.exists():
        for log_file in LOGS_DIR.glob("*.log"):
            log_file.unlink()
            print(f"{ICON_CHECK} 已删除: {log_file}")

    print(f"{ICON_SUCCESS} 清理完成!")

# ==================== 命令行接口 ====================

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(
        description='Docker镜像离线导出工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py              # 正常模式
  python main.py -D           # 调试模式
  python main.py --clean      # 清理模式
  python main.py --clean-all  # 全面清理
        """
    )
    
    parser.add_argument('-D', '--debug', 
                       action='store_true',
                       help='启用调试模式，显示详细日志')
    parser.add_argument('--clean', 
                       action='store_true',
                       help='清理Python缓存文件')
    parser.add_argument('--clean-all', 
                       action='store_true',
                       help='清理所有临时文件和缓存')
    
    args = parser.parse_args()
    
    try:
        if args.clean_all:
            clean_all()
            return 0
        elif args.clean:
            clean_cache()
            return 0
        else:
            exporter = ImageExporter(debug=args.debug)
            return exporter.run()
    
    except KeyboardInterrupt:
        print(f"\n{ICON_CROSS} 程序被用户中断")
        return 1
    except Exception as e:
        print(f"{ICON_CROSS} 程序执行出错: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())