#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配置管理模块"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
VERSIONS_DIR = DATA_DIR / "versions"
IMAGES_DIR = DATA_DIR / "images"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_FILE = PROJECT_ROOT / "config.yaml"


class Config:
    """配置管理器"""
    
    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """加载配置文件"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'docker': {
                'timeout': 300,
                'max_retries': 3,
                'retry_delay': 2
            },
            'concurrency': {
                'max_workers': 10,
                'max_global_retries': 100,
                'retry_backoff_factor': 2
            },
            'validation': {
                'min_file_size': 1048576
            },
            'mirror': {
                'enabled': True,
                'ghcr_registry': 'ghcr.io/freemankevin/',
                'original_prefix': 'docker.io/',
                'special_mappings': {}
            },
            'components': {}
        }
    
    @property
    def docker(self) -> Dict[str, Any]:
        return self._config.get('docker', {})
    
    @property
    def concurrency(self) -> Dict[str, Any]:
        return self._config.get('concurrency', {})
    
    @property
    def validation(self) -> Dict[str, Any]:
        return self._config.get('validation', {})
    
    @property
    def mirror(self) -> Dict[str, Any]:
        return self._config.get('mirror', {})
    
    @property
    def components(self) -> Dict[str, Any]:
        return self._config.get('components', {})
    
    @property
    def timeout(self) -> int:
        return self.docker.get('timeout', 300)
    
    @property
    def max_retries(self) -> int:
        return self.docker.get('max_retries', 3)
    
    @property
    def retry_delay(self) -> int:
        return self.docker.get('retry_delay', 2)
    
    @property
    def max_workers(self) -> int:
        return self.concurrency.get('max_workers', 10)
    
    @property
    def max_global_retries(self) -> int:
        return self.concurrency.get('max_global_retries', 100)
    
    @property
    def retry_backoff_factor(self) -> int:
        return self.concurrency.get('retry_backoff_factor', 2)
    
    @property
    def min_file_size(self) -> int:
        return self.validation.get('min_file_size', 1048576)
    
    @property
    def mirror_enabled(self) -> bool:
        return self.mirror.get('enabled', True)
    
    @property
    def ghcr_registry(self) -> str:
        return self.mirror.get('ghcr_registry', 'ghcr.io/freemankevin/')
    
    @property
    def special_mappings(self) -> Dict[str, str]:
        return self.mirror.get('special_mappings', {})

    @property
    def original_prefix(self) -> str:
        return self.mirror.get('original_prefix', 'docker.io/')


config = Config()


def get_mirrored_image(image: str) -> str:
    """获取 GHCR 镜像名称
    
    转换规则：
    1. 检查是否在特殊映射表中
    2. 移除 docker.io/ 前缀
    3. 添加 ghcr.io/freemankevin/ 前缀
    """
    if not config.mirror_enabled:
        return image
    
    special_mappings = config.special_mappings
    if image in special_mappings:
        return special_mappings[image]
    
    if image.startswith(config.original_prefix):
        image_without_prefix = image[len(config.original_prefix):]
        return config.ghcr_registry + image_without_prefix
    
    return image


def ensure_dirs():
    """确保所有必要的目录都存在"""
    for directory in [DATA_DIR, VERSIONS_DIR, IMAGES_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)