# 💰 盈亏查询接口

## 📊 接口说明

### GET /api/trading/pnl

获取用户的持仓盈亏统计。

---

## 🚀 请求示例

### 查询所有持仓盈亏

```bash
GET /api/trading/pnl
Authorization: Bearer YOUR_TOKEN
```

### 查询指定交易对盈亏

```bash
GET /api/trading/pnl?symbol=BTCUSDT
Authorization: Bearer YOUR_TOKEN
```

---

## 📋 响应格式

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

## 📱 客户端示例

### JavaScript/TypeScript

```javascript
// 获取所有持仓盈亏
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

// 获取指定交易对盈亏
async function getSymbolPnL(symbol) {
    const response = await fetch(`/api/trading/pnl?symbol=${symbol}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    return await response.json();
}

// 实时监控盈亏
function startPnLMonitor() {
    setInterval(async () => {
        const pnl = await getAllPnL();
        
        // 更新 UI
        document.getElementById('total-pnl').textContent = 
            `${pnl.data.total_unrealized_pnl} USDT`;
        
        // 根据盈亏显示颜色
        const pnlElement = document.getElementById('total-pnl');
        if (pnl.data.total_unrealized_pnl > 0) {
            pnlElement.className = 'profit';  // 绿色
        } else if (pnl.data.total_unrealized_pnl < 0) {
            pnlElement.className = 'loss';    // 红色
        }
    }, 5000);  // 每 5 秒更新一次
}
```

### Python

```python
import requests

BASE_URL = "http://localhost:5000"
TOKEN = "your_token"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# 获取所有持仓盈亏
def get_all_pnl():
    response = requests.get(
        f"{BASE_URL}/api/trading/pnl",
        headers=headers
    )
    data = response.json()
    
    print(f"总盈亏: {data['data']['total_unrealized_pnl']} USDT")
    print(f"持仓数: {data['data']['position_count']}")
    
    for pos in data['data']['positions']:
        print(f"{pos['symbol']}: {pos['unrealized_pnl']} USDT ({pos['unrealized_pnl_percent']}%)")
    
    return data

# 获取指定交易对盈亏
def get_symbol_pnl(symbol):
    response = requests.get(
        f"{BASE_URL}/api/trading/pnl",
        headers=headers,
        params={'symbol': symbol}
    )
    return response.json()

# 计算总收益率
def calculate_total_roi(pnl_data):
    total_pnl = pnl_data['data']['total_unrealized_pnl']
    
    # 计算总投入（保证金）
    total_margin = 0
    for pos in pnl_data['data']['positions']:
        entry_value = pos['entry_price'] * pos['size']
        margin = entry_value / pos['leverage']
        total_margin += margin
    
    if total_margin > 0:
        roi = (total_pnl / total_margin) * 100
        print(f"总收益率: {roi:.2f}%")
        return roi
    
    return 0
```

### React 组件示例

```jsx
import React, { useState, useEffect } from 'react';

