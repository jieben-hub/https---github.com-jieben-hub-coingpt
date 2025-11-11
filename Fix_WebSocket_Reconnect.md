# 修复WebSocket重连订阅问题

## 🐛 问题描述

**现象**：
- App重新编译运行后，无法接收WebSocket推送
- 服务端显示订阅成功，但客户端收不到数据
- 必须重启服务器才能恢复正常

**根本原因**：
当App重新启动时，客户端会重新连接并订阅，但服务器端保留了旧连接的房间(room)状态和订阅信息，导致数据推送到了已失效的连接上。

## 🔧 解决方案

### 1. 断开连接时自动清理

在客户端断开连接时，自动清理所有订阅状态：

```python
@socketio.on('disconnect')
def handle_disconnect():
    user_id = session.get('ws_user_id')
    
    if user_id:
        # 自动取消所有交易数据订阅
        all_data_types = ['balance', 'positions', 'pnl', 'orders']
        trading_ws.unsubscribe_user(user_id, all_data_types)
        
        # 取消所有行情订阅
        if trading_ws.ticker_subscribers:
            symbols_to_remove = []
            for symbol, subscribers in trading_ws.ticker_subscribers.items():
                if user_id in subscribers:
                    symbols_to_remove.append(symbol)
            
            if symbols_to_remove:
                trading_ws.unsubscribe_ticker(user_id, symbols_to_remove)
        
        print(f"✅ 已清理用户{user_id}的所有订阅")
```

### 2. 订阅前清理旧状态

在新订阅时，先清理该用户的旧订阅和房间：

#### 交易数据订阅
```python
@socketio.on('subscribe_trading')
def handle_subscribe_trading(data):
    user_id = session.get('ws_user_id')
    data_types = data.get('types', [])
    
    # 先清理旧订阅
    print(f"🔄 清理用户{user_id}的旧订阅...")
    
    # 离开所有旧房间
    valid_types = ['balance', 'positions', 'pnl', 'orders']
    for data_type in valid_types:
        room = f"{data_type}_{user_id}"
        try:
            leave_room(room)
        except:
            pass
    
    # 清理订阅状态
    trading_ws.unsubscribe_user(user_id, valid_types)
    
    # 重新加入房间并订阅
    for data_type in data_types:
        room = f"{data_type}_{user_id}"
        join_room(room)
    
    trading_ws.subscribe_user(user_id, data_types)
```

#### 行情订阅
```python
@socketio.on('subscribe_ticker')
def handle_subscribe_ticker(data):
    user_id = session.get('ws_user_id')
    symbols = data.get('symbols', [])
    
    # 先清理该用户的旧行情订阅
    print(f"🔄 清理用户{user_id}的旧行情订阅...")
    
    if trading_ws.ticker_subscribers:
        old_symbols = []
        for symbol, subscribers in list(trading_ws.ticker_subscribers.items()):
            if user_id in subscribers:
                old_symbols.append(symbol)
                room = f"ticker_{symbol}_{user_id}"
                try:
                    leave_room(room)
                except:
                    pass
        
        if old_symbols:
            trading_ws.unsubscribe_ticker(user_id, old_symbols)
    
    # 重新订阅
    for symbol in symbols:
        room = f"ticker_{symbol}_{user_id}"
        join_room(room)
    
    trading_ws.subscribe_ticker(user_id, symbols)
```

## 📊 修改的文件

- ✅ `app.py` - 修改disconnect、subscribe_trading、subscribe_ticker事件处理

## 🔄 工作流程

### 正常流程
```
1. 客户端连接 → 认证成功
2. 客户端订阅 → 加入房间 → 开始推送
3. 客户端断开 → 清理订阅 → 离开房间
```

### 重连流程（修复后）
```
1. 客户端重新连接 → 认证成功
2. 客户端订阅 → 清理旧订阅 → 离开旧房间 → 加入新房间 → 开始推送
```

## 🧪 测试场景

### 场景1：正常断开重连
```
1. App连接WebSocket
2. 订阅数据
3. 接收推送 ✅
4. App关闭
5. App重新启动
6. 重新连接并订阅
7. 接收推送 ✅（修复后）
```

### 场景2：网络中断重连
```
1. App连接WebSocket
2. 订阅数据
3. 网络中断
4. 网络恢复
5. 自动重连
6. 重新订阅
7. 接收推送 ✅（修复后）
```

### 场景3：多次重连
```
1. 连接 → 订阅 → 断开
2. 连接 → 订阅 → 断开
3. 连接 → 订阅 → 断开
4. 连接 → 订阅 → 接收推送 ✅（修复后）
```

