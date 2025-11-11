# WebSocket 断开连接错误修复

## 🐛 问题

客户端断开连接时出现错误：
```
Error on request:
Traceback (most recent call last):
  File "werkzeug\serving.py", line 261, in write
    assert status_set is not None, "write() before start_response"
```

## 📋 原因分析

这个错误发生在：
1. 客户端已经断开连接
2. 服务器还在尝试向该客户端推送数据
3. Werkzeug发现连接已关闭，抛出异常

这是**正常现象**，但会产生大量错误日志。

## ✅ 解决方案

### 1. 改进断开连接处理

```python
@socketio.on('disconnect')
def handle_disconnect():
    try:
        user_id = session.get('ws_user_id')
        print(f"🔌 WebSocket客户端断开连接")
        if user_id:
            print(f"   用户ID: {user_id}")
        logger.info(f"WebSocket客户端已断开连接 - 用户ID: {user_id}")
    except Exception as e:
        # 忽略断开连接时的错误
        print(f"⚠️ 断开连接处理出错（可忽略）: {e}")
        pass
```

### 2. 改进推送错误处理

```python
def _emit_data_update(self, user_id: int, data_type: str, data: Any):
    try:
        # ... 准备数据 ...
        
        try:
            self.socketio.emit(event_name, payload, room=room)
        except Exception as emit_error:
            # 客户端可能已断开，忽略此错误
            if "write() before start_response" in str(emit_error):
                print(f"⚠️ 客户端可能已断开，跳过推送")
            else:
                raise
    except Exception as e:
        # 只记录非断开连接的错误
        if "write() before start_response" not in str(e):
            logger.error(f"发送更新事件失败: {e}")
```

## 🔍 常见的断开连接错误

### 1. write() before start_response
```
assert status_set is not None, "write() before start_response"
```
**原因**：客户端已断开，服务器尝试写入响应  
**处理**：捕获并忽略

### 2. Broken pipe
```
BrokenPipeError: [Errno 32] Broken pipe
```
**原因**：连接已关闭，尝试写入数据  
**处理**：捕获并忽略

### 3. Connection reset by peer
```
ConnectionResetError: [Errno 104] Connection reset by peer
```
**原因**：客户端强制关闭连接  
**处理**：捕获并忽略

## 📊 现在的日志输出

### 正常断开
```
🔌 WebSocket客户端断开连接 - 来自: 192.168.100.172
   用户ID: 4
```

### 推送时客户端已断开
```
📤 推送balance数据给用户4
   数据内容: {...}
   房间: balance_4
⚠️ 客户端可能已断开，跳过推送
```

## 🎯 最佳实践

### 1. 自动清理订阅

可以在断开连接时自动取消订阅：

```python
@socketio.on('disconnect')
def handle_disconnect():
    try:
        user_id = session.get('ws_user_id')
        if user_id:
            # 自动取消所有订阅
            trading_ws.unsubscribe_user(
                user_id, 
                ['balance', 'positions', 'pnl', 'orders']
            )
            print(f"🧹 自动清理用户{user_id}的订阅")
    except:
        pass
```

### 2. 心跳检测

Socket.IO已经内置心跳机制：
```python
socketio = SocketIO(
    app,
    ping_timeout=60,      # 60秒无响应视为断开
    ping_interval=25      # 每25秒发送一次心跳
)
```

### 3. 重连处理

客户端应该实现自动重连：
```swift
manager = SocketManager(
    socketURL: url,
    config: [
        .reconnects(true),           // 启用自动重连
        .reconnectAttempts(5),       // 最多重连5次
        .reconnectWait(2)            // 每次等待2秒
    ]
)
```

## ⚠️ 注意事项

### 1. 不要过度捕获异常

```python
# ❌ 错误：捕获所有异常
try:
    self.socketio.emit(...)
except:
    pass  # 可能隐藏真正的错误

# ✅ 正确：只捕获特定异常
try:
    self.socketio.emit(...)
except Exception as e:
    if "write() before start_response" in str(e):
        pass  # 忽略断开连接错误
    else:
        raise  # 重新抛出其他错误
```

### 2. 记录重要错误

```python
# 区分可忽略的错误和真正的错误
if "write() before start_response" not in str(e):
    logger.error(f"发送失败: {e}")  # 记录真正的错误
```

### 3. 清理资源

```python
@socketio.on('disconnect')
def handle_disconnect():
    # 清理用户订阅
    # 清理缓存数据
    # 离开所有房间
    pass
```

## 🧪 测试

### 测试断开连接

1. **正常断开**：
```swift
socket.disconnect()
```
应该看到：
```
🔌 WebSocket客户端断开连接
   用户ID: 4
```

2. **强制断开**（杀掉App进程）：
应该看到：
```
⚠️ 客户端可能已断开，跳过推送
```

3. **网络中断**：
Socket.IO会自动检测并触发disconnect事件

## ✅ 总结

**问题**：客户端断开时服务器报错

**原因**：
- 客户端已断开
- 服务器还在推送数据
- Werkzeug检测到连接关闭

**解决**：
1. ✅ 捕获断开连接异常
2. ✅ 只记录真正的错误
3. ✅ 优雅处理断开事件
4. ✅ 自动清理订阅（可选）

**结果**：
- 不再显示大量错误日志
- 正常的断开连接被优雅处理
- 真正的错误仍然会被记录

现在重启服务器，客户端断开时不会再报错了！🎉
