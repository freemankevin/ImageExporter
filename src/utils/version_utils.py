import json
import os
import re
from src.utils.logger import logger

def version_key(version_str):
    """将版本号字符串转换为可比较的元组
    
    Args:
        version_str: 版本号字符串，支持多种格式：
            - 标准版本号: "8.16.0"
            - 带v前缀: "v2.4.3"
            - MinIO格式: "RELEASE.2024-12-18T13-15-44Z"
            - 带后缀: "4.0.5-management-alpine"
        
    Returns:
        tuple: 版本号元组
    """
    try:
        if not version_str:
            return (0, 0, 0)
            
        # 处理 MinIO 的版本格式
        if version_str.startswith('RELEASE.'):
            # 提取日期部分并转换为数字
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', version_str)
            if date_match:
                return tuple(map(int, date_match.groups()))
            
        # 移除 'v' 前缀
        if version_str.startswith('v'):
            version_str = version_str[1:]
            
        # 提取主版本号（处理带后缀的版本号）
        version_parts = version_str.split('-')[0]
        
        # 将版本号分割并转换为整数
        parts = []
        for part in version_parts.split('.'):
            try:
                parts.append(int(part))
            except ValueError:
                parts.append(0)
        
        # 确保至少有三个部分
        while len(parts) < 3:
            parts.append(0)
            
        return tuple(parts[:3])
        
    except Exception as e:
        logger.debug(f"版本号格式处理: {version_str} -> {str(e)}")
        return (0, 0, 0)

def load_version_file(file_path):
    """加载版本文件
    
    Args:
        file_path: 版本文件路径
        
    Returns:
        dict: 版本信息字典，格式为 {组件名: 版本号}
    """
    try:
        if not os.path.exists(file_path):
            return {}
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载版本文件失败: {str(e)}")
        return {}

def save_version_file(file_path, versions):
    """保存版本信息到文件
    
    Args:
        file_path: 版本文件路径
        versions: 版本信息字典，格式为 {组件名: 版本号}
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(versions, f, indent=2, ensure_ascii=False)
            
        logger.info(f"版本信息已保存到: {file_path}")
    except Exception as e:
        logger.error(f"保存版本文件失败: {str(e)}")
        raise
