import json
import os
from datetime import datetime

class Task:
    """任务模型"""
    
    TASKS_FILE = 'data/tasks.json'
    
    def __init__(self, task_id, name, excel_file, txt_folder, status='pending', 
                 progress=0, message='', result_file='', created_at=None):
        self.task_id = task_id
        self.name = name
        self.excel_file = excel_file
        self.txt_folder = txt_folder
        self.status = status  # pending, processing, completed, failed
        self.progress = progress
        self.message = message
        self.result_file = result_file
        self.created_at = created_at or datetime.now()
    
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'name': self.name,
            'excel_file': self.excel_file,
            'txt_folder': self.txt_folder,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'result_file': self.result_file,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def save(self):
        """保存任务到文件"""
        tasks = self.get_all_tasks_dict()
        tasks[self.task_id] = self.to_dict()
        
        os.makedirs(os.path.dirname(self.TASKS_FILE), exist_ok=True)
        with open(self.TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    def update_progress(self, progress, message, status=None, result_file=None):
        """更新任务进度"""
        self.progress = progress
        self.message = message
        if status:
            self.status = status
        if result_file:
            self.result_file = result_file
        self.save()
    
    def update_status(self, status, message, result_file=None):
        """更新任务状态"""
        self.status = status
        self.message = message
        if result_file:
            self.result_file = result_file
        if status == 'completed':
            self.progress = 100
        self.save()
    
    @classmethod
    def get_all_tasks(cls):
        """获取所有任务"""
        tasks_dict = cls.get_all_tasks_dict()
        tasks = []
        for task_data in tasks_dict.values():
            task = cls(
                task_id=task_data['task_id'],
                name=task_data['name'],
                excel_file=task_data['excel_file'],
                txt_folder=task_data['txt_folder'],
                status=task_data['status'],
                progress=task_data['progress'],
                message=task_data['message'],
                result_file=task_data['result_file'],
                created_at=datetime.fromisoformat(task_data['created_at']) if task_data['created_at'] else None
            )
            tasks.append(task)
        return sorted(tasks, key=lambda x: x.created_at, reverse=True)
    
    @classmethod
    def get_task(cls, task_id):
        """获取单个任务"""
        tasks_dict = cls.get_all_tasks_dict()
        task_data = tasks_dict.get(task_id)
        if task_data:
            return cls(
                task_id=task_data['task_id'],
                name=task_data['name'],
                excel_file=task_data['excel_file'],
                txt_folder=task_data['txt_folder'],
                status=task_data['status'],
                progress=task_data['progress'],
                message=task_data['message'],
                result_file=task_data['result_file'],
                created_at=datetime.fromisoformat(task_data['created_at']) if task_data['created_at'] else None
            )
        return None
    
    @classmethod
    def get_all_tasks_dict(cls):
        """获取所有任务的字典形式"""
        try:
            if os.path.exists(cls.TASKS_FILE):
                with open(cls.TASKS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}