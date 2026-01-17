# LAN File Share System
# 主程序入口

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import socket

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from client.client_app import ClientApp
from server.server_app import ServerApp

import time

class ProgressTracker:
    """用于跟踪传输进度的类"""
    def __init__(self, app):
        self.app = app
        self.start_time = None
        self.last_update_time = None
        self.last_sent_size = 0
        self.interrupted = False  # 添加中断标志
    
    def interrupt(self):
        """中断传输"""
        self.interrupted = True
    
    def reset(self):
        """重置中断标志"""
        self.interrupted = False
        
    def update_progress(self, sent_size, total_size):
        """更新进度条和传输速度"""
        current_time = time.time()
        
        if self.start_time is None:
            self.start_time = current_time
            self.last_update_time = current_time
            self.last_sent_size = 0
        
        if total_size > 0:
            progress = (sent_size / total_size) * 100
            self.app.progress_bar['value'] = progress
            self.app.progress_label.config(text=f"传输进度: {progress:.1f}% ({sent_size}/{total_size} bytes)")
            
            # 计算传输速度（每秒更新一次）
            if current_time - self.last_update_time >= 1.0:  # 每秒更新一次速度
                time_diff = current_time - self.last_update_time
                size_diff = sent_size - self.last_sent_size
                speed_kbps = (size_diff / 1024) / time_diff if time_diff > 0 else 0
                
                self.app.speed_label.config(text=f"速度: {speed_kbps:.1f} KB/s")
                
                self.last_update_time = current_time
                self.last_sent_size = sent_size
            
            self.app.root.update_idletasks()


class LANFileShareApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("局域网文件共享系统")
        self.root.geometry("800x600")
        
        # 设置窗口最小尺寸
        self.root.minsize(960, 500)
        
        # 配置窗口的行列权重，使内容随窗口大小变化
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 设置现代化配色方案
        self.colors = {
            'primary': '#1E88E5',      # 主色调（深蓝色）
            'secondary': '#E3F2FD',    # 次要色调（浅蓝）
            'accent': '#FFB74D',       # 强调色（浅橙色）
            'success': '#81C784',      # 成功色（浅绿色）
            'danger': '#E57373',       # 危险色（浅红色）
            'background': '#FFFFFF',   # 背景色（白色）
            'text': '#212121',         # 文字色（深灰）
            'border': '#BBDEFB'        # 边框色（淡蓝）
        }
        
        # 配置渐变背景
        self.setup_gradient_background()
        
        # 应用样式配置
        self.style = ttk.Style()
        self.style.theme_use('clam')  # 使用clam主题获得更好的外观
        
        # 配置样式
        self.style.configure('.', font=('微软雅黑', 9))  # 全局字体设置
        self.style.configure('TButton', font=('微软雅黑', 9, 'bold'))
        self.style.configure('TLabel', foreground=self.colors['text'])
        self.style.configure('Title.TLabel', font=('微软雅黑', 16, 'bold'), foreground=self.colors['primary'])
        self.style.configure('IP.TLabel', font=('微软雅黑', 10, 'italic'), foreground=self.colors['accent'])
        
        # 设置窗口背景色
        self.root.configure(bg=self.colors['secondary'])
        
        # 初始化客户端和服务端
        self.client = ClientApp()
        self.server = ServerApp()
        
        # 启动服务端（文件接收）
        self.server.start()
        
        # 初始化传输历史记录
        self.transfer_history = []
        
        self.setup_ui()
        
        # 初始化状态信息（在UI组件创建后）
        self.update_status_info()
        
        # 启动活动指示器动画
        self.animate_activity_indicator()
    
    def setup_gradient_background(self):
        """设置渐变背景"""
        # 创建Canvas作为背景
        self.background_canvas = tk.Canvas(self.root, highlightthickness=0)
        self.background_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # 绘制渐变背景
        self.draw_gradient_background()
        
        # 绑定窗口大小变化事件
        self.root.bind('<Configure>', self.on_window_resize)

    def draw_gradient_background(self):
        """绘制渐变背景"""
        # 清除画布
        self.background_canvas.delete("all")
        
        # 获取窗口大小
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        # 如果窗口还未初始化，使用默认大小
        if width <= 1 or height <= 1:
            width, height = 800, 600
        
        # 绘制渐变背景
        for i in range(height):
            # 计算渐变颜色
            r = int(245 + (255 - 245) * i / height)
            g = int(245 + (250 - 245) * i / height) 
            b = int(245 + (255 - 245) * i / height)
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            # 绘制线条
            self.background_canvas.create_line(0, i, width, i, fill=color)
        
        # 在背景上绘制装饰元素
        self.draw_decorative_elements(width, height)
    
    def draw_decorative_elements(self, width, height):
        """绘制装饰元素"""
        # 绘制一些半透明的圆形装饰
        import random
        for _ in range(3):  # 减少装饰元素数量
            x = random.randint(0, width)
            y = random.randint(0, height)
            radius = random.randint(20, 60)
            
            # 使用固定颜色，不带透明度
            color = '#E3F2FD' if random.choice([True, False]) else '#BBDEFB'
            
            self.background_canvas.create_oval(
                x-radius, y-radius, x+radius, y+radius,
                fill=color, outline=color, width=1
            )
    
    def on_window_resize(self, event=None):
        """窗口大小变化事件处理"""
        # 只有在主窗口调整大小时才重绘背景
        if event.widget == self.root:
            # 使用after来延迟绘制，避免频繁重绘
            if hasattr(self, '_resize_after_id'):
                self.root.after_cancel(self._resize_after_id)
            self._resize_after_id = self.root.after(100, self.draw_gradient_background)

    def get_local_ip(self):
        """获取本机IP地址"""
        try:
            # 创建一个UDP连接来获取本机IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    def setup_ui(self):
        # 创建主界面
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置主界面的列权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 主标题（居中显示）
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))
        title_frame.columnconfigure(0, weight=1)
        
        # 创建带有状态指示的标题
        title_container = ttk.Frame(title_frame)
        title_container.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 状态指示器
        self.status_indicator = tk.Canvas(title_container, width=12, height=12, highlightthickness=0)
        self.status_indicator.grid(row=0, column=0, padx=(0, 10))
        
        # 绘制初始状态圆点
        self.status_indicator.create_oval(6, 6, 12, 12, fill='#4CAF50', outline='')
        
        title_label = ttk.Label(title_container, text="局域网文件共享系统", style='Title.TLabel')
        title_label.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # 状态标签
        self.status_text_label = ttk.Label(title_container, text="就绪", font=('微软雅黑', 9))
        self.status_text_label.grid(row=0, column=2, padx=(10, 0))
        
        # 网络状态指示器
        self.network_status_indicator = tk.Canvas(title_container, width=12, height=12, highlightthickness=0)
        self.network_status_indicator.grid(row=0, column=3, padx=(10, 0))
        self.network_status_indicator.create_oval(6, 6, 12, 12, fill='#2196F3', outline='')
        
        self.network_status_label = ttk.Label(title_container, text="网络就绪", font=('微软雅黑', 9))
        self.network_status_label.grid(row=0, column=4, padx=(5, 0))
        
        # 显示本机IP地址
        ip_frame = ttk.Frame(main_frame)
        ip_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))
        self.local_ip = self.get_local_ip()
        ip_label = ttk.Label(ip_frame, text=f"本机IP: {self.local_ip}", style='IP.TLabel')
        ip_label.grid(row=0, column=0, sticky=(tk.W,))
        
        # 设备发现区域（左列）
        discovery_frame = ttk.LabelFrame(main_frame, text="设备发现", padding="10")
        discovery_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10), padx=(0, 5))
        discovery_frame.rowconfigure(1, weight=1)
        
        # 第一行：刷新按钮和手动连接区域
        control_frame = ttk.Frame(discovery_frame)
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.refresh_btn = ttk.Button(control_frame, text="🔄 刷新设备", command=self.refresh_devices)
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 手动连接区域
        ttk.Label(control_frame, text="🌐 IP地址:").pack(side=tk.LEFT)
        self.manual_ip_entry = ttk.Entry(control_frame, width=12)
        self.manual_ip_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        self.manual_connect_btn = ttk.Button(control_frame, text="➕ 添加", command=self.add_manual_device)
        self.manual_connect_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # 设备列表
        self.device_listbox = tk.Listbox(discovery_frame, height=8, font=('Consolas', 10))
        self.device_listbox.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
        # 添加滚动条
        device_scrollbar = ttk.Scrollbar(discovery_frame, orient="vertical", command=self.device_listbox.yview)
        device_scrollbar.grid(row=1, column=2, sticky=(tk.N, tk.S))
        self.device_listbox.configure(yscrollcommand=device_scrollbar.set)
        
        # 添加设备状态更新定时器
        self.update_device_status_periodically()
        
        # 传输历史区域（右列，与设备发现区域高度对齐）
        history_frame = ttk.LabelFrame(main_frame, text="传输历史", padding="5")
        history_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5), padx=(5, 0))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        
        # 传输历史列表
        self.history_listbox = tk.Listbox(history_frame, height=6)
        self.history_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 添加滚动条
        history_scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_listbox.yview)
        history_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.history_listbox.configure(yscrollcommand=history_scrollbar.set)
        
        # 系统信息区域（紧接在传输历史下方，与设备发现区域底部对齐）
        info_frame = ttk.LabelFrame(main_frame, text="系统信息", padding="5")
        info_frame.grid(row=3, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0), padx=(5, 0))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(1, weight=1)
        
        # 添加当前状态信息
        status_label = ttk.Label(info_frame, text="当前状态", font=('微软雅黑', 10, 'bold'))
        status_label.grid(row=0, column=0, sticky=(tk.W,), pady=(0, 5))
        
        # 状态详情
        self.status_detail = tk.Text(info_frame, height=4, wrap=tk.WORD, state=tk.DISABLED, bg='#f9f9f9', relief=tk.FLAT)
        self.status_detail.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 添加滚动条
        status_scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=self.status_detail.yview)
        status_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.status_detail.configure(yscrollcommand=status_scrollbar.set)
        
        # 文件传输区域（在设备发现区域下方，与设备发现区域长度一致）
        transfer_frame = ttk.LabelFrame(main_frame, text="文件传输", padding="10")
        transfer_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0), padx=(0, 5))
        transfer_frame.rowconfigure(1, weight=1)
        
        # 顶部控制按钮行
        control_buttons_frame = ttk.Frame(transfer_frame)
        control_buttons_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.select_file_btn = ttk.Button(control_buttons_frame, text="📁 选择文件", command=self.select_file)
        self.select_file_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_file_btn = ttk.Button(control_buttons_frame, text="🗑️ 清除文件", command=self.clear_selected_files)
        self.clear_file_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.interrupt_transfer_btn = ttk.Button(control_buttons_frame, text="⏹️ 终止传输", command=self.interrupt_current_transfer)
        self.interrupt_transfer_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.interrupt_transfer_btn.config(state=tk.DISABLED)  # 初始禁用
        
        self.send_file_btn = ttk.Button(control_buttons_frame, text="📤 发送文件", command=self.send_file, state=tk.DISABLED)
        self.send_file_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 文件列表
        self.file_listbox = tk.Listbox(transfer_frame, height=3)
        self.file_listbox.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 添加滚动条
        file_scrollbar = ttk.Scrollbar(transfer_frame, orient="vertical", command=self.file_listbox.yview)
        file_scrollbar.grid(row=1, column=3, sticky=(tk.N, tk.S), padx=(0, 10))
        self.file_listbox.configure(yscrollcommand=file_scrollbar.set)
        
        # 添加右键菜单以删除单个文件
        self.file_listbox_menu = tk.Menu(self.root, tearoff=0)
        self.file_listbox_menu.add_command(label="删除选中文件", command=self.remove_single_file)
        
        # 绑定右键点击事件
        self.file_listbox.bind("<Button-3>", self.show_file_menu)
        
        # 进度条
        progress_frame = ttk.Frame(transfer_frame)
        progress_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 0))
        progress_frame.columnconfigure(0, weight=1)
        
        # 创建带活动指示器的进度标签
        progress_container = ttk.Frame(progress_frame)
        progress_container.grid(row=0, column=0, sticky=(tk.W,), columnspan=2)
        
        self.activity_indicator = tk.Canvas(progress_container, width=10, height=10, highlightthickness=0)
        self.activity_indicator.grid(row=0, column=0, padx=(0, 5))
        self.activity_indicator.create_oval(5, 5, 10, 10, fill='#9E9E9E', outline='')  # 默认灰色
        
        self.progress_label = ttk.Label(progress_container, text="准备就绪")
        self.progress_label.grid(row=0, column=1, sticky=(tk.W,))
        
        # 传输速度标签
        self.speed_label = ttk.Label(progress_frame, text="速度: -- KB/s")
        self.speed_label.grid(row=1, column=0, sticky=(tk.E,), padx=(0, 0), pady=(5, 0))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 传输活动指示器
        self.transfer_activity = False
        self.activity_color_index = 0
        self.activity_colors = ['#9E9E9E', '#607D8B', '#78909C', '#90A4AE']
        
        # 初始化状态信息
        self.update_status_info()
        
        # 启动状态信息定时更新
        self.start_status_timer()
        
        # 配置网格权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        discovery_frame.columnconfigure(0, weight=1)
        history_frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(1, weight=1)
        transfer_frame.columnconfigure(0, weight=1)
        transfer_frame.rowconfigure(1, weight=1)
        progress_frame.columnconfigure(0, weight=1)
    
    def refresh_devices(self):
        """刷新设备列表"""
        devices = self.client.discover_devices()
        self.device_listbox.delete(0, tk.END)
        for device in devices:
            self.device_listbox.insert(tk.END, f"{device['ip']} - {device['hostname']}")
    
    def add_manual_device(self):
        """手动添加设备"""
        ip_address = self.manual_ip_entry.get().strip()
        if ip_address:
            # 验证IP地址格式
            try:
                parts = ip_address.split('.')
                if len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts):
                    # 检查是否已存在
                    device_exists = False
                    for i in range(self.device_listbox.size()):
                        if self.device_listbox.get(i).startswith(ip_address + " - "):
                            device_exists = True
                            break
                    
                    if not device_exists:
                        self.device_listbox.insert(tk.END, f"{ip_address} - 手动添加")
                        self.manual_ip_entry.delete(0, tk.END)
                        messagebox.showinfo("提示", f"已添加设备: {ip_address}")
                    else:
                        messagebox.showwarning("警告", "该设备已存在于列表中")
                else:
                    messagebox.showerror("错误", "请输入有效的IP地址")
            except:
                messagebox.showerror("错误", "请输入有效的IP地址")
        else:
            messagebox.showwarning("警告", "请输入IP地址")
    
    def add_to_history(self, file_name, target_ip, status):
        """添加传输记录到历史列表"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 根据状态添加相应图标
        if status == "发送成功":
            icon = "✅"
        elif status == "发送失败":
            icon = "❌"
        elif status == "发送错误":
            icon = "⚠️"
        else:
            icon = "ℹ️"
        
        history_entry = f"[{timestamp}] {icon} {status}: {os.path.basename(file_name)} -> {target_ip}"
        
        self.transfer_history.append(history_entry)
        
        # 限制历史记录数量，最多保留50条
        if len(self.transfer_history) > 50:
            self.transfer_history.pop(0)
        
        # 更新历史列表显示
        self.update_history_display()
    
    def update_history_display(self):
        """更新历史记录显示"""
        self.history_listbox.delete(0, tk.END)
        for entry in self.transfer_history:
            self.history_listbox.insert(tk.END, entry)
        
        # 滚动到底部显示最新记录
        if self.transfer_history:
            self.history_listbox.see(tk.END)
    
    def update_status_info(self):
        """更新系统状态信息"""
        # 获取当前状态信息
        # 检查组件是否存在，避免初始化时出错
        device_count = getattr(self, 'device_listbox', None)
        if device_count:
            device_count = self.device_listbox.size()
        else:
            device_count = 0
            
        status_text = f"""• 本机IP: {self.get_local_ip()}