## 📝 服务器日志

### 断开连接时
```
🔌 WebSocket客户端断开连接 - 来自: 192.168.100.172
   用户ID: 4
📋 用户4取消订阅balance数据 - 剩余订阅者: 0
📋 用户4取消订阅positions数据 - 剩余订阅者: 0
📋 用户4取消订阅pnl数据 - 剩余订阅者: 0
📋 用户4取消订阅orders数据 - 剩余订阅者: 0
📊 用户4取消订阅BTCUSDT行情 - 剩余订阅者: 0
   BTCUSDT无订阅者，移除
✅ 已清理用户4的所有订阅
```

### 重新订阅时
```
📡 收到订阅请求: {'types': ['balance', 'positions', 'pnl', 'orders']}
👤 用户ID: 4, 请求订阅: ['balance', 'positions', 'pnl', 'orders']
🔄 清理用户4的旧订阅...
📋 用户4取消订阅balance数据 - 剩余订阅者: 0
📋 用户4取消订阅positions数据 - 剩余订阅者: 0
📋 用户4取消订阅pnl数据 - 剩余订阅者: 0
📋 用户4取消订阅orders数据 - 剩余订阅者: 0
🚪 客户端加入房间: balance_4
🚪 客户端加入房间: positions_4
🚪 客户端加入房间: pnl_4
🚪 客户端加入房间: orders_4
📋 用户4订阅balance数据
📋 用户4订阅positions数据
📋 用户4订阅pnl数据
📋 用户4订阅orders数据
✅ 订阅成功 - 用户4订阅了: ['balance', 'positions', 'pnl', 'orders']
```

## 💡 客户端建议

### Swift - 重连处理
```swift
class WebSocketManager: ObservableObject {
    private var socket: SocketIOClient?
    
    func setupEventHandlers() {
        // 连接成功后自动订阅
        socket?.on(clientEvent: .connect) { data, ack in
            print("✅ WebSocket已连接")
            self.resubscribe()
        }
        
        // 重连成功后自动订阅
        socket?.on(clientEvent: .reconnect) { data, ack in
            print("🔄 WebSocket重连成功")
            self.resubscribe()
        }
        
        // 断开连接
        socket?.on(clientEvent: .disconnect) { data, ack in
            print("❌ WebSocket已断开")
        }
    }
    
    func resubscribe() {
        // 重新订阅交易数据
        socket?.emit("subscribe_trading", [
            "types": ["balance", "positions", "pnl", "orders"]
        ])
        
        // 重新订阅行情
        socket?.emit("subscribe_ticker", [
            "symbols": ["BTCUSDT", "ETHUSDT"]
        ])
    }
}
```

### 自动重连配置
```swift
manager = SocketManager(
    socketURL: url,
    config: [
        .reconnects(true),              // 启用自动重连
        .reconnectAttempts(-1),         // 无限重试
        .reconnectWait(1),              // 重连间隔1秒
        .reconnectWaitMax(5),           // 最大间隔5秒
        .forceWebsockets(true),
        .auth(["token": jwtToken])
    ]
)
```

## ⚠️ 注意事项

### 1. 订阅时机
- ✅ 在`connect`事件后订阅
- ✅ 在`reconnect`事件后重新订阅
- ❌ 不要在连接前订阅

### 2. 重复订阅
- 服务器会自动清理旧订阅
- 客户端可以放心重复订阅
- 不会造成重复推送

### 3. 断线处理
- 自动重连后需要重新订阅
- 监听`reconnect`事件
- 保存订阅状态以便恢复

### 4. 性能优化
```swift
// ✅ 推荐：批量订阅
socket.emit("subscribe_trading", [
    "types": ["balance", "positions", "pnl", "orders"]
])

// ❌ 不推荐：多次单独订阅
socket.emit("subscribe_trading", ["types": ["balance"]])
socket.emit("subscribe_trading", ["types": ["positions"]])
socket.emit("subscribe_trading", ["types": ["pnl"]])
socket.emit("subscribe_trading", ["types": ["orders"]])
```

## ✅ 验证清单

- [x] 断开连接时清理所有订阅
- [x] 断开连接时清理所有房间
- [x] 订阅前清理旧订阅状态
- [x] 订阅前离开旧房间
- [x] 支持多次重连
- [x] 日志输出清晰

## 🎉 完成

现在App可以正常重连并接收WebSocket推送了，无需重启服务器！

### 测试步骤
1. 启动服务器
2. App连接并订阅
3. 验证能接收推送 ✅
4. 关闭App
5. 重新启动App
6. 重新连接并订阅
7. 验证能接收推送 ✅（无需重启服务器）
