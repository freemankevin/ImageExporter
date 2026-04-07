#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""镜像导出器服务"""

import json
import os
import time
import signal
import logging
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import Dict, List, Set, Optional
from threading import Lock

from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, SpinnerColumn, MofNCompleteColumn
from rich.console import Console

from app.core.config import config, get_mirrored_image, IMAGES_DIR, LOGS_DIR, PROJECT_ROOT
from app.core.logging import setup_logger, COLORS, ICONS, get_console, QuietRichHandler
from app.core.shutdown import shutdown_event
from app.models.image import ImageResult
from app.models.task import TaskState
from app.services.docker_api import ContainerRegistryAPI
from app.services.docker_manager import DockerManager
from app.services.version_manager import VersionManager
from app.utils.helpers import version_key, get_major_version, generate_manual_commands
from app.utils.display import pad_string, print_separator, print_banner
from app.utils.report_generator import generate_html_report

console = get_console()
_results_lock = Lock()
_executor: Optional[ThreadPoolExecutor] = None
_active_futures: List[Future] = []


class ImageExporter:
    """镜像导出器主类"""
    
    def __init__(self, debug: bool = False, arch_list: Optional[List[str]] = None, export_images: bool = True):
        self.logger = setup_logger(debug)
        self.docker_api = ContainerRegistryAPI()
        self.docker_manager = DockerManager(self.logger)
        self.version_manager = VersionManager()
        self.today = datetime.now().strftime('%Y%m%d_%H%M')
        self.today_date = datetime.now().strftime('%Y%m%d')
        self.image_results: List[ImageResult] = []
        self.arch_list = arch_list if arch_list else ['amd64', 'arm64']
        self.export_images = export_images
        
        self.state_file = LOGS_DIR / f"task_state_{self.today}.json"
        self.task_state = TaskState(self.state_file)
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        shutdown_event.clear()
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        global _executor, _active_futures
        
        console.print(f"\n[yellow]{ICONS['WARNING']} 收到中断信号，正在停止...[/]")
        
        shutdown_event.set()
        
        for future in _active_futures:
            future.cancel()
        
        if _executor:
            _executor.shutdown(wait=False, cancel_futures=True)
        
        console.print(f"{ICONS['INFO']} 任务状态已保存，下次运行将续传")
        console.print(f"{ICONS['CHECK']} 已停止")
        os._exit(0)
    
    def get_latest_versions(self, components: Dict) -> Dict:
        """获取所有组件的最新版本"""
        print_separator("获取最新版本")
        
        for name, component in components.items():
            print(f"{ICONS['ARROW']} 检查 {component['name']} 版本...")
            
            image_path = component['image']
            exclude_pattern = component.get('exclude_pattern')
            versions = self.docker_api.get_versions(
                image_path, component['tag_pattern'], exclude_pattern,
                component['version_type'], self.logger
            )
            
            component['latest_version'] = versions
            if versions:
                if component['version_type'] == 'multiple':
                    print(f"  {ICONS['CHECK']} {component['name']}: {COLORS['GREEN']}{', '.join(versions)}{COLORS['RESET']}")
                else:
                    print(f"  {ICONS['CHECK']} {component['name']}: {COLORS['GREEN']}{versions[0]}{COLORS['RESET']}")
            else:
                print(f"  {ICONS['CROSS']} {component['name']}: {COLORS['RED']}获取失败{COLORS['RESET']}")
        
        return components
    
    def check_updates(self, components: Dict) -> Dict:
        """检查需要更新的组件"""
        print_separator("版本比较")
        
        history_file = self.version_manager.get_latest_history_file()
        old_versions = {}
        
        if not history_file:
            print(f"{ICONS['WARNING']} 未找到历史版本文件")
            choice = input(f"{ICONS['INFO']} 是否将历史版本文件放入 data/versions 目录? (y/n): ").lower().strip()
            
            if choice == 'y':
                print(f"{ICONS['INFO']} 请将历史版本文件放入: {IMAGES_DIR.parent / 'versions'}")
                input(f"{ICONS['INFO']} 放置完成后按回车键继续...")
                history_file = self.version_manager.get_latest_history_file()
                
                if not history_file:
                    print(f"{ICONS['WARNING']} 未检测到历史版本文件，将获取所有组件的最新版本")
                else:
                    print(f"{ICONS['INFO']} 使用历史版本文件: {history_file.name}")
                    old_versions = self.version_manager.load_history_versions(history_file)
        else:
            print(f"{ICONS['INFO']} 使用历史版本文件: {history_file.name}")
            old_versions = self.version_manager.load_history_versions(history_file)
        
        updates_needed = {}
        col_widths = {'component': 18, 'old_version': 40, 'new_version': 40, 'status': 10}
        
        header = (
            f"{pad_string('组件', col_widths['component'])}│ "
            f"{pad_string('历史版本', col_widths['old_version'])}│ "
            f"{pad_string('最新版本', col_widths['new_version'])}│ "
            f"{pad_string('状态', col_widths['status'])}"
        )
        total_width = sum(col_widths.values()) + 11
        print(f"\n{COLORS['CYAN']}{header}{COLORS['RESET']}")
        print(f"{COLORS['CYAN']}{'─' * total_width}{COLORS['RESET']}")
        
        for name, component in components.items():
            image_name = os.path.basename(component['image'])
            old_version_map = old_versions.get(image_name, {})
            versions = component.get('latest_version', [])
            
            if not versions:
                continue
            
            if component['version_type'] == 'multiple':
                version_groups = {}
                for version in versions:
                    major = get_major_version(version)
                    if major not in version_groups:
                        version_groups[major] = []
                    version_groups[major].append(version)
                
                selected_versions = []
                for major, group in version_groups.items():
                    group.sort(key=version_key)
                    latest_in_group = group[-1]
                    old_version = old_version_map.get(major, "无")
                    
                    if not old_version or old_version == "无" or latest_in_group != old_version:
                        status = f"{COLORS['YELLOW']}需要更新{COLORS['RESET']}"
                        selected_versions.append(latest_in_group)
                    else:
                        status = f"{COLORS['GREEN']}无需更新{COLORS['RESET']}"
                    
                    row = (
                        f"{pad_string(component['name'], col_widths['component'])}│ "
                        f"{pad_string(old_version, col_widths['old_version'])}│ "
                        f"{pad_string(latest_in_group, col_widths['new_version'])}│ "
                        f"{status}"
                    )
                    print(row)
                
                if selected_versions:
                    component['latest_version'] = selected_versions
                    updates_needed[name] = component
            else:
                latest_version = versions[0]
                old_version = list(old_version_map.values())[0] if old_version_map else "无"
                
                if latest_version != "获取失败":
                    if not old_version or old_version == "无" or latest_version != old_version:
                        status = f"{COLORS['YELLOW']}需要更新{COLORS['RESET']}"
                        updates_needed[name] = component
                    else:
                        status = f"{COLORS['GREEN']}无需更新{COLORS['RESET']}"
                    
                    row = (
                        f"{pad_string(component['name'], col_widths['component'])}│ "
                        f"{pad_string(old_version, col_widths['old_version'])}│ "
                        f"{pad_string(latest_version, col_widths['new_version'])}│ "
                        f"{status}"
                    )
                    print(row)
        
        latest_file = self.version_manager.save_latest_versions(components)
        print(f"\n{ICONS['CHECK']} 最新版本文件: {latest_file.name}")
        
        if updates_needed:
            update_file = self.version_manager.save_update_list(updates_needed)
            print(f"{ICONS['CHECK']} 更新列表: {update_file.name}")
            print(f"\n{ICONS['INFO']} 需要处理 {len(updates_needed)} 个组件")
        else:
            print(f"\n{ICONS['INFO']} 无需处理任何组件！")
        
        return updates_needed
    
    def process_images(self, updates_needed: Dict):
        """处理镜像的拉取和导出"""
        if not updates_needed:
            return
        
        print_separator("处理镜像")
        
        tasks_to_process = []
        for name, component in updates_needed.items():
            image_name = component['image']
            versions = component['latest_version']
            
            if not versions:
                continue
            
            if not isinstance(versions, list):
                versions = [versions]
            
            mirrored_image = get_mirrored_image(image_name)
            for version in versions:
                for arch in self.arch_list:
                    image_path = None
                    if self.export_images:
                        output_dir = IMAGES_DIR / self.today_date / arch
                        output_dir.mkdir(parents=True, exist_ok=True)
                        image_filename = f"{os.path.basename(image_name)}_{version}_{arch}.tar.gz"
                        image_path = output_dir / image_filename
                    
                    task_id = f"{mirrored_image}:{version}:{arch}"
                    
                    tasks_to_process.append({
                        'task_id': task_id,
                        'full_image_name': f"{mirrored_image}:{version}",
                        'image_path': image_path,
                        'arch': arch,
                        'component_name': component['name']
                    })
        
        total_tasks = len(tasks_to_process)
        console.print(f"{ICONS['INFO']} 共 {total_tasks} 个镜像任务")
        
        tasks_to_run = []
        skipped_count = 0
        for task in tasks_to_process:
            if self.export_images and task['image_path']:
                if self.task_state.is_completed(task['task_id']):
                    if task['image_path'].exists() and task['image_path'].stat().st_size > config.min_file_size:
                        skipped_count += 1
                        self.logger.info(f"跳过已完成: {task['task_id']}")
                        continue
            else:
                if self.task_state.is_completed(task['task_id']):
                    skipped_count += 1
                    self.logger.info(f"跳过已完成: {task['task_id']}")
                    continue
            tasks_to_run.append(task)
        
        if skipped_count > 0:
            console.print(f"{ICONS['CHECK']} 跳过已完成: {skipped_count} 个")
        
        if not tasks_to_run:
            console.print(f"{ICONS['SUCCESS']} 所有任务已完成")
            return
        
        console.print(f"{ICONS['ARROW']} 需要处理: {len(tasks_to_run)} 个")
        
        for handler in self.logger.handlers:
            if isinstance(handler, QuietRichHandler):
                handler.set_quiet(True)
        
        global _executor, _active_futures
        _executor = None
        _active_futures = []
        
        try:
            for retry_round in range(config.max_global_retries):
                if not tasks_to_run:
                    break
                
                if shutdown_event.is_set():
                    break
                
                console.print(f"\n[yellow]{'─' * 60}[/]")
                console.print(f"[yellow]第 {retry_round + 1}/{config.max_global_retries} 轮处理[/]")
                console.print(f"[yellow]{'─' * 60}[/]")
                
                failed_tasks = []
                completed_count = 0
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(bar_width=40),
                    MofNCompleteColumn(),
                    TimeElapsedColumn(),
                    console=console,
                    refresh_per_second=4,
                ) as progress:
                    overall_task = progress.add_task(
                        f"[cyan]处理镜像",
                        total=len(tasks_to_run)
                    )
                    
                    _executor = ThreadPoolExecutor(max_workers=config.max_workers)
                    futures = {}
                    
                    for task in tasks_to_run:
                        if shutdown_event.is_set():
                            break
                        future = _executor.submit(
                            self._process_single_image,
                            task['full_image_name'], task['image_path'],
                            task['arch'], task['task_id']
                        )
                        futures[future] = task
                        _active_futures.append(future)
                    
                    for future in as_completed(futures):
                        if shutdown_event.is_set():
                            break
                        
                        task = futures[future]
                        _active_futures.remove(future)
                        
                        try:
                            result = future.result()
                            if result.pull_success and (not self.export_images or result.export_success):
                                self.task_state.mark_completed(task['task_id'])
                                completed_count += 1
                                progress.update(overall_task, advance=1)
                                short_name = os.path.basename(task['full_image_name'].split(':')[0])
                                progress.console.print(f"  {ICONS['CHECK']} [green]{short_name}:{task['arch']}[/]")
                            else:
                                failed_tasks.append(task)
                                retry_count = self.task_state.get_retry_count(task['task_id'])
                                self.task_state.mark_failed(task['task_id'], result.error_message, retry_count + 1)
                        except Exception as e:
                            failed_tasks.append(task)
                            retry_count = self.task_state.get_retry_count(task['task_id'])
                            self.task_state.mark_failed(task['task_id'], str(e), retry_count + 1)
                            self.logger.error(f"{ICONS['CROSS']} 处理出错: {task['task_id']}")
                    
                    if _executor:
                        _executor.shutdown(wait=False)
                        _executor = None
                
                if shutdown_event.is_set():
                    break
                
                if not failed_tasks:
                    break
                
                tasks_to_run = failed_tasks
                if retry_round < config.max_global_retries - 1:
                    wait_time = config.retry_delay * (config.retry_backoff_factor ** retry_round)
                    console.print(f"\n{ICONS['WARNING']} {len(failed_tasks)} 个失败，{wait_time}s 后重试...")
                    time.sleep(wait_time)
        finally:
            for handler in self.logger.handlers:
                if isinstance(handler, QuietRichHandler):
                    handler.set_quiet(False)
        
        if self.export_images:
            expected_images = {task['task_id'] for task in tasks_to_process}
            self._validate_images(expected_images)
        self._generate_summary_report()
        
        if self.export_images:
            console.print(f"\n{ICONS['CHECK']} 镜像保存至: {IMAGES_DIR / self.today_date}")
    
    def _process_single_image(self, full_image_name: str, image_path: Path, 
                               arch: str, task_id: Optional[str] = None):
        """处理单个镜像"""
        result = ImageResult(
            image_name=full_image_name.split(':')[0],
            version=full_image_name.split(':')[1],
            arch=arch
        )
        result.file_path = image_path
        
        try:
            pull_result = self.docker_manager.pull_image(full_image_name, arch)
            if pull_result:
                result.pull_success = True
                if self.export_images:
                    export_result = self.docker_manager.export_image(full_image_name, image_path, arch)
                    if export_result:
                        result.export_success = True
                    else:
                        result.error_message = "导出失败"
                        result.export_success = False
                else:
                    result.export_success = True
            else:
                result.pull_success = False
                result.error_message = "拉取失败"
        except Exception as e:
            result.pull_success = False
            result.export_success = False
            result.error_message = str(e)
            self.logger.error(f"[{arch}] {ICONS['CROSS']} 处理失败: {full_image_name}")
        
        with _results_lock:
            self.image_results.append(result)
        return result
    
    def _validate_images(self, expected_images: Set[str]):
        """验证镜像文件"""
        print_separator("镜像验证")
        
        component_map = {}
        for component in config.components.values():
            basename = os.path.basename(component['image'])
            mirrored_image = get_mirrored_image(component['image'])
            component_map[basename] = mirrored_image
        
        actual_files = set()
        invalid_files = []
        
        for arch in self.arch_list:
            arch_dir = IMAGES_DIR / self.today_date / arch
            if not arch_dir.exists():
                continue
            
            for file in arch_dir.glob("*.tar.gz"):
                file_size = file.stat().st_size
                
                if file_size < config.min_file_size:
                    invalid_files.append((file, file_size, "文件太小"))
                    continue
                
                filename = file.name[:-7]  # Remove .tar.gz suffix
                matched = False
                
                arch_suffix = "_amd64"
                if filename.endswith("_arm64"):
                    arch_suffix = "_arm64"
                
                if filename.endswith(arch_suffix):
                    arch_from_file = arch_suffix[1:]
                    version_and_name = filename[:-len(arch_suffix)]
                    
                    for basename, image_name in component_map.items():
                        prefix = f"{basename}_"
                        if version_and_name.startswith(prefix):
                            version = version_and_name[len(prefix):]
                            if arch_from_file == arch:
                                image_key = f"{image_name}:{version}:{arch}"
                                actual_files.add(image_key)
                                matched = True
                                break
                
                if not matched:
                    invalid_files.append((file, file_size, "无法识别"))
        
        missing_files = expected_images - actual_files
        
        print(f"{ICONS['INFO']} 预期: {len(expected_images)} 个")
        print(f"{ICONS['INFO']} 有效: {len(actual_files)} 个")
        
        if invalid_files:
            print(f"\n{ICONS['CROSS']} 无效文件 ({len(invalid_files)} 个):")
            for file, size, reason in invalid_files:
                print(f"  - {file.name} ({size / 1024 / 1024:.2f} MB): {reason}")
        
        if missing_files:
            print(f"\n{ICONS['CROSS']} 缺失文件 ({len(missing_files)} 个):")
            for missing in sorted(missing_files):
                image_name, version, arch = missing.rsplit(':', 2)
                print(f"  - {os.path.basename(image_name)}:{version} ({arch})")
        
        if not missing_files and not invalid_files:
            print(f"{ICONS['CHECK']} 验证通过")
            self.task_state.clear_state()
            return True
        else:
            print(f"{ICONS['CROSS']} 验证失败")
            return False
    
    def _generate_summary_report(self):
        """生成统计报告"""
        print_separator("处理结果")
        
        total_results = len(self.image_results)
        successful_results = [r for r in self.image_results if r.pull_success and r.export_success]
        failed_results = [r for r in self.image_results if not (r.pull_success and r.export_success)]
        
        print(f"{ICONS['INFO']} 总计: {total_results} 个")
        print(f"{ICONS['CHECK']} 成功: {COLORS['GREEN']}{len(successful_results)}{COLORS['RESET']} 个")
        print(f"{ICONS['CROSS']} 失败: {COLORS['RED']}{len(failed_results)}{COLORS['RESET']} 个")
        
        if failed_results:
            print(f"\n{COLORS['RED']}失败详情:{COLORS['RESET']}")
            for result in failed_results:
                status = "拉取失败" if not result.pull_success else "导出失败"
                print(f"  {ICONS['CROSS']} [{result.arch}] {os.path.basename(result.image_name)}:{result.version} - {status}")
                if result.error_message:
                    print(f"    错误: {result.error_message}")
            
            manual_commands = generate_manual_commands(failed_results, self.today_date, PROJECT_ROOT)
            if manual_commands:
                commands_file = LOGS_DIR / f"manual_commands_{self.today}.sh"
                with open(commands_file, 'w', encoding='utf-8') as f:
                    f.write(manual_commands)
                
                try:
                    os.chmod(commands_file, 0o755)
                except Exception:
                    pass
                
                print(f"\n{ICONS['INFO']} 手动命令: {commands_file}")
                print(f"{ICONS['ARROW']} 执行以下命令处理失败镜像:")
                print(f"  chmod +x {commands_file.as_posix()}")
                print(f"  {commands_file.as_posix()}")
        
        report_file = LOGS_DIR / f"report_{self.today}.json"
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'total_processed': total_results,
            'successful_count': len(successful_results),
            'failed_count': len(failed_results),
            'all_success': len(failed_results) == 0,
            'successful_images': [
                {
                    'image': f"{result.image_name}:{result.version}",
                    'arch': result.arch,
                    'file_path': str(result.file_path) if result.file_path else None,
                    'file_size_mb': result.file_path.stat().st_size / 1024 / 1024 if result.file_path and result.file_path.exists() else 0
                }
                for result in successful_results
            ],
            'failed_images': [
                {
                    'image': f"{result.image_name}:{result.version}",
                    'arch': result.arch,
                    'pull_success': result.pull_success,
                    'export_success': result.export_success,
                    'error_message': result.error_message
                }
                for result in failed_results
            ]
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"{ICONS['INFO']} 详细报告: {report_file}")
        
        html_report_file = LOGS_DIR / f"report_{self.today}.html"
        generate_html_report(report_data, html_report_file)
        print(f"{ICONS['INFO']} HTML报告: {html_report_file}")
        
        return len(failed_results) == 0
    
    def run(self):
        """运行主程序"""
        try:
            print_banner()
            start_time = datetime.now()
            
            components = config.components.copy()
            
            print(f"{COLORS['YELLOW']}组件列表:{COLORS['RESET']}")
            for component in components.values():
                mirrored = get_mirrored_image(component['image'])
                print(f"  {ICONS['COMPONENT']} {component['name']} ({mirrored})")
            
            print(f"\n{COLORS['CYAN']}配置:{COLORS['RESET']}")
            print(f"  {ICONS['INFO']} 架构: {', '.join(self.arch_list)}")
            print(f"  {ICONS['INFO']} 导出离线镜像: {'是' if self.export_images else '否'}")
            print(f"  {ICONS['INFO']} 并发数: {config.max_workers}")
            print(f"  {ICONS['INFO']} 全局重试: {config.max_global_retries}")
            print(f"  {ICONS['INFO']} 单任务重试: {config.max_retries}")
            
            components = self.get_latest_versions(components)
            updates_needed = self.check_updates(components)
            self.process_images(updates_needed)
            
            all_success = all(r.pull_success and r.export_success for r in self.image_results)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            print_separator("执行总结")
            print(f"{ICONS['INFO']} 执行时间: {duration}")
            print(f"{ICONS['INFO']} 检查组件: {len(components)}")
            
            if updates_needed:
                print(f"{ICONS['WARNING']} 处理组件: {len(updates_needed)} 个")
                for component in updates_needed.values():
                    versions = component['latest_version']
                    versions_str = ', '.join(versions) if isinstance(versions, list) else versions
                    print(f"  {ICONS['COMPONENT']} {component['name']} ({versions_str})")
                if self.export_images:
                    print(f"{ICONS['CHECK']} 保存至: data/images/{self.today_date}/")
            else:
                print(f"{ICONS['INFO']} 无需处理")
                return 0
            
            if all_success:
                print(f"\n{ICONS['SUCCESS']} 所有任务成功！")
                self.task_state.clear_state()
                return 0
            else:
                failed_count = sum(1 for r in self.image_results if not (r.pull_success and r.export_success))
                print(f"\n{ICONS['CROSS']} {failed_count} 个镜像失败")
                print(f"{ICONS['INFO']} 请检查日志和手动命令脚本")
                return 1
            
        except KeyboardInterrupt:
            print(f"\n{ICONS['CROSS']} 用户中断")
            print(f"{ICONS['INFO']} 任务状态已保存，下次运行将续传")
            return 1
        except Exception as e:
            self.logger.error(f"{ICONS['CROSS']} 执行出错: {str(e)}")
            return 1