# CoinGPT 会员系统概览

## ✅ 当前系统状态

系统**已经有**会员计划的基础架构，但**没有支付功能**。

## 📊 现有功能

### 1. 会员等级

在`User`模型中定义：
```python
membership = Column(String(50), default='free', nullable=False)
```

**支持的会员类型**：
- `free` - 免费用户（默认）
- 其他等级（如`premium`、`vip`等）- 付费会员

### 2. 免费用户限制

#### 会话限制
```python
FREE_USER_LIMITS = {
    'max_sessions': 5,  # 免费用户最多可以创建5个会话
    'max_messages_per_session': 10  # 每个会话最多可以发送10条消息
}
```

#### 功能限制
- ❌ **无法删除会话** - 只有付费会员可以删除会话
- ✅ **可以通过邀请好友获得额外会话次数**

### 3. 邀请奖励系统

```python
dialog_count = Column(Integer, default=0, nullable=False)  # 奖励的会话次数
inviter_id = Column(BigInteger, ForeignKey('users.id'), nullable=True)  # 邀请人ID
```

**工作机制**：
- 用户邀请好友注册
- 邀请人获得额外的`dialog_count`
- 总会话配额 = 基础配额(5) + 奖励次数

### 4. 会员权益对比

| 功能 | 免费用户 | 付费会员 |
|------|---------|---------|
| 会话数量 | 5个（基础）+ 邀请奖励 | 无限制 |
| 每会话消息数 | 10条 | 无限制 |
| 删除会话 | ❌ 不可以 | ✅ 可以 |
| 交易功能 | ✅ 可用 | ✅ 可用 |
| WebSocket推送 | ✅ 可用 | ✅ 可用 |
| API访问 | ✅ 可用 | ✅ 可用 |

## 🔍 相关代码文件

### 1. 数据模型
- `models.py` - User模型，包含`membership`和`dialog_count`字段

### 2. 限制服务
- `services/limit_service.py` - 管理免费用户限制
  - `check_session_limit()` - 检查会话数量限制
  - `check_message_limit()` - 检查消息数量限制
  - `get_user_usage()` - 获取用户使用情况
  - `check_dialog_count()` - 检查剩余会话次数

### 3. 路由
- `routes/auth_routes.py` - 包含会员检查逻辑
  - 创建会话时检查限制
  - 删除会话时检查会员状态

## ❌ 缺失的功能

### 1. 支付系统
- ❌ 没有支付接口（如Stripe、PayPal、支付宝、微信支付）
- ❌ 没有订阅管理
- ❌ 没有订单记录

### 2. 会员管理
- ❌ 没有升级会员的API端点
- ❌ 没有会员到期管理
- ❌ 没有自动续费

### 3. 定价方案
- ❌ 没有定义具体的会员套餐和价格
- ❌ 没有会员等级细分（如月费、年费）

## 🛠️ 如何使用现有系统

### 手动设置用户为付费会员

```python
from models import db, User

# 获取用户
user = User.query.get(user_id)

# 设置为付费会员
user.membership = 'premium'  # 或 'vip'
db.session.commit()

print(f"用户{user.id}已升级为{user.membership}会员")
```

### 检查用户使用情况

```python
from services.limit_service import LimitService

# 获取用户使用统计
usage = LimitService.get_user_usage(user_id)
print(usage)

# 输出示例：
# {
#     "status": "success",
#     "data": {
#         "user_id": 4,
#         "membership": "free",
#         "session_count": 3,
#         "dialog_count": 2,
#         "max_sessions": 7,  # 5(基础) + 2(奖励)
#         "remaining_sessions": 4,
#         "sessions": [...]
#     }
# }
```

### 生成邀请码

```python
from services.limit_service import LimitService

invite_code = LimitService.generate_invite_code(user_id)
print(f"邀请码: {invite_code}")
# 输出: COINGPT-4-1234
```

## 📝 API端点

### 获取用户使用情况
```http
GET /api/auth/usage
Authorization: Bearer <JWT_TOKEN>
```

**响应**：
```json
{
    "status": "success",
    "data": {
        "user_id": 4,
        "membership": "free",
        "session_count": 3,
        "dialog_count": 2,
        "max_sessions": 7,
        "remaining_sessions": 4,
        "sessions": [
            {
                "session_id": 1,
                "message_count": 5,
                "max_messages": 10,
                "remaining_messages": 5
            }
        ]
    }
}
```

### 创建会话（带限制检查）
```http
POST /api/auth/sessions
Authorization: Bearer <JWT_TOKEN>
```

**免费用户超限响应**：
```json
{
    "status": "error",
    "message": "免费用户剩余会话次数已用完，请邀请好友或升级会员",
    "code": "DIALOG_COUNT_LIMIT"
}
```

### 删除会话（仅会员）
```http
DELETE /api/auth/sessions/{session_id}
Authorization: Bearer <JWT_TOKEN>
```

**免费用户响应**：
```json
{
    "status": "error",
    "message": "免费用户无法删除会话，请升级会员",
    "code": "PREMIUM_REQUIRED"
}
```

## 🎯 建议的改进方向

### 1. 添加支付系统

