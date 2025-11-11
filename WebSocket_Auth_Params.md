# WebSocket 认证参数详解

## 🔍 服务器端代码分析

### 服务器如何读取认证参数

```python
# 文件: chatgpt_crypto_ai/app.py
@socketio.on('connect')
def handle_connect(auth):
    """处理WebSocket连接，验证JWT token"""
    
    # 获取token - 从 auth 参数中读取
    token = None
    if auth and 'token' in auth:
        token = auth['token']  # ⚠️ 关键：从 auth['token'] 读取
    
    if not token:
        return False  # 拒绝连接
    
    # 验证JWT token
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    user_id = payload.get('sub')
    
    # 保存到session
    session['ws_user_id'] = int(user_id)
    session['ws_authenticated'] = True
    
    return True  # 允许连接
```

## 📱 客户端配置对比

### ✅ 正确方式（Swift）

```swift
import SocketIO

// 使用 .auth() 配置项
let manager = SocketManager(
    socketURL: URL(string: "http://192.168.100.173:5000")!,
    config: [
        .auth(["token": jwtToken])  // ✅ 这会传递到服务器的 auth 参数
    ]
)

let socket = manager.defaultSocket
socket.connect()
```

**传递的数据结构：**
```
connect 事件
├── auth (字典)
    └── "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### ❌ 错误方式

```swift
// 错误1：使用 connectParams
let manager = SocketManager(
    socketURL: URL(string: "http://192.168.100.173:5000")!,
    config: [
        .connectParams(["token": jwtToken])  // ❌ 这不会传递到 auth 参数
    ]
)

// 错误2：使用 extraHeaders
let manager = SocketManager(
    socketURL: URL(string: "http://192.168.100.173:5000")!,
    config: [
        .extraHeaders(["Authorization": "Bearer \(jwtToken)"])  // ❌ 这是HTTP头，不是auth参数
    ]
)
```

## 🔄 完整的认证流程

### 1. 客户端连接

```swift
// Swift客户端
let jwtToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0IiwiaWF0IjoxNzYyNzIxMjA3LCJleHAiOjE3NjMzMjYwMDd9.taqUsvsF4wEh44yOlZG-n5E94jQtdoVHB4l7PLmGEuk"

let manager = SocketManager(
    socketURL: URL(string: "http://192.168.100.173:5000")!,
    config: [
        .log(true),
        .auth(["token": jwtToken])  // 传递认证信息
    ]
)

socket = manager.defaultSocket
socket.connect()
```

### 2. 服务器验证

```python
# Python服务器
@socketio.on('connect')
def handle_connect(auth):
    # 1. 读取token
    token = auth['token']  # 从 auth 字典中获取
    
    # 2. 验证token
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    user_id = payload.get('sub')  # 从token中提取用户ID
    
    # 3. 保存认证状态
    session['ws_user_id'] = int(user_id)
    session['ws_authenticated'] = True
    
    # 4. 返回连接确认
    socketio.emit('connected', {
        'message': '连接成功',
        'user_id': int(user_id),
        'authenticated': True
    })
    
    return True
```

### 3. 客户端接收确认

```swift
// Swift客户端
socket.on("connected") { data, ack in
    if let responseData = data.first as? [String: Any] {
        let userId = responseData["user_id"] as? Int
        let authenticated = responseData["authenticated"] as? Bool
        
        print("✅ 连接成功，用户ID: \(userId ?? 0)")
        
        // 订阅交易数据
        socket.emit("subscribe_trading", [
            "types": ["balance", "positions", "pnl", "orders"]
        ])
    }
}
```

## 📊 数据流向图

```
客户端                                    服务器
  │                                        │
  │  1. connect + auth: {token: "..."}   │
  ├────────────────────────────────────>  │
  │                                        │ 2. 验证token
  │                                        │    jwt.decode(token)
  │                                        │    提取user_id
  │                                        │
  │  3. connected: {user_id: 4}          │
  │  <────────────────────────────────────┤
  │                                        │
  │  4. subscribe_trading                 │
  ├────────────────────────────────────>  │
  │                                        │ 5. 从session获取user_id
  │                                        │    订阅数据推送
  │                                        │
  │  6. subscribed: {status: "success"}  │
  │  <────────────────────────────────────┤
  │                                        │
  │  7. balance_update                    │
  │  <────────────────────────────────────┤
  │                                        │
```

## 🧪 测试代码

### Python测试客户端

```python
import socketio

sio = socketio.Client()

jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

@sio.event
def connect():
    print("✅ 连接成功")

@sio.event
def connected(data):
    print(f"📨 收到确认: {data}")
    sio.emit('subscribe_trading', {'types': ['balance', 'pnl']})

@sio.event
def subscribed(data):
    print(f"✅ 订阅成功: {data}")

# 连接时传递auth参数
sio.connect('http://192.168.100.173:5000', auth={'token': jwt_token})
```

### Swift测试代码

```swift
import SocketIO

let jwtToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

let manager = SocketManager(
    socketURL: URL(string: "http://192.168.100.173:5000")!,
    config: [
        .log(true),
        .auth(["token": jwtToken])  // ⚠️ 关键配置
    ]
)

let socket = manager.defaultSocket

socket.on(clientEvent: .connect) { data, ack in
    print("✅ 连接成功")
}

socket.on("connected") { data, ack in
    print("📨 收到确认: \(data)")
    socket.emit("subscribe_trading", ["types": ["balance", "pnl"]])
}

socket.on("subscribed") { data, ack in
    print("✅ 订阅成功: \(data)")
}

socket.connect()
```

## ⚠️ 常见错误

### 错误1：使用错误的配置项
```swift
// ❌ 错误
.connectParams(["token": jwtToken])

// ✅ 正确
.auth(["token": jwtToken])
```

### 错误2：token格式错误
```swift
// ❌ 错误：添加了Bearer前缀
.auth(["token": "Bearer \(jwtToken)"])

// ✅ 正确：直接传递token
.auth(["token": jwtToken])
```

### 错误3：字段名错误
```swift
// ❌ 错误：字段名不对
.auth(["jwt": jwtToken])
.auth(["authorization": jwtToken])

// ✅ 正确：必须是 "token"
.auth(["token": jwtToken])
```

## 📝 总结

### 关键点：
1. **服务器读取**: `auth['token']`
2. **客户端配置**: `.auth(["token": jwtToken])`
3. **不需要传递**: userId（服务器从token中解析）
4. **订阅时**: 不需要传递user_id，服务器从session获取

### 必需参数：
- ✅ `serverURL`: WebSocket服务器地址
- ✅ `jwtToken`: JWT认证令牌
- ❌ `userId`: 不需要（自动从token解析）

### Socket.IO配置：
```swift
.auth(["token": jwtToken])  // ⚠️ 这是唯一正确的方式
```
