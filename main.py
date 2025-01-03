#!/usr/bin/env python3
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint
from src import CONFIG, ImageManager, logger

console = Console()

def main():
    """主程序入口"""
    try:
        # 显示任务标题
        console.print(Panel.fit(
            "[bold blue]Docker 镜像自动更新工具[/bold blue]\n"
            "[dim]用于检查和导出最新版本的 Docker 镜像[/dim]",
            border_style="blue"
        ))
        
        console.print("\n[bold cyan]任务开始[/bold cyan]")
        console.print("=" * 50)
        
        # 初始化镜像管理器
        manager = ImageManager()
        
        # 显示当前配置的组件
        components = CONFIG.get("components")
        console.print("\n[yellow]配置的组件列表：[/yellow]")
        for name, component in components.items():
            console.print(f"  • {component['name']} ({component['image']})")
        
        console.print("\n[bold green]开始执行更新检查...[/bold green]")
        
        # 执行主要逻辑
        manager.run()
        
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