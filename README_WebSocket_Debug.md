# WebSocket 认证调试指南

## 🔍 查看认证字段信息

### 1️⃣ 启动服务器
```bash
cd chatgpt_crypto_ai
python run.py
```

### 2️⃣ 运行测试脚本
```bash
python test_auth_debug.py
```

### 3️⃣ 观察服务器终端输出

服务器会打印详细的认证信息：

```
============================================================
🔌 WebSocket连接请求 - 来自: 192.168.100.172
📋 Request Headers: {'Host': '192.168.100.173:5000', 'User-Agent': '...', ...}
📋 Request Args: {}
📋 认证参数类型: <class 'dict'>
📋 认证参数内容: {'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'}
============================================================
✅ auth 参数存在
   auth 类型: <class 'dict'>
   auth 内容: {'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'}
   auth 的键: ['token']
   ✅ 找到 token 字段: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
🔑 从 auth['token'] 获取到token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
✅ WebSocket连接成功 - 用户ID: 4
```

## 📊 测试场景

### ✅ 测试1：正确的auth参数
```python
sio.connect(
    'http://192.168.100.173:5000',
    auth={'token': jwt_token}  # ✅ 正确
)
```

**服务器输出：**
```
📋 认证参数内容: {'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'}
   auth 的键: ['token']
   ✅ 找到 token 字段
✅ WebSocket连接成功 - 用户ID: 4
```

### ❌ 测试2：错误的字段名
```python
sio.connect(
    'http://192.168.100.173:5000',
    auth={'jwt': jwt_token}  # ❌ 错误：应该是 'token'
)
```

**服务器输出：**
```
📋 认证参数内容: {'jwt': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'}
   auth 的键: ['jwt']
   其他字段 jwt: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
❌ WebSocket连接被拒绝：缺少token
```

### ❌ 测试3：无认证信息
```python
sio.connect('http://192.168.100.173:5000')  # ❌ 没有auth参数
```

**服务器输出：**
```
📋 认证参数类型: <class 'NoneType'>
📋 认证参数内容: None
❌ auth 参数为空或None
❌ WebSocket连接被拒绝：缺少token
```

## 🎯 关键信息解读

### 认证参数结构
```python
auth = {
    'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
}
```

### 字段要求
- ✅ 字段名必须是 `'token'`
- ✅ 值必须是完整的JWT token字符串
- ❌ 不能是 `'jwt'`, `'authorization'`, `'bearer'` 等其他名称
- ❌ 不能添加 `'Bearer '` 前缀

## 📱 Swift客户端对应配置

```swift
// ✅ 正确配置
let manager = SocketManager(
    socketURL: URL(string: "http://192.168.100.173:5000")!,
    config: [
        .auth(["token": jwtToken])  // 对应 Python 的 auth={'token': jwt_token}
    ]
)
```

## 🔧 调试技巧

### 1. 检查auth参数是否传递
看服务器输出中的：
```
📋 认证参数类型: <class 'dict'>  ✅ 应该是 dict
📋 认证参数内容: {'token': '...'}  ✅ 应该包含 token 字段
```

### 2. 检查字段名
看服务器输出中的：
```
auth 的键: ['token']  ✅ 应该是 ['token']
```

### 3. 检查token值
看服务器输出中的：
```
✅ 找到 token 字段: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 🐛 常见问题

### 问题1：auth参数为None
```
❌ auth 参数为空或None
```
**原因**：客户端没有传递auth参数  
**解决**：使用 `.auth(["token": jwtToken])` 配置

### 问题2：找不到token字段
```
auth 的键: ['jwt']
其他字段 jwt: ...
❌ WebSocket连接被拒绝：缺少token
```
**原因**：字段名错误  
**解决**：必须使用 `'token'` 作为字段名

### 问题3：token格式错误
```
✅ 找到 token 字段: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
❌ WebSocket连接被拒绝：token无效
```
**原因**：token包含了 'Bearer ' 前缀  
**解决**：直接传递token字符串，不要添加前缀

## ✅ 验证清单

- [ ] 服务器显示 `auth 参数存在`
- [ ] 服务器显示 `auth 的键: ['token']`
- [ ] 服务器显示 `✅ 找到 token 字段`
- [ ] 服务器显示 `从 auth['token'] 获取到token`
- [ ] 服务器显示 `✅ WebSocket连接成功 - 用户ID: X`
- [ ] 客户端收到 `connected` 事件

全部打勾表示配置正确！
