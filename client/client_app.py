# client/client_app.py
import sys
import os
import threading
from datetime import datetime

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.discovery import DeviceDiscovery
from server.file_transfer import FileSender


class ClientApp:
    def __init__(self):
        self.device_discovery = DeviceDiscovery()
        self.file_sender = FileSender()
        self.progress_tracker = None
        self.is_running = False
        
    def start(self):
        """启动客户端应用"""
        self.is_running = True
        self.device_discovery.start_discovery()
        
    def stop(self):
        """停止客户端应用"""
        self.is_running = False
        self.device_discovery.stop_discovery()
        
    def discover_devices(self):
        """发现局域网内的设备"""
        return self.device_discovery.discover_devices()
        
    def send_file_to_device(self, file_path, target_ip, target_port=50002, progress_callback=None):
        """向指定设备发送文件"""
        try:
            # 设置进度回调
            if progress_callback:
                self.progress_tracker = progress_callback
                self.file_sender.transfer_callback = progress_callback.update_progress
            
            # 启动文件发送
            self.file_sender.send_file(file_path, target_ip, target_port)
            print(f"文件 {file_path} 已成功发送到 {target_ip}:{target_port}")
            return True
        except Exception as e:
            print(f"发送文件失败: {e}")
            raise