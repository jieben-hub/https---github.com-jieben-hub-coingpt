# 实时行情 API 文档

## 📋 API 接口

### 获取交易对实时行情

```
GET /api/trading/ticker
```

**说明**：获取指定交易对的实时行情数据。

**认证**：需要JWT token

## 🔧 请求参数

### Headers

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| Authorization | string | 是 | Bearer {jwt_token} |

### Query Parameters

| 参数 | 类型 | 必需 | 说明 | 示例 |
|------|------|------|------|------|
| symbol | string | 是 | 交易对符号 | BTCUSDT |
| exchange | string | 否 | 交易所名称 | bybit |

## 📊 响应格式

### 成功响应

```json
{
    "status": "success",
    "data": {
        "symbol": "BTCUSDT",
        "last_price": 106333.5,
        "bid_price": 106333.0,
        "ask_price": 106334.0,
        "high_24h": 107000.0,
        "low_24h": 105000.0,
        "volume_24h": 12345.67,
        "change_24h": 2.5,
        "timestamp": "2025-11-10T09:45:00"
    }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| symbol | string | 交易对符号 |
| last_price | float | 最新成交价 |
| bid_price | float | 买一价 |
| ask_price | float | 卖一价 |
| high_24h | float | 24小时最高价 |
| low_24h | float | 24小时最低价 |
| volume_24h | float | 24小时成交量 |
| change_24h | float | 24小时涨跌幅（%） |
| timestamp | string | 时间戳 |

### 错误响应

```json
{
    "status": "error",
    "message": "缺少必填参数: symbol"
}
```

## 💡 使用场景

### 1. 显示实时价格

```swift
// 获取BTC实时价格
func fetchBTCPrice() async {
    let url = URL(string: "http://192.168.100.173:5000/api/trading/ticker?symbol=BTCUSDT")!
    var request = URLRequest(url: url)
    request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
    
    do {
        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode(TickerResponse.self, from: data)
        
        if response.status == "success" {
            let price = response.data.lastPrice
            print("BTC价格: $\(price)")
            updateUI(price: price)
        }
    } catch {
        print("获取价格失败: \(error)")
    }
}

struct TickerResponse: Codable {
    let status: String
    let data: TickerData
}

struct TickerData: Codable {
    let symbol: String
    let lastPrice: Double
    let bidPrice: Double
    let askPrice: Double
    let high24h: Double
    let low24h: Double
    let volume24h: Double
    let change24h: Double
    let timestamp: String
    
    enum CodingKeys: String, CodingKey {
        case symbol
        case lastPrice = "last_price"
        case bidPrice = "bid_price"
        case askPrice = "ask_price"
        case high24h = "high_24h"
        case low24h = "low_24h"
        case volume24h = "volume_24h"
        case change24h = "change_24h"
        case timestamp
    }
}
```

### 2. 价格监控

```swift
class PriceMonitor: ObservableObject {
    @Published var currentPrice: Double = 0
    @Published var priceChange: Double = 0
    
    private var timer: Timer?
    
    func startMonitoring(symbol: String) {
        // 每5秒更新一次价格
        timer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { _ in
            Task {
                await self.fetchPrice(symbol: symbol)
            }
        }
    }
    
    func stopMonitoring() {
        timer?.invalidate()
        timer = nil
    }
    
    func fetchPrice(symbol: String) async {
        // 调用API获取价格
        let ticker = await fetchTicker(symbol: symbol)
        
        DispatchQueue.main.async {
            self.currentPrice = ticker.lastPrice
            self.priceChange = ticker.change24h
        }
    }
}
```

### 3. 下单前获取价格

```swift
func placeMarketOrder(symbol: String, side: String, amount: Double) async {
    // 1. 先获取当前价格
    let ticker = await fetchTicker(symbol: symbol)
    let currentPrice = ticker.lastPrice
    
    // 2. 计算数量
    let quantity = amount / currentPrice
    
    // 3. 下单
    let order = [
        "symbol": symbol,
        "side": side,
        "quantity_type": "usdt",
        "amount": amount,
        "order_type": "market"
    ]
    
    // 发送下单请求...
}
```

### 4. 价格提醒

```swift
class PriceAlert {
    var targetPrice: Double
    var isAbove: Bool  // true=突破提醒, false=跌破提醒
    
    func checkAlert(currentPrice: Double) -> Bool {
        if isAbove {
            return currentPrice >= targetPrice
        } else {
            return currentPrice <= targetPrice
        }
    }
}

// 使用
let alert = PriceAlert(targetPrice: 110000, isAbove: true)

// 定期检查
let ticker = await fetchTicker(symbol: "BTCUSDT")
if alert.checkAlert(currentPrice: ticker.lastPrice) {
    showNotification("BTC突破 $110,000!")
}
```

## 🎨 UI 设计建议

### 价格显示卡片

```swift
struct PriceCard: View {
    let ticker: TickerData
    
    var priceColor: Color {
        ticker.change24h >= 0 ? .green : .red
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(ticker.symbol)
                    .font(.headline)
                Spacer()
                Text("\(ticker.change24h, specifier: "%.2f")%")
                    .foregroundColor(priceColor)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(priceColor.opacity(0.1))
                    .cornerRadius(4)
            }
            
            HStack(alignment: .bottom) {
                Text("$\(ticker.lastPrice, specifier: "%.2f")")
                    .font(.system(size: 32, weight: .bold))
                    .foregroundColor(priceColor)
                Spacer()
            }
            