• 设备数量: {device_count} 个
• 已传输文件: {len(self.transfer_history)} 条记录
• 当前时间: {time.strftime('%H:%M:%S')}"""
        
        # 更新状态文本框
        try:
            self.status_detail.config(state=tk.NORMAL)
            self.status_detail.delete(1.0, tk.END)
            self.status_detail.insert(1.0, status_text)
            self.status_detail.config(state=tk.DISABLED)
        except AttributeError:
            # 如果组件尚未初始化，则跳过更新
            pass
    
    def start_status_timer(self):
        """启动状态信息定时更新"""
        self.update_status_periodically()
    
    def update_device_status_periodically(self):
        """周期性更新设备状态"""
        # 这里可以实现设备在线状态检查
        # 暂时只更新时间戳
        self.root.after(5000, self.update_device_status_periodically)  # 每5秒更新一次

    def animate_activity_indicator(self):
        """动画活动指示器"""
        if self.transfer_activity:
            # 传输活动中，循环显示颜色
            color = self.activity_colors[self.activity_color_index % len(self.activity_colors)]
            self.activity_indicator.delete("all")
            self.activity_indicator.create_oval(5, 5, 10, 10, fill=color, outline='')
            self.activity_color_index = (self.activity_color_index + 1) % len(self.activity_colors)
        else:
            # 非活动状态，显示灰色
            self.activity_indicator.delete("all")
            self.activity_indicator.create_oval(5, 5, 10, 10, fill='#9E9E9E', outline='')
        
        # 每200毫秒更新一次
        self.root.after(200, self.animate_activity_indicator)

    def update_status_periodically(self):
        """周期性更新状态信息"""
        self.update_status_info()
        # 每秒更新一次
        self.root.after(1000, self.update_status_periodically)
    
    def refresh_devices(self):
        """刷新设备列表"""
        devices = self.client.discover_devices()
        self.device_listbox.delete(0, tk.END)
        for device in devices:
            self.device_listbox.insert(tk.END, f"{device['ip']} - {device['hostname']}")
        # 更新状态信息
        self.update_status_info()
    
    def select_file(self):
        """选择要发送的文件"""
        # 如果已有选中的文件，先保存它们
        existing_files = getattr(self, 'selected_files', [])
        
        # 弹出文件选择对话框
        new_filenames = filedialog.askopenfilenames(title="选择要发送的文件")
        if new_filenames:
            # 将新选择的文件添加到现有文件列表中（去重）
            all_filenames = existing_files + list(new_filenames)
            # 去重但保持顺序
            unique_filenames = []
            for f in all_filenames:
                if f not in unique_filenames:
                    unique_filenames.append(f)
            
            self.selected_files = unique_filenames
            self.file_listbox.delete(0, tk.END)
            for filename in unique_filenames:
                file_size = os.path.getsize(filename)
                display_name = f"{os.path.basename(filename)} ({round(file_size / (1024*1024), 2)} MB)"
                self.file_listbox.insert(tk.END, display_name)
            self.send_file_btn.config(state=tk.NORMAL)

    def clear_selected_files(self):
        """清除已选择的文件"""
        if hasattr(self, 'selected_files'):
            delattr(self, 'selected_files')
        self.file_listbox.delete(0, tk.END)
        self.send_file_btn.config(state=tk.DISABLED)

    def show_file_menu(self, event):
        """显示文件列表右键菜单"""
        # 选中鼠标右击位置的项目
        selection = self.file_listbox.nearest(event.y)
        self.file_listbox.selection_clear(0, tk.END)
        self.file_listbox.selection_set(selection)
        
        # 显示右键菜单
        try:
            self.file_listbox_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.file_listbox_menu.grab_release()

    def remove_single_file(self, event=None):
        """从已选列表中移除单个文件"""
        selection = self.file_listbox.curselection()
        if selection and hasattr(self, 'selected_files'):
            # 获取选中的索引
            index = selection[0]
            # 从列表中移除对应文件
            del self.selected_files[index]
            
            # 如果列表为空，禁用发送按钮
            if not self.selected_files:
                delattr(self, 'selected_files')
                self.send_file_btn.config(state=tk.DISABLED)
            
            # 更新界面显示
            self.file_listbox.delete(index)
            # 如果还有剩余文件，重新填充列表
            if hasattr(self, 'selected_files') and self.selected_files:
                # 重新填充列表（因为删除项后索引可能变化）
                self.file_listbox.delete(0, tk.END)
                for filename in self.selected_files:
                    file_size = os.path.getsize(filename)
                    display_name = f"{os.path.basename(filename)} ({round(file_size / (1024*1024), 2)} MB)"
                    self.file_listbox.insert(tk.END, display_name)
            else:
                self.send_file_btn.config(state=tk.DISABLED)

    def interrupt_current_transfer(self):
        """中断当前传输"""
        if hasattr(self, 'current_progress_tracker'):
            self.current_progress_tracker.interrupt()
            self.interrupt_transfer_btn.config(state=tk.DISABLED)
            messagebox.showinfo("提示", "正在中断当前传输...")
    
    def send_file(self):
        """发送选定的文件"""
        if not hasattr(self, 'selected_files') or len(self.selected_files) == 0:
            messagebox.showwarning("警告", "请先选择要发送的文件")
            return
        
        selection = self.device_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择目标设备")
            return
        
        # 获取选中设备信息
        device_info = self.device_listbox.get(selection[0])
        target_ip = device_info.split(' - ')[0]  # 提取IP地址
        
        # 确认发送操作
        confirm = messagebox.askyesno("确认发送", f"确定要向设备 {target_ip} 发送 {len(self.selected_files)} 个文件吗？\n\n{', '.join([os.path.basename(f) for f in self.selected_files[:3]])}{'...' if len(self.selected_files) > 3 else ''}")
        if not confirm:
            return
        
        # 创建进度跟踪器
        self.current_progress_tracker = ProgressTracker(self)
        
        # 启用终止传输按钮
        self.interrupt_transfer_btn.config(state=tk.NORMAL)
        
        # 设置传输活动状态
        self.transfer_activity = True
        
        # 开始批量文件传输
        try:
            for i, file_path in enumerate(self.selected_files):
                self.progress_label.config(text=f"正在发送 ({i+1}/{len(self.selected_files)}): {os.path.basename(file_path)}")
                self.progress_bar['value'] = 0  # 重置进度条
                self.speed_label.config(text="速度: -- KB/s")
                
                success = self.client.send_file_to_device(file_path, target_ip, progress_callback=self.current_progress_tracker)
                if success:
                    self.progress_label.config(text=f"发送完成 ({i+1}/{len(self.selected_files)}): {os.path.basename(file_path)}")
                    self.progress_bar['value'] = 100
                    # 添加成功记录到历史
                    self.add_to_history(file_path, target_ip, "发送成功")
                else:
                    self.progress_label.config(text=f"发送失败 ({i+1}/{len(self.selected_files)}): {os.path.basename(file_path)}")
                    # 添加失败记录到历史
                    self.add_to_history(file_path, target_ip, "发送失败")
                    messagebox.showerror("错误", f"文件 {os.path.basename(file_path)} 发送失败！")
            
            messagebox.showinfo("成功", f"{len(self.selected_files)} 个文件全部发送完成！")
            
            # 重置进度条和速度显示
            self.progress_bar['value'] = 0
            self.speed_label.config(text="速度: -- KB/s")
            
            # 更新状态信息
            self.update_status_info()
            
        except InterruptedError:
            self.progress_label.config(text="传输被用户中断")
            self.progress_bar['value'] = 0
            self.speed_label.config(text="速度: -- KB/s")
            messagebox.showinfo("提示", "文件传输已被用户中断")
        except FileNotFoundError as fnf_error:
            self.progress_label.config(text="文件未找到")
            self.progress_bar['value'] = 0
            self.speed_label.config(text="速度: -- KB/s")
            messagebox.showerror("错误", f"找不到文件: {fnf_error}")
        except ConnectionRefusedError:
            self.progress_label.config(text="连接被拒绝")
            self.progress_bar['value'] = 0
            self.speed_label.config(text="速度: -- KB/s")
            messagebox.showerror("错误", f"无法连接到目标设备 {target_ip}，可能设备不在线或防火墙阻止了连接。")
        except TimeoutError:
            self.progress_label.config(text="连接超时")
            self.progress_bar['value'] = 0
            self.speed_label.config(text="速度: -- KB/s")
            messagebox.showerror("错误", f"连接到目标设备 {target_ip} 超时，请检查网络连接。")
        except Exception as e:
            self.progress_label.config(text="发送失败")
            self.progress_bar['value'] = 0
            self.speed_label.config(text="速度: -- KB/s")
            # 添加错误记录到历史
            for file_path in self.selected_files:
                self.add_to_history(file_path, target_ip, "发送错误")
            messagebox.showerror("错误", f"发送过程中出现错误: {str(e)}")
        finally:
            # 禁用终止传输按钮
            self.interrupt_transfer_btn.config(state=tk.DISABLED)
            # 重置进度跟踪器
            if hasattr(self, 'current_progress_tracker'):
                self.current_progress_tracker.reset()
            # 重置传输活动状态
            self.transfer_activity = False
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """关闭窗口时的清理操作"""
        self.client.stop()
        self.server.stop()
        self.root.destroy()


if __name__ == "__main__":
    app = LANFileShareApp()
    app.run()