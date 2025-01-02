#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
import argparse
from datetime import datetime
from src.utils.logger import logger

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent

class Cleaner:
    def __init__(self):
        self.project_root = PROJECT_ROOT
        
    def clean_pycache(self):
        """清理所有 Python 缓存文件"""
        try:
            # 查找所有 __pycache__ 目录
            for root, dirs, files in os.walk(self.project_root):
                for dir_name in dirs:
                    if dir_name == "__pycache__":
                        cache_path = os.path.join(root, dir_name)
                        shutil.rmtree(cache_path)
                        logger.info(f"已删除缓存目录: {os.path.relpath(cache_path, self.project_root)}")
                        
            # 删除 .pyc 文件
            for pyc_file in Path(self.project_root).rglob("*.pyc"):
                os.remove(pyc_file)
                logger.info(f"已删除缓存文件: {os.path.relpath(pyc_file, self.project_root)}")
        except Exception as e:
            logger.error(f"清理 Python 缓存时出错: {str(e)}")

    def clean_state(self):
        """清理状态文件"""
        try:
            state_file = os.path.join(self.project_root, "state.json")
            if os.path.exists(state_file):
                os.remove(state_file)
                logger.info("已删除状态文件: state.json")
        except Exception as e:
            logger.error(f"清理状态文件时出错: {str(e)}")

    def clean_output(self):
        """清理输出目录"""
        try:
            output_dir = os.path.join(self.project_root, "data", "output")
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
                os.makedirs(output_dir)
                logger.info("已清空输出目录: data/output")
        except Exception as e:
            logger.error(f"清理输出目录时出错: {str(e)}")

    def clean_versions(self):
        """清理版本文件
        
        只清理今天的版本文件（latest-YYYYMMDD.txt 和 update-YYYYMMDD.txt），
        保留历史日期的版本文件用于比较。
        """
        try:
            versions_dir = os.path.join(self.project_root, "data", "versions")
            if not os.path.exists(versions_dir):
                return

            # 获取今天的日期
            today = datetime.now().strftime("%Y%m%d")
            
            # 查找今天的版本文件
            today_files = []
            for file in os.listdir(versions_dir):
                if file.startswith(("latest-", "update-")):
                    try:
                        # 提取文件中的日期
                        file_date = file.split("-")[1].split(".")[0]
                        file_path = os.path.join(versions_dir, file)
                        
                        # 只处理今天的文件
                        if file_date == today:
                            today_files.append((file, file_path))
                    except IndexError:
                        logger.warning(f"跳过格式不正确的文件: {file}")
                        continue

            if not today_files:
                logger.info("没有找到今天的版本文件，无需清理")
                return

            # 删除今天的版本文件
            for file_name, file_path in today_files:
                try:
                    os.remove(file_path)
                    logger.info(f"已删除今天的版本文件: {file_name}")
                except Exception as e:
                    logger.error(f"删除文件 {file_name} 失败: {str(e)}")
            
            # 显示保留的历史文件信息
            history_files = [
                f for f in os.listdir(versions_dir)
                if f.startswith(("latest-", "update-")) and 
                   f.split("-")[1].split(".")[0] != today
            ]
            
            if history_files:
                logger.info("\n保留的历史版本文件:")
                # 按日期排序显示
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
                            # 尝试关闭日志处理器
                            for handler in logger.handlers[:]:
                                if hasattr(handler, 'baseFilename') and handler.baseFilename == log_path:
                                    logger.removeHandler(handler)
                                    handler.close()
                            
                            # 尝试删除文件
                            os.remove(log_path)
                            success_count += 1
                        except Exception as e:
                            failed_files.append((log_file, str(e)))
                
                # 输出清理结果
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
    
    # 添加命令行参数（同时支持长短命令）
    parser.add_argument(
        '-c', '--cache', 
        action='store_true', 
        help='清理 Python 缓存文件（__pycache__ 目录和 .pyc 文件）'
    )
    parser.add_argument(
        '-s', '--state', 
        action='store_true', 
        help='清理状态文件（state.json）'
    )
    parser.add_argument(
        '-o', '--output', 
        action='store_true', 
        help='清理输出目录（data/output）'
    )
    parser.add_argument(
        '-v', '--versions', 
        action='store_true', 
        help='清理今天的版本文件（保留历史版本用于比较）'
    )
    parser.add_argument(
        '-l', '--logs', 
        action='store_true', 
        help='清理日志文件（自动处理文件占用）'
    )
    parser.add_argument(
        '-a', '--all', 
        action='store_true', 
        help='清理所有内容（保留历史版本文件）'
    )
    
    args = parser.parse_args()
    cleaner = Cleaner()
    
    # 如果没有指定任何参数，显示帮助信息
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    try:
        # 执行清理操作
        if args.all:
            logger.info("开始全面清理...")
            cleaner.clean_all()
        else:
            # 分别执行各个清理操作
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