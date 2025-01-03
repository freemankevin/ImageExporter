#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
import argparse
from datetime import datetime
from src import (
    logger,
    PROJECT_ROOT,
    OUTPUT_DIR,
    VERSIONS_DIR
)

class Cleaner:
    def __init__(self):
        self.project_root = PROJECT_ROOT

    def _remove_directory(self, path, description):
        if os.path.exists(path):
            shutil.rmtree(path)
            logger.info(f"已删除{description}: {os.path.relpath(path, self.project_root)}")

    def _remove_file(self, path, description):
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"已删除{description}: {os.path.relpath(path, self.project_root)}")

    def clean_pycache(self):
        """清理所有 Python 缓存文件"""
        try:
            for root, dirs, _ in os.walk(self.project_root):
                for dir_name in dirs:
                    if dir_name == "__pycache__":
                        self._remove_directory(os.path.join(root, dir_name), "缓存目录")
            for pyc_file in Path(self.project_root).rglob("*.pyc"):
                self._remove_file(pyc_file, "缓存文件")
        except Exception as e:
            logger.error(f"清理 Python 缓存时出错: {str(e)}")

    def clean_state(self):
        """清理状态文件"""
        try:
            self._remove_file(os.path.join(self.project_root, "state.json"), "状态文件")
        except Exception as e:
            logger.error(f"清理状态文件时出错: {str(e)}")

    def clean_output(self):
        """清理输出目录"""
        try:
            self._remove_directory(OUTPUT_DIR, "输出目录")
            os.makedirs(OUTPUT_DIR)
            logger.info("已清空输出目录: data/output")
        except Exception as e:
            logger.error(f"清理输出目录时出错: {str(e)}")

    def clean_versions(self):
        """清理版本文件"""
        try:
            if not os.path.exists(VERSIONS_DIR):
                return

            today = datetime.now().strftime("%Y%m%d")
            today_files = [os.path.join(VERSIONS_DIR, file) for file in os.listdir(VERSIONS_DIR)
                           if file.startswith(("latest-", "update-")) and file.split("-")[1].split(".")[0] == today]

            if not today_files:
                logger.info("没有找到今天的版本文件，无需清理")
                return

            for file_path in today_files:
                self._remove_file(file_path, "今天的版本文件")

            history_files = [f for f in os.listdir(VERSIONS_DIR)
                             if f.startswith(("latest-", "update-")) and f.split("-")[1].split(".")[0] != today]

            if history_files:
                logger.info("\n保留的历史版本文件:")
                for file in sorted(history_files, reverse=True):
                    logger.info(f"  - {file}")

        except Exception as e:
            logger.error(f"清理版本目录时出错: {str(e)}")

    def clean_logs(self):
        """清理日志文件"""
        try:
            logs_dir = os.path.join(self.project_root, "logs")
            if os.path.exists(logs_dir):
                success_count = 0
                failed_files = []

                for log_file in os.listdir(logs_dir):
                    if log_file.endswith(".log"):
                        log_path = os.path.join(logs_dir, log_file)
                        try:
                            for handler in logger.handlers[:]:
                                if hasattr(handler, 'baseFilename') and handler.baseFilename == log_path:
                                    logger.removeHandler(handler)
                                    handler.close()
                            os.remove(log_path)
                            success_count += 1
                        except Exception as e:
                            failed_files.append((log_file, str(e)))

                if success_count > 0:
                    logger.info(f"成功清理 {success_count} 个日志文件")

                if failed_files:
                    logger.warning("以下日志文件清理失败:")
                    for file_name, error in failed_files:
                        logger.warning(f"  - {file_name}: {error}")
                    logger.warning("提示: 可能是因为文件正在被使用，请关闭相关程序后重试")

                if not success_count and not failed_files:
                    logger.info("没有找到需要清理的日志文件")

        except Exception as e:
            logger.error(f"清理日志文件时出错: {str(e)}")

    def clean_all(self):
        """清理所有临时文件和缓存"""
        self.clean_pycache()
        self.clean_state()
        self.clean_output()
        self.clean_versions()
        self.clean_logs()
        logger.info("已完成所有清理工作")

def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description='项目清理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python clean.py -a              # 清理所有内容（保留历史版本文件）
  python clean.py -c              # 只清理 Python 缓存
  python clean.py -v              # 只清理今天的版本文件
  python clean.py -c -s           # 组合清理多种内容
  python clean.py --versions      # 使用完整命令
  
注意:
  - 版本文件清理只会删除今天的文件，保留历史文件用于版本比较
  - 日志清理会尝试关闭正在使用的日志文件
  - 建议在开始新的操作前执行清理
""")
    
    parser.add_argument('-c', '--cache', action='store_true', help='清理 Python 缓存文件（__pycache__ 目录和 .pyc 文件）')
    parser.add_argument('-s', '--state', action='store_true', help='清理状态文件（state.json）')
    parser.add_argument('-o', '--output', action='store_true', help='清理输出目录（data/output）')
    parser.add_argument('-v', '--versions', action='store_true', help='清理今天的版本文件（保留历史版本用于比较）')
    parser.add_argument('-l', '--logs', action='store_true', help='清理日志文件（自动处理文件占用）')
    parser.add_argument('-a', '--all', action='store_true', help='清理所有内容（保留历史版本文件）')
    
    args = parser.parse_args()
    cleaner = Cleaner()
    
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    try:
        if args.all:
            logger.info("开始全面清理...")
            cleaner.clean_all()
        else:
            if args.cache:
                logger.info("清理 Python 缓存...")
                cleaner.clean_pycache()
            if args.state:
                logger.info("清理状态文件...")
                cleaner.clean_state()
            if args.output:
                logger.info("清理输出目录...")
                cleaner.clean_output()
            if args.versions:
                logger.info("清理今天的版本文件...")
                cleaner.clean_versions()
            if args.logs:
                logger.info("清理日志文件...")
                cleaner.clean_logs()
        
        logger.info("清理完成！")
        
    except KeyboardInterrupt:
        logger.warning("\n清理操作被用户中断")
        return 1
    except Exception as e:
        logger.error(f"清理过程中发生错误: {str(e)}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())