# WebSocket交易接口集成方案

## 🔥 高优先级接口 (实时数据)

### 1. 余额更新 `/api/trading/balance`
- **轮询频率**: 每5-10秒
- **WebSocket优势**: 余额变化时立即推送
- **触发场景**: 交易完成、转账、手续费扣除
- **数据结构**:
```json
{
  "type": "balance_update",
  "data": {
    "coin": "USDT",
    "available": 1000.50,
    "total": 1200.00,
    "equity": 1150.75
  },
  "timestamp": "2025-11-10T07:23:00.000Z"
}
```

### 2. 持仓更新 `/api/trading/positions`
- **轮询频率**: 每3-5秒
- **WebSocket优势**: 持仓变化、价格波动实时推送
- **触发场景**: 开仓、平仓、价格变动、强平
- **数据结构**:
```json
{
  "type": "position_update",
  "data": [
    {
      "symbol": "BTCUSDT",
      "side": "Buy",
      "size": 0.1,
      "entry_price": 50000.00,
      "mark_price": 50500.00,
      "unrealized_pnl": 50.00,
      "leverage": 10
    }
  ],
  "timestamp": "2025-11-10T07:23:00.000Z"
}
```

### 3. 盈亏更新 `/api/trading/pnl`
- **轮询频率**: 每3-5秒
- **WebSocket优势**: 实时盈亏变化，价格波动立即反映
- **触发场景**: 价格变动、持仓变化
- **数据结构**:
```json
{
  "type": "pnl_update",
  "data": {
    "total_unrealized_pnl": 125.50,
    "total_realized_pnl": 300.00,
    "position_details": [...]
  },
  "timestamp": "2025-11-10T07:23:00.000Z"
}
```

## 🟡 中优先级接口 (准实时数据)

### 4. 挂单更新 `/api/trading/orders`
- **轮询频率**: 每10-15秒
- **WebSocket优势**: 订单状态变化立即通知
- **触发场景**: 订单成交、部分成交、取消、过期
- **数据结构**:
```json
{
  "type": "order_update",
  "data": [
    {
      "order_id": "12345",
      "symbol": "BTCUSDT",
      "side": "Buy",
      "type": "Limit",
      "quantity": 0.1,
      "price": 49000.00,
      "status": "PartiallyFilled",
      "filled_quantity": 0.05
    }
  ],
  "timestamp": "2025-11-10T07:23:00.000Z"
}
```

## 🔴 不适合WebSocket的接口 (操作性接口)

- **创建订单** - 需要用户主动触发
- **取消订单** - 需要用户主动触发  
- **平仓操作** - 需要用户主动触发
- **设置杠杆** - 需要用户主动触发

## 📈 实施建议

### 阶段1: 核心数据实时化
1. **持仓数据** - 最高优先级，影响用户决策
2. **盈亏数据** - 用户最关心的数据
3. **余额数据** - 交易基础信息

### 阶段2: 订单状态实时化
1. **挂单状态** - 订单执行情况
2. **交易历史** - 成交记录推送

### 阶段3: 市场数据集成
1. **价格推送** - 关注币种价格变化
2. **深度数据** - 买卖盘信息
3. **K线数据** - 实时图表更新

## 🛠️ 技术实现

### WebSocket事件类型
- `balance_update` - 余额更新
- `position_update` - 持仓更新  
- `pnl_update` - 盈亏更新
- `order_update` - 订单更新
- `price_update` - 价格更新

### 客户端订阅方式
```javascript
// 订阅交易数据
socket.emit('subscribe', {
  user_id: userId,
  types: ['balance', 'positions', 'pnl', 'orders']
});
```

### 服务端推送频率控制
- **高频数据**: 价格变动 (1-3秒)
- **中频数据**: 持仓盈亏 (3-5秒)  
- **低频数据**: 余额订单 (5-10秒)

## 💡 优化建议

1. **数据去重**: 避免相同数据重复推送
2. **批量推送**: 多个更新合并推送
3. **增量更新**: 只推送变化的数据
4. **优先级队列**: 重要数据优先推送
5. **断线重连**: 自动重连和数据同步
