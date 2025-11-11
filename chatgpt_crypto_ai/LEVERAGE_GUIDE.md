# 🎚️ 杠杆设置指南

## 🎯 两种设置方式

### 方式 1：下单时自动设置（推荐）⭐⭐⭐⭐⭐

在下单请求中直接包含 `leverage` 参数，系统会自动先设置杠杆，然后下单：

```bash
POST /api/trading/order
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "side": "buy",
  "quantity": 0.001,
  "order_type": "market",
  "position_side": "long",
  "leverage": 10  // ✅ 自动设置 10 倍杠杆
}
```

**优势**：
- ✅ 一步完成，无需单独调用
- ✅ 代码简洁
- ✅ 即使设置杠杆失败，也会继续下单

---

### 方式 2：单独设置杠杆

先设置杠杆，再下单：

```bash
# 1. 设置杠杆
POST /api/trading/leverage
{
  "symbol": "BTCUSDT",
  "leverage": 10
}

# 2. 下单
POST /api/trading/order
{
  "symbol": "BTCUSDT",
  "side": "buy",
  "quantity": 0.001,
  "position_side": "long"
}
```

**优势**：
- ✅ 可以提前设置好杠杆
- ✅ 多次下单无需重复设置
- ✅ 更灵活

---

## 📱 客户端示例

### JavaScript/TypeScript

```javascript
// 方式 1：下单时自动设置（推荐）
async function createOrderWithLeverage() {
    const response = await fetch('/api/trading/order', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            symbol: 'BTCUSDT',
            side: 'buy',
            quantity: 0.001,
            order_type: 'market',
            position_side: 'long',
            leverage: 10  // ✅ 自动设置杠杆
        })
    });
    
    return await response.json();
}

// 方式 2：单独设置
async function setLeverageAndOrder() {
    // 1. 设置杠杆
    await fetch('/api/trading/leverage', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            symbol: 'BTCUSDT',
            leverage: 10
        })
    });
    
    // 2. 下单
    const response = await fetch('/api/trading/order', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            symbol: 'BTCUSDT',
            side: 'buy',
            quantity: 0.001,
            order_type: 'market',
            position_side: 'long'
        })
    });
    
    return await response.json();
}
```

### Python

```python
import requests

BASE_URL = "http://localhost:5000"
TOKEN = "your_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 方式 1：下单时自动设置
def create_order_with_leverage():
    response = requests.post(
        f"{BASE_URL}/api/trading/order",
        headers=headers,
        json={
            "symbol": "BTCUSDT",
            "side": "buy",
            "quantity": 0.001,
            "order_type": "market",
            "position_side": "long",
            "leverage": 10  # ✅ 自动设置杠杆
        }
    )
    return response.json()

# 方式 2：单独设置
def set_leverage_and_order():
    # 1. 设置杠杆
    requests.post(
        f"{BASE_URL}/api/trading/leverage",
        headers=headers,
        json={
            "symbol": "BTCUSDT",
            "leverage": 10
        }
    )
    
    # 2. 下单
    response = requests.post(
        f"{BASE_URL}/api/trading/order",
        headers=headers,
        json={
            "symbol": "BTCUSDT",
            "side": "buy",
            "quantity": 0.001,
            "order_type": "market",
            "position_side": "long"
        }
    )
    return response.json()
```

---

## 🎚️ 杠杆倍数说明

### Bybit 支持的杠杆

| 交易对 | 最小杠杆 | 最大杠杆 |
|--------|---------|---------|
| BTCUSDT | 1x | 100x |
| ETHUSDT | 1x | 100x |
| 其他主流币 | 1x | 50x-100x |
| 小币种 | 1x | 25x-50x |

**注意**：实际可用杠杆取决于：
- 交易对
- 持仓大小
- 账户等级
- 风险限额

---

## ⚠️ 风险提示

### 杠杆风险

| 杠杆倍数 | 爆仓价格距离 | 风险等级 |
|---------|------------|---------|
| 1x | 100% | ⭐ 低 |
| 5x | 20% | ⭐⭐ 中低 |
| 10x | 10% | ⭐⭐⭐ 中 |
| 20x | 5% | ⭐⭐⭐⭐ 高 |
| 50x | 2% | ⭐⭐⭐⭐⭐ 极高 |
| 100x | 1% | 💀 极度危险 |

### 建议

- ✅ **新手建议**: 1x-5x
- ✅ **有经验**: 5x-10x
- ⚠️ **高风险**: 10x-20x
- ❌ **不推荐**: 20x 以上

---

## 🔧 完整交易流程示例

### 做多 BTC（10倍杠杆）

