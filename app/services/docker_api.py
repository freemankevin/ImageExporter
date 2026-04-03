#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Docker Hub API服务"""

import re
import logging
from typing import List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.utils.helpers import version_key


class DockerHubAPI:
    """Docker Hub API客户端"""
    
    def __init__(self):
        self.base_url = "https://registry.hub.docker.com/v2"
        self.session = self._create_session()
    
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
        """获取符合指定模式的所有版本或最新版本"""
        try:
            matching_tags = []
            page = 1
            
            while True:
                url = f"{self.base_url}/repositories/{repository}/tags"
                params = {
                    'page_size': 100,
                    'page': page,
                    'ordering': 'last_updated'
                }
                
                logger.debug(f"获取 {repository} 标签列表，页面: {page}")
                
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                results = data.get('results', [])
                if not results:
                    break
                
                for tag in results:
                    tag_name = tag['name']
                    if not re.match(tag_pattern, tag_name):
                        continue
                    if exclude_pattern and re.match(exclude_pattern, tag_name):
                        continue
                    matching_tags.append(tag_name)
                
                if not data.get('next'):
                    break
                
                page += 1
            
            logger.debug(f"找到 {len(matching_tags)} 个匹配标签: {repository}")
            
            if not matching_tags:
                logger.error(f"未找到符合模式的标签: {repository}")
                return []
            
            if version_type == 'multiple':
                matching_tags.sort(key=version_key)
                return matching_tags
            else:
                if 'RELEASE' in tag_pattern:
                    return [matching_tags[0]]
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