## 功能介绍

这是一个用于 AddPlus 平台自动涨分的 GUI 工具，具有以下功能：

- 🍪 **Cookie 管理**：输入和保存用户的 Cookie 信息
- 📊 **数据同步**：自动从服务器获取用户名数据
- 💾 **智能存储**：只保存新增的用户名数据到本地文件
- 🚀 **自动涨分**：批量发送涨分请求到 AddPlus 平台
- 📝 **实时日志**：显示详细的操作日志和状态信息

## 使用步骤

### 1. 启动工具

```bash
python addplus.py
```

### 2. 输入 Cookie

在 Cookie 输入框中粘贴从浏览器获取的完整 Cookie 字符串。

**获取 Cookie 的方法：**
1. 打开浏览器，访问 `https://addplus.org`
2. 按 F12 打开开发者工具
3. 切换到 Network 标签页
4. 刷新页面或进行任何操作
5. 找到任意请求，查看 Request Headers 中的 Cookie 字段
6. 复制完整的 Cookie 值

<img width="1864" height="1306" alt="image" src="https://github.com/user-attachments/assets/fa17cba9-512f-4d61-88f9-bf574e4c852e" />


### 3. 点击涨分启动

点击「开始涨分」按钮，工具将自动执行以下流程：

1. **获取数据**：从 服务器获取最新的用户名列表
2. **数据处理**：检查本地 `client_username.json` 文件，只保存新增的用户名
3. **发送请求**：为每个用户名发送涨分请求到 AddPlus 平台
4. **显示结果**：在日志区域显示每个请求的成功/失败状态

### 4. 监控状态

- 📊 **进度条**：显示当前处理进度
- 📝 **状态日志**：实时显示操作日志
- ⏹️ **停止按钮**：可随时停止处理流程

## 文件说明

### client_username.json

存储用户名数据的本地文件，格式如下：

```json
[
  {
    "number": 1,
    "username": "testuser123"
  },
  {
    "number": 2,
    "username": "anotheruser456"
  }
]
```

### 数据同步逻辑

- 工具会检查本地文件中的最大编号
- 只从 API 获取编号大于本地最大编号的新数据
- 避免重复处理已有的用户名