            HStack {
                VStack(alignment: .leading) {
                    Text("24H高")
                        .font(.caption)
                        .foregroundColor(.gray)
                    Text("$\(ticker.high24h, specifier: "%.2f")")
                        .font(.subheadline)
                }
                
                Spacer()
                
                VStack(alignment: .leading) {
                    Text("24H低")
                        .font(.caption)
                        .foregroundColor(.gray)
                    Text("$\(ticker.low24h, specifier: "%.2f")")
                        .font(.subheadline)
                }
                
                Spacer()
                
                VStack(alignment: .leading) {
                    Text("24H量")
                        .font(.caption)
                        .foregroundColor(.gray)
                    Text("\(ticker.volume24h, specifier: "%.0f")")
                        .font(.subheadline)
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
}
```

### 价格趋势指示器

```swift
struct PriceTrendIndicator: View {
    let change: Double
    
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: change >= 0 ? "arrow.up.right" : "arrow.down.right")
            Text("\(abs(change), specifier: "%.2f")%")
        }
        .foregroundColor(change >= 0 ? .green : .red)
        .font(.caption)
        .padding(.horizontal, 6)
        .padding(.vertical, 3)
        .background((change >= 0 ? Color.green : Color.red).opacity(0.1))
        .cornerRadius(4)
    }
}
```

## 🧪 测试示例

### cURL 测试

```bash
# 获取BTC行情
curl -X GET "http://192.168.100.173:5000/api/trading/ticker?symbol=BTCUSDT" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 获取ETH行情
curl -X GET "http://192.168.100.173:5000/api/trading/ticker?symbol=ETHUSDT" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Python 测试

```python
import requests

url = "http://192.168.100.173:5000/api/trading/ticker"
headers = {
    "Authorization": f"Bearer {jwt_token}"
}
params = {
    "symbol": "BTCUSDT"
}

response = requests.get(url, headers=headers, params=params)
data = response.json()

if data['status'] == 'success':
    ticker = data['data']
    print(f"Symbol: {ticker['symbol']}")
    print(f"Price: ${ticker['last_price']}")
    print(f"24h Change: {ticker['change_24h']}%")
    print(f"24h High: ${ticker['high_24h']}")
    print(f"24h Low: ${ticker['low_24h']}")
```

### JavaScript 测试

```javascript
async function fetchTicker(symbol) {
    const response = await fetch(
        `http://192.168.100.173:5000/api/trading/ticker?symbol=${symbol}`,
        {
            headers: {
                'Authorization': `Bearer ${jwtToken}`
            }
        }
    );
    
    const data = await response.json();
    
    if (data.status === 'success') {
        console.log('Price:', data.data.last_price);
        console.log('Change:', data.data.change_24h + '%');
    }
}

fetchTicker('BTCUSDT');
```

## 📝 批量获取行情

如果需要获取多个交易对的行情，可以并发请求：

```swift
func fetchMultipleTickers(symbols: [String]) async -> [String: TickerData] {
    var tickers: [String: TickerData] = [:]
    
    await withTaskGroup(of: (String, TickerData?).self) { group in
        for symbol in symbols {
            group.addTask {
                let ticker = await self.fetchTicker(symbol: symbol)
                return (symbol, ticker)
            }
        }
        
        for await (symbol, ticker) in group {
            if let ticker = ticker {
                tickers[symbol] = ticker
            }
        }
    }
    
    return tickers
}

// 使用
let symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT"]
let tickers = await fetchMultipleTickers(symbols: symbols)

for (symbol, ticker) in tickers {
    print("\(symbol): $\(ticker.lastPrice)")
}
```

## ⚠️ 注意事项

### 1. 请求频率

- 建议间隔至少1秒
- 避免频繁请求同一交易对
- 使用WebSocket获取实时推送更高效

### 2. 数据实时性

- 数据来自交易所API
- 可能有1-2秒延迟
- 关键交易建议使用WebSocket

### 3. 错误处理

```swift
func fetchTicker(symbol: String) async throws -> TickerData {
    // 添加重试逻辑
    var retryCount = 0
    let maxRetries = 3
    
    while retryCount < maxRetries {
        do {
            let ticker = try await fetchTickerOnce(symbol: symbol)
            return ticker
        } catch {
            retryCount += 1
            if retryCount >= maxRetries {
                throw error
            }
            try await Task.sleep(nanoseconds: 1_000_000_000) // 等待1秒
        }
    }
    
    throw NSError(domain: "TickerError", code: -1)
}
```

### 4. 缓存策略

```swift
class TickerCache {
    private var cache: [String: (ticker: TickerData, timestamp: Date)] = [:]
    private let cacheTimeout: TimeInterval = 5.0  // 5秒缓存
    
    func get(symbol: String) -> TickerData? {
        guard let cached = cache[symbol] else { return nil }
        
        let age = Date().timeIntervalSince(cached.timestamp)
        if age < cacheTimeout {
            return cached.ticker
        }
        
        cache.removeValue(forKey: symbol)
        return nil
    }
    
    func set(symbol: String, ticker: TickerData) {
        cache[symbol] = (ticker, Date())
    }
}
```

## ✅ 总结

**API接口**：`GET /api/trading/ticker`

**认证**：需要JWT token

**参数**：
- `symbol`（必需）- 交易对符号
- `exchange`（可选）- 交易所名称

**返回数据**：
- 最新价格
- 买卖价
- 24小时高低价
- 24小时成交量
- 24小时涨跌幅

**使用场景**：
- 实时价格显示
- 价格监控
- 下单前价格查询
- 价格提醒

**建议**：
- 合理控制请求频率
- 使用缓存减少请求
- 关键场景使用WebSocket

现在可以获取任意交易对的实时行情了！🎉
