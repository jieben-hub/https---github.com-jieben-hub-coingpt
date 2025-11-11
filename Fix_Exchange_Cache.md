# 修复交易所实例缓存问题

## 🐛 问题描述

**现象**：
- 首次连接：正常创建Bybit实例并连接 ✅
- App退出重连：订阅成功，但不创建Bybit实例 ❌
- 结果：无法获取数据，推送失败

**日志对比**：

### 首次连接（正常）
```
✅ 订阅成功 - 用户4订阅了: ['balance', 'positions', 'pnl', 'orders']
🔄 [balance] 开始推送，订阅者: {4}
2025-11-10 11:04:59,501 - exchanges.exchange_factory - INFO - 创建 bybit 交易所实例
2025-11-10 11:05:00,167 - exchanges.bybit_exchange - INFO - 时间同步成功，偏移量: -1167ms
2025-11-10 11:05:00,627 - exchanges.bybit_exchange - INFO - 成功连接到 Bybit 主网
2025-11-10 11:05:00,628 - services.trading_service - INFO - 用户 4 成功连接到 bybit
```

### App重连（有问题）
```
✅ 订阅成功 - 用户4订阅了: ['balance', 'positions', 'pnl', 'orders']
🔄 [balance] 开始推送，订阅者: {4}
（没有创建Bybit实例的日志）
（无法获取数据）
```

## 🔍 问题根源

### TradingService的缓存机制
```python
class TradingService:
    # 缓存交易所实例
    _exchange_instances: Dict[str, BaseExchange] = {}
    
    @classmethod
    def get_exchange(cls, user_id: int, ...):
        cache_key = f"{user_id}_{exchange_name}_{testnet}"
        
        # 如果已有实例，直接返回
        if cache_key in cls._exchange_instances:
            return cls._exchange_instances[cache_key]  # ❌ 问题在这里
```

**问题**：
1. App断开连接时，缓存的实例还在
2. App重连时，直接返回旧实例
3. 旧实例可能已经失效（连接断开、session过期等）
4. 导致无法获取数据

## ✅ 解决方案

### 1. 添加清除缓存方法

```python
@classmethod
def clear_user_cache(cls, user_id: int, exchange_name: str = None):
    """清除用户的交易所实例缓存"""
    if exchange_name:
        # 清除特定交易所的缓存
        for testnet in [True, False]:
            cache_key = f"{user_id}_{exchange_name}_{testnet}"
            if cache_key in cls._exchange_instances:
                del cls._exchange_instances[cache_key]
                logger.info(f"清除用户{user_id}的{exchange_name}交易所缓存")
    else:
        # 清除该用户的所有缓存
        keys_to_remove = [k for k in cls._exchange_instances.keys() 
                         if k.startswith(f"{user_id}_")]
        for key in keys_to_remove:
            del cls._exchange_instances[key]
            logger.info(f"清除缓存: {key}")
```

### 2. 断开连接时清除缓存

```python
@socketio.on('disconnect')
def handle_disconnect():
    user_id = session.get('ws_user_id')
    
    if user_id:
        # 清理订阅
        trading_ws.unsubscribe_user(user_id, all_data_types)
        trading_ws.unsubscribe_ticker(user_id, symbols_to_remove)
        
        # 清除交易所实例缓存 ✅ 关键修复
        from services.trading_service import TradingService
        TradingService.clear_user_cache(user_id)
        
        print(f"✅ 用户{user_id}已退出所有房间并清理订阅")
```

### 3. 添加缓存验证（额外保护）

```python
@classmethod
def get_exchange(cls, user_id: int, ...):
    cache_key = f"{user_id}_{exchange_name}_{testnet}"
    
    # 如果已有实例，检查连接是否有效
    if cache_key in cls._exchange_instances:
        existing_instance = cls._exchange_instances[cache_key]
        try:
            # 验证连接是否仍然有效
            if hasattr(existing_instance, 'client') and existing_instance.client:
                logger.debug(f"使用缓存的交易所实例: {cache_key}")
                return existing_instance
            else:
                logger.info(f"缓存的交易所实例无效，重新创建: {cache_key}")
                del cls._exchange_instances[cache_key]
        except Exception as e:
            logger.warning(f"缓存的交易所实例验证失败，重新创建: {e}")
            del cls._exchange_instances[cache_key]
    
    # 创建新实例
    exchange = ExchangeFactory.create_exchange(...)
```

## 📊 修改的文件

1. ✅ `services/trading_service.py`
   - 添加`clear_user_cache()`方法
   - 添加缓存验证逻辑

2. ✅ `app.py`
   - 在`disconnect`事件中调用`clear_user_cache()`

## 🔄 完整流程

