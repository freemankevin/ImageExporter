#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日志配置模块"""

import logging
from datetime import datetime
from typing import Optional

from rich.logging import RichHandler
from rich.console import Console

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

_shared_console: Optional[Console] = None


def get_console() -> Console:
    """获取共享的 rich Console 实例"""
    global _shared_console
    if _shared_console is None:
        _shared_console = Console()
    return _shared_console


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


class QuietRichHandler(RichHandler):
    """静默的 Rich 日志处理器，用于在进度条运行时抑制控制台输出"""
    
    def __init__(self, *args, quiet: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self._quiet = quiet
    
    def set_quiet(self, quiet: bool):
        """设置是否静默控制台输出"""
        self._quiet = quiet
    
    def emit(self, record):
        if self._quiet:
            return
        super().emit(record)


def setup_logger(debug: bool = False, quiet_console: bool = False) -> logging.Logger:
    """设置日志记录器
    
    Args:
        debug: 是否启用调试模式
        quiet_console: 是否静默控制台输出（用于进度条运行时）
    """
    logger = logging.getLogger('ImageExporter')
    logger.handlers.clear()
    
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)
    
    ensure_dirs()
    log_file = LOGS_DIR / f"exporter_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(
        fmt='%(asctime)s │ %(levelname)-8s │ %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(file_handler)
    
    console = get_console()
    rich_handler = QuietRichHandler(
        console=console,
        show_path=False,
        show_time=True,
        quiet=quiet_console
    )
    rich_handler.setFormatter(logging.Formatter(fmt='%(message)s'))
    logger.addHandler(rich_handler)
    
    logger.propagate = False
    return logger