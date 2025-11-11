# WebSocket 应用上下文问题修复

## 🐛 问题

```
获取用户4的pnl数据失败: Working outside of application context.
```

### 原因分析

WebSocket推送服务在后台线程中运行，这些线程需要访问Flask应用资源（如数据库、session等），但没有Flask应用上下文。

## ✅ 解决方案

### 1. 修改 TradingWebSocketService 类

添加app参数以保存Flask应用实例：

```python
class TradingWebSocketService:
    def __init__(self, socketio, app=None):
        self.socketio = socketio
        self.app = app  # 保存Flask app实例
        self.running = False
        # ...
```

### 2. 在推送数据时使用应用上下文

```python
def _push_user_data(self, user_id: int, data_type: str):
    """为特定用户推送特定类型的数据"""
    try:
        # 使用Flask应用上下文
        if self.app:
            with self.app.app_context():
                # 获取最新数据
                new_data = self._fetch_user_data(user_id, data_type)
                
                if new_data is None:
                    return
                
                # 检查数据是否有变化
                if self._has_data_changed(user_id, data_type, new_data):
                    # 更新缓存
                    self._update_cache(user_id, data_type, new_data)
                    
                    # 推送数据
                    self._emit_data_update(user_id, data_type, new_data)
        # ...
```

### 3. 更新初始化函数

```python
def init_trading_websocket_service(socketio: SocketIO, app=None) -> TradingWebSocketService:
    """初始化交易WebSocket服务"""
    global trading_ws_service
    trading_ws_service = TradingWebSocketService(socketio, app)
    return trading_ws_service
```

### 4. 在app.py中传递app实例

```python
# 初始化交易WebSocket服务，传递app实例以支持应用上下文
trading_ws = init_trading_websocket_service(socketio, app)
```

## 🔍 为什么需要应用上下文

Flask应用上下文提供了访问以下资源的能力：

1. **数据库连接** - `db.session`
2. **配置信息** - `current_app.config`
3. **请求上下文** - `request`, `session`
4. **扩展实例** - 各种Flask扩展

在后台线程中，这些资源默认不可用，必须显式创建应用上下文。

## 📊 修复后的执行流程

```
后台推送线程
    │
    ├─> with app.app_context():
    │       │
    │       ├─> 获取数据库连接
    │       ├─> 调用 TradingService
    │       ├─> 访问用户session
    │       └─> 推送数据到客户端
    │
    └─> 继续下一次推送
```

## 🧪 测试

重启服务器后，应该看到：

```
🚀 启动交易数据WebSocket推送服务
🔄 启动balance数据推送线程 - 推送间隔: 10秒
🔄 启动positions数据推送线程 - 推送间隔: 5秒
🔄 启动pnl数据推送线程 - 推送间隔: 5秒
🔄 启动orders数据推送线程 - 推送间隔: 15秒
📤 推送pnl数据给用户4
📤 推送balance数据给用户4
```

不再出现 "Working outside of application context" 错误。

## ⚠️ 注意事项

### 1. 应用上下文的作用域

```python
with app.app_context():
    # 在这个块内可以访问Flask资源
    data = db.session.query(...)
    
# 在这个块外无法访问Flask资源
```

### 2. 线程安全

每个后台线程都需要自己的应用上下文：

```python
# ✅ 正确：每次推送都创建新的上下文
def _push_user_data(self, user_id, data_type):
    with self.app.app_context():
        # 推送数据
        pass

# ❌ 错误：在线程启动时创建一次上下文
def _data_push_loop(self, data_type):
    with self.app.app_context():  # 不要这样做
        while self.running:
            # 推送数据
            pass
```

### 3. 性能考虑

创建应用上下文有一定开销，但通常可以忽略不计。如果需要优化：

- 减少推送频率
- 批量处理多个用户
- 使用缓存避免重复查询

## ✅ 总结

**问题**：后台线程无法访问Flask应用资源

**解决**：
1. 保存Flask app实例
2. 使用 `with app.app_context()` 包装需要访问Flask资源的代码
3. 在初始化时传递app实例

**结果**：WebSocket推送服务可以正常访问数据库和其他Flask资源

现在重启服务器，应该能正常推送数据了！🎉