```javascript
async function longBTC() {
    try {
        // 1. 查看余额
        const balance = await fetch('/api/trading/balance?coin=USDT', {
            headers: { 'Authorization': `Bearer ${token}` }
        }).then(r => r.json());
        
        console.log(`可用余额: ${balance.data.available} USDT`);
        
        // 2. 创建做多订单（自动设置 10 倍杠杆）
        const order = await fetch('/api/trading/order', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: 'BTCUSDT',
                side: 'buy',
                quantity: 0.001,
                order_type: 'market',
                position_side: 'long',
                leverage: 10  // ✅ 10 倍杠杆
            })
        }).then(r => r.json());
        
        console.log('开多成功:', order.data);
        
        // 3. 查看持仓
        const positions = await fetch('/api/trading/positions?symbol=BTCUSDT', {
            headers: { 'Authorization': `Bearer ${token}` }
        }).then(r => r.json());
        
        console.log('当前持仓:', positions.data);
        
    } catch (error) {
        console.error('交易失败:', error);
    }
}
```

---

## 📊 杠杆计算示例

### 示例 1：10 倍杠杆做多 BTC

```
当前价格: $100,000
杠杆倍数: 10x
保证金: $1,000

实际控制: $1,000 × 10 = $10,000
数量: $10,000 / $100,000 = 0.1 BTC

价格涨到 $110,000:
盈利: 0.1 × ($110,000 - $100,000) = $1,000
收益率: 100%

价格跌到 $90,000:
亏损: 0.1 × ($100,000 - $90,000) = $1,000
爆仓: 亏损 100%
```

### 示例 2：5 倍杠杆做空 ETH

```
当前价格: $4,000
杠杆倍数: 5x
保证金: $1,000

实际控制: $1,000 × 5 = $5,000
数量: $5,000 / $4,000 = 1.25 ETH

价格跌到 $3,600:
盈利: 1.25 × ($4,000 - $3,600) = $500
收益率: 50%

价格涨到 $4,800:
亏损: 1.25 × ($4,800 - $4,000) = $1,000
爆仓: 亏损 100%
```

---

## 🎯 最佳实践

### 1. 根据策略选择杠杆

```javascript
// 短线交易（日内）
const shortTermLeverage = 5;  // 5-10x

// 中线交易（几天）
const midTermLeverage = 3;    // 2-5x

// 长线交易（几周）
const longTermLeverage = 1;   // 1-2x
```

### 2. 动态调整杠杆

```javascript
async function adjustLeverage(symbol, volatility) {
    let leverage;
    
    if (volatility < 0.02) {
        leverage = 10;  // 低波动，可用高杠杆
    } else if (volatility < 0.05) {
        leverage = 5;   // 中波动，中等杠杆
    } else {
        leverage = 2;   // 高波动，低杠杆
    }
    
    await setLeverage(symbol, leverage);
}
```

### 3. 设置止损

```javascript
async function createOrderWithStopLoss() {
    // 1. 开仓
    const order = await fetch('/api/trading/order', {
        method: 'POST',
        body: JSON.stringify({
            symbol: 'BTCUSDT',
            side: 'buy',
            quantity: 0.001,
            position_side: 'long',
            leverage: 10
        })
    });
    
    // 2. 设置止损（假设当前价格 100000）
    const stopLoss = await fetch('/api/trading/order', {
        method: 'POST',
        body: JSON.stringify({
            symbol: 'BTCUSDT',
            side: 'sell',
            quantity: 0.001,
            order_type: 'limit',
            price: 95000,  // 止损价格（5% 止损）
            position_side: 'long'
        })
    });
}
```

---

## ✅ 总结

### 推荐使用方式

**一步到位**（推荐）：
```json
{
  "symbol": "BTCUSDT",
  "side": "buy",
  "quantity": 0.001,
  "position_side": "long",
  "leverage": 10  // ✅ 直接在下单时设置
}
```

### 关键点

- ✅ 支持 1x-100x 杠杆（取决于交易对）
- ✅ 可以在下单时自动设置
- ✅ 也可以单独设置
- ⚠️ 高杠杆高风险，谨慎使用
- ⚠️ 建议设置止损保护

**现在你可以灵活设置杠杆了！** 🎉

---

## 💰 盈亏查询接口

### 📊 接口说明

```bash
GET /api/trading/pnl?symbol=BTCUSDT
Authorization: Bearer YOUR_TOKEN
```

**功能**：查询持仓盈亏统计

---

### 📋 响应格式

