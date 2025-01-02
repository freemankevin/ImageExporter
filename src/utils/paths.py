import os
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 定义各种路径
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
VERSIONS_DIR = os.path.join(DATA_DIR, "versions")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

def get_version_file_path(filename=""):
    """获取版本文件的完整路径
    
    Args:
        filename: 版本文件名，如果为空则返回版本目录路径
        
    Returns:
        str: 版本文件的完整路径
    """
    # 确保版本目录存在
    os.makedirs(VERSIONS_DIR, exist_ok=True)
    
    if not filename:
        return VERSIONS_DIR
    return os.path.join(VERSIONS_DIR, filename)

def get_output_dir(date_str=None):
    """获取输出目录路径
    
    Args:
        date_str: 日期字符串（YYYYMMDD），如果为空则使用 output 目录
        
    Returns:
        str: 输出目录的完整路径
    """
    if not date_str:
        return OUTPUT_DIR
    
    output_dir = os.path.join(OUTPUT_DIR, date_str)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def ensure_dirs():
    """确保所有必要的目录都存在"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(VERSIONS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)