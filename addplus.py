import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
import os
import threading
import time
from datetime import datetime
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PointClaimGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Add+ 涨分机器人 by wanfeng")
        self.root.geometry("800x650")
        self.root.configure(bg='#f0f0f0')
        
        # 设置样式
        self.setup_styles()
        
        # 创建主框架
        main_frame = ttk.Frame(root, style='Main.TFrame', padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题区域
        title_frame = ttk.Frame(main_frame, style='Title.TFrame')
        title_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="🎯 Add+ 自动涨分工具", style='Title.TLabel')
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="智能获取用户名并自动增长积分", style='Subtitle.TLabel')
        subtitle_label.pack(pady=(5, 0))
        
        # Cookie输入区域
        cookie_frame = ttk.LabelFrame(main_frame, text="🍪 Cookie 配置", style='Section.TLabelframe', padding="15")
        cookie_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        cookie_info = ttk.Label(cookie_frame, text="请粘贴您的 AddPlus 网站 Cookie：", style='Info.TLabel')
        cookie_info.pack(anchor='w', pady=(0, 8))
        
        self.cookie_text = scrolledtext.ScrolledText(cookie_frame, height=6, width=80, 
                                                    font=('Consolas', 10), wrap=tk.WORD,
                                                    bg='#ffffff', fg='#333333', 
                                                    selectbackground='#0078d4', selectforeground='white')
        self.cookie_text.pack(fill='both', expand=True)
        
        # 控制按钮区域
        control_frame = ttk.LabelFrame(main_frame, text="⚡ 操作控制", style='Section.TLabelframe', padding="15")
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        button_container = ttk.Frame(control_frame)
        button_container.pack(fill='x')
        
        self.start_button = ttk.Button(button_container, text="🚀 开始涨分", command=self.start_claim_process, style='Start.TButton')
        self.start_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.stop_button = ttk.Button(button_container, text="⏹️ 停止运行", command=self.stop_process, state=tk.DISABLED, style='Stop.TButton')
        self.stop_button.pack(side=tk.LEFT)
        
        # 状态信息区域
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill='x', pady=(15, 0))
        
        self.status_label = ttk.Label(status_frame, text="📊 状态：就绪", style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT)
        
        self.count_label = ttk.Label(status_frame, text="📈 处理数量：0", style='Status.TLabel')
        self.count_label.pack(side=tk.RIGHT)
        
        # 进度条
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate', style='Custom.Horizontal.TProgressbar')
        self.progress.pack(fill='x', pady=(10, 0))
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="📋 运行日志", style='Section.TLabelframe', padding="15")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=18, width=80,
                                                 font=('Consolas', 9), wrap=tk.WORD,
                                                 bg='#1e1e1e', fg='#ffffff',
                                                 selectbackground='#264f78', selectforeground='white',
                                                 insertbackground='white')
        self.log_text.pack(fill='both', expand=True)
        
        # 配置网格权重
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        cookie_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 控制变量
        self.is_running = False
        self.client_username_file = "client_username.json"
        self.processed_count = 0
        
        self.log_message("🎉 GUI工具已启动，请输入Cookie后点击开始涨分")
    
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        
        # 主题配置
        style.configure('Main.TFrame', background='#f0f0f0')
        style.configure('Title.TFrame', background='#f0f0f0')
        
        # 标题样式
        style.configure('Title.TLabel', background='#f0f0f0', foreground='#2c3e50', 
                       font=('Microsoft YaHei UI', 18, 'bold'))
        style.configure('Subtitle.TLabel', background='#f0f0f0', foreground='#7f8c8d', 
                       font=('Microsoft YaHei UI', 10))
        
        # 分组框样式
        style.configure('Section.TLabelframe', background='#f0f0f0', foreground='#34495e',
                       font=('Microsoft YaHei UI', 10, 'bold'))
        style.configure('Section.TLabelframe.Label', background='#f0f0f0', foreground='#34495e',
                       font=('Microsoft YaHei UI', 10, 'bold'))
        
        # 信息标签样式
        style.configure('Info.TLabel', background='#ffffff', foreground='#555555',
                       font=('Microsoft YaHei UI', 9))
        
        # 状态标签样式
        style.configure('Status.TLabel', background='#f0f0f0', foreground='#2980b9',
                       font=('Microsoft YaHei UI', 9, 'bold'))
        
        # 按钮样式
        style.configure('Start.TButton', font=('Microsoft YaHei UI', 10, 'bold'))
        style.configure('Stop.TButton', font=('Microsoft YaHei UI', 10, 'bold'))
        
        # 进度条样式
        style.configure('Custom.Horizontal.TProgressbar', background='#3498db')
    
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_status(self, status_text):
        """更新状态显示"""
        self.status_label.config(text=f"📊 状态：{status_text}")
        self.root.update_idletasks()
    
    def update_count(self, count):
        """更新处理数量显示"""
        self.processed_count = count
        self.count_label.config(text=f"📈 处理数量：{count}")
        self.root.update_idletasks()
    
    def get_usernames_from_api(self):
        """从API获取用户名数据"""
        try:
            self.log_message("正在从API获取用户名数据...")
            response = requests.get("http://81.70.150.62:3000/api/usernames", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                usernames = data.get("data", [])
                self.log_message(f"成功获取到 {len(usernames)} 个用户名")
                return usernames
            else:
                self.log_message("API返回失败状态")
                return []
        except requests.exceptions.RequestException as e:
            self.log_message(f"API请求失败: {str(e)}")
            return []
        except Exception as e:
            self.log_message(f"获取用户名数据时出错: {str(e)}")
            return []
    
    def load_client_username_file(self):
        """加载client_username.json文件"""
        try:
            if os.path.exists(self.client_username_file):
                with open(self.client_username_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
            else:
                return []
        except Exception as e:
            self.log_message(f"加载client_username文件失败: {str(e)}")
            return []
    
    def save_client_username_file(self, data):
        """保存数据到client_username.json文件"""
        try:
            with open(self.client_username_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.log_message(f"已保存 {len(data)} 个用户名到 {self.client_username_file}")
            return True
        except Exception as e:
            self.log_message(f"保存client_username文件失败: {str(e)}")
            return False
    
    def update_client_username_data(self, api_usernames):
        """更新client_username数据"""
        # 加载现有数据
        existing_data = self.load_client_username_file()
        
        # 获取当前最大编号
        max_number = 0
        if existing_data:
            max_number = max([item.get("number", 0) for item in existing_data])
        
        self.log_message(f"当前文件中最大编号: {max_number}")
        
        # 筛选出需要添加的新数据（编号大于当前最大编号）
        new_data = []
        for user in api_usernames:
            if user.get("number", 0) > max_number:
                new_data.append({
                    "number": user.get("number"),
                    "username": user.get("username")
                })
        
        if new_data:
            # 按编号排序
            new_data.sort(key=lambda x: x.get("number", 0))
            
            # 用新数据覆盖整个文件
            if self.save_client_username_file(new_data):
                self.log_message(f"发现 {len(new_data)} 个新用户名，已覆盖保存")
                return new_data
        else:
            self.log_message("没有新的用户名数据需要添加")
            return []
        
        return []
    
    def send_claim_request(self, username, cookie):
        """发送涨分请求"""
        try:
            url = "https://addplus.org/api/trpc/users.claimPoints?batch=1"
            
            headers = {
                "Host": "addplus.org",
                "Connection": "keep-alive",
                "sec-ch-ua-platform": "\"Windows\"",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
                "trpc-accept": "application/jsonl",
                "content-type": "application/json",
                "x-trpc-source": "nextjs-react",
                "sec-ch-ua-mobile": "?0",
                "Accept": "*/*",
                "Origin": "https://addplus.org",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Referer": f"https://addplus.org/boost/{username}",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Cookie": cookie
            }
            
            payload = {
                "0": {
                    "json": {
                        "username": username
                    }
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30, verify=False)
            
            if response.status_code == 200:
                self.log_message(f"✅ {username} - 涨分成功")
                return True
            else:
                self.log_message(f"❌ {username} - 涨分失败 (状态码: {response.status_code})")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_message(f"❌ {username} - 网络请求失败: {str(e)}")
            return False
        except Exception as e:
            self.log_message(f"❌ {username} - 发送请求时出错: {str(e)}")
            return False
    
    def claim_process(self):
        """涨分处理流程"""
        try:
            # 获取Cookie
            cookie = self.cookie_text.get("1.0", tk.END).strip()
            if not cookie:
                self.log_message("❌ 请先输入Cookie")
                self.update_status("错误：缺少Cookie")
                return
            
            self.log_message("🚀 开始涨分...")
            self.update_status("正在获取数据")
            
            # 1. 从API获取用户名数据
            api_usernames = self.get_usernames_from_api()
            if not api_usernames:
                self.log_message("❌ 无法获取用户名数据，停止处理")
                self.update_status("错误：无法获取数据")
                return
            
            # 2. 更新client_username文件
            self.update_status("正在分析数据")
            client_data = self.update_client_username_data(api_usernames)
            if not client_data:
                self.log_message("❌ 没有可处理的用户名数据")
                self.update_status("完成：无新数据")
                return
            
            # 3. 依次发送涨分请求
            self.log_message(f"开始 {len(client_data)} 个涨分链接...")
            self.update_status(f"处理中 (0/{len(client_data)})")
            
            success_count = 0
            for i, user_data in enumerate(client_data):
                if not self.is_running:
                    self.log_message("⏹️ 用户停止了处理流程")
                    self.update_status("已停止")
                    break
                
                username = user_data.get("username")
                number = user_data.get("number")
                
                if username:
                    self.log_message(f"正在处理 #{number} - {username}... ({i+1}/{len(client_data)})")
                    self.update_status(f"处理中 ({i+1}/{len(client_data)})")
                    self.update_count(i+1)
                    
                    if self.send_claim_request(username, cookie):
                        success_count += 1
                    
                    # 添加延迟避免请求过快
                    if self.is_running and i < len(client_data) - 1:  # 不是最后一个
                        time.sleep(2)
            
            if self.is_running:
                self.log_message(f"🎉 涨分完成！成功: {success_count}/{len(client_data)}")
                self.update_status(f"完成 ({success_count}/{len(client_data)} 成功)")
            
        except Exception as e:
            self.log_message(f"❌ 涨分流程出错: {str(e)}")
            self.update_status("错误")
        finally:
            self.is_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.progress.stop()
    
    def start_claim_process(self):
        """启动涨分流程"""
        if not self.is_running:
            # 验证Cookie输入
            cookie = self.cookie_text.get("1.0", tk.END).strip()
            if not cookie:
                messagebox.showwarning("警告", "请先输入Cookie后再开始！")
                return
            
            self.is_running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.progress.start()
            self.update_status("启动中")
            self.update_count(0)
            
            self.log_message("🎯 准备开始涨分...")
            
            # 在新线程中运行涨分流程
            thread = threading.Thread(target=self.claim_process)
            thread.daemon = True
            thread.start()
    
    def stop_process(self):
        """停止处理流程"""
        if self.is_running:
            self.is_running = False
            self.log_message("🛑 正在停止处理流程...")
            self.update_status("正在停止")
        else:
            self.log_message("ℹ️ 当前没有运行中的流程")

def main():
    root = tk.Tk()
    app = PointClaimGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()