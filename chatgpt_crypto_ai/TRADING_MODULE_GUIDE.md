# 📈 交易模块使用指南

## 🎯 功能概述

本模块提供了模块化、可扩展的交易所下单功能，目前支持 **Bybit**，未来可轻松扩展到币安、火币等其他交易所。

### 核心特性

- ✅ **模块化设计** - 基于抽象基类，易于扩展
- ✅ **统一接口** - 所有交易所使用相同的 API
- ✅ **支持合约交易** - 做多/做空、杠杆设置、持仓管理
- ✅ **完整的订单管理** - 市价单、限价单、查询、取消
- ✅ **测试网支持** - 安全测试，不影响真实资金

---

## 📦 架构设计

```
exchanges/
├── base_exchange.py        # 抽象基类（定义接口）
├── bybit_exchange.py       # Bybit 实现
├── exchange_factory.py     # 工厂类（创建交易所实例）
└── __init__.py

services/
└── trading_service.py      # 交易服务层（统一接口）

routes/
└── trading_routes.py       # API 路由
```

### 设计模式

1. **抽象工厂模式** - `ExchangeFactory` 根据配置创建交易所实例
2. **策略模式** - 不同交易所实现相同接口
3. **单例模式** - 交易所连接复用

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install pybit>=5.6.0
```

### 2. 配置环境变量

在 `.env` 文件中添加：

```bash
# 交易配置
TRADING_EXCHANGE=bybit          # 交易所名称
TRADING_API_KEY=your_api_key    # API Key
TRADING_API_SECRET=your_secret  # API Secret
TRADING_TESTNET=True            # 使用测试网（建议先用测试网）
```

### 3. 获取 Bybit API Key

#### 测试网（推荐先用测试网）

1. 访问 [Bybit 测试网](https://testnet.bybit.com/)
2. 注册账号并登录
3. 进入 API 管理页面
4. 创建 API Key，权限选择：
   - ✅ 合约交易
   - ✅ 读取账户信息
5. 复制 API Key 和 Secret 到 `.env`

#### 主网（真实交易）

1. 访问 [Bybit 主网](https://www.bybit.com/)
2. 完成 KYC 认证
3. 创建 API Key
4. 设置 `TRADING_TESTNET=False`

---

## 📡 API 接口

### 1. 获取账户余额

```bash
GET /api/trading/balance?coin=USDT
```

**响应**：
```json
{
  "status": "success",
  "data": {
    "coin": "USDT",
    "available": 1000.0,
    "total": 1000.0,
    "equity": 1000.0
  }
}
```

---

### 2. 创建订单

```bash
POST /api/trading/order
```

**请求 Body**：
```json
{
  "symbol": "BTCUSDT",
  "side": "buy",           // buy 或 sell
  "quantity": 0.001,
  "order_type": "market",  // market 或 limit
  "price": 50000,          // 限价单必填
  "position_side": "long"  // long 或 short（合约必填）
}
```

**响应**：
```json
{
  "status": "success",
  "data": {
    "order_id": "1234567890",
    "symbol": "BTCUSDT",
    "side": "Buy",
    "quantity": 0.001,
    "order_type": "Market",
    "status": "Created",
    "position_side": "Long"
  }
}
```

---

### 3. 取消订单

```bash
DELETE /api/trading/order/{order_id}?symbol=BTCUSDT
```

**响应**：
```json
{
  "status": "success",
  "data": {
    "order_id": "1234567890",
    "status": "Cancelled"
  }
}
```

---

### 4. 获取当前挂单

```bash
GET /api/trading/orders?symbol=BTCUSDT
```

**响应**：
```json
{
  "status": "success",
  "data": [
    {
      "order_id": "1234567890",
      "symbol": "BTCUSDT",
      "side": "Buy",
      "quantity": 0.001,
      "price": 50000,
      "status": "New"
    }
  ]
}
```

---

### 5. 获取持仓

```bash
GET /api/trading/positions?symbol=BTCUSDT
```

**响应**：
```json
{
  "status": "success",
  "data": [
    {
      "symbol": "BTCUSDT",
      "side": "Buy",
      "size": 0.001,
      "entry_price": 50000.0,
      "mark_price": 51000.0,
      "unrealized_pnl": 1.0,
      "leverage": 10.0
    }
  ]
}
```

---

### 6. 平仓

```bash
POST /api/trading/position/close
```

**请求 Body**：
```json
{
  "symbol": "BTCUSDT",
  "position_side": "long"  // long 或 short
}
```

**响应**：
```json
{
  "status": "success",
  "data": {
    "order_id": "1234567890",
    "symbol": "BTCUSDT",
    "side": "Sell",
    "quantity": 0.001,
    "status": "Created"
  }
}
```

---

### 7. 设置杠杆

```bash
POST /api/trading/leverage
```

**请求 Body**：
```json
{
  "symbol": "BTCUSDT",
  "leverage": 10
}
```

**响应**：
```json
{
  "status": "success",
  "data": {
    "symbol": "BTCUSDT",
    "leverage": 10,
    "status": "Success"
  }
}
```

---

## 💻 代码示例

### Python 示例

```python
import requests

