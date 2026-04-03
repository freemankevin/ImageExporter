#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""版本管理服务"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from app.core.config import VERSIONS_DIR
from app.utils.helpers import get_major_version
from app.utils.display import ICONS


class VersionManager:
    """版本管理器"""
    
    def __init__(self):
        self.today = datetime.now().strftime('%Y%m%d_%H%M')
        self.today_date = datetime.now().strftime('%Y%m%d')
    
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
                    if timestamp_str != current_timestamp:
                        history_files.append((timestamp_str, file))
            
            if not history_files:
                return None
            
            history_files.sort(reverse=True)
            return history_files[0][1]
            
        except Exception as e:
            print(f"{ICONS['CROSS']} 查找历史版本文件出错: {str(e)}")
            return None
    
    def load_history_versions(self, history_file: Path) -> Dict[str, Dict[str, str]]:
        """加载历史版本信息"""
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
            print(f"{ICONS['CROSS']} 读取历史版本失败: {str(e)}")
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