# 定义组件配置
COMPONENTS = {
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
        'tag_pattern': r'^[0-9]+\.[0-9]+\.[0-9]+$',
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

# 验证组件配置
for name, component in COMPONENTS.items():
    assert isinstance(component, dict), f"组件 {name} 必须是字典类型"
    assert all(key in component for key in ['name', 'image', 'tag_pattern', 'latest_version']), \
        f"组件 {name} 缺少必要的配置项" 