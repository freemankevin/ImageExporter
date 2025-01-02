import os
import json
from datetime import datetime
from src.services import image_fetch, image_update, image_pull
from src.utils import file_utils
from src.utils.logger import logger
from src.services.image_update import ImageUpdateService
from src.config.components import COMPONENTS

class ImageManager:
    def __init__(self):
        self.state_file = "state.json"
        self.current_date = datetime.now().strftime('%Y%m%d')
        self.state = self.load_state()

    def load_state(self):
        """从状态文件中加载上次执行的状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("状态文件损坏，将重新开始任务")
                return None
        return None

    def save_state(self, last_step, updates_needed):
        """保存当前状态到状态文件"""
        state = {
            "current_date": self.current_date,
            "last_step": last_step,
            "updates_needed": updates_needed
        }
        with open(self.state_file, "w") as f:
            json.dump(state, f)

    def clean_state(self):
        """清理状态文件"""
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    def check_and_pull_updates(self, verbose=True):
        """检查版本更新并拉取镜像"""
        try:
            if self.state:
                current_date = self.state["current_date"]
                updates_needed = self.state["updates_needed"]
                last_step = self.state["last_step"]
            else:
                current_date = self.current_date
                # 获取最新版本信息
                latest_ik_version = image_fetch.get_latest_ik_plugin(verbose, print_title=True)
                latest_versions = image_fetch.fetch_latest_images(verbose, print_title=True)
                
                # 保存最新版本信息
                current_file_name = f'latest-{current_date}.txt'
                file_utils.write_versions_to_file(current_file_name, latest_versions)
                
                # 比较版本并确定需要更新的镜像
                update_service = ImageUpdateService()
                updates_needed = update_service.compare_and_update(current_file_name, verbose)
                last_step = "fetch_latest_images"
                self.save_state(last_step, updates_needed)

            # 如果上次中断在获取镜像列表后，继续执行拉取任务
            if last_step == "fetch_latest_images" and updates_needed:
                try:
                    image_pull.pull_and_export_images(updates_needed, current_date, verbose)
                    last_step = "pull_and_export_images"
                    self.save_state(last_step, updates_needed)
                except Exception as e:
                    logger.error(f"拉取镜像过程中出现错误: {str(e)}")
                    raise

            # 任务完成后清理状态文件
            if last_step == "pull_and_export_images":
                self.clean_state()
            
        except Exception as e:
            logger.error(f"执行过程中出现错误: {str(e)}")
            raise

def check_and_pull_updates(verbose=True):
    """检查并拉取更新"""
    try:
        # 创建服务实例
        update_service = ImageUpdateService()
        
        # 调用实例方法
        updates = update_service.compare_and_update(COMPONENTS)
        
        return updates
        
    except Exception as e:
        logger.error(f"检查更新时出错: {str(e)}")
        raise