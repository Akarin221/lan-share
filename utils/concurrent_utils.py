# utils/concurrent_utils.py
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


class TaskManager:
    """任务管理器，用于处理并发任务"""
    
    def __init__(self, max_workers=5):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.futures = {}
        self.task_counter = 0
        
    def submit_task(self, func, *args, **kwargs):
        """提交任务到线程池"""
        future = self.executor.submit(func, *args, **kwargs)
        task_id = self.task_counter
        self.futures[task_id] = future
        self.task_counter += 1
        return task_id
        
    def get_result(self, task_id):
        """获取任务结果"""
        if task_id in self.futures:
            return self.futures[task_id].result()
        return None
        
    def is_task_done(self, task_id):
        """检查任务是否完成"""
        if task_id in self.futures:
            return self.futures[task_id].done()
        return False
        
    def cancel_task(self, task_id):
        """取消任务"""
        if task_id in self.futures:
            return self.futures[task_id].cancel()
        return False
        
    def get_active_tasks_count(self):
        """获取活跃任务数量"""
        count = 0
        for future in self.futures.values():
            if not future.done():
                count += 1
        return count
        
    def shutdown(self, wait=True):
        """关闭任务管理器"""
        self.executor.shutdown(wait=wait)
        

class TransferQueue:
    """文件传输队列，管理待传输的文件"""
    
    def __init__(self):
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        
    def add_transfer_task(self, file_path, target_ip, target_port=50002):
        """添加传输任务"""
        task = {
            'file_path': file_path,
            'target_ip': target_ip,
            'target_port': target_port,
            'status': 'pending',  # pending, in_progress, completed, failed
            'progress': 0,
            'timestamp': time.time()
        }
        
        with self.lock:
            self.queue.put(task)
        return task
        
    def get_next_task(self):
        """获取下一个任务"""
        try:
            with self.lock:
                if not self.queue.empty():
                    return self.queue.get_nowait()
                return None
        except queue.Empty:
            return None
            
    def get_queue_size(self):
        """获取队列大小"""
        return self.queue.qsize()
        
    def is_empty(self):
        """检查队列是否为空"""
        return self.queue.empty()