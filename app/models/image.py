#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""镜像结果数据模型"""

from pathlib import Path
from typing import Optional


class ImageResult:
    """镜像处理结果"""
    
    def __init__(self, image_name: str, version: str, arch: str):
        self.image_name = image_name
        self.version = version
        self.arch = arch
        self.full_image_name = f"{image_name}:{version}"
        self.pull_success = False
        self.export_success = False
        self.error_message = ""
        self.file_path: Optional[Path] = None