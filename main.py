import argparse
import sys
import traceback
from src.core.image_manager import check_and_pull_updates
from src.utils.logger import logger

def main():
    try:
        # 执行检查和拉取更新
        updates = check_and_pull_updates(verbose=not args.quiet)
        
        if updates:
            logger.info("发现以下组件需要更新:")
            for name, version in updates.items():
                logger.info(f"  - {name}: {version}")
        else:
            logger.info("所有组件均为最新版本")
            
        return 0
    except KeyboardInterrupt:
        logger.info("\n用户手动终止了程序执行")
        return 0
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Docker镜像版本检查和离线包制作工具')
    parser.add_argument('-q', '--quiet', action='store_true', help='静默模式，减少输出信息')
    args = parser.parse_args()
    exit(main())