# 导入错误修复

## 🐛 问题

```
ImportError: cannot import name 'TradingPnLHistory' from 'models'
```

## ✅ 修复

### 1. 正确的类名
- ❌ `TradingPnLHistory` (大写L)
- ✅ `TradingPnlHistory` (小写l)

### 2. 正确的导入路径

**修改前**：
```python
from models import db, User, TradingPnLHistory, TradingOrderHistory
```

**修改后**：
```python
from models import db, User
from models.trading_history import TradingPnlHistory, TradingOrderHistory
```

### 3. 字段名修复

TradingPnlHistory模型的字段：
```python
open_time       # 开仓时间
open_price      # 开仓价格
open_size       # 开仓数量
close_time      # 平仓时间
close_price     # 平仓价格
close_size      # 平仓数量
realized_pnl    # 已实现盈亏
pnl_percentage  # 盈亏百分比
fee             # 手续费
net_pnl         # 净盈亏
leverage        # 杠杆
order_id        # 订单ID
```

## 📝 修改的文件

- `services/sync_trading_history.py` - 修复导入和字段名

## ✅ 现在可以正常启动

```bash
python run.py
```

应该看到：
```
sync.sync_pnl_history: /api/sync/trading/pnl [POST]
sync.sync_order_history: /api/sync/trading/orders [POST]
sync.sync_all_history: /api/sync/trading/all [POST]
```
