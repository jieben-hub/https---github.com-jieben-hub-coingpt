# 下单数量类型说明

## 📋 两种下单方式

系统支持两种下单方式：

### 1. 按币种数量下单（默认）
指定要买卖的币种数量，例如：0.001 BTC

### 2. 按USDT金额下单
指定要花费的USDT金额，系统自动计算币种数量

## 🔧 API参数说明

### 通用参数
```json
{
    "symbol": "BTCUSDT",
    "side": "buy",
    "order_type": "market",
    "position_side": "long",
    "leverage": 10,
    "quantity_type": "coin"  // ⚠️ 关键参数
}
```

### quantity_type 参数

| 值 | 说明 | 必需参数 |
|----|------|---------|
| `"coin"` | 按币种数量（默认） | `quantity` |
| `"usdt"` | 按USDT金额 | `amount` |

## 📊 使用示例

### 方式1：按币种数量下单

```json
POST /api/trading/order
{
    "symbol": "BTCUSDT",
    "side": "buy",
    "quantity_type": "coin",  // 或者不传，默认就是coin
    "quantity": 0.001,  // 买0.001个BTC
    "order_type": "market",
    "position_side": "long",
    "leverage": 10
}
```

**说明**：
- 直接指定币种数量
- 适合精确控制持仓数量
- 不需要计算

### 方式2：按USDT金额下单

```json
POST /api/trading/order
{
    "symbol": "BTCUSDT",
    "side": "buy",
    "quantity_type": "usdt",  // ⚠️ 设置为usdt
    "amount": 1000,  // 花1000 USDT
    "order_type": "market",
    "position_side": "long",
    "leverage": 10
}
```

**说明**：
- 指定USDT金额
- 系统自动计算币种数量
- 适合按资金比例下单

## 🔍 计算逻辑

### 市价单（按USDT金额）

```
1. 获取当前市场价格
2. 计算币种数量 = USDT金额 / 当前价格
3. 下单

示例：
- USDT金额: 1000
- BTC当前价格: 106000
- 计算数量: 1000 / 106000 = 0.00943396 BTC
- 实际下单: 0.00943396 BTC
```

### 限价单（按USDT金额）

```
1. 使用指定的限价
2. 计算币种数量 = USDT金额 / 限价
3. 下单

示例：
- USDT金额: 1000
- 限价: 105000
- 计算数量: 1000 / 105000 = 0.00952381 BTC
- 实际下单: 0.00952381 BTC @ 105000
```

## 📱 App端集成

### Swift示例

```swift
// 方式1：按币种数量
let orderParams1: [String: Any] = [
    "symbol": "BTCUSDT",
    "side": "buy",
    "quantity_type": "coin",
    "quantity": 0.001,
    "order_type": "market",
    "position_side": "long",
    "leverage": 10
]

// 方式2：按USDT金额
let orderParams2: [String: Any] = [
    "symbol": "BTCUSDT",
    "side": "buy",
    "quantity_type": "usdt",
    "amount": 1000,  // 花1000 USDT
    "order_type": "market",
    "position_side": "long",
    "leverage": 10
]

// 发送请求
let url = URL(string: "http://192.168.100.173:5000/api/trading/order")!
var request = URLRequest(url: url)
request.httpMethod = "POST"
request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
request.setValue("application/json", forHTTPHeaderField: "Content-Type")
request.httpBody = try? JSONSerialization.data(withJSONObject: orderParams2)

// 发送请求...
```

### UI设计建议

