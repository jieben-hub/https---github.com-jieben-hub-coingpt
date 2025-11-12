# 自动同步交易历史

## 🎯 功能说明

系统会**自动定时**从Bybit同步所有用户的历史交易记录到数据库，无需手动操作。

## ⏰ 同步时间表

### 默认配置

```
每30秒 - 同步所有用户最近1天的交易历史
```

### 特点

- ✅ **高频率** - 每30秒执行一次
- ✅ **近实时** - 数据几乎实时更新
- ✅ **短周期** - 只同步最近1天，减少API调用

## 📦 工作原理

### 1. 定时任务

使用APScheduler定时调度：

```python
# 每30秒执行一次
scheduler.add_job(
    func=AutoSyncService.sync_all_users_history(days=1),
    trigger='interval',
    seconds=30
)
```

### 2. 同步流程

```
1. 定时任务触发（每30秒）
   ↓
2. 获取所有活跃用户
   ↓
3. 遍历每个用户
   ├─ 调用Bybit API获取最近1天的平仓记录
   ├─ 调用Bybit API获取最近1天的订单记录
   ├─ 解析数据
   ├─ 去重检查（通过order_id）
   └─ 保存到数据库
   ↓
4. 记录同步结果
   ├─ 成功用户数
   ├─ 失败用户数
   ├─ 新增记录数
   └─ 跳过记录数
   ↓
5. 完成，30秒后再次执行
```

## 📊 同步内容

### 每个用户同步

- ✅ 最近1天的已平仓位记录
- ✅ 最近1天的订单历史记录
- ✅ 所有交易对（不限制symbol）

### 自动去重

- ✅ 通过`order_id`检查是否已存在
- ✅ 已存在的记录会跳过
- ✅ 订单记录会更新状态

## 🔧 配置

### 1. 安装依赖

```bash
pip install apscheduler
```

### 2. 启动服务器

```bash
python run.py
```

### 3. 查看日志

启动时应该看到：

```
自动同步定时任务已启动
  - 每30秒同步所有用户最近1天的交易历史
```

### 4. 同步时日志

每30秒会看到：

```
开始自动同步所有用户的交易历史，最近1天
同步用户4的交易历史
获取已平仓盈亏记录: {'category': 'linear', 'limit': 100, 'startTime': ...}
获取到15条平仓记录
同步平仓记录: BTCUSDT Buy PnL=100.5
用户4同步完成: 平仓10条, 订单20条
自动同步完成: 成功1个用户, 失败0个用户
总计: 新增30条记录, 跳过5条记录
```

## ⚙️ 自定义配置

### 修改同步时间

编辑 `services/auto_sync_service.py`:

```python
# 修改为每天凌晨2点
scheduler.add_job(
    func=lambda: app.app_context().push() or AutoSyncService.sync_all_users_history(days=7),
    trigger='cron',
    hour=2,  # 修改这里
    minute=0
)
```

### 修改同步天数

```python
# 同步最近30天
AutoSyncService.sync_all_users_history(days=30)
```

### 启用更频繁的同步

取消注释：

```python
# 每6小时同步一次最近1天的数据
scheduler.add_job(
    func=lambda: app.app_context().push() or AutoSyncService.sync_all_users_history(days=1),
    trigger='interval',
    hours=6,
    id='auto_sync_trading_history_frequent',
    name='自动同步交易历史（频繁）',
    replace_existing=True
)
```

### 只同步特定用户

```python
# 只同步用户ID为4的用户
AutoSyncService.sync_user_history(user_id=4, days=7)
```

## 📝 代码结构

### services/auto_sync_service.py

```python
class AutoSyncService:
    @staticmethod
    def sync_all_users_history(days=7):
        """同步所有用户的交易历史"""
        # 1. 获取所有活跃用户
        # 2. 遍历每个用户
        # 3. 调用TradingHistorySync.sync_all_history()
        # 4. 记录结果
    
    @staticmethod
    def sync_user_history(user_id, days=7):
        """同步单个用户的交易历史"""
        # 调用TradingHistorySync.sync_all_history()

def init_auto_sync(app):
    """初始化定时任务"""
    # 创建APScheduler
    # 添加定时任务
    # 启动调度器
```

