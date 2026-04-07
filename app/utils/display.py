#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""显示工具函数"""

from app.core.logging import COLORS, ICONS


def display_width(s: str) -> int:
    """计算字符串的显示宽度"""
    width = 0
    for char in s:
        width += 2 if ord(char) > 127 else 1
    return width


def pad_string(s: str, width: int) -> str:
    """按显示宽度填充字符串"""
    current_width = display_width(s)
    return s + " " * (width - current_width)


def print_banner():
    """打印程序横幅"""
    banner = f"""
{COLORS['CYAN']}╔════════════════════════════════════════════════════════════════╗
║{COLORS['GREEN']}              DOCKER IMAGE EXPORTER v2.0                      {COLORS['CYAN']}║
║{COLORS['YELLOW']}              Support AMD64 & ARM64 Architecture              {COLORS['CYAN']}║
╚════════════════════════════════════════════════════════════════╝{COLORS['RESET']}
"""
    print(banner)


def print_separator(title: str = ""):
    """打印分隔符"""
    if title:
        print(f"\n{COLORS['BLUE']}{'─' * 20} {title} {'─' * 20}{COLORS['RESET']}")
    else:
        print(f"{COLORS['BLUE']}{'─' * 60}{COLORS['RESET']}")