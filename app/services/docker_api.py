#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""容器镜像 API服务 - 支持 GHCR via GitHub API"""

import os
import re
import logging
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

from app.utils.helpers import version_key

load_dotenv(Path(__file__).parent.parent.parent / '.env')


class ContainerRegistryAPI:
    """容器镜像仓库 API客户端 - 支持 GHCR via GitHub API"""
    
    def __init__(self):
        self.session = self._create_session()
        self.github_token = os.getenv('GHCR_TOKEN') or os.getenv('PAT_TOKEN')
        
        if self.github_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.github_token}',
                'Accept': 'application/vnd.github+json'
            })
    
    def _create_session(self) -> requests.Session:
        """创建带重试策略的会话"""
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_redirect=False,
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retries, pool_maxsize=10)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        return session
    
    def get_versions(self, repository: str, tag_pattern: str, 
                     exclude_pattern: Optional[str], version_type: str,
                     logger: logging.Logger) -> List[str]:
        """获取符合指定模式的所有版本或最新版本
        
        repository 格式: freemankevin/library/nginx 或 freemankevin/minio/aistor/minio
        使用 GitHub Packages API 查询 GHCR 镜像版本
        
        注意: GitHub Packages 中包名使用 __ 替代 /
        例如: library/nginx -> library__nginx
        """
        try:
            if not self.github_token:
                logger.error("未配置 GitHub Token，无法查询 GHCR 镜像版本")
                return []
            
            matching_tags = []
            
            parts = repository.split('/')
            if len(parts) < 2:
                logger.error(f"无效的镜像路径: {repository}")
                return []
            
            owner = parts[0]
            package_path = '/'.join(parts[1:])
            package_name = quote(package_path, safe='')
            
            url = f"https://api.github.com/users/{owner}/packages/container/{package_name}/versions"
            params = {'per_page': 100, 'state': 'active'}
            
            logger.debug(f"获取 GHCR 标签列表: {repository} -> {package_name}")
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 404:
                logger.error(f"镜像不存在或无权限访问: {repository}")
                return []
            
            if response.status_code == 401:
                logger.error(f"GitHub Token 无效或权限不足: {repository}")
                return []
            
            response.raise_for_status()
            data = response.json()
            
            for version_info in data:
                metadata = version_info.get('metadata', {})
                tags = metadata.get('container', {}).get('tags', [])
                
                for tag_name in tags:
                    if not re.match(tag_pattern, tag_name):
                        continue
                    if exclude_pattern and re.match(exclude_pattern, tag_name):
                        continue
                    matching_tags.append(tag_name)
            
            logger.debug(f"找到 {len(matching_tags)} 个匹配标签: {repository}")
            
            if not matching_tags:
                logger.error(f"未找到符合模式的标签: {repository}")
                return []
            
            matching_tags = list(set(matching_tags))
            
            if version_type == 'multiple':
                matching_tags.sort(key=version_key)
                return matching_tags
            else:
                if 'RELEASE' in tag_pattern:
                    matching_tags.sort(key=version_key)
                    return [matching_tags[-1]]
                elif 'management-alpine' in tag_pattern:
                    matching_tags.sort(key=lambda v: version_key(v.split('-')[0]))
                elif tag_pattern.startswith('^v'):
                    matching_tags.sort(key=lambda v: version_key(v[1:]))
                else:
                    matching_tags.sort(key=version_key)
                return [matching_tags[-1]]
                
        except Exception as e:
            logger.error(f"获取版本失败 {repository}: {str(e)}")
            return []