# 订阅到期时间管理指南

## ✅ 已添加的功能

### 1. 订阅记录表（Subscription）

新增了完整的订阅记录表，包含以下字段：

```python
class Subscription(db.Model):
    """订阅记录表"""
    id                          # 主键
    user_id                     # 用户ID
    product_id                  # 产品ID（如：dev.zonekit.coingpt.Premium.year）
    product_type                # 产品类型（yearly, monthly）
    transaction_id              # App Store交易ID（唯一）
    original_transaction_id     # 原始交易ID
    purchase_date               # 购买时间 ✅
    expires_date                # 过期时间 ✅
    status                      # 状态（active, expired, cancelled）
    is_trial_period             # 是否试用期
    is_in_intro_offer_period    # 是否优惠期
    auto_renew_status           # 是否自动续期
    created_at                  # 创建时间
    updated_at                  # 更新时间
```

### 2. 订阅管理功能

#### 自动保存订阅记录
购买成功后，系统会自动：
- ✅ 保存订阅记录到数据库
- ✅ 记录购买时间和过期时间
- ✅ 更新用户会员状态

#### 订阅状态查询
```python
# 检查订阅是否有效
subscription.is_active()  # 返回 True/False

# 距离过期还有多少天
subscription.days_until_expiry()  # 返回天数
```

### 3. 过期检查服务

创建了 `SubscriptionChecker` 服务：

```python
# 检查并处理过期订阅
SubscriptionChecker.check_expired_subscriptions()

# 获取即将过期的订阅
SubscriptionChecker.get_expiring_soon_subscriptions(days=7)

# 获取订阅统计
SubscriptionChecker.get_subscription_stats()
```

## 📊 API端点

### 1. 用户端 - 查看订阅状态

```http
GET /api/subscription/status
Authorization: Bearer <JWT_TOKEN>
```

**响应（包含到期时间）**：
```json
{
    "status": "success",
    "data": {
        "user_id": 4,
        "membership": "premium",
        "is_premium": true,
        "is_free": false,
        "subscription": {
            "product_id": "dev.zonekit.coingpt.Premium.year",
            "product_type": "yearly",
            "purchase_date": "2024-11-11T14:30:00",
            "expires_date": "2025-11-11T14:30:00",
            "days_until_expiry": 365,
            "is_active": true,
            "is_trial_period": false,
            "auto_renew_status": true
        }
    }
}
```

### 2. 管理端 - 订阅统计

```http
GET /api/admin/subscription/stats
Authorization: Bearer <JWT_TOKEN>
```

**响应**：
```json
{
    "status": "success",
    "data": {
        "total_subscriptions": 100,
        "active_subscriptions": 80,
        "expired_subscriptions": 15,
        "cancelled_subscriptions": 5,
        "premium_users": 80,
        "free_users": 200
    }
}
```

### 3. 管理端 - 即将过期订阅

```http
GET /api/admin/subscription/expiring-soon?days=7
Authorization: Bearer <JWT_TOKEN>
```

**响应**：
```json
{
    "status": "success",
    "data": [
        {
            "user_id": 4,
            "username": "user@example.com",
            "email": "user@example.com",
            "product_id": "dev.zonekit.coingpt.Premium.year",
            "product_type": "yearly",
            "purchase_date": "2024-11-04T14:30:00",
            "expires_date": "2025-11-04T14:30:00",
            "days_until_expiry": 7
        }
    ]
}
```

### 4. 管理端 - 手动检查过期订阅

```http
POST /api/admin/subscription/check-expired
Authorization: Bearer <JWT_TOKEN>
```

**响应**：
```json
{
    "status": "success",
    "message": "过期订阅检查完成"
}
```

### 5. 管理端 - 查看用户订阅历史

```http
GET /api/admin/subscription/user/{user_id}
Authorization: Bearer <JWT_TOKEN>
```

**响应**：
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

## 🔄 完整购买流程（含到期时间）

