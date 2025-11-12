# 订阅系统部署指南

## 🚀 快速部署步骤

### 1. 运行数据库迁移

```bash
cd e:\开发\coingpt\chatgpt_crypto_ai

# 方法1：使用Flask-Migrate
flask db upgrade

# 方法2：直接创建表
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 2. 配置App Store共享密钥

在 `.env` 文件中添加：

```bash
APP_STORE_SHARED_SECRET=43d4a9d1453447c1b24fd7cd64e8c393
```

### 3. 重启服务器

```bash
python run.py
```

### 4. 验证路由已注册

启动后应该看到以下路由：

```
✅ subscription.verify_receipt: /api/subscription/verify [POST]
✅ subscription.restore_purchases: /api/subscription/restore [POST]
✅ subscription.get_subscription_status: /api/subscription/status [GET]
✅ subscription.get_products: /api/subscription/products [GET]
✅ admin_subscription.check_expired: /api/admin/subscription/check-expired [POST]
✅ admin_subscription.get_stats: /api/admin/subscription/stats [GET]
✅ admin_subscription.get_expiring_soon: /api/admin/subscription/expiring-soon [GET]
✅ admin_subscription.get_user_subscriptions: /api/admin/subscription/user/<user_id> [GET]
```

## 📊 新增的数据表

### subscriptions 表结构

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| user_id | BigInteger | 用户ID（外键） |
| product_id | String(255) | 产品ID |
| product_type | String(50) | 产品类型（yearly/monthly） |
| transaction_id | String(255) | 交易ID（唯一） |
| original_transaction_id | String(255) | 原始交易ID |
| purchase_date | DateTime | 购买时间 ✅ |
| expires_date | DateTime | 过期时间 ✅ |
| status | String(20) | 状态（active/expired/cancelled） |
| is_trial_period | Boolean | 是否试用期 |
| is_in_intro_offer_period | Boolean | 是否优惠期 |
| auto_renew_status | Boolean | 是否自动续期 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## 🧪 测试步骤

### 1. 测试产品列表

```bash
curl http://192.168.100.173:5000/api/subscription/products
```

**预期响应**：
```json
{
    "status": "success",
    "data": {
        "products": [
            {
                "product_id": "dev.zonekit.coingpt.Premium.year",
                "type": "yearly",
                "duration_days": 365,
                "membership": "premium",
                "name": "年度会员",
                "description": "享受无限制使用CoinGPT的所有功能"
            }
        ]
    }
}
```

### 2. 测试订阅状态查询

```bash
curl -H "Authorization: Bearer <JWT_TOKEN>" \
  http://192.168.100.173:5000/api/subscription/status
```

**预期响应**：
```json
{
    "status": "success",
    "data": {
        "user_id": 4,
        "membership": "free",
        "is_premium": false,
        "is_free": true,
        "subscription": null
    }
}
```

### 3. 测试iOS购买流程

#### iOS端代码
```swift
// 1. 购买产品
IAPManager.shared.purchaseProduct()

// 2. 购买成功后获取收据
let receiptData = getReceiptData()

// 3. 验证收据
POST /api/subscription/verify
{
    "receipt_data": receiptData
}
```

#### 预期服务器日志
```
验证用户4的收据，环境: 沙盒
收据验证成功，产品: dev.zonekit.coingpt.Premium.year, 过期时间: 2025-11-11
创建新订阅记录: 1000000123456789
用户4订阅已激活: free -> premium
订阅过期时间: 2025-11-11 14:30:00
```

#### 预期API响应
```json
{
    "status": "success",
    "message": "订阅激活成功，会员有效期至 2025-11-11",
    "data": {
        "product_id": "dev.zonekit.coingpt.Premium.year",
        "transaction_id": "1000000123456789",
        "expires_date": "2025-11-11T14:30:00",
        "is_trial_period": false
    }
}
```

### 4. 验证订阅记录已保存

```bash
# 查询用户订阅记录
curl -H "Authorization: Bearer <JWT_TOKEN>" \
  http://192.168.100.173:5000/api/admin/subscription/user/4
