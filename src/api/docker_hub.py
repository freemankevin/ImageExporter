import requests
import re
from src.utils.logger import logger
from src.utils.version_utils import version_key

def get_es_compatible_version(ik_version):
    """根据 IK 插件版本确定兼容的 ES 版本"""
    # IK 插件版本号通常与 ES 主版本号对应
    es_major = ik_version.split('.')[0]
    return get_latest_version(
        'docker.io/library/elasticsearch',
        rf'^{es_major}\.[0-9]+\.[0-9]+$'
    )

def get_latest_ik_version():
    """获取 IK 插件的最新稳定版本"""
    try:
        url = "https://release.infinilabs.com/analysis-ik/stable/"
        response = requests.get(url)
        response.raise_for_status()
        
        # 使用正则表达式查找版本号
        versions = re.findall(r'elasticsearch-analysis-ik-(\d+\.\d+\.\d+)\.zip', response.text)
        if not versions:
            return None
            
        # 按版本号排序并返回最新版本
        return sorted(versions, key=version_key, reverse=True)[0]
    except Exception as e:
        logger.error(f"获取 IK 插件最新版本失败: {str(e)}")
        return None

def get_latest_version(image, tag_pattern):
    """从 Docker Hub 获取最新版本"""
    try:
        # 处理镜像名称
        if image.startswith('docker.io/library/'):
            image = image[len('docker.io/library/'):]
        elif image.startswith('docker.io/'):
            image = image[len('docker.io/'):]
            
        # 构建 API URL
        if '/' in image:
            url = f"https://hub.docker.com/v2/repositories/{image}/tags"
        else:
            url = f"https://hub.docker.com/v2/repositories/library/{image}/tags"
            
        # 获取标签列表
        response = requests.get(url, params={'page_size': 100})
        response.raise_for_status()
        
        # 解析响应
        data = response.json()
        if not data.get('results'):
            return None
            
        # 过滤并排序版本号
        valid_versions = []
        pattern = re.compile(tag_pattern)
        
        for tag in data['results']:
            tag_name = tag['name']
            if pattern.match(tag_name):
                valid_versions.append(tag_name)
                
        if not valid_versions:
            return None
            
        # 按版本号排序并返回最新版本
        return sorted(valid_versions, key=version_key, reverse=True)[0]
        
    except Exception as e:
        logger.error(f"获取镜像 {image} 最新版本失败: {str(e)}")
        return None