```swift
// 下单界面
struct OrderView: View {
    @State private var quantityType: QuantityType = .coin
    @State private var coinQuantity: Double = 0.001
    @State private var usdtAmount: Double = 1000
    
    enum QuantityType: String, CaseIterable {
        case coin = "币种数量"
        case usdt = "USDT金额"
    }
    
    var body: some View {
        VStack {
            // 数量类型选择
            Picker("下单方式", selection: $quantityType) {
                ForEach(QuantityType.allCases, id: \.self) { type in
                    Text(type.rawValue).tag(type)
                }
            }
            .pickerStyle(SegmentedPickerStyle())
            
            // 根据类型显示不同输入框
            if quantityType == .coin {
                TextField("币种数量", value: $coinQuantity, format: .number)
                    .keyboardType(.decimalPad)
                Text("约 \(coinQuantity * currentPrice) USDT")
                    .foregroundColor(.gray)
            } else {
                TextField("USDT金额", value: $usdtAmount, format: .number)
                    .keyboardType(.decimalPad)
                Text("约 \(usdtAmount / currentPrice) BTC")
                    .foregroundColor(.gray)
            }
            
            // 下单按钮
            Button("下单") {
                placeOrder()
            }
        }
    }
    
    func placeOrder() {
        var params: [String: Any] = [
            "symbol": "BTCUSDT",
            "side": "buy",
            "order_type": "market",
            "position_side": "long",
            "leverage": 10
        ]
        
        if quantityType == .coin {
            params["quantity_type"] = "coin"
            params["quantity"] = coinQuantity
        } else {
            params["quantity_type"] = "usdt"
            params["amount"] = usdtAmount
        }
        
        // 发送请求...
    }
}
```

## ⚠️ 注意事项

### 1. 最小下单量

不同交易对有不同的最小下单量限制：

```
BTCUSDT: 最小 0.001 BTC
ETHUSDT: 最小 0.01 ETH
```

按USDT金额下单时，确保计算出的币种数量满足最小限制。

### 2. 价格精度

计算出的数量会保留足够的精度：

```python
# 服务器端会自动处理精度
quantity = amount / price
# 例如：1000 / 106333.5 = 0.009404396...
```

### 3. 滑点影响

市价单按USDT金额下单时：
- 获取的是当前价格
- 实际成交价可能略有不同
- 最终成交数量可能略有偏差

### 4. 限价单

限价单按USDT金额下单：
- 使用指定的限价计算数量
- 只有在该价格成交时才会执行
- 计算更精确

## 🧪 测试示例

### 测试1：按币种数量（市价单）
```bash
curl -X POST http://192.168.100.173:5000/api/trading/order \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "side": "buy",
    "quantity_type": "coin",
    "quantity": 0.001,
    "order_type": "market",
    "position_side": "long",
    "leverage": 10
  }'
```

### 测试2：按USDT金额（市价单）
```bash
curl -X POST http://192.168.100.173:5000/api/trading/order \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "side": "buy",
    "quantity_type": "usdt",
    "amount": 1000,
    "order_type": "market",
    "position_side": "long",
    "leverage": 10
  }'
```

### 测试3：按USDT金额（限价单）
```bash
curl -X POST http://192.168.100.173:5000/api/trading/order \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "side": "buy",
    "quantity_type": "usdt",
    "amount": 1000,
    "order_type": "limit",
    "price": 105000,
    "position_side": "long",
    "leverage": 10
  }'
```

## 📊 服务器日志

### 按币种数量
```
INFO - 创建订单: BTCUSDT buy 0.001
```

### 按USDT金额
```
INFO - 按USDT金额下单: 1000 USDT / 106333.5 = 0.009404396 BTCUSDT
INFO - 创建订单: BTCUSDT buy 0.009404396
```

## ✅ 总结

**两种下单方式**：
1. ✅ 按币种数量（`quantity_type="coin"`）
   - 直接指定币种数量
   - 适合精确控制
   
2. ✅ 按USDT金额（`quantity_type="usdt"`）
   - 指定USDT金额
   - 自动计算币种数量
   - 适合按资金比例

**默认行为**：
- 如果不指定 `quantity_type`，默认为 `"coin"`
- 保持向后兼容

**建议**：
- 新手用户：推荐按USDT金额
- 专业用户：可以按币种数量
- App可以提供两种选项让用户选择

现在可以支持两种下单方式了！🎉