```json
{
  "status": "success",
  "data": {
    "total_unrealized_pnl": 150.5,      // 总未实现盈亏（USDT）
    "total_realized_pnl": 0.0,          // 总已实现盈亏（暂不支持）
    "position_count": 2,                 // 持仓数量
    "positions": [
      {
        "symbol": "BTCUSDT",
        "side": "Buy",                   // Buy=做多, Sell=做空
        "size": 0.001,                   // 持仓数量
        "entry_price": 100000.0,         // 开仓均价
        "mark_price": 101000.0,          // 标记价格
        "unrealized_pnl": 1.0,           // 未实现盈亏（USDT）
        "unrealized_pnl_percent": 1.0,   // 盈亏百分比
        "leverage": 10.0                 // 杠杆倍数
      },
      {
        "symbol": "ETHUSDT",
        "side": "Sell",
        "size": 0.5,
        "entry_price": 4000.0,
        "mark_price": 3900.0,
        "unrealized_pnl": 50.0,
        "unrealized_pnl_percent": 2.5,
        "leverage": 5.0
      }
    ]
  }
}
```

---

### 📱 使用示例

#### 获取所有持仓盈亏

```javascript
async function getAllPnL() {
    const response = await fetch('/api/trading/pnl', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    const data = await response.json();
    
    console.log(`总盈亏: ${data.data.total_unrealized_pnl} USDT`);
    console.log(`持仓数: ${data.data.position_count}`);
    
    data.data.positions.forEach(pos => {
        console.log(`${pos.symbol}: ${pos.unrealized_pnl} USDT (${pos.unrealized_pnl_percent}%)`);
    });
    
    return data;
}
```

#### 实时监控盈亏

```javascript
function startPnLMonitor() {
    setInterval(async () => {
        const pnl = await fetch('/api/trading/pnl', {
            headers: { 'Authorization': `Bearer ${token}` }
        }).then(r => r.json());
        
        // 更新 UI
        const totalPnl = pnl.data.total_unrealized_pnl;
        document.getElementById('total-pnl').textContent = 
            `${totalPnl > 0 ? '+' : ''}${totalPnl.toFixed(2)} USDT`;
        
        // 根据盈亏显示颜色
        const element = document.getElementById('total-pnl');
        if (totalPnl > 0) {
            element.className = 'profit';  // 绿色
        } else if (totalPnl < 0) {
            element.className = 'loss';    // 红色
        }
    }, 5000);  // 每 5 秒更新一次
}
```

#### React 组件示例

```jsx
import React, { useState, useEffect } from 'react';

function PnLDashboard() {
    const [pnlData, setPnlData] = useState(null);
    
    useEffect(() => {
        // 初始加载
        fetchPnL();
        
        // 每 5 秒更新一次
        const interval = setInterval(fetchPnL, 5000);
        return () => clearInterval(interval);
    }, []);
    
    const fetchPnL = async () => {
        const response = await fetch('/api/trading/pnl', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        const data = await response.json();
        setPnlData(data.data);
    };
    
    if (!pnlData) return <div>加载中...</div>;
    
    const totalPnl = pnlData.total_unrealized_pnl;
    const isProfit = totalPnl > 0;
    
    return (
        <div className="pnl-dashboard">
            <div className={`total-pnl ${isProfit ? 'profit' : 'loss'}`}>
                <h2>总盈亏</h2>
                <div className="amount">
                    {isProfit ? '+' : ''}{totalPnl.toFixed(2)} USDT
                </div>
            </div>
            
            <div className="positions">
                <h3>持仓详情 ({pnlData.position_count})</h3>
                {pnlData.positions.map(pos => (
                    <div key={pos.symbol} className="position-card">
                        <div className="symbol">{pos.symbol}</div>
                        <div className="side">{pos.side === 'Buy' ? '做多' : '做空'}</div>
                        <div className={`pnl ${pos.unrealized_pnl > 0 ? 'profit' : 'loss'}`}>
                            {pos.unrealized_pnl > 0 ? '+' : ''}{pos.unrealized_pnl.toFixed(2)} USDT
                            <span>({pos.unrealized_pnl_percent}%)</span>
                        </div>
                        <div className="leverage">{pos.leverage}x</div>
                    </div>
                ))}
            </div>
        </div>
    );
}
```

---

### 🧮 盈亏计算公式

#### 做多（Buy）

```
未实现盈亏 = 持仓数量 × (标记价格 - 开仓均价)
盈亏百分比 = ((标记价格 - 开仓均价) / 开仓均价) × 100%
```

**示例**：
```
持仓: 0.1 BTC
开仓价: $100,000
当前价: $101,000

未实现盈亏 = 0.1 × ($101,000 - $100,000) = $100
盈亏百分比 = 1%
```

#### 做空（Sell）

```
未实现盈亏 = 持仓数量 × (开仓均价 - 标记价格)
盈亏百分比 = ((开仓均价 - 标记价格) / 开仓均价) × 100%
```

