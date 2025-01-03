import requests
import re
from bs4 import BeautifulSoup
from src.utils.docker_utils import logger

class DockerHubAPI:
    def __init__(self, base_url):
        self.base_url = base_url
        self.logger = logger

    def get_latest_version(self, repository, tag_pattern):
        """获取符合指定模式的最新版本"""
        url = f"{self.base_url}/repositories/{repository}/tags"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                # 筛选符合模式的版本
                matching_tags = [
                    tag['name'] for tag in data['results']
                    if re.match(tag_pattern, tag['name'])
                ]
                if matching_tags:
                    return matching_tags[0]
                else:
                    self.logger.error(f"No matching tags found for {repository} with pattern {tag_pattern}")
                    return None
            else:
                self.logger.error(f"No tags found for {repository}")
                return None
        else:
            logger.error(f"[bold red]Failed to fetch latest version for {repository}: Status {response.status_code}[/bold red]")
            return None

class InfiniLabsAPI:
    def __init__(self):
        self.base_url = "https://release.infinilabs.com/analysis-ik/stable/"

    def get_latest_version(self):
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
            
            # 使用 BeautifulSoup 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有链接
            links = soup.find_all('a')
            
            # 提取版本号
            versions = []
            pattern = re.compile(r'elasticsearch-analysis-ik-(\d+\.\d+\.\d+)\.zip')
            
            for link in links:
                href = link.get('href')
                if href:
                    match = pattern.match(href)
                    if match:
                        versions.append(match.group(1))
            
            if not versions:
                return None
                
            # 按版本号排序
            versions.sort(key=lambda v: [int(x) for x in v.split('.')])
            return versions[-1]  # 返回最新版本
            
        except Exception as e:
            logger.error(f"从 InfiniLabs 获取版本信息失败: {str(e)}")
            return None

class Config:
    _instance = None
    _default_config = {
        "docker_hub_api_url": "https://hub.docker.com/v2",
        "timeout": 300,
        "max_retries": 3,
        "retry_delay": 2,
        "log_level": "INFO",
        "output_dir": "output",
        "concurrent_downloads": 2,
        "components": {
            'elasticsearch': {
                'name': 'elasticsearch',
                'image': 'docker.io/library/elasticsearch',
                'tag_pattern': r'^[0-9]+\.[0-9]+\.[0-9]+$',
                'latest_version': None
            },
            'minio': {
                'name': 'minio',
                'image': 'docker.io/minio/minio',
                'tag_pattern': r'^RELEASE\.[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}-[0-9]{2}-[0-9]{2}Z$',
                'latest_version': None
            },
            'nacos': {
                'name': 'nacos',
                'image': 'docker.io/nacos/nacos-server',
                'tag_pattern': r'^v[0-9]+\.[0-9]+\.[0-9]+$',
                'latest_version': None
            },
            'nginx': {
                'name': 'nginx',
                'image': 'docker.io/library/nginx',
                'tag_pattern': r'^\d+\.\d+\.\d+$',
                'latest_version': None
            },
            'rabbitmq': {
                'name': 'rabbitmq',
                'image': 'docker.io/library/rabbitmq',
                'tag_pattern': r'^[0-9]+\.[0-9]+\.[0-9]+-management-alpine$',
                'latest_version': None
            },
            'redis': {
                'name': 'redis',
                'image': 'docker.io/library/redis',
                'tag_pattern': r'^[0-9]+\.[0-9]+\.[0-9]+$',
                'latest_version': None
            },
            'geoserver': {
                'name': 'geoserver',
                'image': 'docker.io/kartoza/geoserver',
                'tag_pattern': r'^[0-9]+\.[0-9]+\.[0-9]+$',
                'latest_version': None
            }
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.config = cls._default_config.copy()
            cls._instance.docker_hub = DockerHubAPI(cls._default_config["docker_hub_api_url"])
            cls._instance.infinilabs = InfiniLabsAPI()
            
            # 验证组件配置
            for name, component in cls._instance.config['components'].items():
                assert isinstance(component, dict), f"组件 {name} 必须是字典类型"
                assert all(key in component for key in ['name', 'image', 'tag_pattern', 'latest_version']), \
                    f"组件 {name} 缺少必要的配置项"
        
        return cls._instance
    
    def get(self, key, default=None):
        return self.config.get(key, default)

    def get_latest_version(self, component_name):
        """获取组件的最新版本"""
        component = self.config['components'].get(component_name)
        if not component:
            return None

        if component_name == 'analysis-ik':
            return self.infinilabs.get_latest_version()
        else:
            image_path = component['image'].replace('docker.io/', '')
            return self.docker_hub.get_latest_version(image_path, component['tag_pattern'])

# 创建全局配置实例
CONFIG = Config()