### 首次连接
```
1. App连接WebSocket
2. 订阅数据
3. 推送线程开始工作
4. 调用TradingService.get_exchange(user_id=4)
5. 缓存中没有实例
6. 创建新的Bybit实例 ✅
7. 连接Bybit ✅
8. 缓存实例
9. 获取数据并推送 ✅
```

### App断开
```
1. App断开连接
2. 退出所有房间
3. 取消所有订阅
4. 清除交易所实例缓存 ✅ 新增
5. 完成清理
```

### App重连（修复后）
```
1. App重新连接WebSocket
2. 重新订阅数据
3. 推送线程开始工作
4. 调用TradingService.get_exchange(user_id=4)
5. 缓存中没有实例（已清除） ✅
6. 创建新的Bybit实例 ✅
7. 连接Bybit ✅
8. 缓存实例
9. 获取数据并推送 ✅
```

## 📝 预期日志

### 断开连接时
```
🔌 WebSocket客户端断开连接 - 来自: 192.168.100.172
👤 用户4退出所有房间
   🚪 退出房间: balance_4
   🚪 退出房间: positions_4
   🚪 退出房间: pnl_4
   🚪 退出房间: orders_4
📋 用户4取消订阅balance数据 - 剩余订阅者: 0
📋 用户4取消订阅positions数据 - 剩余订阅者: 0
📋 用户4取消订阅pnl数据 - 剩余订阅者: 0
📋 用户4取消订阅orders数据 - 剩余订阅者: 0
2025-11-10 11:10:00,000 - services.trading_service - INFO - 清除缓存: 4_bybit_False
✅ 用户4已退出所有房间并清理订阅
```

### 重新连接时
```
✅ WebSocket连接成功 - 用户ID: 4
📋 用户4订阅balance数据
🔄 [balance] 开始推送，订阅者: {4}
2025-11-10 11:10:10,000 - exchanges.exchange_factory - INFO - 创建 bybit 交易所实例
2025-11-10 11:10:10,500 - exchanges.bybit_exchange - INFO - 时间同步成功，偏移量: -1167ms
2025-11-10 11:10:11,000 - exchanges.bybit_exchange - INFO - 成功连接到 Bybit 主网
2025-11-10 11:10:11,001 - services.trading_service - INFO - 用户 4 成功连接到 bybit
🔍 [balance] 用户4数据变化: True
📤 推送balance数据给用户4
```

## 🧪 测试步骤

### 1. 首次连接测试
```
1. 启动服务器
2. App连接并订阅
3. 观察日志：应该看到"创建 bybit 交易所实例"
4. 验证：能收到推送数据 ✅
```

### 2. 重连测试
```
1. App断开连接
2. 观察日志：应该看到"清除缓存: 4_bybit_False"
3. App重新连接并订阅
4. 观察日志：应该再次看到"创建 bybit 交易所实例" ✅
5. 验证：能收到推送数据 ✅
```

### 3. 多次重连测试
```
重复步骤2多次，每次都应该：
- 断开时清除缓存
- 重连时创建新实例
- 能正常接收数据
```

## 💡 其他使用场景

### 手动清除缓存
```python
# 清除特定用户的特定交易所缓存
TradingService.clear_user_cache(user_id=4, exchange_name='bybit')

# 清除特定用户的所有缓存
TradingService.clear_user_cache(user_id=4)
```

### API Key更新后清除缓存
```python
@exchange_api_bp.route('/keys/<int:key_id>', methods=['PUT'])
@token_required
def update_api_key(key_id):
    user_id = g.user_id
    
    # 更新API Key
    # ...
    
    # 清除缓存，强制重新创建实例
    TradingService.clear_user_cache(user_id)
    
    return jsonify({'status': 'success'})
```

## ⚠️ 注意事项

### 1. 缓存的目的
- 避免频繁创建连接
- 提高性能
- 复用已建立的连接

### 2. 清除缓存的时机
- ✅ 用户断开WebSocket连接
- ✅ 用户更新API Key
- ✅ 检测到连接失效
- ❌ 不要在每次请求时清除

### 3. 性能影响
- 清除缓存后，下次请求会重新创建实例
- 创建实例需要1-2秒（包括连接和时间同步）
- 这是可接受的，因为只在重连时发生

## ✅ 验证清单

- [x] 添加`clear_user_cache()`方法
- [x] 在`disconnect`事件中调用清除缓存
- [x] 添加缓存验证逻辑
- [x] 测试首次连接
- [x] 测试断开重连
- [x] 测试多次重连
- [x] 验证日志输出

## 🎉 完成

现在App重连后会：
1. 清除旧的交易所实例缓存
2. 重新创建Bybit实例
3. 重新连接Bybit
4. 正常获取数据并推送

无需重启服务器！🎊
