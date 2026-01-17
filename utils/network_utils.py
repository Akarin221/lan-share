# utils/network_utils.py
import socket
import struct
import json
import threading
import time
from datetime import datetime

def get_local_ip():
    """获取本地IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def create_broadcast_socket(port):
    """创建UDP广播套接字"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(2)
    sock.bind(('', port))
    return sock

def create_udp_socket():
    """创建UDP套接字用于接收广播"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.1)  # 设置短超时以避免阻塞
    return sock

def send_discovery_broadcast(sock, port, hostname, ip_address):
    """发送设备发现广播消息"""
    discovery_msg = {
        'type': 'discovery',
        'hostname': hostname,
        'ip': ip_address,
        'port': port,
        'timestamp': datetime.now().isoformat()
    }
    message = json.dumps(discovery_msg).encode('utf-8')
    sock.sendto(message, ('<broadcast>', port))

def send_response_broadcast(sock, response_port, hostname, ip_address, listen_port):
    """发送响应广播消息"""
    response_msg = {
        'type': 'response',
        'hostname': hostname,
        'ip': ip_address,
        'listen_port': listen_port,
        'timestamp': datetime.now().isoformat()
    }
    message = json.dumps(response_msg).encode('utf-8')
    sock.sendto(message, ('<broadcast>', response_port))

def receive_broadcast_messages(sock, timeout=1.0):
    """接收广播消息"""
    start_time = time.time()
    messages = []
    
    while time.time() - start_time < timeout:
        try:
            data, addr = sock.recvfrom(1024)
            try:
                message = json.loads(data.decode('utf-8'))
                messages.append((message, addr))
            except json.JSONDecodeError:
                continue
        except socket.timeout:
            continue
    
    return messages

def create_tcp_server_socket(host, port):
    """创建TCP服务器套接字"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(5)
    return sock

def create_tcp_client_socket():
    """创建TCP客户端套接字"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return sock