### 1. iOS端购买
```swift
// 购买成功后
case .purchased:
    verifyReceipt(transaction: transaction)
```

### 2. 服务器验证并保存
```python
# 1. 验证收据
success, message, subscription_info = IAPService.verify_receipt(receipt_data, user_id)

# subscription_info 包含：
{
    'product_id': 'dev.zonekit.coingpt.Premium.year',
    'transaction_id': '1000000123456789',
    'original_transaction_id': '1000000123456789',
    'purchase_date': datetime(2024, 11, 11, 14, 30, 0),
    'expires_date': datetime(2025, 11, 11, 14, 30, 0),  # ✅ 到期时间
    'is_trial_period': False,
    'is_in_intro_offer_period': False
}

# 2. 保存订阅记录
new_subscription = Subscription(
    user_id=user_id,
    product_id=subscription_info['product_id'],
    product_type='yearly',
    transaction_id=subscription_info['transaction_id'],
    original_transaction_id=subscription_info['original_transaction_id'],
    purchase_date=subscription_info['purchase_date'],
    expires_date=subscription_info['expires_date'],  # ✅ 保存到期时间
    status='active',
    is_trial_period=subscription_info['is_trial_period']
)
db.session.add(new_subscription)

# 3. 更新用户会员状态
user.membership = 'premium'
db.session.commit()
```

### 3. 返回给客户端
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

## ⏰ 过期处理机制

### 自动检查（可选）

如果安装了 `apscheduler`：

```bash
pip install apscheduler
```

系统会自动：
- ✅ 每天凌晨2点检查过期订阅
- ✅ 将过期订阅标记为 `expired`
- ✅ 将用户降级为 `free`

### 手动检查

```python
from services.subscription_checker import SubscriptionChecker

# 在Flask应用上下文中
with app.app_context():
    SubscriptionChecker.check_expired_subscriptions()
```

或通过API：
```bash
curl -X POST http://192.168.100.173:5000/api/admin/subscription/check-expired \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### 过期流程

```
1. 定时任务触发（每天凌晨2点）
2. 查询所有 status='active' 且 expires_date < now() 的订阅
3. 对于每个过期订阅：
   a. 更新 subscription.status = 'expired'
   b. 检查用户是否有其他有效订阅
   c. 如果没有，降级 user.membership = 'free'
4. 提交数据库更改
```

## 📱 iOS端显示到期时间

### Swift代码示例

```swift
struct SubscriptionView: View {
    @State private var subscription: SubscriptionInfo?
    
    var body: some View {
        VStack {
            if let sub = subscription {
                if sub.isPremium {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Premium会员")
                            .font(.title)
                            .fontWeight(.bold)
                        
                        HStack {
                            Image(systemName: "calendar")
                            Text("购买日期: \(formatDate(sub.purchaseDate))")
                        }
                        
                        HStack {
                            Image(systemName: "clock")
                            Text("到期时间: \(formatDate(sub.expiresDate))")
                        }
                        
                        HStack {
                            Image(systemName: "hourglass")
                            Text("剩余天数: \(sub.daysUntilExpiry)天")
                                .foregroundColor(sub.daysUntilExpiry < 7 ? .red : .green)
                        }
                        
                        if sub.autoRenewStatus {
                            HStack {
                                Image(systemName: "arrow.clockwise")
                                Text("自动续期已开启")
                                    .foregroundColor(.green)
                            }
                        } else {
                            HStack {
                                Image(systemName: "exclamationmark.triangle")
                                Text("自动续期已关闭")
                                    .foregroundColor(.orange)
                            }
                        }
                    }
                    .padding()
                    .background(Color.blue.opacity(0.1))
                    .cornerRadius(10)
                } else {
                    Text("免费用户")
                    Button("升级为Premium") {
                        // 跳转到订阅页面
                    }
                }
            }
        }
        .onAppear {
            fetchSubscriptionStatus()
        }
    }
    
    func fetchSubscriptionStatus() async {
        // 调用API获取订阅状态
        let url = URL(string: "http://192.168.100.173:5000/api/subscription/status")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
        
        do {
            let (data, _) = try await URLSession.shared.data(for: request)
            let response = try JSONDecoder().decode(SubscriptionResponse.self, from: data)
            
            if let subData = response.data.subscription {
                subscription = SubscriptionInfo(
                    isPremium: response.data.isPremium,
                    purchaseDate: subData.purchaseDate,
                    expiresDate: subData.expiresDate,
                    daysUntilExpiry: subData.daysUntilExpiry,
                    autoRenewStatus: subData.autoRenewStatus
                )
            }
        } catch {
            print("获取订阅状态失败: \(error)")
        }
    }
    
    func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        if let date = formatter.date(from: dateString) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateStyle = .medium
            displayFormatter.timeStyle = .none
            return displayFormatter.string(from: date)
        }
        return dateString
    }
}

