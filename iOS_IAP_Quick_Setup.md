# iOS内购快速配置指南

## ✅ 已完成的工作

### 1. 服务器端代码
- ✅ `services/iap_service.py` - iOS内购验证服务
- ✅ `routes/subscription_routes.py` - 订阅管理API
- ✅ `app.py` - 已注册订阅路由

### 2. API端点
- ✅ `POST /api/subscription/verify` - 验证收据并激活订阅
- ✅ `POST /api/subscription/restore` - 恢复购买
- ✅ `GET /api/subscription/status` - 获取订阅状态
- ✅ `GET /api/subscription/products` - 获取产品列表

### 3. 产品配置
- ✅ 产品ID: `dev.zonekit.coingpt.Premium.year`
- ✅ 类型: 年度订阅
- ✅ 会员等级: Premium

## 🔧 需要配置的内容

### 1. 获取App Store共享密钥

**步骤**：
1. 登录 [App Store Connect](https://appstoreconnect.apple.com/)
2. 进入"我的App" → 选择 CoinGPT
3. 点击"App内购买项目"
4. 点击"管理"旁边的"App专用共享密钥"
5. 如果没有，点击"生成"
6. 复制生成的密钥（格式类似：`a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`）

### 2. 配置环境变量

在 `.env` 文件中添加：

```bash
# iOS内购配置
APP_STORE_SHARED_SECRET=你的共享密钥
```

**示例**：
```bash
APP_STORE_SHARED_SECRET=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

### 3. 重启服务器

```bash
python run.py
```

## 📱 iOS客户端集成清单

### 必需步骤

- [ ] 在App Store Connect中配置产品 `dev.zonekit.coingpt.Premium.year`
- [ ] 创建沙盒测试账号
- [ ] 在Xcode中启用In-App Purchase能力
- [ ] 集成StoreKit框架
- [ ] 实现购买流程
- [ ] 实现收据验证（调用服务器API）
- [ ] 实现恢复购买
- [ ] 添加订阅页面UI

### 代码集成

参考完整代码：`iOS_IAP_Integration_Guide.md`

**核心流程**：
```swift
// 1. 初始化
SKPaymentQueue.default().add(IAPManager.shared)

// 2. 购买
IAPManager.shared.purchaseProduct()

// 3. 获取收据
let receiptData = getReceiptData()

// 4. 验证收据
POST /api/subscription/verify
{
    "receipt_data": receiptData
}

// 5. 更新UI
if response.status == "success" {
    // 显示Premium会员状态
}
```

## 🧪 测试流程

### 1. 沙盒测试

```
1. 在App Store Connect创建沙盒测试账号
2. 在iOS设备上：设置 → App Store → 沙盒账户
3. 登录测试账号
4. 运行App
5. 点击购买
6. 使用沙盒账号完成支付（不会真实扣费）
7. 查看服务器日志
```

**预期日志**：
```
验证用户4的收据，环境: 沙盒
收据验证成功，产品: dev.zonekit.coingpt.Premium.year, 过期时间: 2026-11-11
用户4订阅已激活: free -> premium
```

### 2. 验证会员状态

```http
GET /api/subscription/status
Authorization: Bearer <JWT_TOKEN>
```

**响应**：
```json
{
    "status": "success",
    "data": {
        "membership": "premium",
        "is_premium": true
    }
}
```

### 3. 测试会员权益

- ✅ 创建超过5个会话（免费用户限制）
- ✅ 发送超过10条消息（免费用户限制）
- ✅ 删除会话（免费用户不可用）

## 📊 API使用示例

### Swift代码

```swift
class SubscriptionManager {
    let baseURL = "http://192.168.100.173:5000"
    var jwtToken: String = ""
    
    // 验证收据
    func verifyReceipt(receiptData: String) async throws -> Bool {
        let url = URL(string: "\(baseURL)/api/subscription/verify")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = ["receipt_data": receiptData]
        request.httpBody = try JSONEncoder().encode(body)
        
        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode(VerifyResponse.self, from: data)
        
        return response.status == "success"
    }
    
    // 获取订阅状态
    func getSubscriptionStatus() async throws -> SubscriptionStatus {
        let url = URL(string: "\(baseURL)/api/subscription/status")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
        
        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode(StatusResponse.self, from: data)
        
        return response.data
    }
    
    // 恢复购买
    func restorePurchases(receiptData: String) async throws -> Bool {
        let url = URL(string: "\(baseURL)/api/subscription/restore")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = ["receipt_data": receiptData]
        request.httpBody = try JSONEncoder().encode(body)
        
        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode(VerifyResponse.self, from: data)
        
        return response.status == "success"
    }
}

// 数据模型
struct VerifyResponse: Codable {
    let status: String
    let message: String
    let data: VerifyData?
}

struct VerifyData: Codable {
    let productId: String
    let transactionId: String
    let expiresDate: String
    let isTrialPeriod: Bool
    
    enum CodingKeys: String, CodingKey {
        case productId = "product_id"
        case transactionId = "transaction_id"
        case expiresDate = "expires_date"
        case isTrialPeriod = "is_trial_period"
    }
}

struct StatusResponse: Codable {
    let status: String
    let data: SubscriptionStatus
}

struct SubscriptionStatus: Codable {
    let userId: Int
    let membership: String
    let isPremium: Bool
    let isFree: Bool
    
    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case membership
        case isPremium = "is_premium"
        case isFree = "is_free"
    }
}
```

## ⚠️ 常见问题

### 1. 收据验证失败

**问题**: `"message": "收据无法验证"`

**解决**:
- 检查共享密钥是否正确配置
- 确认使用的是正确的环境（沙盒/生产）
- 检查收据数据是否完整

### 2. 订阅已过期

**问题**: `"message": "订阅已过期"`

**解决**:
- 沙盒订阅有效期很短（几分钟到几小时）
- 重新购买测试
- 生产环境订阅才是真实的1年

### 3. 共享密钥未配置

**问题**: 验证请求返回错误

**解决**:
```bash
# 在.env中添加
APP_STORE_SHARED_SECRET=你的密钥
```

### 4. 产品ID不匹配

**问题**: `"message": "未知的产品ID"`

**解决**:
- 确认App Store Connect中的产品ID
- 更新`services/iap_service.py`中的`PRODUCT_IDS`配置

## 📝 下一步

### 立即可做

1. ✅ 配置共享密钥
2. ✅ 重启服务器
3. ✅ 测试API端点

### iOS开发需要

1. 📱 集成StoreKit
2. 📱 实现购买流程
3. 📱 设计订阅页面
4. 📱 测试沙盒购买

### 可选改进

1. 📊 添加订阅记录表（保存历史）
2. ⏰ 添加定时任务（检查过期）
3. 🔔 添加Webhook（接收App Store通知）
4. 📈 添加订阅统计（收入分析）

## 🎉 完成检查

- [x] 创建IAP验证服务
- [x] 创建订阅API路由
- [x] 注册路由到Flask应用
- [x] 配置产品ID
- [x] 添加环境变量配置
- [ ] 配置App Store共享密钥 ⬅️ **你需要做的**
- [ ] iOS客户端集成 ⬅️ **你需要做的**
- [ ] 沙盒测试 ⬅️ **你需要做的**

## 📚 相关文档

- `iOS_IAP_Integration_Guide.md` - 完整集成指南（包含详细代码）
- `Membership_System_Overview.md` - 会员系统概览
- `.env.example` - 环境变量配置示例

## 🚀 启动服务器

```bash
# 1. 配置.env
nano .env  # 或使用你喜欢的编辑器
# 添加: APP_STORE_SHARED_SECRET=你的密钥

# 2. 重启服务器
python run.py

# 3. 验证路由已注册
# 查看日志，应该看到：
# subscription.verify_receipt: /api/subscription/verify [POST]
# subscription.restore_purchases: /api/subscription/restore [POST]
# subscription.get_subscription_status: /api/subscription/status [GET]
# subscription.get_products: /api/subscription/products [GET]
```

现在你的服务器已经准备好接收iOS内购验证请求了！🎊
