import re
import yaml
import os

# 默认配置
DEFAULT_CONFIG = {
    'docker_hub_api_url': "https://hub.docker.com/v2",
    'ik_plugin_url': "https://release.infinilabs.com/analysis-ik/stable/",
    'timeout': 300,
    'max_retries': 3,
    'retry_delay': 2,
    'log_level': 'INFO',
    'output_dir': 'data/output',  # 修改为正确的输出路径
    'concurrent_downloads': 2
}

# 组件配置
DEFAULT_COMPONENTS = {
    "docker.io/library/elasticsearch": lambda x: x.startswith('8.'),
    "docker.io/minio/minio": lambda x: not x.endswith(('.fips', '-cpuv1')),
    "docker.io/nacos/nacos-server": lambda x: not x.endswith('-slim'),
    "docker.io/library/nginx": lambda x: re.match(r'^\d+\.\d+\.\d+$', x),
    "docker.io/library/rabbitmq": lambda x: x.endswith('-management-alpine') and not ('beta' in x or 'rc' in x),
    "docker.io/library/redis": lambda x: re.match(r'^\d+\.\d+\.\d+$', x),
    "docker.io/kartoza/geoserver": lambda x: re.match(r'^\d+\.\d+\.\d+$', x)
}

def load_config():
    """加载配置文件，如果不存在则使用默认配置"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            user_config = yaml.safe_load(f)
            return {**DEFAULT_CONFIG, **user_config}
    return DEFAULT_CONFIG

# 导出配置
CONFIG = load_config()
COMPONENTS = DEFAULT_COMPONENTS