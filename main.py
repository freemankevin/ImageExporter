#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Docker镜像离线导出工具 - 主入口"""

import sys
import io
import os

# 设置环境编码，解决Windows下中文输出问题
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


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(
        description='Docker镜像离线导出工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py              正常模式
  python main.py -D           调试模式
  python main.py --clean      清理缓存
  python main.py --clean-data 清理数据和日志目录
  python main.py --clean-all  全面清理
        """
    )
    
    parser.add_argument('-D', '--debug', action='store_true', help='启用调试模式')
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


if __name__ == "__main__":
    exit(main())