struct SubscriptionInfo {
    let isPremium: Bool
    let purchaseDate: String
    let expiresDate: String
    let daysUntilExpiry: Int
    let autoRenewStatus: Bool
}
```

## 🗄️ 数据库迁移

### 创建订阅表

```bash
# 1. 生成迁移文件（已创建）
# migrations/versions/add_subscription_table.py

# 2. 运行迁移
flask db upgrade

# 或使用Python
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 迁移文件内容

```python
def upgrade():
    op.create_table('subscriptions',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('product_id', sa.String(255), nullable=False),
        sa.Column('product_type', sa.String(50), nullable=False),
        sa.Column('transaction_id', sa.String(255), nullable=False),
        sa.Column('original_transaction_id', sa.String(255), nullable=False),
        sa.Column('purchase_date', sa.DateTime(), nullable=False),
        sa.Column('expires_date', sa.DateTime(), nullable=False),  # ✅ 到期时间字段
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('is_trial_period', sa.Boolean()),
        sa.Column('is_in_intro_offer_period', sa.Boolean()),
        sa.Column('auto_renew_status', sa.Boolean()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_id')
    )
```

## 📝 使用示例

### Python后端

```python
from models import Subscription, User
from datetime import datetime

# 查询用户的有效订阅
active_sub = Subscription.query.filter_by(
    user_id=4,
    status='active'
).first()

if active_sub:
    print(f"产品: {active_sub.product_id}")
    print(f"购买时间: {active_sub.purchase_date}")
    print(f"过期时间: {active_sub.expires_date}")
    print(f"剩余天数: {active_sub.days_until_expiry()}")
    print(f"是否有效: {active_sub.is_active()}")
```

### Swift客户端

```swift
// 获取订阅状态
let manager = SubscriptionManager()
let status = try await manager.getSubscriptionStatus()

if let sub = status.subscription {
    print("过期时间: \(sub.expiresDate)")
    print("剩余天数: \(sub.daysUntilExpiry)")
}
```

## ⚠️ 注意事项

### 1. 沙盒环境订阅时长

沙盒环境的订阅时长会被压缩：
- 1年订阅 → 1小时
- 1个月订阅 → 5分钟

所以测试时会很快过期，这是正常的。

### 2. 时区处理

所有时间都使用UTC时间存储：
```python
datetime.utcnow()  # 使用UTC时间
```

客户端显示时需要转换为本地时间。

### 3. 自动续期

- `auto_renew_status` 字段记录用户是否开启自动续期
- 需要通过App Store Server Notifications接收续期通知
- 建议实现Webhook接收续期事件

## 🎉 总结

现在系统已经完整支持订阅到期时间管理：

- ✅ 保存购买时间和过期时间
- ✅ 查询订阅状态和剩余天数
- ✅ 自动检查和处理过期订阅
- ✅ 管理后台查看订阅统计
- ✅ 即将过期提醒
- ✅ 订阅历史记录

所有功能已就绪，运行数据库迁移后即可使用！
