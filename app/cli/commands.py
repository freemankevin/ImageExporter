#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI命令模块"""

import shutil
from datetime import datetime
from pathlib import Path

from app.core.config import IMAGES_DIR, VERSIONS_DIR, LOGS_DIR, PROJECT_ROOT
from app.utils.display import print_banner, print_separator, COLORS, ICONS


def clean_cache():
    """清理Python缓存文件"""
    print(f"{COLORS['YELLOW']}清理Python缓存...{COLORS['RESET']}")
    for root, dirs, files in PROJECT_ROOT.walk():
        for dir_name in dirs:
            if dir_name == "__pycache__":
                cache_dir = Path(root) / dir_name
                shutil.rmtree(cache_dir, ignore_errors=True)
                print(f"{ICONS['CHECK']} 删除: {cache_dir}")
        
        for file_name in files:
            if file_name.endswith('.pyc'):
                pyc_file = Path(root) / file_name
                pyc_file.unlink(missing_ok=True)
                print(f"{ICONS['CHECK']} 删除: {pyc_file}")


def clean_all():
    """清理所有临时文件"""
    print(f"{COLORS['YELLOW']}全面清理...{COLORS['RESET']}")
    
    clean_cache()
    
    if IMAGES_DIR.exists():
        shutil.rmtree(IMAGES_DIR, ignore_errors=True)
        print(f"{ICONS['CHECK']} 清理: {IMAGES_DIR}")
    
    today_date = datetime.now().strftime('%Y%m%d')
    if VERSIONS_DIR.exists():
        for file in VERSIONS_DIR.iterdir():
            if file.name.startswith(f"latest-{today_date}") or file.name.startswith(f"update-{today_date}"):
                file.unlink()
                print(f"{ICONS['CHECK']} 删除: {file}")
    
    if LOGS_DIR.exists():
        for log_file in LOGS_DIR.glob("*.log"):
            log_file.unlink()
            print(f"{ICONS['CHECK']} 删除: {log_file}")
    
    print(f"{ICONS['SUCCESS']} 清理完成!")