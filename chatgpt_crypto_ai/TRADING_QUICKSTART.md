# 🚀 交易模块快速开始

## 5 分钟快速上手

### 1️⃣ 安装依赖

```bash
pip install pybit>=5.6.0
```

### 2️⃣ 获取 Bybit 测试网 API Key

1. 访问 https://testnet.bybit.com/
2. 注册并登录
3. 进入 **API 管理** → **创建新密钥**
4. 权限选择：
   - ✅ 合约交易
   - ✅ 读取账户信息
5. 复制 **API Key** 和 **Secret**

### 3️⃣ 配置环境变量

在 `.env` 文件中添加：

```bash
# 交易配置
TRADING_EXCHANGE=bybit
TRADING_API_KEY=你的API_KEY
TRADING_API_SECRET=你的API_SECRET
TRADING_TESTNET=True
```

### 4️⃣ 测试连接

```bash
python test_trading_module.py
```

**预期输出**：
```
✅ 成功连接到 Bybit
✅ 余额查询成功
✅ 当前无持仓
✅ 当前无挂单
```

### 5️⃣ 启动服务

```bash
python run.py
```

---

## 📡 快速测试 API

### 获取余额

```bash
curl -X GET "http://localhost:5000/api/trading/balance?coin=USDT" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 创建市价做多单

```bash
curl -X POST "http://localhost:5000/api/trading/order" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "side": "buy",
    "quantity": 0.001,
    "order_type": "market",
    "position_side": "long"
  }'
```

### 获取持仓

```bash
curl -X GET "http://localhost:5000/api/trading/positions" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 平仓

```bash
curl -X POST "http://localhost:5000/api/trading/position/close" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "position_side": "long"
  }'
```

---

## 🐍 Python 代码示例

```python
from services.trading_service import TradingService

# 1. 获取余额
balance = TradingService.get_balance(coin="USDT")
print(f"可用余额: {balance['available']} USDT")

# 2. 创建市价做多单
order = TradingService.create_order(
    symbol="BTCUSDT",
    side="buy",
    quantity=0.001,
    order_type="market",
    position_side="long"
)
print(f"订单ID: {order['order_id']}")

# 3. 查看持仓
positions = TradingService.get_positions(symbol="BTCUSDT")
for pos in positions:
    print(f"持仓: {pos['size']} BTC @ {pos['entry_price']}")

# 4. 平仓
result = TradingService.close_position(
    symbol="BTCUSDT",
    position_side="long"
)
print(f"平仓成功: {result['order_id']}")
```

---

## ⚠️ 重要提示

### 测试网 vs 主网

| 环境 | 配置 | 资金 | 用途 |
|------|------|------|------|
| **测试网** | `TRADING_TESTNET=True` | 虚拟资金 | ✅ 学习测试 |
| **主网** | `TRADING_TESTNET=False` | 真实资金 | ⚠️ 真实交易 |

### 安全建议

1. ✅ **先用测试网** - 充分测试后再用主网
2. ✅ **小额测试** - 主网先用最小金额测试
3. ✅ **设置止损** - 控制风险
4. ✅ **IP 白名单** - 在 Bybit 设置 IP 限制
5. ❌ **不要泄露** - API Key 永远不要提交到 Git

---

## 🎯 完整流程示例

### 做多 BTC 完整流程

```python
from services.trading_service import TradingService

# 1. 检查余额
balance = TradingService.get_balance()
print(f"余额: {balance['available']} USDT")

# 2. 设置杠杆
TradingService.set_leverage(symbol="BTCUSDT", leverage=10)
print("杠杆设置为 10x")

# 3. 开多单
order = TradingService.create_order(
    symbol="BTCUSDT",
    side="buy",
    quantity=0.001,
    order_type="market",
    position_side="long"
)
print(f"开多成功: {order['order_id']}")

# 4. 查看持仓
positions = TradingService.get_positions(symbol="BTCUSDT")
for pos in positions:
    print(f"持仓: {pos['size']} @ {pos['entry_price']}")
    print(f"未实现盈亏: {pos['unrealized_pnl']} USDT")

# 5. 平仓
result = TradingService.close_position(
    symbol="BTCUSDT",
    position_side="long"
)
print(f"平仓成功: {result['order_id']}")
```

---

## 🐛 常见问题

### Q: 连接失败？

**A**: 检查：
1. API Key 是否正确
2. `TRADING_TESTNET` 是否与 API Key 匹配
3. 网络是否正常

### Q: 下单失败？

**A**: 检查：
1. 余额是否足够
2. 数量是否太小（最小 0.001 BTC）
3. 杠杆是否已设置

### Q: 如何切换到主网？

**A**: 
1. 在 Bybit 主网创建 API Key
2. 设置 `TRADING_TESTNET=False`
3. 更新 API Key 和 Secret

---

## 📚 更多文档

- 📖 [完整使用指南](./TRADING_MODULE_GUIDE.md)
- 🏗️ [架构设计](./TRADING_MODULE_GUIDE.md#架构设计)
- 🔌 [扩展其他交易所](./TRADING_MODULE_GUIDE.md#扩展到其他交易所)

---

**开始交易吧！记得先用测试网！** 🎉
