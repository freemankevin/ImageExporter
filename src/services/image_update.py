import os
from datetime import datetime
from src.utils.logger import logger
from src.utils.paths import get_version_file_path
from rich.console import Console
from rich.table import Table
from src.api.docker_hub import get_latest_ik_version, get_es_compatible_version, get_latest_version

console = Console()

__all__ = ['ImageUpdateService']  # 确保类被正确导出

class ImageUpdateService:
    def __init__(self):
        self.today = datetime.now().strftime("%Y%m%d")
        
    def compare_and_update(self, components):
        """比较版本并输出需要更新的镜像"""
        try:
            # 1. 首先获取 IK 插件最新版本
            ik_version = get_latest_ik_version()
            if not ik_version:
                return {}
            
            # 2. 根据 IK 版本确定 ES 兼容版本
            es_version = get_es_compatible_version(ik_version)
            if not es_version:
                return {}
            
            # 3. 更新 ES 组件的最新版本
            components['elasticsearch']['latest_version'] = es_version
            
            # 4. 获取其他组件的最新版本
            for name, component in components.items():
                if name != 'elasticsearch':
                    latest = get_latest_version(component['image'], component['tag_pattern'])
                    if latest:
                        component['latest_version'] = latest
            
            # 5. 获取历史版本文件
            history_versions = self._find_latest_history_version()
            if not history_versions:
                return {}
            
            # 6. 加载历史版本信息
            old_versions = {}
            with open(history_versions, 'r') as f:
                for line in f:
                    if line.strip():
                        image_path = line.strip()
                        image_parts = image_path.split('/')
                        name_and_tag = image_parts[-1].split(':')
                        name = name_and_tag[0]
                        version = name_and_tag[1]
                        for comp_name, comp in components.items():
                            if name == comp['name']:
                                old_versions[comp_name] = version
                                break
            
            # 7. 创建更新检查结果表格
            table = Table(title="版本更新检查结果")
            table.add_column("组件", style="cyan")
            table.add_column("当前版本", style="yellow")
            table.add_column("最新版本", style="green")
            table.add_column("状态", style="magenta")
            
            updates_needed = {}
            for name, component in components.items():
                old_version = old_versions.get(name)
                latest_version = component['latest_version']
                
                if latest_version:
                    status = "无需更新" if old_version == latest_version else "需要更新"
                    table.add_row(
                        component['name'],
                        old_version or "无",
                        latest_version,
                        status
                    )
                    
                    if not old_version or latest_version != old_version:
                        updates_needed[name] = latest_version
            
            # 8. 只显示表格
            console.print(table)
            
            # 9. 保存最新版本列表
            if updates_needed:
                latest_file = get_version_file_path(f"latest-{self.today}.txt")
                with open(latest_file, 'w') as f:
                    for name, component in components.items():
                        if component['latest_version']:
                            f.write(f"{component['image']}:{component['latest_version']}\n")
            
            return updates_needed
            
        except Exception as e:
            logger.error(f"检查更新时出错: {str(e)}")
            raise
        
    def _get_all_latest_versions(self, components):
        """获取所有组件的最新版本"""
        return {name: component['latest_version'] 
                for name, component in components.items()}
        
    def _find_latest_history_version(self):
        """查找最近的历史版本文件"""
        try:
            version_dir = get_version_file_path("")
            history_files = []
            
            for file in os.listdir(version_dir):
                if file.startswith("latest-") and file != f"latest-{self.today}.txt":
                    file_date = file.split("-")[1].split(".")[0]
                    history_files.append((file_date, os.path.join(version_dir, file)))
            
            if not history_files:
                return None
                
            history_files.sort(reverse=True)
            return history_files[0][1]
            
        except Exception as e:
            logger.error(f"查找历史版本文件时出错: {str(e)}")
            return None