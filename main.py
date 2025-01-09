#!/usr/bin/env python3
import argparse
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint
from src import CONFIG, ImageManager, logger
from datetime import datetime
from rich.table import Table
from colorama import init, Fore, Style

init()

console = Console()

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Docker 镜像自动更新工具')
    parser.add_argument('-D', '--debug', 
                       action='store_true',
                       help='启用调试模式，显示详细日志')
    return parser.parse_args()

def main():
    """主程序入口"""
    try:
        args = parse_args()
        
        # 根据命令行参数设置日志级别
        if args.debug:
            logger.setLevel('DEBUG')
        else:
            logger.setLevel('INFO')
        
        # 显示任务标题
        console.print(r"""[blue bold italic]
 ____  ___ ___   ____   ____    ___    ___  __ __  ____    ___   ____   ______    ___  ____  
|    ||   |   | /    | /    |  /  _]  /  _]|  |  ||    \  /   \ |    \ |      |  /  _]|    \ 
 |  | | _   _ ||  o  ||   __| /  [_  /  [_ |  |  ||  o  )|     ||  D  )|      | /  [_ |  D  )
 |  | |  \_/  ||     ||  |  ||    _]|    _]|_   _||   _/ |  O  ||    / |_|  |_||    _]|    / 
 |  | |   |   ||  _  ||  |_ ||   [_ |   [_ |     ||  |   |     ||    \   |  |  |   [_ |    \ 
 |  | |   |   ||  |  ||     ||     ||     ||  |  ||  |   |     ||  .  \  |  |  |     ||  .  \
|____||___|___||__|__||___,_||_____||_____||__|__||__|    \___/ |__|\_|  |__|  |_____||__|\_|
[/blue bold italic]""")
        
        console.print("\n[bold cyan]任务开始[/bold cyan]")
        console.print("=" * 50)
        
        # 初始化镜像管理器
        manager = ImageManager()
        
        # 显示当前配置的组件
        components = CONFIG.get("components")
        console.print("\n[yellow]配置的组件列表：[/yellow]")
        for name, component in components.items():
            console.print(f"  • {component['name']} ({component['image']})")
        
        # 执行主要逻辑
        start_time = datetime.now()
        updates_needed = manager.run()
        end_time = datetime.now()
        
        # 显示执行总结
        console.print("\n[bold cyan]执行结果总结[/bold cyan]")
        console.print("=" * 50)
        
        # 计算执行时间
        duration = end_time - start_time
        minutes = duration.seconds // 60
        seconds = duration.seconds % 60
        
        # 创建总结表格
        table = Table(show_header=False)
        table.add_column("项目", style="bold cyan")
        table.add_column("结果", style="bold")
        
        table.add_row("执行时间", f"{minutes}分{seconds}秒")
        table.add_row("检查组件数", str(len(components)))
        
        if updates_needed:
            table.add_row(
                "需要更新",
                f"[bold red]{len(updates_needed)}个[/bold red]"
            )
            table.add_row(
                "更新组件",
                "\n".join(f"• {comp['name']}" for comp in updates_needed.values())
            )
            table.add_row(
                "镜像文件",
                f"已保存至 data/images/{datetime.now().strftime('%Y%m%d')}/"
            )
        else:
            table.add_row("检查结果", "[bold green]所有组件均为最新版本[/bold green]")
        
        table.add_row(
            "版本文件",
            f"latest-{datetime.now().strftime('%Y%m%d')}.txt"
        )
        if updates_needed:
            table.add_row(
                "更新列表",
                f"update-{datetime.now().strftime('%Y%m%d')}.txt"
            )
        
        console.print(table)
        console.print("\n[bold green]任务完成！[/bold green]")
        console.print("=" * 50)
        return 0
        
    except KeyboardInterrupt:
        console.print("\n[bold red]操作被用户中断[/bold red]")
        return 1
    except Exception as e:
        console.print(f"\n[bold red]程序执行出错: {str(e)}[/bold red]")
        return 1

if __name__ == "__main__":
    exit(main())