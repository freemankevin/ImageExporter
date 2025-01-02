import os
from concurrent.futures import ThreadPoolExecutor
from src.utils.docker_utils import pull_image, export_image  # 确保 docker_utils.py 在 utils 目录下
from src.utils.file_utils import get_output_path, write_versions_to_file
from src.utils.paths import VERSIONS_DIR, OUTPUT_DIR
from src.utils.logger import logger
from config import CONFIG

def process_single_image(args):
    """处理单个镜像的拉取和导出"""
    component, version, arch, current_date, verbose = args
    
    try:
        image_name = component.split('/')[-1]
        full_image_name = f"{component}:{version}"
        image_filename = f"{image_name}_{version}_{arch}_{current_date}.tar.gz"
        output_path = os.path.join(get_output_path(current_date, arch.upper()), image_filename)
        
        pull_image(component, full_image_name, arch, verbose=verbose)
        export_image(full_image_name, output_path, arch, verbose=verbose)
        
        return True, None
    except Exception as e:
        return False, (component, arch, str(e))

def pull_and_export_images(updates_needed, current_date, verbose=True):
    """并发拉取并导出指定架构的镜像"""
    if not updates_needed:
        logger.info("\n无需拉取任何镜像。")
        return

    update_file_name = f'update-{current_date}.txt'
    write_versions_to_file(update_file_name, updates_needed)

    if os.path.exists(os.path.join(VERSIONS_DIR, update_file_name)):
        logger.info("\n>>>>>>>>>>>>>> 开始拉取镜像 <<<<<<<<<<<<<<")
        
        tasks = [
            (component, version, arch, current_date, verbose)
            for component, version in updates_needed.items()
            for arch in ["amd64", "arm64"]
        ]

        failed_tasks = []
        with ThreadPoolExecutor(max_workers=CONFIG['concurrent_downloads']) as executor:
            results = list(executor.map(process_single_image, tasks))
            
            for success, error in results:
                if not success and error:
                    component, arch, error_msg = error
                    failed_tasks.append(f"[{arch}] {component}: {error_msg}")

        if failed_tasks:
            logger.error("\n以下镜像处理失败:")
            for task in failed_tasks:
                logger.error(task)
        else:
            logger.info("\n所有镜像文件离线完成。")
            logger.info(f"所在目录位置: {os.path.abspath(OUTPUT_DIR)}")
    else:
        logger.info("没有需要拉取的镜像，跳过拉取任务。")