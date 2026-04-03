#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""辅助工具函数"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Tuple, List

from app.core.config import PROJECT_ROOT
from app.models.image import ImageResult
from app.utils.display import ICONS


def version_key(version_str: str) -> Tuple[int, ...]:
    """将版本号字符串转换为可比较的元组"""
    try:
        if not version_str:
            return (0, 0, 0)
        
        if version_str.startswith('RELEASE.'):
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', version_str)
            if date_match:
                return tuple(map(int, date_match.groups()))
        
        if version_str.startswith('v'):
            version_str = version_str[1:]
        
        version_parts = version_str.split('-')[0]
        parts = []
        for part in version_parts.split('.'):
            try:
                parts.append(int(part))
            except ValueError:
                parts.append(0)
        
        while len(parts) < 3:
            parts.append(0)
        
        return tuple(parts[:3])
    except Exception:
        return (0, 0, 0)


def get_major_version(version: str) -> str:
    """获取主版本号"""
    if not version:
        return ""
    return version.split('.')[0]


def generate_manual_commands(failed_results: List[ImageResult], today: str, project_root: Path) -> str:
    """生成手动拉取和导出命令"""
    if not failed_results:
        return ""
    
    commands = [
        "#!/bin/bash",
        "# 手动拉取和导出失败的镜像",
        f"# 生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "# 切换到项目根目录",
        f"cd \"{project_root.as_posix()}\" || exit 1",
        ""
    ]
    
    arch_groups = {}
    for result in failed_results:
        if result.arch not in arch_groups:
            arch_groups[result.arch] = []
        arch_groups[result.arch].append(result)
    
    for arch, results in arch_groups.items():
        commands.append(f"# {arch.upper()} 架构镜像")
        commands.append("")
        
        for result in results:
            image_name = os.path.basename(result.image_name)
            filename = f"{image_name}_{result.version}_{arch}.tar.gz"
            output_dir = f"data/images/{today}/{arch}"
            
            commands.extend([
                f"# 拉取 {result.full_image_name} ({arch})",
                f"docker pull --platform=linux/{arch} {result.full_image_name}",
                "",
                f"# 导出 {result.full_image_name} ({arch})",
                f"mkdir -p \"{output_dir}\"",
                f"docker save {result.full_image_name} --platform=linux/{arch} | gzip > \"{output_dir}/{filename}\"",
                ""
            ])
    
    return "\n".join(commands)