BASE_URL = "http://localhost:5000"
TOKEN = "your_auth_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 1. 获取余额
response = requests.get(f"{BASE_URL}/api/trading/balance", headers=headers)
print(response.json())

# 2. 创建市价做多单
order_data = {
    "symbol": "BTCUSDT",
    "side": "buy",
    "quantity": 0.001,
    "order_type": "market",
    "position_side": "long"
}
response = requests.post(f"{BASE_URL}/api/trading/order", json=order_data, headers=headers)
print(response.json())

# 3. 获取持仓
response = requests.get(f"{BASE_URL}/api/trading/positions", headers=headers)
print(response.json())

# 4. 平仓
close_data = {
    "symbol": "BTCUSDT",
    "position_side": "long"
}
response = requests.post(f"{BASE_URL}/api/trading/position/close", json=close_data, headers=headers)
print(response.json())
```

### JavaScript 示例

```javascript
const BASE_URL = "http://localhost:5000";
const TOKEN = "your_auth_token";

const headers = {
    "Authorization": `Bearer ${TOKEN}`,
    "Content-Type": "application/json"
};

// 创建订单
async function createOrder() {
    const response = await fetch(`${BASE_URL}/api/trading/order`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            symbol: "BTCUSDT",
            side: "buy",
            quantity: 0.001,
            order_type: "market",
            position_side: "long"
        })
    });
    
    const data = await response.json();
    console.log(data);
}

// 获取持仓
async function getPositions() {
    const response = await fetch(`${BASE_URL}/api/trading/positions`, {
        method: 'GET',
        headers: headers
    });
    
    const data = await response.json();
    console.log(data);
}
```

---

## 🔧 直接使用服务层

如果你想在后端代码中直接调用，不通过 API：

```python
from services.trading_service import TradingService
from exchanges.base_exchange import OrderSide, PositionSide

# 创建订单
result = TradingService.create_order(
    symbol="BTCUSDT",
    side="buy",
    quantity=0.001,
    order_type="market",
    position_side="long"
)

# 获取余额
balance = TradingService.get_balance(coin="USDT")

# 获取持仓
positions = TradingService.get_positions(symbol="BTCUSDT")

# 平仓
result = TradingService.close_position(
    symbol="BTCUSDT",
    position_side="long"
)
```

---

## 🔌 扩展到其他交易所

### 添加币安交易所示例

#### 1. 创建 `exchanges/binance_exchange.py`

```python
from .base_exchange import BaseExchange, OrderSide, PositionSide
from binance.client import Client

class BinanceExchange(BaseExchange):
    def connect(self) -> bool:
        self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)
        # 测试连接
        try:
            self.client.ping()
            return True
        except:
            return False
    
    def get_balance(self, coin: str = "USDT"):
        # 实现币安的余额查询
        pass
    
    def create_market_order(self, symbol, side, quantity, position_side=None):
        # 实现币安的市价单
        pass
    
    # ... 实现其他抽象方法
