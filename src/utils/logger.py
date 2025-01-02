import logging
import os
import sys
from datetime import datetime

def setup_logger():
    """配置日志记录器"""
    # 创建logs目录
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # 设置日志文件名（包含日期）
    log_file = os.path.join(log_dir, f'image_exporter_{datetime.now().strftime("%Y%m%d")}.log')
    
    # 创建日志记录器
    logger = logging.getLogger('ImageExporter')
    logger.setLevel(logging.DEBUG)  # 设置为DEBUG级别以捕获所有日志
    
    # 清除已有的处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)  # 文件记录INFO及以上级别
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # 控制台显示INFO及以上级别
    console_handler.setFormatter(logging.Formatter(
        '%(message)s'  # 简化的控制台输出格式
    ))
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 创建全局logger实例
logger = setup_logger()

# 导出logger实例和日志方法
__all__ = ['logger', 'info', 'error', 'warning', 'debug']

# 定义日志方法
def info(msg, *args, **kwargs):
    logger.info(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    logger.error(msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    logger.warning(msg, *args, **kwargs)

def debug(msg, *args, **kwargs):
    logger.debug(msg, *args, **kwargs)