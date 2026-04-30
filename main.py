#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""容器镜像离线导出工具 - 支持 Docker 和 Podman"""

import sys
import io
import os
from datetime import datetime

if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import argparse

from app.services.exporter import ImageExporter
from app.cli.commands import clean_cache, clean_all, clean_data
from app.core.logging import COLORS, ICONS
from app.core.config import VERSIONS_DIR, LOGS_DIR, IMAGES_DIR


def clean_today_records():
    """彻底清理今天的所有记录和镜像文件"""
    today = datetime.now().strftime('%Y%m%d')
    today_prefix = datetime.now().strftime('%Y%m%d_')
    
    cleaned = 0
    
    print(f"{COLORS['YELLOW']}{'─' * 50}{COLORS['RESET']}")
    print(f"{ICONS['WARNING']} 清理今天的所有记录")
    print(f"{COLORS['YELLOW']}{'─' * 50}{COLORS['RESET']}")
    
    print(f"\n{ICONS['INFO']} 清理版本记录文件...")
    if VERSIONS_DIR.exists():
        for file in VERSIONS_DIR.iterdir():
            if file.name.startswith(f'latest-{today_prefix}') or file.name.startswith(f'update-{today_prefix}'):
                try:
                    file.unlink()
                    print(f"  {ICONS['CHECK']} {file.name}")
                    cleaned += 1
                except Exception as e:
                    print(f"  {ICONS['CROSS']} 失败: {file.name} - {e}")
    
    print(f"\n{ICONS['INFO']} 清理任务状态和日志文件...")
    if LOGS_DIR.exists():
        for file in LOGS_DIR.iterdir():
            if file.name.startswith(f'task_state_{today_prefix}') or file.name.startswith(f'exporter_{today}') or \
               file.name.startswith(f'report_{today_prefix}') or file.name.startswith(f'manual_commands_{today_prefix}'):
                try:
                    file.unlink()
                    print(f"  {ICONS['CHECK']} {file.name}")
                    cleaned += 1
                except Exception as e:
                    print(f"  {ICONS['CROSS']} 失败: {file.name} - {e}")
    
    print(f"\n{ICONS['INFO']} 清理今天的镜像文件...")
    images_today = IMAGES_DIR / today
    if images_today.exists():
        try:
            import shutil
            shutil.rmtree(images_today)
            print(f"  {ICONS['CHECK']} 删除目录: data/images/{today}")
            cleaned += 1
        except Exception as e:
            print(f"  {ICONS['CROSS']} 失败: {e}")
    else:
        print(f"  {ICONS['INFO']} 镜像目录不存在")
    
    print(f"\n{COLORS['GREEN']}{'─' * 50}{COLORS['RESET']}")
    print(f"{ICONS['SUCCESS']} 清理完成: {cleaned} 项")
    print(f"{COLORS['GREEN']}{'─' * 50}{COLORS['RESET']}")


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(
        description='容器镜像离线导出工具 (支持 Docker/Podman)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py              正常模式
  python main.py -D           调试模式
  python main.py --reset      重置今天的记录，重新执行
  python main.py --clean      清理缓存
  python main.py --clean-data 清理数据和日志目录
  python main.py --clean-all  全面清理
        """
    )
    
    parser.add_argument('-D', '--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--reset', action='store_true', help='重置今天的版本记录，重新执行')
    parser.add_argument('--retry-failed', action='store_true', help='跳过版本检查，只重试之前失败的镜像')
    parser.add_argument('--clean', action='store_true', help='清理Python缓存')
    parser.add_argument('--clean-data', action='store_true', help='清理数据和日志目录')
    parser.add_argument('--clean-all', action='store_true', help='清理所有临时文件')
    parser.add_argument('--arch', choices=['amd64', 'arm64', 'all'], default='all',
                        help='指定架构: amd64, arm64 或 all (默认: all)')
    parser.add_argument('--no-export', action='store_true', help='仅拉取镜像，不导出离线镜像')
    
    args = parser.parse_args()
    
    try:
        if args.clean_all:
            clean_all()
            return 0
        elif args.clean_data:
            clean_data()
            return 0
        elif args.clean:
            clean_cache()
            return 0
        elif args.reset:
            clean_today_records()
            arch_list = None if args.arch == 'all' else [args.arch]
            exporter = ImageExporter(debug=args.debug, arch_list=arch_list, export_images=not args.no_export)
            return exporter.run()
        elif args.retry_failed:
            arch_list = None if args.arch == 'all' else [args.arch]
            exporter = ImageExporter(debug=args.debug, arch_list=arch_list, export_images=not args.no_export)
            return exporter.retry_failed()
        else:
            arch_list = None if args.arch == 'all' else [args.arch]
            exporter = ImageExporter(debug=args.debug, arch_list=arch_list, export_images=not args.no_export)
            return exporter.run()
    
    except KeyboardInterrupt:
        print(f"\n{ICONS['CROSS']} 用户中断")
        return 1
    except Exception as e:
        print(f"{ICONS['CROSS']} 执行出错: {str(e)}")
        return 1
    except Exception as e:
        print(f"{ICONS['CROSS']} 执行出错: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())