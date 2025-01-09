import requests
import re
from bs4 import BeautifulSoup
from src.utils.docker_utils import logger
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class DockerHubAPI:
    def __init__(self, base_url):
        self.base_url = base_url
        self.logger = logger
        
        # 配置更强大的重试策略
        self.session = requests.Session()
        retries = Retry(
            total=5,  # 增加重试次数
            backoff_factor=1,  # 增加退避时间
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"],  # 明确允许的方法
            raise_on_redirect=False,
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retries, pool_maxsize=10)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

    def get_latest_version(self, repository, tag_pattern):
        """获取符合指定模式的最新版本"""
        try:
            matching_tags = []
            page = 1
            while True:
                url = f"https://registry.hub.docker.com/v2/repositories/{repository}/tags?page_size=100&page={page}&ordering=last_updated"
                
                # 调试信息改为 debug 级别
                self.logger.debug(f"Fetching tags from: {url}")
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                results = data.get('results', [])
                if not results:
                    break
                    
                # 筛选符合模式的版本
                for tag in results:
                    if re.match(tag_pattern, tag['name']):
                        matching_tags.append(tag['name'])
                
                # 检查是否有下一页
                if not data.get('next'):
                    break
                    
                page += 1
            
            # 调试信息改为 debug 级别
            self.logger.debug(f"Found {len(matching_tags)} matching tags for {repository}")
            self.logger.debug(f"First 10 matching tags: {matching_tags[:10]}")
            
            if not matching_tags:
                if 'nginx' in repository:
                    self.logger.error(f"No matching tags found for nginx. Pattern: {tag_pattern}")
                return None
            
            # 根据不同的版本格式进行排序
            try:
                if 'RELEASE' in tag_pattern:
                    return matching_tags[0]  # minio 使用时间戳，保持原始顺序
                elif 'management-alpine' in tag_pattern:
                    # rabbitmq 版本号排序
                    matching_tags.sort(key=lambda v: [
                        int(x) for x in v.split('-')[0].split('.')
                    ])
                elif tag_pattern.startswith('^v'):
                    # nacos 版本号排序
                    matching_tags.sort(key=lambda v: [
                        int(x) for x in v[1:].split('.')
                    ])
                else:
                    # 标准版本号排序
                    matching_tags.sort(key=lambda v: [
                        int(x) for x in v.split('-')[0].split('.')  # 处理可能的 -alpine 后缀
                    ])
                return matching_tags[-1]
                
            except Exception as e:
                self.logger.error(f"Error sorting versions for {repository}: {str(e)}")
                # 如果排序失败，至少返回一个匹配的版本
                return matching_tags[0]
                
        except Exception as e:
            self.logger.error(f"Error processing {repository}: {str(e)}")
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
                'tag_pattern': r'^[0-9]+\.[0-9]+\.[0-9]+(?:-alpine)?$',
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