function PnLDashboard() {
    const [pnlData, setPnlData] = useState(null);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        // 初始加载
        fetchPnL();
        
        // 每 5 秒更新一次
        const interval = setInterval(fetchPnL, 5000);
        
        return () => clearInterval(interval);
    }, []);
    
    const fetchPnL = async () => {
        try {
            const response = await fetch('/api/trading/pnl', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            const data = await response.json();
            setPnlData(data.data);
            setLoading(false);
        } catch (error) {
            console.error('获取盈亏失败:', error);
        }
    };
    
    if (loading) return <div>加载中...</div>;
    
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
                        <div className="size">{pos.size}</div>
                        <div className={`pnl ${pos.unrealized_pnl > 0 ? 'profit' : 'loss'}`}>
                            {pos.unrealized_pnl > 0 ? '+' : ''}{pos.unrealized_pnl.toFixed(2)} USDT
                            <span className="percent">({pos.unrealized_pnl_percent}%)</span>
                        </div>
                        <div className="leverage">{pos.leverage}x</div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default PnLDashboard;
```

---

## 📊 数据说明

### 字段解释

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_unrealized_pnl` | float | 所有持仓的未实现盈亏总和（USDT） |
| `total_realized_pnl` | float | 已实现盈亏（暂不支持，返回 0） |
| `position_count` | int | 当前持仓数量 |
| `positions` | array | 持仓详情列表 |

### 持仓详情字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `symbol` | string | 交易对 |
| `side` | string | Buy=做多, Sell=做空 |
| `size` | float | 持仓数量 |
| `entry_price` | float | 开仓均价 |
| `mark_price` | float | 当前标记价格 |
| `unrealized_pnl` | float | 未实现盈亏（USDT） |
| `unrealized_pnl_percent` | float | 盈亏百分比 |
| `leverage` | float | 杠杆倍数 |

---

## 🧮 盈亏计算公式

### 做多（Buy）

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
盈亏百分比 = (($101,000 - $100,000) / $100,000) × 100% = 1%
```

### 做空（Sell）

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
盈亏百分比 = (($100,000 - $99,000) / $100,000) × 100% = 1%
```

---

## 💡 使用场景

### 1. 实时监控

```javascript
// 在交易页面实时显示盈亏
function updatePnLDisplay() {
    setInterval(async () => {
        const pnl = await fetch('/api/trading/pnl').then(r => r.json());
        
        document.getElementById('total-pnl').textContent = 
            `${pnl.data.total_unrealized_pnl.toFixed(2)} USDT`;
    }, 3000);
}
```

### 2. 风险预警

```javascript
async function checkRiskAlert() {
    const pnl = await fetch('/api/trading/pnl').then(r => r.json());
    
    for (const pos of pnl.data.positions) {
        // 亏损超过 5% 预警
        if (pos.unrealized_pnl_percent < -5) {
            alert(`⚠️ ${pos.symbol} 亏损 ${pos.unrealized_pnl_percent}%，建议止损！`);
        }
        
        // 盈利超过 10% 提示止盈
        if (pos.unrealized_pnl_percent > 10) {
            alert(`✅ ${pos.symbol} 盈利 ${pos.unrealized_pnl_percent}%，建议止盈！`);
        }
    }
}
```

### 3. 统计分析

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

## 🎨 UI 展示建议

### 盈亏颜色

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

### 盈亏图标

```javascript
function getPnLIcon(pnl) {
    if (pnl > 0) return '📈';  // 上涨
    if (pnl < 0) return '📉';  // 下跌
    return '➖';               // 持平
}
```

---

## ⚠️ 注意事项

### 1. 更新频率

- ✅ 建议 3-5 秒更新一次
- ❌ 不要过于频繁（避免 API 限流）

### 2. 数据延迟

- 标记价格可能有 1-2 秒延迟
- 未实现盈亏是实时计算的估值

### 3. 已实现盈亏

- 目前 `total_realized_pnl` 返回 0
- 大多数交易所不提供实时已实现盈亏 API
- 需要自己记录交易历史计算

---

## 📊 完整示例

```javascript
// 完整的盈亏监控系统
class PnLMonitor {
    constructor(token) {
        this.token = token;
        this.updateInterval = null;
    }
    
    // 开始监控
    start(intervalMs = 5000) {
        this.updateInterval = setInterval(() => {
            this.update();
        }, intervalMs);
        
        // 立即执行一次
        this.update();
    }
    
    // 停止监控
    stop() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
    
    // 更新盈亏数据
    async update() {
        try {
            const response = await fetch('/api/trading/pnl', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
            
            const data = await response.json();
            
            // 更新 UI
            this.updateUI(data.data);
            
            // 检查风险
            this.checkRisk(data.data);
            
        } catch (error) {
            console.error('更新盈亏失败:', error);
        }
    }
    
    // 更新 UI
    updateUI(pnlData) {
        const totalPnl = pnlData.total_unrealized_pnl;
        const element = document.getElementById('total-pnl');
        
        element.textContent = `${totalPnl > 0 ? '+' : ''}${totalPnl.toFixed(2)} USDT`;
        element.className = totalPnl > 0 ? 'profit' : (totalPnl < 0 ? 'loss' : 'neutral');
    }
    
    // 风险检查
    checkRisk(pnlData) {
        for (const pos of pnlData.positions) {
            if (pos.unrealized_pnl_percent < -10) {
                this.showAlert(`⚠️ ${pos.symbol} 亏损 ${Math.abs(pos.unrealized_pnl_percent)}%`);
            }
        }
    }
    
    // 显示提醒
    showAlert(message) {
        // 实现你的提醒逻辑
        console.warn(message);
    }
}

// 使用
const monitor = new PnLMonitor(userToken);
monitor.start(5000);  // 每 5 秒更新
```

---

## ✅ 总结

### 核心功能

- ✅ 查询所有持仓盈亏
- ✅ 查询指定交易对盈亏
- ✅ 计算盈亏百分比
- ✅ 支持做多和做空

### 使用建议

- 📊 实时监控盈亏变化
- ⚠️ 设置风险预警
- 📈 统计分析交易表现
- 🎯 及时止盈止损

**现在可以实时监控盈亏了！** 💰
