# WebSocket 订阅字段说明

## 🐛 问题

客户端发送的订阅请求：
```json
{
    "subscribeTypes": ["balance", "positions", "pnl", "orders"],
    "jwtToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

服务器期望的字段名是 `types`，但客户端发送的是 `subscribeTypes`。

## ✅ 解决方案

服务器已更新，现在支持两种字段名：

### 服务器端代码
```python
# 支持多种字段名：types 或 subscribeTypes
data_types = data.get('types') or data.get('subscribeTypes', [])
```

## 📱 客户端配置

### 方式1: 使用 types（推荐）
```swift
socket.emit("subscribe_trading", [
    "types": ["balance", "positions", "pnl", "orders"]
])
```

### 方式2: 使用 subscribeTypes（也支持）
```swift
socket.emit("subscribe_trading", [
    "subscribeTypes": ["balance", "positions", "pnl", "orders"]
])
```

## ⚠️ 注意事项

### 不要发送 jwtToken
订阅时**不需要**再次发送 `jwtToken`，因为：
1. Token已经在连接时验证过了
2. 用户ID已经存储在服务器session中
3. 服务器会从session获取用户ID

### 正确的订阅请求
```swift
// ✅ 正确：只发送订阅类型
socket.emit("subscribe_trading", [
    "types": ["balance", "positions", "pnl", "orders"]
])

// ❌ 错误：不需要再发送token
socket.emit("subscribe_trading", [
    "types": ["balance", "positions", "pnl", "orders"],
    "jwtToken": token  // 不需要！
])
```

## 📊 服务器日志

### 成功的订阅
```
📡 收到订阅请求: {'types': ['balance', 'positions', 'pnl', 'orders']}
👤 用户ID: 4, 请求订阅: ['balance', 'positions', 'pnl', 'orders']
📋 原始数据字段: ['types']
📋 用户4订阅balance数据 - 当前订阅者: 1
📋 用户4订阅positions数据 - 当前订阅者: 1
📋 用户4订阅pnl数据 - 当前订阅者: 1
📋 用户4订阅orders数据 - 当前订阅者: 1
✅ 订阅成功 - 用户4订阅了: ['balance', 'positions', 'pnl', 'orders']
```

### 使用 subscribeTypes 字段（也支持）
```
📡 收到订阅请求: {'subscribeTypes': ['balance', 'positions', 'pnl', 'orders']}
👤 用户ID: 4, 请求订阅: ['balance', 'positions', 'pnl', 'orders']
📋 原始数据字段: ['subscribeTypes']
✅ 订阅成功 - 用户4订阅了: ['balance', 'positions', 'pnl', 'orders']
```

## 🎯 完整的订阅流程

### 1. 连接WebSocket
```swift
let manager = SocketManager(
    socketURL: URL(string: "http://192.168.100.173:5000")!,
    config: [
        .auth(["token": jwtToken]),
        .extraHeaders(["Authorization": "Bearer \(jwtToken)"])
    ]
)
socket = manager.defaultSocket
socket.connect()
```

### 2. 监听连接成功
```swift
socket.on("connected") { data, ack in
    print("✅ 连接成功")
    // 现在可以订阅数据
}
```

### 3. 订阅交易数据
```swift
socket.emit("subscribe_trading", [
    "types": ["balance", "positions", "pnl", "orders"]
])
```

### 4. 监听订阅确认
```swift
socket.on("subscribed") { data, ack in
    print("✅ 订阅成功: \(data)")
}
```

### 5. 接收数据更新
```swift
socket.on("balance_update") { data, ack in
    print("💰 余额更新: \(data)")
}

socket.on("positions_update") { data, ack in
    print("📊 持仓更新: \(data)")
}

socket.on("pnl_update") { data, ack in
    print("📈 盈亏更新: \(data)")
}

socket.on("orders_update") { data, ack in
    print("📋 订单更新: \(data)")
}
```

## 🔧 调试技巧

### 查看发送的数据
```swift
let subscribeData: [String: Any] = [
    "types": ["balance", "positions", "pnl", "orders"]
]
print("发送订阅请求: \(subscribeData)")
socket.emit("subscribe_trading", subscribeData)
```

### 查看服务器响应
服务器会打印：
- 收到的完整数据
- 解析出的订阅类型
- 原始数据的所有字段名

## ✅ 总结

**支持的字段名：**
- ✅ `types`（推荐）
- ✅ `subscribeTypes`（也支持）

**不需要的字段：**
- ❌ `jwtToken`（已经在连接时验证）
- ❌ `userId`（服务器从session获取）

**订阅数据类型：**
- `"balance"` - 余额数据
- `"positions"` - 持仓数据
- `"pnl"` - 盈亏数据
- `"orders"` - 订单数据

现在重启服务器，你的订阅应该能成功了！🎉