#### 方案A：集成Stripe
```python
# 安装
pip install stripe

# 创建订阅
import stripe
stripe.api_key = "sk_test_..."

# 创建客户
customer = stripe.Customer.create(
    email=user.email,
    metadata={'user_id': user.id}
)

# 创建订阅
subscription = stripe.Subscription.create(
    customer=customer.id,
    items=[{'price': 'price_monthly_premium'}]
)
```

#### 方案B：集成支付宝/微信支付（国内用户）
```python
# 适合中国用户
from alipay import AliPay
from wechatpy.pay import WeChatPay
```

### 2. 定义会员套餐

```python
MEMBERSHIP_PLANS = {
    'free': {
        'name': '免费版',
        'price': 0,
        'max_sessions': 5,
        'max_messages_per_session': 10,
        'can_delete_sessions': False
    },
    'monthly': {
        'name': '月度会员',
        'price': 9.99,  # USD
        'max_sessions': float('inf'),
        'max_messages_per_session': float('inf'),
        'can_delete_sessions': True
    },
    'yearly': {
        'name': '年度会员',
        'price': 99.99,  # USD (节省17%)
        'max_sessions': float('inf'),
        'max_messages_per_session': float('inf'),
        'can_delete_sessions': True,
        'discount': 0.17
    }
}
```

### 3. 添加订阅管理表

```python
class Subscription(db.Model):
    """订阅记录表"""
    __tablename__ = 'subscriptions'
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    plan = Column(String(50), nullable=False)  # 'monthly', 'yearly'
    status = Column(String(20), default='active')  # active, cancelled, expired
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=False)
    stripe_subscription_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="subscriptions")
```

### 4. 添加支付记录表

```python
class Payment(db.Model):
    """支付记录表"""
    __tablename__ = 'payments'
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    subscription_id = Column(BigInteger, ForeignKey('subscriptions.id'))
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default='USD')
    payment_method = Column(String(50))  # stripe, alipay, wechat
    payment_id = Column(String(255))  # 第三方支付ID
    status = Column(String(20), default='pending')  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="payments")
```

### 5. 创建会员管理API

```python
# routes/subscription_routes.py

@subscription_bp.route('/plans', methods=['GET'])
def get_plans():
    """获取所有会员套餐"""
    return jsonify({
        'status': 'success',
        'data': MEMBERSHIP_PLANS
    })

@subscription_bp.route('/subscribe', methods=['POST'])
@token_required
def subscribe():
    """订阅会员"""
    user_id = g.user_id
    plan = request.json.get('plan')
    payment_method = request.json.get('payment_method')
    
    # 创建订阅
    # ...
    
    return jsonify({
        'status': 'success',
        'message': '订阅成功'
    })

@subscription_bp.route('/cancel', methods=['POST'])
@token_required
def cancel_subscription():
    """取消订阅"""
    user_id = g.user_id
    
    # 取消订阅
    # ...
    
    return jsonify({
        'status': 'success',
        'message': '已取消订阅'
    })
```

## 📱 客户端集成建议

### Swift - 显示会员状态

```swift
struct UserProfile {
    let userId: Int
    let membership: String
    let sessionCount: Int
    let maxSessions: Int
    let remainingSessions: Int
    
    var isFree: Bool {
        return membership == "free"
    }
    
    var isPremium: Bool {
        return membership != "free"
    }
}

// 获取用户使用情况
func fetchUserUsage() async throws -> UserProfile {
    let url = URL(string: "\(baseURL)/api/auth/usage")!
    var request = URLRequest(url: url)
    request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
    
    let (data, _) = try await URLSession.shared.data(for: request)
    let response = try JSONDecoder().decode(UsageResponse.self, from: data)
    
    return UserProfile(
        userId: response.data.userId,
        membership: response.data.membership,
        sessionCount: response.data.sessionCount,
        maxSessions: response.data.maxSessions,
        remainingSessions: response.data.remainingSessions
    )
}

// 显示升级提示
func showUpgradePrompt() {
    let alert = UIAlertController(
        title: "升级会员",
        message: "免费用户剩余会话次数已用完，升级会员享受无限制使用",
        preferredStyle: .alert
    )
    
    alert.addAction(UIAlertAction(title: "升级", style: .default) { _ in
        // 跳转到订阅页面
        self.showSubscriptionPage()
    })
    
    alert.addAction(UIAlertAction(title: "邀请好友", style: .default) { _ in
        // 显示邀请码
        self.showInviteCode()
    })
    
    alert.addAction(UIAlertAction(title: "取消", style: .cancel))
    
    present(alert, animated: true)
}
```

## 🎉 总结

### 现状
- ✅ 有会员系统的基础架构
- ✅ 有免费用户限制机制
- ✅ 有邀请奖励系统
- ❌ 没有支付功能
- ❌ 没有订阅管理

### 下一步
1. 选择支付方案（Stripe、支付宝、微信支付）
2. 定义会员套餐和定价
3. 创建订阅和支付数据表
4. 实现支付API
5. 添加订阅管理功能
6. 客户端集成支付界面

如果需要实现完整的支付系统，请告诉我选择哪种支付方式！