```

#### 2. 注册到工厂类

```python
# exchanges/exchange_factory.py

from .binance_exchange import BinanceExchange

class ExchangeFactory:
    EXCHANGES = {
        'bybit': BybitExchange,
        'binance': BinanceExchange,  # ✅ 添加这行
    }
```

#### 3. 使用

```python
# 在 .env 中设置
TRADING_EXCHANGE=binance

# 或者在代码中指定
TradingService.create_order(
    symbol="BTCUSDT",
    side="buy",
    quantity=0.001,
    exchange_name="binance"  # ✅ 指定交易所
)
```

---

## 🧪 测试

### 测试脚本

创建 `test_trading.py`：

```python
from services.trading_service import TradingService

# 测试连接
try:
    exchange = TradingService.get_exchange()
    print("✅ 连接成功")
except Exception as e:
    print(f"❌ 连接失败: {e}")

# 测试获取余额
try:
    balance = TradingService.get_balance()
    print(f"✅ 余额: {balance}")
except Exception as e:
    print(f"❌ 获取余额失败: {e}")

# 测试创建订单（小额测试）
try:
    result = TradingService.create_order(
        symbol="BTCUSDT",
        side="buy",
        quantity=0.001,  # 最小数量
        order_type="market",
        position_side="long"
    )
    print(f"✅ 订单创建成功: {result}")
except Exception as e:
    print(f"❌ 创建订单失败: {e}")
```

运行测试：
```bash
python test_trading.py
```

---

## ⚠️ 注意事项

### 安全建议

1. **使用测试网** - 先在测试网测试，确保功能正常
2. **API Key 权限** - 只授予必要的权限
3. **不要泄露** - 永远不要将 API Key 提交到 Git
4. **IP 白名单** - 在交易所设置 IP 白名单
5. **小额测试** - 真实交易前先用小额测试

### 风险提示

- ⚠️ 加密货币交易有风险，可能导致资金损失
- ⚠️ 本模块仅供学习和研究使用
- ⚠️ 使用前请充分了解交易规则和风险
- ⚠️ 建议设置止损和仓位管理

---

## 📊 支持的交易所

| 交易所 | 状态 | 说明 |
|--------|------|------|
| **Bybit** | ✅ 已支持 | 完整实现 |
| 币安 (Binance) | 🔄 计划中 | 待实现 |
| 火币 (Huobi) | 🔄 计划中 | 待实现 |
| OKX | 🔄 计划中 | 待实现 |

---

## 🐛 常见问题

### Q1: 连接失败怎么办？

**A**: 检查以下几点：
1. API Key 和 Secret 是否正确
2. 是否使用了正确的网络（测试网/主网）
3. API Key 是否有足够的权限
4. 网络连接是否正常

### Q2: 下单失败？

**A**: 可能的原因：
1. 余额不足
2. 数量太小（低于最小下单量）
3. 杠杆未设置
4. 交易对格式错误（应该是 "BTCUSDT" 而不是 "BTC/USDT"）

### Q3: 如何切换到主网？

**A**: 在 `.env` 中设置：
```bash
TRADING_TESTNET=False
```

### Q4: 支持现货交易吗？

**A**: 目前主要支持合约交易，现货交易需要修改 `category` 参数。

---

## 📝 更新日志

### v1.0.0 (2025-11-10)

- ✅ 初始版本
- ✅ 支持 Bybit 合约交易
- ✅ 市价单、限价单
- ✅ 持仓管理、杠杆设置
- ✅ 模块化设计，易于扩展

---

## 🎯 下一步计划

1. ✅ 支持 Bybit（已完成）
2. 🔄 添加币安交易所支持
3. 🔄 添加火币交易所支持
4. 🔄 添加现货交易支持
5. 🔄 添加止损止盈单
6. 🔄 添加订单历史查询
7. 🔄 添加交易记录导出

---

**开始使用吧！记得先用测试网测试！** 🚀
