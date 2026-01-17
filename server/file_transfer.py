# server/file_transfer.py
import socket
import threading
import os
import sys
import os
from datetime import datetime

# 自定义异常类
class InterruptedError(Exception):
    """传输被中断异常"""
    pass

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CHUNK_SIZE
from utils.network_utils import create_tcp_server_socket, create_tcp_client_socket

class FileReceiver:
    def __init__(self, host='0.0.0.0', port=50002):
        self.host = host
        self.port = port
        self.running = False
        self.receive_thread = None
        self.download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "LANFileShare")
        
        # 确保下载目录存在
        os.makedirs(self.download_dir, exist_ok=True)
        
    def start_server(self):
        """启动文件接收服务器"""
        self.running = True
        self.receive_thread = threading.Thread(target=self._server_loop, daemon=True)
        self.receive_thread.start()
        
    def stop_server(self):
        """停止文件接收服务器"""
        self.running = False
        
    def _server_loop(self):
        """服务器主循环"""
        server_socket = create_tcp_server_socket(self.host, self.port)
        
        print(f"文件接收服务器启动于 {self.host}:{self.port}")
        
        while self.running:
            try:
                conn, addr = server_socket.accept()
                print(f"收到连接来自: {addr}")
                
                # 为每个连接创建新线程处理
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(conn, addr),
                    daemon=True
                )
                client_thread.start()
                
            except socket.error:
                if self.running:
                    print("服务器套接字错误")
                break
            except Exception as e:
                print(f"接收连接时发生错误: {e}")
                
        server_socket.close()
        
    def _handle_client(self, conn, addr):
        """处理客户端连接"""
        try:
            # 首先接收文件信息（大小和名称）
            header_data = self._recv_all(conn, 4)
            if not header_data:
                print(f"无法接收文件头信息来自: {addr}")
                return
                
            header_size = int.from_bytes(header_data, 'big')
            header_json = self._recv_all(conn, header_size).decode('utf-8')
                
            import json
            file_info = json.loads(header_json)
            file_name = file_info['name']
            file_size = file_info['size']
                
            print(f"开始接收文件: {file_name}, 大小: {file_size} bytes, 来自: {addr}")
                
            # 构建保存路径
            save_path = os.path.join(self.download_dir, file_name)
                
            # 如果文件已存在，添加数字后缀
            counter = 1
            base_name, ext = os.path.splitext(save_path)
            while os.path.exists(save_path):
                save_path = f"{base_name}_{counter}{ext}"
                counter += 1
                
            # 接收文件内容
            received_size = 0
            with open(save_path, 'wb') as f:
                while received_size < file_size:
                    chunk_size = min(CHUNK_SIZE, file_size - received_size)
                    chunk = conn.recv(chunk_size)
                        
                    if not chunk:
                        print(f"文件传输中断: {file_name}, 接收了 {received_size}/{file_size} 字节")
                        break
                            
                    f.write(chunk)
                    received_size += len(chunk)
                        
                    # 计算进度
                    progress = (received_size / file_size) * 100
                    print(f"\r接收进度: {progress:.1f}% ({received_size}/{file_size})", end='', flush=True)
                
            print(f"\n文件接收完成: {save_path}")
                
            # 发送确认消息
            try:
                conn.sendall(b"OK")
            except socket.error as se:
                print(f"发送确认消息失败: {se}")
                
        except json.JSONDecodeError:
            print(f"接收到了无效的JSON数据来自: {addr}")
        except Exception as e:
            print(f"处理客户端连接时出错: {e}")
        finally:
            conn.close()
            
    def _recv_all(self, conn, size):
        """接收指定大小的数据"""
        data = b''
        while len(data) < size:
            packet = conn.recv(size - len(data))
            if not packet:
                return None
            data += packet
        return data


class FileSender:
    def __init__(self):
        self.transfer_callback = None
        
    def send_file(self, file_path, target_ip, target_port=50002):
        """发送文件到目标设备"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        try:
            # 获取文件信息
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            print(f"开始发送文件: {file_name} 到 {target_ip}:{target_port}, 大小: {file_size} bytes")
            
            # 创建连接
            sock = create_tcp_client_socket()
            sock.connect((target_ip, target_port))
            
            # 发送文件信息
            import json
            file_info = {
                'name': file_name,
                'size': file_size
            }
            header_json = json.dumps(file_info)
            header_bytes = header_json.encode('utf-8')
            header_size = len(header_bytes)
            
            # 先发送头部长度，再发送头部内容
            sock.sendall(header_size.to_bytes(4, 'big'))
            sock.sendall(header_bytes)
            
            # 发送文件内容
            sent_size = 0
            with open(file_path, 'rb') as f:
                while sent_size < file_size:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    # 检查中断信号
                    if self.transfer_callback and hasattr(self.transfer_callback, 'interrupted') and self.transfer_callback.interrupted:
                        print(f"\n传输被用户中断: {file_name}")
                        raise InterruptedError("传输被用户中断")
                    
                    sock.sendall(chunk)
                    sent_size += len(chunk)
                    
                    # 计算进度
                    progress = (sent_size / file_size) * 100
                    print(f"\r发送进度: {progress:.1f}% ({sent_size}/{file_size})", end='', flush=True)
                    
                    # 调用回调函数更新UI
                    if self.transfer_callback:
                        self.transfer_callback(sent_size, file_size)
            
            print(f"\n文件发送完成: {file_name}")
            
            # 等待确认
            try:
                sock.settimeout(10)  # 设置10秒超时等待确认
                response = sock.recv(1024)
                if response == b"OK":
                    print("接收方确认收到文件")
                else:
                    print(f"接收方返回未知响应: {response.decode('utf-8', errors='ignore')}")
            except socket.timeout:
                print("等待接收方确认超时")
                raise TimeoutError("等待接收方确认超时")
            except socket.error as se:
                print(f"接收确认消息时发生网络错误: {se}")
                raise
                
        except InterruptedError:
            print("传输被中断")
            raise
        except FileNotFoundError:
            print(f"文件不存在: {file_path}")
            raise
        except ConnectionRefusedError:
            print(f"无法连接到目标设备: {target_ip}:{target_port}")
            raise
        except socket.timeout:
            print(f"连接目标设备超时: {target_ip}:{target_port}")
            raise
        except Exception as e:
            print(f"发送文件时出错: {e}")
            raise
        finally:
            sock.close()