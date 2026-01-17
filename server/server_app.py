# server/server_app.py
import sys
import os
import threading
from datetime import datetime

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from server.file_transfer import FileReceiver
except ImportError:
    from .file_transfer import FileReceiver  # 尝试相对导入


class ServerApp:
    def __init__(self):
        self.file_receiver = FileReceiver()
        self.is_running = False
        
    def start(self):
        """启动服务端应用"""
        self.is_running = True
        self.file_receiver.start_server()
        
    def stop(self):
        """停止服务端应用"""
        self.is_running = False
        self.file_receiver.stop_server()