```

**预期响应**：
```json
{
    "status": "success",
    "data": [
        {
            "id": 1,
            "product_id": "dev.zonekit.coingpt.Premium.year",
            "product_type": "yearly",
            "transaction_id": "1000000123456789",
            "purchase_date": "2024-11-11T14:30:00",
            "expires_date": "2025-11-11T14:30:00",
            "status": "active",
            "is_active": true,
            "days_until_expiry": 365,
            "is_trial_period": false,
            "auto_renew_status": true,
            "created_at": "2024-11-11T14:30:00"
        }
    ]
}
```

### 5. 测试过期检查

```bash
# 手动触发过期检查
curl -X POST -H "Authorization: Bearer <JWT_TOKEN>" \
  http://192.168.100.173:5000/api/admin/subscription/check-expired
```

### 6. 查看订阅统计

```bash
curl -H "Authorization: Bearer <JWT_TOKEN>" \
  http://192.168.100.173:5000/api/admin/subscription/stats
```

**预期响应**：
```json
{
    "status": "success",
    "data": {
        "total_subscriptions": 1,
        "active_subscriptions": 1,
        "expired_subscriptions": 0,
        "cancelled_subscriptions": 0,
        "premium_users": 1,
        "free_users": 3
    }
}
```

## 📝 已创建/修改的文件

### 新增文件
1. ✅ `services/iap_service.py` - iOS内购验证服务
2. ✅ `services/subscription_checker.py` - 订阅检查服务
3. ✅ `routes/subscription_routes.py` - 订阅API路由
4. ✅ `routes/admin_subscription_routes.py` - 管理后台路由
5. ✅ `migrations/versions/add_subscription_table.py` - 数据库迁移文件

### 修改文件
1. ✅ `models.py` - 添加Subscription模型
2. ✅ `app.py` - 注册订阅路由
3. ✅ `.env.example` - 添加共享密钥配置

### 文档文件
1. ✅ `iOS_IAP_Integration_Guide.md` - iOS集成完整指南
2. ✅ `iOS_IAP_Quick_Setup.md` - 快速配置指南
3. ✅ `Subscription_Expiry_Guide.md` - 到期时间管理指南
4. ✅ `Deploy_Subscription_System.md` - 本文档

## 🔧 可选配置

### 启用自动过期检查（定时任务）

```bash
# 安装APScheduler
pip install apscheduler
```

然后在 `app.py` 中添加：

```python
from services.subscription_checker import init_subscription_checker

# 在create_app函数中
scheduler = init_subscription_checker(app)
```

这将启用每天凌晨2点自动检查过期订阅。

### 手动检查过期订阅

如果不想使用定时任务，可以手动运行：

```python
from app import create_app
from services.subscription_checker import SubscriptionChecker

app = create_app()
with app.app_context():
    SubscriptionChecker.check_expired_subscriptions()
```

或通过API：
```bash
curl -X POST -H "Authorization: Bearer <JWT_TOKEN>" \
  http://192.168.100.173:5000/api/admin/subscription/check-expired
```

## ⚠️ 重要提示

### 1. 沙盒测试
- 沙盒订阅时长被压缩（1年→1小时）
- 测试时订阅会快速过期
- 这是正常现象

### 2. 共享密钥安全
- ✅ 已配置在 `.env` 文件中
- ✅ `.env` 文件已在 `.gitignore` 中
- ❌ 不要提交到Git仓库

### 3. 数据库备份
在运行迁移前，建议备份数据库：
```bash
pg_dump coingpt > backup_$(date +%Y%m%d).sql
```

### 4. 生产环境
- 确保使用生产环境的共享密钥
- 配置HTTPS
- 添加管理员权限验证

## ✅ 部署检查清单

- [ ] 数据库迁移已运行
- [ ] `subscriptions` 表已创建
- [ ] App Store共享密钥已配置
- [ ] 服务器已重启
- [ ] 订阅路由已注册
- [ ] 管理路由已注册
- [ ] 产品列表API可访问
- [ ] 订阅状态API可访问
- [ ] iOS客户端已集成StoreKit
- [ ] 沙盒测试账号已创建
- [ ] 购买流程已测试

## 🎉 完成

现在你的订阅系统已经完整部署，包含：

- ✅ 订阅记录保存
- ✅ 购买时间和过期时间跟踪
- ✅ 订阅状态查询
- ✅ 过期自动检查
- ✅ 管理后台统计
- ✅ 即将过期提醒

开始测试吧！🚀
