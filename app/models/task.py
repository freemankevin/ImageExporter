#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""任务状态数据模型"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Set


class TaskState:
    """任务状态管理器"""
    
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Dict[str, Dict] = {}
        self.load_state()
    
    def load_state(self):
        """加载任务状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.completed_tasks = set(data.get('completed', []))
                    self.failed_tasks = data.get('failed', {})
            except Exception:
                pass
    
    def save_state(self):
        """保存任务状态"""
        try:
            data = {
                'completed': list(self.completed_tasks),
                'failed': self.failed_tasks,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def mark_completed(self, task_id: str):
        """标记任务完成"""
        self.completed_tasks.add(task_id)
        if task_id in self.failed_tasks:
            del self.failed_tasks[task_id]
        self.save_state()
    
    def mark_failed(self, task_id: str, error: str, attempt: int):
        """标记任务失败"""
        self.failed_tasks[task_id] = {
            'error': error,
            'attempts': attempt,
            'last_failed': datetime.now().isoformat()
        }
        self.save_state()
    
    def is_completed(self, task_id: str) -> bool:
        """检查任务是否已完成"""
        return task_id in self.completed_tasks
    
    def get_retry_count(self, task_id: str) -> int:
        """获取任务重试次数"""
        if task_id in self.failed_tasks:
            return self.failed_tasks[task_id].get('attempts', 0)
        return 0
    
    def clear_state(self):
        """清除状态文件"""
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        if self.state_file.exists():
            self.state_file.unlink()