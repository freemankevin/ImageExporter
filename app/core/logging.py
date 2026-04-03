#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日志配置模块"""

import logging
from datetime import datetime

from app.core.config import LOGS_DIR, ensure_dirs

COLORS = {
    'GREEN': "\033[92m",
    'RED': "\033[91m",
    'YELLOW': "\033[93m",
    'BLUE': "\033[94m",
    'CYAN': "\033[96m",
    'RESET': "\033[0m"
}

ICONS = {
    'CHECK': "✓",
    'CROSS': "✗",
    'INFO': "●",
    'SUCCESS': "★",
    'WARNING': "!",
    'COMPONENT': "◆",
    'ARROW': "→"
}


class ColoredFormatter(logging.Formatter):
    """自定义彩色日志格式化器"""
    
    LEVEL_COLORS = {
        'DEBUG': COLORS['CYAN'],
        'INFO': COLORS['GREEN'],
        'WARNING': COLORS['YELLOW'],
        'ERROR': COLORS['RED'],
        'CRITICAL': COLORS['RED']
    }
    
    def format(self, record):
        level_color = self.LEVEL_COLORS.get(record.levelname, COLORS['RESET'])
        record.levelname_colored = f"{level_color}{record.levelname}{COLORS['RESET']}"
        return super().format(record)


def setup_logger(debug: bool = False) -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger('ImageExporter')
    logger.handlers.clear()
    
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)
    
    formatter = ColoredFormatter(
        fmt='%(asctime)s │ %(levelname)-8s │ %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    ensure_dirs()
    log_file = LOGS_DIR / f"exporter_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(
        fmt='%(asctime)s │ %(levelname)-8s │ %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(file_handler)
    
    logger.propagate = False
    return logger