**示例**：
```
持仓: 0.1 BTC
开仓价: $100,000
当前价: $99,000

未实现盈亏 = 0.1 × ($100,000 - $99,000) = $100
盈亏百分比 = 1%
```

---

### 💡 使用场景

#### 1. 风险预警

```javascript
async function checkRiskAlert() {
    const pnl = await fetch('/api/trading/pnl').then(r => r.json());
    
    for (const pos of pnl.data.positions) {
        // 亏损超过 5% 预警
        if (pos.unrealized_pnl_percent < -5) {
            alert(`⚠️ ${pos.symbol} 亏损 ${Math.abs(pos.unrealized_pnl_percent)}%，建议止损！`);
        }
        
        // 盈利超过 10% 提示止盈
        if (pos.unrealized_pnl_percent > 10) {
            alert(`✅ ${pos.symbol} 盈利 ${pos.unrealized_pnl_percent}%，建议止盈！`);
        }
    }
}
```

#### 2. 统计分析

```javascript
async function analyzePnL() {
    const pnl = await fetch('/api/trading/pnl').then(r => r.json());
    
    // 盈利持仓
    const profitPositions = pnl.data.positions.filter(p => p.unrealized_pnl > 0);
    
    // 亏损持仓
    const lossPositions = pnl.data.positions.filter(p => p.unrealized_pnl < 0);
    
    console.log(`盈利持仓: ${profitPositions.length}`);
    console.log(`亏损持仓: ${lossPositions.length}`);
    console.log(`胜率: ${(profitPositions.length / pnl.data.position_count * 100).toFixed(2)}%`);
}
```

---

### 🎨 UI 展示建议

#### CSS 样式

```css
.profit {
    color: #00c853;  /* 绿色 */
}

.loss {
    color: #ff1744;  /* 红色 */
}

.neutral {
    color: #757575;  /* 灰色 */
}
```

#### 盈亏图标

```javascript
function getPnLIcon(pnl) {
    if (pnl > 0) return '📈';  // 上涨
    if (pnl < 0) return '📉';  // 下跌
    return '➖';               // 持平
}
```

---

## 📊 完整交易接口列表

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/trading/balance` | GET | 获取余额 |
| `/api/trading/order` | POST | 创建订单（支持 leverage） |
| `/api/trading/order/:id` | DELETE | 取消订单 |
| `/api/trading/orders` | GET | 获取挂单 |
| `/api/trading/positions` | GET | 获取持仓 |
| `/api/trading/pnl` | GET | **获取盈亏** 💰 |
| `/api/trading/position/close` | POST | 平仓 |
| `/api/trading/leverage` | POST | 设置杠杆 |

---

## 🎯 完整交易流程（含盈亏监控）

```javascript
async function completeTrading() {
    try {
        // 1. 查看余额
        const balance = await fetch('/api/trading/balance?coin=USDT', {
            headers: { 'Authorization': `Bearer ${token}` }
        }).then(r => r.json());
        console.log(`余额: ${balance.data.available} USDT`);
        
        // 2. 创建订单（10倍杠杆）
        const order = await fetch('/api/trading/order', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: 'BTCUSDT',
                side: 'buy',
                quantity: 0.001,
                order_type: 'market',
                position_side: 'long',
                leverage: 10
            })
        }).then(r => r.json());
        console.log('开仓成功:', order.data);
        
        // 3. 实时监控盈亏
        const pnlInterval = setInterval(async () => {
            const pnl = await fetch('/api/trading/pnl?symbol=BTCUSDT', {
                headers: { 'Authorization': `Bearer ${token}` }
            }).then(r => r.json());
            
            if (pnl.data.positions.length > 0) {
                const pos = pnl.data.positions[0];
                console.log(`当前盈亏: ${pos.unrealized_pnl} USDT (${pos.unrealized_pnl_percent}%)`);
                
                // 止盈：盈利超过 5%
                if (pos.unrealized_pnl_percent > 5) {
                    console.log('触发止盈！');
                    await closePosition('BTCUSDT', 'long');
                    clearInterval(pnlInterval);
                }
                
                // 止损：亏损超过 3%
                if (pos.unrealized_pnl_percent < -3) {
                    console.log('触发止损！');
                    await closePosition('BTCUSDT', 'long');
                    clearInterval(pnlInterval);
                }
            }
        }, 3000);  // 每 3 秒检查一次
        
    } catch (error) {
        console.error('交易失败:', error);
    }
}

async function closePosition(symbol, positionSide) {
    await fetch('/api/trading/position/close', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            symbol: symbol,
            position_side: positionSide
        })
    });
}
```

---

**现在你可以实时监控盈亏并自动止盈止损了！** 💰📈
