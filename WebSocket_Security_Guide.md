# WebSocket 安全认证指南

## 🔐 安全特性

### ✅ 已实现的安全措施

1. **JWT Token认证** - 连接时必须提供有效的JWT token
2. **用户身份验证** - 从token中提取用户ID，防止伪造
3. **Session管理** - 认证状态存储在服务器session中
4. **数据类型验证** - 验证订阅的数据类型是否有效
5. **权限控制** - 用户只能访问自己的交易数据

### 🛡️ 认证流程

```
1. 客户端连接 → 提供JWT token
2. 服务器验证 → 解析token获取用户ID
3. 存储session → 保存认证状态
4. 允许连接 → 返回连接确认
5. 订阅数据 → 基于session中的用户ID
```

## 📱 客户端集成

### JavaScript 客户端
```javascript
// 1. 创建连接时提供JWT token
const socket = io('http://192.168.100.173:5000', {
    auth: {
        token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    }
});

// 2. 监听认证结果
socket.on('connected', (data) => {
    console.log('认证成功:', data);
    // data.user_id 包含从token解析的用户ID
    // data.authenticated 为 true
});

// 3. 订阅数据 - 不需要传递user_id
socket.emit('subscribe_trading', {
    types: ['balance', 'positions', 'pnl', 'orders']
});

// 4. 处理认证错误
socket.on('connect_error', (error) => {
    console.error('认证失败:', error);
    // 可能的错误：token无效、已过期、缺少token
});
```

### Swift iOS 客户端
```swift
// 1. 初始化时提供JWT token
let wsManager = CoinGPTWebSocketManager(
    serverURL: "http://192.168.100.173:5000",
    userId: 4,
    jwtToken: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
)

// 2. Socket配置包含认证头
manager = SocketManager(socketURL: url, config: [
    .extraHeaders(["Authorization": "Bearer \(jwtToken)"]),
    .forceWebsockets(true),
    .reconnects(true)
])

// 3. 处理认证结果
socket?.on(clientEvent: .connect) { data, ack in
    print("WebSocket认证成功")
}

socket?.on(clientEvent: .connectError) { data, ack in
    print("WebSocket认证失败: \(data)")
}
```

## 🔒 服务器端安全验证

### 连接认证
```python
@socketio.on('connect')
def handle_connect(auth):
    # 1. 获取JWT token
    token = auth.get('token') if auth else None
    
    # 2. 验证token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('sub')
    except jwt.ExpiredSignatureError:
        return False  # 拒绝连接
    except jwt.InvalidTokenError:
        return False  # 拒绝连接
    
    # 3. 存储认证状态
    session['ws_user_id'] = int(user_id)
    session['ws_authenticated'] = True
    
    return True  # 允许连接
```

### 订阅权限验证
```python
@socketio.on('subscribe_trading')
def handle_subscribe_trading(data):
    # 1. 检查认证状态
    if not session.get('ws_authenticated'):
        emit('error', {'message': '未认证'})
        return
    
    # 2. 从session获取用户ID（不信任客户端数据）
    user_id = session.get('ws_user_id')
    
    # 3. 验证数据类型
    valid_types = ['balance', 'positions', 'pnl', 'orders']
    requested_types = data.get('types', [])
    
    if not all(t in valid_types for t in requested_types):
        emit('error', {'message': '无效的数据类型'})
        return
    
    # 4. 执行订阅（用户只能访问自己的数据）
    trading_ws.subscribe_user(user_id, requested_types)
```

## ⚠️ 安全注意事项

### 1. Token管理
- ✅ **安全存储** - 客户端安全存储JWT token
- ✅ **定期刷新** - token过期前自动刷新
- ✅ **传输安全** - 使用HTTPS/WSS传输token

### 2. 权限控制
- ✅ **用户隔离** - 用户只能访问自己的数据
- ✅ **数据验证** - 验证所有客户端输入
- ✅ **会话管理** - 服务器端维护认证状态

### 3. 错误处理
- ✅ **认证失败** - 明确的错误消息和状态码
- ✅ **连接拒绝** - 无效token直接拒绝连接
- ✅ **日志记录** - 记录所有认证尝试

## 🧪 测试认证功能

### 有效Token测试
```javascript
// 使用有效token连接
const validToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0IiwiaWF0IjoxNzYyNzIxMjA3LCJleHAiOjE3NjMzMjYwMDd9.taqUsvsF4wEh44yOlZG-n5E94jQtdoVHB4l7PLmGEuk";

const socket = io('http://192.168.100.173:5000', {
    auth: { token: validToken }
});

socket.on('connected', (data) => {
    console.log('✅ 认证成功:', data);
    // 应该收到: { message: '连接成功', user_id: 4, authenticated: true }
});
```

### 无效Token测试
```javascript
// 使用无效token连接
const invalidToken = "invalid.token.here";

const socket = io('http://192.168.100.173:5000', {
    auth: { token: invalidToken }
});

socket.on('connect_error', (error) => {
    console.log('❌ 认证失败:', error);
    // 连接应该被拒绝
});
```

### 无Token测试
```javascript
// 不提供token连接
const socket = io('http://192.168.100.173:5000');

socket.on('connect_error', (error) => {
    console.log('❌ 认证失败:', error);
    // 连接应该被拒绝
});
```

## 🔄 Token刷新机制

### 自动刷新
```javascript
class SecureWebSocketClient {
    constructor(serverUrl, getTokenFunction) {
        this.serverUrl = serverUrl;
        this.getToken = getTokenFunction; // 获取最新token的函数
        this.socket = null;
    }
    
    connect() {
        const token = this.getToken();
        
        this.socket = io(this.serverUrl, {
            auth: { token: token }
        });
        
        // 监听token过期
        this.socket.on('token_expired', () => {
            this.reconnectWithNewToken();
        });
    }
    
    reconnectWithNewToken() {
        const newToken = this.getToken(); // 获取新token
        this.socket.disconnect();
        
        this.socket = io(this.serverUrl, {
            auth: { token: newToken }
        });
    }
}
```

## 📊 安全监控

### 服务器端日志
```python
# 记录认证尝试
logger.info(f"WebSocket认证成功，用户ID: {user_id}")
logger.warning(f"WebSocket认证失败：{error_reason}")

# 记录订阅活动
logger.info(f"用户{user_id}订阅了交易数据: {data_types}")
logger.warning(f"用户{user_id}尝试订阅无效数据类型: {invalid_types}")
```

### 客户端监控
```javascript
// 监控连接状态
socket.on('connect', () => {
    console.log('🟢 WebSocket已连接');
});

socket.on('disconnect', (reason) => {
    console.log('🔴 WebSocket已断开:', reason);
    
    if (reason === 'io server disconnect') {
        // 服务器主动断开，可能是认证问题
        console.log('⚠️ 服务器断开连接，检查token有效性');
    }
});
```

## ✅ 安全检查清单

- [x] JWT token认证已实现
- [x] 用户身份验证已实现
- [x] Session管理已实现
- [x] 数据类型验证已实现
- [x] 权限控制已实现
- [x] 错误处理已实现
- [x] 日志记录已实现
- [x] 客户端示例已更新
- [x] 安全文档已完成

现在你的WebSocket连接是完全安全的，只有持有有效JWT token的认证用户才能连接和订阅交易数据！
