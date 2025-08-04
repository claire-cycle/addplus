import requests
import json
import os
import threading
import time
from datetime import datetime
import urllib3
import argparse
import concurrent.futures
import sys

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PointClaimCLI:
    def __init__(self):
        # 控制变量
        self.is_running = True
        self.client_username_file = "client_username.json"
        self.processed_count = 0
        self.success_count = 0
        self.lock = threading.Lock()  # 用于线程安全的计数器更新
        self.accounts = []
        self.max_workers = 5  # 默认线程数
    
    def log_message(self, message):
        """输出日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
    
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
                return True
            else:
                return False
                
        except requests.exceptions.RequestException:
            return False
        except Exception:
            return False
    
    def process_username(self, username_data, account_index):
        """处理单个用户名的涨分请求"""
        if not self.is_running:
            return False
        
        username = username_data.get("username")
        number = username_data.get("number")
        cookie = self.accounts[account_index % len(self.accounts)]
        
        success = self.send_claim_request(username, cookie)
        
        with self.lock:
            self.processed_count += 1
            if success:
                self.success_count += 1
                self.log_message(f"✅ #{number} - {username} - 涨分成功 (账户 {account_index % len(self.accounts) + 1})")
            else:
                self.log_message(f"❌ #{number} - {username} - 涨分失败 (账户 {account_index % len(self.accounts) + 1})")
        
        return success
    
    def load_accounts(self, accounts_file):
        """从配置文件加载账户信息"""
        try:
            if not os.path.exists(accounts_file):
                self.log_message(f"账户配置文件 {accounts_file} 不存在")
                return False
            
            with open(accounts_file, 'r', encoding='utf-8') as f:
                accounts_data = json.load(f)
            
            if not isinstance(accounts_data, list) or len(accounts_data) == 0:
                self.log_message("账户配置文件格式错误或为空")
                return False
            
            self.accounts = [account.get("cookie", "") for account in accounts_data if account.get("cookie")]
            
            if not self.accounts:
                self.log_message("未找到有效的账户Cookie")
                return False
            
            self.log_message(f"成功加载 {len(self.accounts)} 个账户")
            return True
            
        except json.JSONDecodeError:
            self.log_message("账户配置文件不是有效的JSON格式")
            return False
        except Exception as e:
            self.log_message(f"加载账户配置文件时出错: {str(e)}")
            return False
    
    def claim_process(self):
        """涨分处理流程"""
        try:
            if not self.accounts:
                self.log_message("❌ 未加载任何账户，请先配置账户")
                return
            
            self.log_message("🚀 开始涨分...")
            
            # 1. 从API获取用户名数据
            api_usernames = self.get_usernames_from_api()
            if not api_usernames:
                self.log_message("❌ 无法获取用户名数据，停止处理")
                return
            
            # 2. 更新client_username文件
            client_data = self.update_client_username_data(api_usernames)
            if not client_data:
                self.log_message("❌ 没有可处理的用户名数据")
                return
            
            # 3. 使用线程池并发处理涨分请求
            self.log_message(f"开始处理 {len(client_data)} 个涨分链接，使用 {self.max_workers} 个线程...")
            self.processed_count = 0
            self.success_count = 0
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 为每个用户名分配一个账户（循环使用）
                futures = {executor.submit(self.process_username, user_data, i): i 
                          for i, user_data in enumerate(client_data)}
                
                for future in concurrent.futures.as_completed(futures):
                    if not self.is_running:
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
                    try:
                        future.result()  # 获取结果，但我们不需要使用它
                    except Exception as e:
                        self.log_message(f"处理过程中出错: {str(e)}")
            
            if self.is_running:
                self.log_message(f"🎉 涨分完成！成功: {self.success_count}/{len(client_data)}")
            
        except Exception as e:
            self.log_message(f"❌ 涨分流程出错: {str(e)}")
        finally:
            self.is_running = False
    
    def handle_interrupt(self):
        """处理中断信号"""
        self.log_message("🛑 正在停止处理流程...")
        self.is_running = False

def main():
    parser = argparse.ArgumentParser(description="Add+ 涨分工具 CLI版本")
    parser.add_argument("-a", "--accounts", default="accounts.json", help="账户配置文件路径")
    parser.add_argument("-t", "--threads", type=int, default=5, help="线程数量")
    args = parser.parse_args()
    
    app = PointClaimCLI()
    app.max_workers = args.threads
    
    # 加载账户配置
    if not app.load_accounts(args.accounts):
        print(f"请创建账户配置文件 {args.accounts}，格式如下：")
        print('''[
  {
    "name": "账户1",
    "cookie": "你的完整cookie字符串"
  },
  {
    "name": "账户2",
    "cookie": "另一个cookie字符串"
  }
]''')
        return
    
    try:
        # 注册中断处理
        def signal_handler(sig, frame):
            app.handle_interrupt()
            sys.exit(0)
        
        import signal
        signal.signal(signal.SIGINT, signal_handler)
        
        # 开始涨分流程
        app.claim_process()
        
    except KeyboardInterrupt:
        app.handle_interrupt()

if __name__ == "__main__":
    main()