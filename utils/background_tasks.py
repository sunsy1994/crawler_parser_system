import threading
import time
from utils.file_processor import FileProcessor
from models.task import Task
import logging

logger = logging.getLogger('BackgroundTasks')

class TaskProcessor:
    """任务处理器 - 使用线程池"""
    
    _active_tasks = {}  # 存储活跃任务
    
    @classmethod
    def process_task_async(cls, task_id):
        """异步处理任务"""
        if task_id in cls._active_tasks:
            logger.warning(f"任务 {task_id} 已在处理中")
            return
        
        # 创建新线程处理任务
        thread = threading.Thread(target=cls._process_task, args=(task_id,))
        thread.daemon = True
        thread.start()
        
        cls._active_tasks[task_id] = {
            'thread': thread,
            'start_time': time.time()
        }
        
        logger.info(f"开始异步处理任务: {task_id}")
    
    @classmethod
    def _process_task(cls, task_id):
        """处理任务的实际逻辑"""
        try:
            task = Task.get_task(task_id)
            if not task:
                logger.error(f"任务不存在: {task_id}")
                return
            
            # 更新任务状态为处理中
            task.update_status('processing', '开始处理')
            
            # 处理任务
            result_file = FileProcessor.process_task(task_id, task.excel_file, task.txt_folder)
            
            # 更新任务状态为完成
            task.update_status('completed', '处理完成', result_file=result_file)
            
            logger.info(f"任务处理完成: {task_id}")
            
        except Exception as e:
            logger.error(f"异步处理任务失败: {e}")
            task = Task.get_task(task_id)
            if task:
                task.update_status('failed', f'处理失败: {str(e)}')
        finally:
            # 从活跃任务中移除
            cls._active_tasks.pop(task_id, None)
    
    @classmethod
    def get_active_tasks_count(cls):
        """获取活跃任务数量"""
        return len(cls._active_tasks)
    
    @classmethod
    def cancel_task(cls, task_id):
        """取消任务（简化实现）"""
        if task_id in cls._active_tasks:
            # 在实际项目中，这里应该实现更复杂的取消逻辑
            # 目前只是标记任务为取消状态
            task = Task.get_task(task_id)
            if task:
                task.update_status('cancelled', '任务已取消')
            cls._active_tasks.pop(task_id, None)
            return True
        return False