# 修复模型导入错误

## 🐛 错误

```
No module named 'models.trading_history'; 'models' is not a package
```

## 🔍 原因

`models.py`是一个文件，不是包（package），所以不能使用`from models.trading_history import`。

## ✅ 修复

### 修改前

```python
from models import db, User
from models.trading_history import TradingPnlHistory, TradingOrderHistory
```

### 修改后

```python
from models import db, User, TradingPnlHistory, TradingOrderHistory
```

## 📝 说明

`TradingPnlHistory`和`TradingOrderHistory`类定义在`models.py`文件中（第220行和第258行），可以直接从`models`导入。

## ✅ 现在可以启动

```bash
python run.py
```

应该看到：

```
自动同步定时任务已启动
  - 每30秒同步所有用户最近1天的交易历史
```
