# 币种列表 API 文档

## 📋 API 接口

### 获取币种列表

```
GET /api/trading/symbols
```

**说明**：获取所有可交易的币种列表，支持返回基础币种或交易对。

**特点**：
- ✅ 无需认证（公开接口）
- ✅ 数据来自缓存，响应快速
- ✅ 支持多种返回格式

## 🔧 请求参数

### Query Parameters

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| type | string | 否 | "all" | 返回类型 |

### type 参数值

| 值 | 说明 | 返回内容 |
|----|------|---------|
| `"base"` | 基础币种 | 只返回币种符号（如BTC, ETH） |
| `"pairs"` | 交易对 | 只返回交易对（如BTCUSDT, ETHUSDT） |
| `"all"` | 全部 | 返回基础币种和交易对 |

## 📊 响应格式

### 1. 只获取交易对

**请求**：
```bash
GET /api/trading/symbols?type=pairs
```

**响应**：
```json
{
    "status": "success",
    "data": {
        "symbols": [
            "BTCUSDT",
            "ETHUSDT",
            "SOLUSDT",
            "DOGEUSDT",
            "XRPUSDT",
            "ADAUSDT",
            "AVAXUSDT",
            "DOTUSDT",
            "MATICUSDT",
            "LINKUSDT",
            ...
        ],
        "count": 1604
    }
}
```


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

### 1. App启动时加载币种列表

```swift
func loadSymbols() async {
    let url = URL(string: "http://192.168.100.173:5000/api/trading/symbols?type=base")!
    
    do {
        let (data, _) = try await URLSession.shared.data(from: url)
        let response = try JSONDecoder().decode(SymbolsResponse.self, from: data)
        
        if response.status == "success" {
            self.availableSymbols = response.data.symbols
            print("加载了 \(response.data.count) 个币种")
        }
    } catch {
        print("加载币种失败: \(error)")
    }
}

struct SymbolsResponse: Codable {
    let status: String
    let data: SymbolsData
}

struct SymbolsData: Codable {
    let symbols: [String]
    let count: Int
}
```

### 2. 搜索/筛选币种

```swift
struct CoinPickerView: View {
    @State private var allCoins: [String] = []
    @State private var searchText = ""
    
    var filteredCoins: [String] {
        if searchText.isEmpty {
            return allCoins
        }
        return allCoins.filter { $0.contains(searchText.uppercased()) }
    }
    
    var body: some View {
        VStack {
            SearchBar(text: $searchText, placeholder: "搜索币种")
            
            List(filteredCoins, id: \.self) { coin in
                Button(action: {
                    selectCoin(coin)
                }) {
                    HStack {
                        Text(coin)
                            .font(.headline)
                        Spacer()
                        Text("\(coin)USDT")
                            .foregroundColor(.gray)
                    }
                }
            }
        }
        .onAppear {
            loadSymbols()
        }
    }
    
    func loadSymbols() {
        // 调用API加载币种
    }
}
```

### 3. 验证币种是否支持

```swift
func isSymbolSupported(_ symbol: String) -> Bool {
    return availableSymbols.contains(symbol.uppercased())
}

// 使用
if isSymbolSupported("BTC") {
    // 可以交易
} else {
    // 不支持该币种
}
```

### 4. 热门币种推荐

```swift
let popularCoins = ["BTC", "ETH", "SOL", "DOGE", "XRP"]

func getPopularCoins() -> [String] {
    return allCoins.filter { popularCoins.contains($0) }
}
```

## 🧪 测试示例

### cURL 测试

```bash
# 获取所有信息
curl http://192.168.100.173:5000/api/trading/symbols

# 只获取基础币种
curl http://192.168.100.173:5000/api/trading/symbols?type=base

# 只获取交易对
curl http://192.168.100.173:5000/api/trading/symbols?type=pairs
```

### Python 测试

```python
import requests

# 获取基础币种
response = requests.get('http://192.168.100.173:5000/api/trading/symbols?type=base')
data = response.json()

if data['status'] == 'success':
    symbols = data['data']['symbols']
    print(f"共有 {len(symbols)} 个币种")
    print("前10个:", symbols[:10])
```

### JavaScript 测试

```javascript
// 获取交易对
fetch('http://192.168.100.173:5000/api/trading/symbols?type=pairs')
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log(`共有 ${data.data.count} 个交易对`);
            console.log('前10个:', data.data.symbols.slice(0, 10));
        }
    });
```

## 📝 数据来源

### Bybit交易所

数据来自Bybit交易所的线性合约（USDT永续合约）：

- **基础币种**：441个
- **交易对**：1604个
- **更新频率**：应用启动时从缓存加载，缓存每24小时更新一次

### 缓存机制

```python
# 缓存文件位置
cache/bybit_symbols.json

# 缓存内容
{
    "base_symbols": ["BTC", "ETH", ...],
    "trading_pairs": ["BTCUSDT", "ETHUSDT", ...],
    "timestamp": "2025-11-10T09:00:00"
}
```

## 🎯 UI设计建议

### 币种选择器

```
┌─────────────────────────────┐
│  🔍 搜索币种                │
├─────────────────────────────┤
│  热门                       │
│  ⭐ BTC    Bitcoin          │
│  ⭐ ETH    Ethereum         │
│  ⭐ SOL    Solana           │
├─────────────────────────────┤
│  全部 (441)                 │
│  📊 ADA    Cardano          │
│  📊 AVAX   Avalanche        │
│  📊 BNB    Binance Coin     │
│  📊 DOT    Polkadot         │
│  ...                        │
└─────────────────────────────┘
```

### 分类显示

```swift
struct CoinListView: View {
    @State private var coins: [String] = []
    @State private var category: CoinCategory = .popular
    
    enum CoinCategory: String, CaseIterable {
        case popular = "热门"
        case all = "全部"
        case defi = "DeFi"
        case layer1 = "Layer1"
    }
    
    var body: some View {
        VStack {
            Picker("分类", selection: $category) {
                ForEach(CoinCategory.allCases, id: \.self) { cat in
                    Text(cat.rawValue).tag(cat)
                }
            }
            .pickerStyle(SegmentedPickerStyle())
            
            List(filteredCoins, id: \.self) { coin in
                CoinRow(coin: coin)
            }
        }
    }
}
```

## ⚠️ 注意事项

### 1. 数据实时性

- 币种列表来自缓存
- 不是实时数据
- 如需最新数据，可以重启应用

### 2. 交易对格式

- 所有交易对都是USDT结算
- 格式：`{币种}USDT`
- 例如：BTCUSDT, ETHUSDT

### 3. 币种可用性

- 列表中的币种不一定都可以交易
- 某些币种可能暂停交易
- 下单前建议先获取ticker确认

### 4. 性能优化

```swift
// ✅ 推荐：App启动时加载一次
func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
    loadSymbols()
    return true
}

// ❌ 不推荐：每次需要时都请求
func showCoinPicker() {
    loadSymbols()  // 不要这样做
}
```

## ✅ 总结

**API接口**：`GET /api/trading/symbols`

**特点**：
- ✅ 无需认证
- ✅ 快速响应（缓存）
- ✅ 支持多种格式

**返回类型**：
- `type=base` - 基础币种（441个）
- `type=pairs` - 交易对（1604个）
- `type=all` - 全部信息

**使用场景**：
- App启动时加载
- 币种选择器
- 搜索/筛选
- 验证支持

现在可以获取所有支持的币种列表了！🎉
