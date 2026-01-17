# client/discovery.py
import socket
import json
import threading
import time
import sys
import os
from datetime import datetime

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.network_utils import create_udp_socket, receive_broadcast_messages, get_local_ip
from config import UDP_PORT, UDP_BROADCAST_ADDR, LOCAL_HOSTNAME

class DeviceDiscovery:
    def __init__(self):
        self.devices = {}  # 存储发现的设备 {'ip': {'hostname': ..., 'last_seen': ...}}
        self.local_ip = get_local_ip()
        self.running = False
        self.discovery_thread = None
        
    def start_discovery(self):
        """启动设备发现服务"""
        self.running = True
        self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self.discovery_thread.start()
        
    def stop_discovery(self):
        """停止设备发现服务"""
        self.running = False
        if self.discovery_thread:
            self.discovery_thread.join(timeout=2)
            
    def _discovery_loop(self):
        """设备发现主循环"""
        discovery_sock = create_udp_socket()
        broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        while self.running:
            try:
                # 发送发现广播
                self._send_discovery_broadcast(broadcast_sock)
                
                # 接收响应
                responses = receive_broadcast_messages(discovery_sock, timeout=1.0)
                
                # 处理收到的消息
                for msg, addr in responses:
                    if msg.get('type') == 'discovery':
                        self._handle_discovery_message(msg, addr)
                    elif msg.get('type') == 'response':
                        self._handle_response_message(msg, addr)
                
                # 清理过期设备
                self._cleanup_expired_devices()
                
            except Exception as e:
                print(f"设备发现循环中出现错误: {e}")
            
            # 等待一段时间再继续
            time.sleep(5)  # 每5秒发送一次发现请求
            
        discovery_sock.close()
        broadcast_sock.close()
        
    def _send_discovery_broadcast(self, sock):
        """发送设备发现广播"""
        discovery_msg = {
            'type': 'discovery',
            'hostname': LOCAL_HOSTNAME,
            'ip': self.local_ip,
            'timestamp': datetime.now().isoformat()
        }
        message = json.dumps(discovery_msg).encode('utf-8')
        sock.sendto(message, (UDP_BROADCAST_ADDR, UDP_PORT))
        
    def _handle_discovery_message(self, msg, addr):
        """处理收到的发现消息"""
        sender_ip = msg.get('ip', addr[0])
        sender_hostname = msg.get('hostname', 'Unknown')
        
        # 更新设备列表
        self.devices[sender_ip] = {
            'hostname': sender_hostname,
            'last_seen': datetime.now(),
            'ip': sender_ip
        }
        
    def _handle_response_message(self, msg, addr):
        """处理收到的响应消息"""
        sender_ip = msg.get('ip', addr[0])
        sender_hostname = msg.get('hostname', 'Unknown')
        
        # 更新设备列表
        self.devices[sender_ip] = {
            'hostname': sender_hostname,
            'last_seen': datetime.now(),
            'ip': sender_ip,
            'listen_port': msg.get('listen_port', 50002)
        }
        
    def _cleanup_expired_devices(self):
        """清理过期的设备（超过60秒未响应）"""
        current_time = datetime.now()
        expired_ips = []
        
        for ip, device_info in self.devices.items():
            if (current_time - device_info['last_seen']).seconds > 60:
                expired_ips.append(ip)
                
        for ip in expired_ips:
            del self.devices[ip]
            
    def discover_devices(self):
        """主动发现设备"""
        # 发送一次发现广播并等待响应
        discovery_sock = create_udp_socket()
        broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # 发送发现请求
        self._send_discovery_broadcast(broadcast_sock)
        
        # 等待响应
        responses = receive_broadcast_messages(discovery_sock, timeout=2.0)
        
        # 处理响应
        for msg, addr in responses:
            if msg.get('type') == 'discovery':
                self._handle_discovery_message(msg, addr)
            elif msg.get('type') == 'response':
                self._handle_response_message(msg, addr)
        
        discovery_sock.close()
        broadcast_sock.close()
        
        # 返回当前已知的所有设备
        return list(self.devices.values())
        
    def get_devices(self):
        """获取当前发现的设备列表"""
        # 清理过期设备
        self._cleanup_expired_devices()
        return list(self.devices.values())