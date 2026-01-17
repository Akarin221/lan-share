# 网络配置常量
import socket

# UDP 广播相关配置
UDP_PORT = 50001  # 设备发现端口
UDP_BROADCAST_ADDR = '<broadcast>'
UDP_TIMEOUT = 5  # 秒

# TCP 文件传输相关配置
TCP_PORT_RANGE_START = 50002  # TCP 传输端口范围起始
TCP_PORT_RANGE_END = 50100    # TCP 传输端口范围结束

# 设备信息
LOCAL_HOSTNAME = socket.gethostname()
LOCAL_IP = socket.gethostbyname(socket.gethostname())

# 文件传输相关配置
CHUNK_SIZE = 1024 * 1024  # 1MB chunks