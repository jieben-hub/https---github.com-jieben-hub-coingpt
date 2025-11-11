# Bybit 双向持仓模式设置指南

## 📋 什么是双向持仓模式

双向持仓模式（Hedge Mode）允许你在同一个合约上同时持有多头和空头仓位。

### 示例
```
BTCUSDT 合约
├─ 做多仓位: +0.1 BTC  (positionIdx = 1)
└─ 做空仓位: -0.05 BTC (positionIdx = 2)
```

## 🔧 如何在Bybit开启双向持仓

### 方法1：通过网页端

1. **登录 Bybit**
   - 访问 https://www.bybit.com
   - 登录你的账户

2. **进入合约交易**
   - 点击顶部菜单的 "衍生品"
   - 选择 "USDT永续合约"

3. **切换持仓模式**
   - 在交易界面右上角找到 "持仓模式" 设置
   - 点击切换到 "双向持仓模式"
   - 确认切换

### 方法2：通过App

1. 打开 Bybit App
2. 进入 "合约交易"
3. 点击右上角设置图标
4. 找到 "持仓模式"
5. 选择 "双向持仓"

### 方法3：通过API（高级）

```python
# 使用Bybit API设置持仓模式
result = client.set_position_mode(
    category="linear",
    mode=3  # 0=单向持仓, 3=双向持仓
)
```

## ⚠️ 重要注意事项

### 1. 切换前必须平仓
在切换持仓模式之前，必须：
- ✅ 平掉所有现有持仓
- ✅ 取消所有挂单
- ✅ 确保没有未完成的订单

### 2. 切换后不能立即切回
- 切换后需要等待一段时间才能再次切换
- 建议谨慎选择持仓模式

### 3. 影响范围
- 持仓模式是账户级别的设置
- 影响所有USDT永续合约
- 不影响现货交易

## 📊 代码已配置为双向持仓模式

### 当前配置

```python
# 市价单
if position_side:
    order_params["positionIdx"] = 1 if position_side == PositionSide.LONG else 2

# 限价单
if position_side:
    order_params["positionIdx"] = 1 if position_side == PositionSide.LONG else 2
```

### positionIdx 参数说明

| position_side | positionIdx | 说明 |
|--------------|-------------|------|
| LONG | 1 | 做多仓位 |
| SHORT | 2 | 做空仓位 |

## 🧪 测试双向持仓

### 1. 开多头仓位
```json
POST /api/trading/order
{
    "symbol": "BTCUSDT",
    "side": "buy",
    "position_side": "long",
    "order_type": "limit",
    "quantity": 0.001,
    "price": 106000,
    "leverage": 1
}
```

**预期**：创建多头仓位（positionIdx = 1）

### 2. 同时开空头仓位
```json
POST /api/trading/order
{
    "symbol": "BTCUSDT",
    "side": "sell",
    "position_side": "short",
    "order_type": "limit",
    "quantity": 0.001,
    "price": 107000,
    "leverage": 1
}
```

**预期**：创建空头仓位（positionIdx = 2），与多头仓位共存

### 3. 查看持仓
```
GET /api/trading/positions
```

**预期**：看到两个独立的仓位
```json
[
    {
        "symbol": "BTCUSDT",
        "side": "Buy",
        "size": 0.001,
        "positionIdx": 1
    },
    {
        "symbol": "BTCUSDT",
        "side": "Sell",
        "size": 0.001,
        "positionIdx": 2
    }
]
```

## 💡 使用场景

### 1. 对冲策略
```
场景：持有现货BTC，担心短期下跌
操作：
- 保持现货多头
- 开合约空头对冲风险
```

### 2. 套利策略
```
场景：发现不同交易所价差
操作：
- 在A交易所做多
- 在B交易所做空
- 赚取价差
```

### 3. 网格交易
```
场景：震荡行情
操作：
- 低位做多
- 高位做空
- 来回套利
```

## 🔄 如果要切换回单向持仓

### 修改代码
```python
# 改为单向持仓模式
if position_side:
    order_params["positionIdx"] = 0
```

### 在Bybit设置
1. 平掉所有持仓
2. 取消所有挂单
3. 在设置中切换回 "单向持仓模式"

## 📝 API下单示例

### App端请求
```swift
let orderParams: [String: Any] = [
    "symbol": "BTCUSDT",
    "side": "buy",
    "position_side": "long",  // ⚠️ 指定持仓方向
    "order_type": "limit",
    "quantity": 0.001,
    "price": 106000,
    "leverage": 1
]

// 发送POST请求到 /api/trading/order
```

### 服务器处理
```python
# 1. 接收参数
position_side = data.get('position_side')  # 'long' 或 'short'

# 2. 转换为枚举
position_side_enum = PositionSide.LONG if position_side == 'long' else PositionSide.SHORT

# 3. 设置positionIdx
order_params["positionIdx"] = 1 if position_side_enum == PositionSide.LONG else 2

# 4. 下单
result = client.place_order(**order_params)
```

## ⚠️ 常见错误

### 错误1：未开启双向持仓
```
position idx not match position mode (ErrCode: 10001)
```
**解决**：在Bybit后台开启双向持仓模式

### 错误2：有未平仓位时切换模式
```
Cannot switch position mode with open positions
```
**解决**：先平掉所有持仓

### 错误3：positionIdx设置错误
```
invalid positionIdx
```
**解决**：
- 单向持仓：positionIdx = 0
- 双向持仓做多：positionIdx = 1
- 双向持仓做空：positionIdx = 2

## ✅ 检查清单

在使用双向持仓前，确保：

- [ ] 在Bybit后台开启了双向持仓模式
- [ ] 代码中设置了正确的positionIdx
- [ ] 理解多空仓位会独立存在
- [ ] 知道如何分别平仓
- [ ] 了解保证金要求会增加

## 📚 相关文档

- [Bybit持仓模式说明](https://www.bybit.com/zh-TW/help-center/bybitHC_Article?id=000001067&language=zh_TW)
- [Bybit API文档](https://bybit-exchange.github.io/docs/v5/position/position-mode)

## 🎯 总结

**双向持仓模式已配置**：
- ✅ 代码支持positionIdx = 1（做多）和 2（做空）
- ✅ 可以同时持有多空仓位
- ⚠️ 需要在Bybit后台手动开启

**下一步**：
1. 在Bybit后台开启双向持仓模式
2. 重启服务器
3. 测试下单

现在可以使用双向持仓功能了！🎉
