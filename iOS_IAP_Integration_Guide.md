# iOS内购集成指南

## 📱 产品配置

### App Store Connect配置

**产品ID**: `dev.zonekit.coingpt.Premium.year`
- **类型**: 自动续期订阅（Auto-Renewable Subscription）
- **订阅期限**: 1年
- **会员等级**: Premium

## 🔧 服务器端配置

### 1. 环境变量配置

在`.env`文件中添加：

```bash
# App Store共享密钥（从App Store Connect获取）
APP_STORE_SHARED_SECRET=your_shared_secret_here
```

**获取共享密钥步骤**：
1. 登录 [App Store Connect](https://appstoreconnect.apple.com/)
2. 进入"我的App" → 选择你的App
3. 点击"App内购买项目"
4. 点击"管理"旁边的"App专用共享密钥"
5. 生成或查看共享密钥
6. 复制密钥到`.env`文件

### 2. 更新iap_service.py

在`services/iap_service.py`中，将共享密钥配置改为从环境变量读取：

```python
import os

# 在verify_receipt方法中
payload = {
    'receipt-data': receipt_data,
    'password': os.getenv('APP_STORE_SHARED_SECRET', ''),  # 从环境变量读取
    'exclude-old-transactions': True
}
```

## 📊 API端点

### 1. 验证收据并激活订阅

```http
POST /api/subscription/verify
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
    "receipt_data": "base64编码的收据数据"
}
```

**成功响应**：
```json
{
    "status": "success",
    "message": "订阅激活成功，会员有效期至 2026-11-11",
    "data": {
        "product_id": "dev.zonekit.coingpt.Premium.year",
        "transaction_id": "1000000123456789",
        "expires_date": "2026-11-11T14:30:00",
        "is_trial_period": false
    }
}
```

**失败响应**：
```json
{
    "status": "error",
    "message": "订阅已过期"
}
```

### 2. 恢复购买

```http
POST /api/subscription/restore
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
    "receipt_data": "base64编码的收据数据"
}
```

**响应格式同上**

### 3. 获取订阅状态

```http
GET /api/subscription/status
Authorization: Bearer <JWT_TOKEN>
```

**响应**：
```json
{
    "status": "success",
    "data": {
        "user_id": 4,
        "membership": "premium",
        "is_premium": true,
        "is_free": false
    }
}
```

### 4. 获取产品列表

```http
GET /api/subscription/products
```

**响应**：
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

## 📱 iOS客户端集成

### 1. 导入StoreKit

```swift
import StoreKit
```

### 2. 请求产品信息

```swift
class IAPManager: NSObject, SKProductsRequestDelegate {
    static let shared = IAPManager()
    
    private let productID = "dev.zonekit.coingpt.Premium.year"
    private var product: SKProduct?
    
    func fetchProducts() {
        let request = SKProductsRequest(productIdentifiers: [productID])
        request.delegate = self
        request.start()
    }
    
    func productsRequest(_ request: SKProductsRequest, didReceive response: SKProductsResponse) {
        if let product = response.products.first {
            self.product = product
            print("产品: \(product.localizedTitle)")
            print("价格: \(product.price) \(product.priceLocale.currencySymbol ?? "")")
        }
    }
}
```

### 3. 购买产品

```swift
extension IAPManager: SKPaymentTransactionObserver {
    func purchaseProduct() {
        guard let product = product else {
            print("产品未加载")
            return
        }
        
        let payment = SKPayment(product: product)
        SKPaymentQueue.default().add(payment)
    }
    
    func paymentQueue(_ queue: SKPaymentQueue, updatedTransactions transactions: [SKPaymentTransaction]) {
        for transaction in transactions {
            switch transaction.transactionState {
            case .purchased:
                print("购买成功")
                verifyReceipt(transaction: transaction)
                SKPaymentQueue.default().finishTransaction(transaction)
                
            case .failed:
                print("购买失败: \(transaction.error?.localizedDescription ?? "")")
                SKPaymentQueue.default().finishTransaction(transaction)
                
            case .restored:
                print("购买已恢复")
                verifyReceipt(transaction: transaction)
                SKPaymentQueue.default().finishTransaction(transaction)
                
            case .purchasing, .deferred:
                print("购买中...")
                
            @unknown default:
                break
            }
        }
    }
}
```

### 4. 获取收据数据

```swift
extension IAPManager {
    func getReceiptData() -> String? {
        guard let receiptURL = Bundle.main.appStoreReceiptURL,
              let receiptData = try? Data(contentsOf: receiptURL) else {
            print("无法获取收据")
            return nil
        }
        
        return receiptData.base64EncodedString()
    }
}
```

### 5. 验证收据

```swift
extension IAPManager {
    func verifyReceipt(transaction: SKPaymentTransaction) {
        guard let receiptData = getReceiptData() else {
            print("无法获取收据数据")
            return
        }
        
        let url = URL(string: "http://192.168.100.173:5000/api/subscription/verify")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "receipt_data": receiptData
        ]
        
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("验证失败: \(error.localizedDescription)")
                return
            }
            
            guard let data = data else {
                print("无响应数据")
                return
            }
            
            do {
                let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
                if let status = json?["status"] as? String, status == "success" {
                    print("订阅激活成功")
                    // 更新UI，显示会员状态
                    DispatchQueue.main.async {
                        self.updateMembershipStatus()
                    }
                } else {
                    let message = json?["message"] as? String ?? "未知错误"
                    print("验证失败: \(message)")
                }
            } catch {
                print("解析响应失败: \(error)")
            }
        }.resume()
    }
}
```

### 6. 恢复购买

```swift
extension IAPManager {
    func restorePurchases() {
        SKPaymentQueue.default().restoreCompletedTransactions()
    }
    
    func paymentQueueRestoreCompletedTransactionsFinished(_ queue: SKPaymentQueue) {
        print("恢复完成")
        
        // 验证收据
        guard let receiptData = getReceiptData() else {
            print("无法获取收据数据")
            return
        }
        
        let url = URL(string: "http://192.168.100.173:5000/api/subscription/restore")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "receipt_data": receiptData
        ]
        
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            // 处理响应...
        }.resume()
    }
}
```

### 7. 初始化

在`AppDelegate`或`App`中：

```swift
// AppDelegate
func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
    // 添加交易观察者
    SKPaymentQueue.default().add(IAPManager.shared)
    
    // 获取产品信息
    IAPManager.shared.fetchProducts()
    
    return true
}

func applicationWillTerminate(_ application: UIApplication) {
    // 移除交易观察者
    SKPaymentQueue.default().remove(IAPManager.shared)
}
```

或在SwiftUI中：

```swift
@main
struct CoinGPTApp: App {
    init() {
        SKPaymentQueue.default().add(IAPManager.shared)
        IAPManager.shared.fetchProducts()
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
```

## 🎨 UI示例

### 订阅页面

```swift
struct SubscriptionView: View {
    @State private var product: SKProduct?
    @State private var isPurchasing = false
    @State private var showAlert = false
    @State private var alertMessage = ""
    
    var body: some View {
        VStack(spacing: 20) {
            Text("升级为Premium会员")
                .font(.largeTitle)
                .fontWeight(.bold)
            
            VStack(alignment: .leading, spacing: 10) {
                FeatureRow(icon: "infinity", text: "无限会话")
                FeatureRow(icon: "message", text: "无限消息")
                FeatureRow(icon: "trash", text: "删除会话")
                FeatureRow(icon: "chart.line.uptrend.xyaxis", text: "高级交易功能")
            }
            .padding()
            
            if let product = product {
                VStack {
                    Text("\(product.price) \(product.priceLocale.currencySymbol ?? "")/年")
                        .font(.title)
                        .fontWeight(.bold)
                    
                    Text("约 \(yearlyPricePerMonth(product)) /月")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
                
                Button(action: {
                    purchaseSubscription()
                }) {
                    if isPurchasing {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                    } else {
                        Text("订阅")
                            .fontWeight(.semibold)
                    }
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.blue)
                .foregroundColor(.white)
                .cornerRadius(10)
                .disabled(isPurchasing)
            }
            
            Button("恢复购买") {
                restorePurchases()
            }
            .foregroundColor(.blue)
            
            Text("订阅将自动续期，可随时取消")
                .font(.caption)
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)
        }
        .padding()
        .alert(isPresented: $showAlert) {
            Alert(title: Text("提示"), message: Text(alertMessage), dismissButton: .default(Text("确定")))
        }
        .onAppear {
            loadProduct()
        }
    }
    
    func loadProduct() {
        // 加载产品信息
        IAPManager.shared.fetchProducts()
    }
    
    func purchaseSubscription() {
        isPurchasing = true
        IAPManager.shared.purchaseProduct()
    }
    
    func restorePurchases() {
        IAPManager.shared.restorePurchases()
    }
    
    func yearlyPricePerMonth(_ product: SKProduct) -> String {
        let monthlyPrice = product.price.doubleValue / 12
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.locale = product.priceLocale
        return formatter.string(from: NSNumber(value: monthlyPrice)) ?? ""
    }
}

struct FeatureRow: View {
    let icon: String
    let text: String
    
    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(.blue)
            Text(text)
        }
    }
}
```

## 🧪 测试

### 沙盒测试

1. **创建沙盒测试账号**：
   - App Store Connect → 用户和访问 → 沙盒测试员
   - 创建新的测试账号

2. **在设备上测试**：
   - 设置 → App Store → 沙盒账户
   - 登录测试账号
   - 运行App并测试购买

3. **验证流程**：
   - 购买产品
   - 查看服务器日志，确认收据验证成功
   - 检查用户会员状态是否更新

### 生产环境测试

1. 使用TestFlight分发
2. 使用真实Apple ID测试
3. 确认收据验证切换到生产环境

## ⚠️ 注意事项

### 1. 收据验证环境

系统会自动检测并切换环境：
- 沙盒收据 → 自动使用沙盒验证URL
- 生产收据 → 自动使用生产验证URL

### 2. 共享密钥安全

- ✅ 存储在`.env`文件（不提交到Git）
- ✅ 使用环境变量
- ❌ 不要硬编码在代码中

### 3. 订阅过期处理

目前系统只在验证时检查过期，建议添加：
- 定时任务检查订阅状态
- 订阅到期前提醒
- 自动降级过期用户

### 4. 错误处理

常见错误码：
- `21000`: JSON格式错误
- `21002`: 收据数据格式错误
- `21003`: 收据无法验证
- `21005`: 服务器不可用
- `21006`: 订阅已过期
- `21007`: 沙盒收据（自动切换）
- `21008`: 生产收据（自动切换）

## 📝 下一步改进

### 1. 添加订阅记录表

```python
class Subscription(db.Model):
    """订阅记录表"""
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    product_id = Column(String(255))
    transaction_id = Column(String(255), unique=True)
    original_transaction_id = Column(String(255))
    purchase_date = Column(DateTime)
    expires_date = Column(DateTime)
    is_trial_period = Column(Boolean, default=False)
    status = Column(String(20), default='active')  # active, expired, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 2. 添加定时任务

```python
from apscheduler.schedulers.background import BackgroundScheduler

def check_expired_subscriptions():
    """检查并处理过期订阅"""
    expired = Subscription.query.filter(
        Subscription.expires_date < datetime.now(),
        Subscription.status == 'active'
    ).all()
    
    for sub in expired:
        sub.status = 'expired'
        sub.user.membership = 'free'
    
    db.session.commit()

# 每天检查一次
scheduler = BackgroundScheduler()
scheduler.add_job(check_expired_subscriptions, 'interval', days=1)
scheduler.start()
```

### 3. 添加Webhook

接收App Store的服务器通知：
- 订阅续期
- 订阅取消
- 退款

## 🎉 完成

现在你的系统已经支持iOS内购了！

**已实现**：
- ✅ 收据验证
- ✅ 订阅激活
- ✅ 恢复购买
- ✅ 订阅状态查询
- ✅ 产品列表

**需要配置**：
- 📝 在`.env`中添加`APP_STORE_SHARED_SECRET`
- 📝 在App Store Connect中配置产品
- 📝 创建沙盒测试账号

**客户端需要**：
- 📱 集成StoreKit
- 📱 实现购买流程
- 📱 实现收据验证
- 📱 实现恢复购买
