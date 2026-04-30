#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""版本管理服务"""

import json
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
                if file.name.startswith("latest-") and file.suffix in ['.txt', '.json']:
                    timestamp_str = file.stem.replace("latest-", "")
                    if timestamp_str != current_timestamp:
                        history_files.append((timestamp_str, file))
            
            if not history_files:
                return None
            
            history_files.sort(reverse=True)
            return history_files[0][1]
            
        except Exception as e:
            print(f"{ICONS['CROSS']} 查找历史版本文件出错: {str(e)}")
            return None
    
    def load_history_versions(self, history_file: Path) -> Dict[str, Dict[str, Dict]]:
        """加载历史版本信息，包含版本和sha256"""
        old_versions = {}
        try:
            if history_file.suffix == '.json':
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for image_name, versions in data.get('images', {}).items():
                        old_versions[image_name] = {}
                        for major, info in versions.items():
                            old_versions[image_name][major] = {
                                'version': info.get('version'),
                                'sha256': info.get('sha256')
                            }
            else:
                with open(history_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            parts = line.strip().split('|')
                            image_path = parts[0]
                            image_name = os.path.basename(image_path.split(':')[0])
                            version = image_path.split(':')[1]
                            sha256 = parts[1] if len(parts) > 1 else None
                            if image_name not in old_versions:
                                old_versions[image_name] = {}
                            major_version = get_major_version(version)
                            old_versions[image_name][major_version] = {
                                'version': version,
                                'sha256': sha256
                            }
            return old_versions
        except Exception as e:
            print(f"{ICONS['CROSS']} 读取历史版本失败: {str(e)}")
            return {}
    
    def save_latest_versions(self, components: Dict, sha256_records: Dict = None) -> Path:
        """保存最新版本列表，包含sha256"""
        latest_file = VERSIONS_DIR / f"latest-{self.today}.json"
        data = {
            'timestamp': datetime.now().isoformat(),
            'images': {}
        }
        
        for component in components.values():
            if component.get('latest_version'):
                image_name = os.path.basename(component['image'])
                versions = component['latest_version']
                if not isinstance(versions, list):
                    versions = [versions]
                
                if image_name not in data['images']:
                    data['images'][image_name] = {}
                
                for version in versions:
                    major = get_major_version(version)
                    sha256 = None
                    if sha256_records:
                        key = f"{component['image']}:{version}"
                        sha256 = sha256_records.get(key)
                    data['images'][image_name][major] = {
                        'version': version,
                        'sha256': sha256
                    }
        
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return latest_file
    
    def save_update_list(self, updates_needed: Dict) -> Path:
        """保存需要更新的镜像列表"""
        update_file = VERSIONS_DIR / f"update-{self.today}.txt"
        with open(update_file, 'w', encoding='utf-8') as f:
            for component in updates_needed.values():
                if isinstance(component['latest_version'], list):
                    for version in component['latest_version']:
                        f.write(f"{component['image']}:{version}\n")
                else:
                    f.write(f"{component['image']}:{component['latest_version']}\n")
        return update_file