### app.py

```python
# 初始化自动同步服务
from services.auto_sync_service import init_auto_sync
auto_sync_scheduler = init_auto_sync(app)
```

## 🧪 测试

### 1. 手动触发同步

在Python控制台：

```python
from app import create_app
from services.auto_sync_service import AutoSyncService

app = create_app()
with app.app_context():
    # 同步所有用户
    AutoSyncService.sync_all_users_history(days=7)
    
    # 或只同步特定用户
    AutoSyncService.sync_user_history(user_id=4, days=7)
```

### 2. 验证数据库

```sql
-- 查看最近同步的记录
SELECT * FROM trading_pnl_history 
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;

SELECT * FROM trading_order_history 
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;
```

### 3. 查看定时任务状态

```python
from apscheduler.schedulers.background import BackgroundScheduler

# 查看所有任务
scheduler.get_jobs()

# 查看下次执行时间
job = scheduler.get_job('auto_sync_trading_history')
print(f"下次执行时间: {job.next_run_time}")
```

## ⚠️ 注意事项

### 1. APScheduler依赖

如果没有安装APScheduler：

```
APScheduler未安装，自动同步定时任务未启动
如需启用自动同步，请安装: pip install apscheduler
```

安装后重启服务器即可。

### 2. 同步时间选择

- ✅ 凌晨3点 - 用户少，服务器负载低
- ✅ 避开高峰期
- ✅ 给Bybit API足够的时间生成数据

### 3. 同步频率

- **每天一次（推荐）**: 足够获取所有历史数据
- **每6小时一次**: 更实时，但API调用更频繁
- **按需同步**: 用户可以手动触发（保留API端点）

### 4. 错误处理

- ✅ 单个用户失败不影响其他用户
- ✅ 失败会记录日志
- ✅ 下次同步会重试

### 5. 性能考虑

- 每个用户同步约需1-3秒
- 100个用户约需2-5分钟
- 在凌晨执行不影响用户使用

## 📊 监控

### 查看同步日志

```bash
# 查看今天的同步日志
grep "自动同步" logs/app.log | grep "$(date +%Y-%m-%d)"

# 查看同步结果
grep "同步完成" logs/app.log | tail -10
```

### 同步统计

```sql
-- 今天同步的记录数
SELECT COUNT(*) FROM trading_pnl_history 
WHERE DATE(created_at) = CURRENT_DATE;

SELECT COUNT(*) FROM trading_order_history 
WHERE DATE(created_at) = CURRENT_DATE;

-- 按用户统计
SELECT user_id, COUNT(*) as count 
FROM trading_pnl_history 
WHERE DATE(created_at) = CURRENT_DATE
GROUP BY user_id;
```

## 🎉 优势

### vs 手动同步

| 特性 | 手动同步 | 自动同步 |
|------|---------|---------|
| 操作 | 需要用户点击 | 完全自动 |
| 时机 | 用户想起来才同步 | 定时执行 |
| 覆盖 | 只同步当前用户 | 所有用户 |
| 遗漏 | 可能忘记同步 | 不会遗漏 |
| 数据完整性 | 依赖用户 | 系统保证 |

### 完整性保证

- ✅ 每天自动同步，不会遗漏
- ✅ 所有用户都会同步
- ✅ 数据始终保持最新
- ✅ 用户无需关心

## 🔄 与手动同步的配合

### 自动同步（后台）

```
每天凌晨3点 - 同步所有用户最近7天
```

### 手动同步（API）

```
POST /api/sync/trading/all - 用户可以立即同步
```

### 使用场景

- **自动同步**: 保证数据完整性，定期更新
- **手动同步**: 用户需要立即查看最新数据时

## ✅ 总结

现在系统会：

1. ✅ **自动定时同步** - 每天凌晨3点
2. ✅ **同步所有用户** - 不遗漏任何用户
3. ✅ **同步最近7天** - 保证数据完整
4. ✅ **自动去重** - 避免重复记录
5. ✅ **错误处理** - 单个失败不影响整体
6. ✅ **详细日志** - 可追踪同步状态
7. ✅ **保留手动同步** - 用户可按需触发

交易历史数据会自动保持最新，用户无需任何操作！🚀
