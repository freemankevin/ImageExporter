import os
from pathlib import Path
from src.utils.version_utils import version_key  # 直接导入 version_key 函数
from src.utils.logger import logger

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 定义相对路径
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
VERSIONS_DIR = os.path.join(DATA_DIR, 'versions')
OUTPUT_DIR = os.path.join(DATA_DIR, 'output')

def read_versions_from_file(filename):
    """从文件中读取版本信息
    
    Args:
        filename: 版本文件名
        
    Returns:
        dict: 组件及其版本号的字典
    """
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

def find_previous_version_file():
    """查找最近的版本文件
    
    Returns:
        str: 找到的版本文件名,未找到则返回None
    """
    try:
        if not os.path.exists(VERSIONS_DIR):
            return None
            
        latest_files = [f for f in os.listdir(VERSIONS_DIR) 
                       if f.startswith('latest-') and f.endswith('.txt')]
        if not latest_files:
            return None
            
        # 按日期降序排序
        latest_files.sort(reverse=True)
        if len(latest_files) > 1:
            # 返回第二新的文件（即上一个版本）
            return os.path.join(VERSIONS_DIR, latest_files[1])
        return None
    except Exception as e:
        logger.error(f"查找版本文件出错: {str(e)}")
        return None

def write_versions_to_file(filename, versions):
    """将版本信息写入文件
    
    Args:
        filename: 目标文件名
        versions: 包含组件及版本号的字典
    """
    try:
        full_path = os.path.join(VERSIONS_DIR, filename)
        os.makedirs(VERSIONS_DIR, exist_ok=True)
        
        with open(full_path, 'w') as file:
            for component, version in sorted(versions.items()):
                file.write(f"{component}:{version}\n")
                
    except Exception as e:
        logger.error(f"写入版本文件出错: {str(e)}")

def compare_versions(current_versions, previous_versions):
    """比较版本,找出需要更新的组件
    
    Args:
        current_versions: 当前版本字典
        previous_versions: 之前版本字典
        
    Returns:
        dict: 需要更新的组件及其新版本号
    """
    updates_needed = {}
    try:
        for component, current_version in current_versions.items():
            if component not in previous_versions:
                logger.info(f"发现新组件: {component} ({current_version})")
                updates_needed[component] = current_version
            elif version_key(current_version) > version_key(previous_versions[component]):  # 直接使用导入的函数
                logger.info(f"发现版本更新: {component} ({previous_versions[component]} -> {current_version})")
                updates_needed[component] = current_version
    except Exception as e:
        logger.error(f"比较版本出错: {str(e)}")
    return updates_needed

def get_output_path(date_str, arch):
    """获取输出路径
    
    Args:
        date_str: 日期字符串
        arch: 架构类型(AMD64/ARM64)
        
    Returns:
        str: 输出路径
    """
    output_path = os.path.join(OUTPUT_DIR, date_str, arch)
    os.makedirs(output_path, exist_ok=True)
    return output_path

def init_directories():
    """初始化项目所需的目录结构"""
    os.makedirs(VERSIONS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# 在模块导入时初始化目录
init_directories()