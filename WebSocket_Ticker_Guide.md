# WebSocket 实时行情推送指南

## 🎯 功能说明

通过WebSocket订阅交易对的实时行情，服务器每2秒推送一次价格更新（仅在价格变化时推送）。

## 📋 WebSocket事件

### 1. 订阅行情

**事件名**：`subscribe_ticker`

**发送数据**：
```json
{
    "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
}
```

**服务器响应**：
```json
{
    "user_id": 4,
    "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
    "status": "success"
}
```

### 2. 取消订阅

**事件名**：`unsubscribe_ticker`

**发送数据**：
```json
{
    "symbols": ["BTCUSDT"]
}
```

**服务器响应**：
```json
{
    "user_id": 4,
    "symbols": ["BTCUSDT"],
    "status": "success"
}
```

### 3. 接收行情更新

**事件名**：`ticker_update`

**推送数据**：
```json
{
    "type": "ticker_update",
    "symbol": "BTCUSDT",
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
    },
    "timestamp": "2025-11-10T09:45:00",
    "user_id": 4
}
```

## 📱 Swift客户端实现

### 完整示例

```swift
import SocketIO

class TickerWebSocketManager: ObservableObject {
    @Published var tickers: [String: TickerData] = [:]
    @Published var isConnected = false
    
    private var manager: SocketManager?
    private var socket: SocketIOClient?
    
    let serverURL = "http://192.168.100.173:5000"
    let jwtToken: String
    
    init(jwtToken: String) {
        self.jwtToken = jwtToken
        setupSocket()
    }
    
    // MARK: - Socket配置
    private func setupSocket() {
        guard let url = URL(string: serverURL) else { return }
        
        manager = SocketManager(
            socketURL: url,
            config: [
                .log(true),
                .forceWebsockets(true),
                .reconnects(true),
                .auth(["token": jwtToken]),
                .extraHeaders(["Authorization": "Bearer \(jwtToken)"])
            ]
        )
        
        socket = manager?.defaultSocket
        setupEventHandlers()
    }
    
    // MARK: - 事件处理
    private func setupEventHandlers() {
        guard let socket = socket else { return }
        
        // 连接成功
        socket.on(clientEvent: .connect) { data, ack in
            print("✅ WebSocket已连接")
            self.isConnected = true
        }
        
        // 连接确认
        socket.on("connected") { data, ack in
            print("📨 收到连接确认: \(data)")
        }
        
        // 行情订阅确认
        socket.on("ticker_subscribed") { data, ack in
            print("✅ 行情订阅成功: \(data)")
        }
        
        // 接收行情更新
        socket.on("ticker_update") { data, ack in
            self.handleTickerUpdate(data: data)
        }
        
        // 断开连接
        socket.on(clientEvent: .disconnect) { data, ack in
            print("❌ WebSocket已断开")
            self.isConnected = false
        }
        
        // 错误处理
        socket.on("error") { data, ack in
            print("❌ 错误: \(data)")
        }
    }
    
    // MARK: - 连接管理
    func connect() {
        socket?.connect()
    }
    
    func disconnect() {
        socket?.disconnect()
    }
    
    // MARK: - 行情订阅
    func subscribeTicker(symbols: [String]) {
        guard isConnected else {
            print("⚠️ 未连接，无法订阅")
            return
        }
        
        socket?.emit("subscribe_ticker", ["symbols": symbols])
        print("📊 订阅行情: \(symbols)")
    }
    
    func unsubscribeTicker(symbols: [String]) {
        socket?.emit("unsubscribe_ticker", ["symbols": symbols])
        print("📊 取消订阅行情: \(symbols)")
    }
    
    // MARK: - 数据处理
    private func handleTickerUpdate(data: [Any]) {
        guard let json = data.first as? [String: Any],
              let symbol = json["symbol"] as? String,
              let tickerData = json["data"] as? [String: Any] else {
            return
        }
        
        // 解析行情数据
        let ticker = TickerData(
            symbol: symbol,
            lastPrice: tickerData["last_price"] as? Double ?? 0,
            bidPrice: tickerData["bid_price"] as? Double ?? 0,
            askPrice: tickerData["ask_price"] as? Double ?? 0,
            high24h: tickerData["high_24h"] as? Double ?? 0,
            low24h: tickerData["low_24h"] as? Double ?? 0,
            volume24h: tickerData["volume_24h"] as? Double ?? 0,
            change24h: tickerData["change_24h"] as? Double ?? 0,
            timestamp: tickerData["timestamp"] as? String ?? ""
        )
        
        DispatchQueue.main.async {
            self.tickers[symbol] = ticker
            print("📊 \(symbol) 价格更新: $\(ticker.lastPrice)")
        }
    }
}

// MARK: - 数据模型
struct TickerData {
    let symbol: String
    let lastPrice: Double
    let bidPrice: Double
    let askPrice: Double
    let high24h: Double
    let low24h: Double
    let volume24h: Double
    let change24h: Double
    let timestamp: String
}
```

### SwiftUI视图示例

```swift
struct TickerView: View {
    @StateObject private var wsManager: TickerWebSocketManager
    
    let symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT"]
    
    init(jwtToken: String) {
        _wsManager = StateObject(wrappedValue: TickerWebSocketManager(jwtToken: jwtToken))
    }
    
    var body: some View {
        VStack {
            // 连接状态
            HStack {
                Circle()
                    .fill(wsManager.isConnected ? Color.green : Color.red)
                    .frame(width: 10, height: 10)
                Text(wsManager.isConnected ? "已连接" : "未连接")
                    .foregroundColor(.gray)
            }
            .padding()
            
            // 行情列表
            List(symbols, id: \.self) { symbol in
                if let ticker = wsManager.tickers[symbol] {
                    TickerRow(ticker: ticker)
                } else {
                    Text(symbol)
                        .foregroundColor(.gray)
                }
            }
        }
        .onAppear {
            wsManager.connect()
            
            // 等待连接后订阅
            DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
                wsManager.subscribeTicker(symbols: symbols)
            }
        }
        .onDisappear {
            wsManager.unsubscribeTicker(symbols: symbols)
            wsManager.disconnect()
        }
    }
}

struct TickerRow: View {
    let ticker: TickerData
    
    var priceColor: Color {
        ticker.change24h >= 0 ? .green : .red
    }
    
    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text(ticker.symbol)
                    .font(.headline)
                Text("24H: \(ticker.change24h, specifier: "%.2f")%")
                    .font(.caption)
                    .foregroundColor(priceColor)
            }
            
            Spacer()
            
            VStack(alignment: .trailing) {
                Text("$\(ticker.lastPrice, specifier: "%.2f")")
                    .font(.title3)
                    .fontWeight(.bold)
                    .foregroundColor(priceColor)
                Text("Vol: \(ticker.volume24h, specifier: "%.0f")")
                    .font(.caption)
                    .foregroundColor(.gray)
            }
        }
        .padding(.vertical, 4)
    }
}
```

## 🔄 完整流程

### 1. 连接WebSocket
```swift
let wsManager = TickerWebSocketManager(jwtToken: jwtToken)
wsManager.connect()
```

### 2. 订阅行情
```swift
// 连接成功后订阅
socket.on("connected") { data, ack in
    wsManager.subscribeTicker(symbols: ["BTCUSDT", "ETHUSDT"])
}
```

### 3. 接收实时更新
```swift
// 每2秒自动推送（价格变化时）
socket.on("ticker_update") { data, ack in
    // 处理行情数据
    handleTickerUpdate(data: data)
}
```

### 4. 取消订阅
```swift
wsManager.unsubscribeTicker(symbols: ["BTCUSDT"])
```

## ⚙️ 推送机制

### 推送频率
- **检查间隔**：每2秒检查一次
- **推送条件**：价格变化 或 超过5秒未推送
- **优化**：只推送有变化的数据

### 推送逻辑
```python
# 服务器端
if last_price != cached_price or time.time() - last_update > 5:
    # 推送更新
    emit('ticker_update', ticker_data)
```

## 📊 服务器日志

### 订阅时
```
📊 收到行情订阅请求: {'symbols': ['BTCUSDT', 'ETHUSDT']}
👤 用户ID: 4, 请求订阅行情: ['BTCUSDT', 'ETHUSDT']
🚪 客户端加入房间: ticker_BTCUSDT_4
🚪 客户端加入房间: ticker_ETHUSDT_4
📊 用户4订阅BTCUSDT行情
   当前订阅BTCUSDT的用户: 1
📊 用户4订阅ETHUSDT行情
   当前订阅ETHUSDT的用户: 1
✅ 行情订阅成功 - 用户4订阅了: ['BTCUSDT', 'ETHUSDT']
```

### 推送时
```
📊 推送BTCUSDT行情给用户4
   价格: 106333.5
   房间: ticker_BTCUSDT_4
```

## 💡 使用建议

### 1. 订阅管理
```swift
// ✅ 推荐：只订阅当前需要的交易对
wsManager.subscribeTicker(symbols: ["BTCUSDT"])

// ❌ 不推荐：订阅过多交易对
wsManager.subscribeTicker(symbols: allSymbols) // 100+个
```

### 2. 内存管理
```swift
// 离开页面时取消订阅
.onDisappear {
    wsManager.unsubscribeTicker(symbols: symbols)
}
```

### 3. 错误处理
```swift
socket.on("error") { data, ack in
    if let error = data.first as? [String: Any],
       let message = error["message"] as? String {
        print("错误: \(message)")
        // 重新订阅或提示用户
    }
}
```

### 4. 重连处理
```swift
socket.on(clientEvent: .reconnect) { data, ack in
    print("重新连接成功")
    // 重新订阅
    wsManager.subscribeTicker(symbols: symbols)
}
```

## ⚠️ 注意事项

### 1. 认证要求
- 必须先连接WebSocket并认证
- 使用JWT token认证
- 认证失败无法订阅

### 2. 订阅限制
- 建议每个用户订阅不超过20个交易对
- 过多订阅会增加服务器负担
- 按需订阅，及时取消

### 3. 数据实时性
- 推送间隔：2秒
- 价格变化时立即推送
- 最大延迟：2秒

### 4. 网络断开
- 自动重连
- 重连后需要重新订阅
- 监听reconnect事件

## ✅ 总结

**WebSocket行情推送**：
- ✅ 实时推送（2秒间隔）
- ✅ 多交易对支持
- ✅ 价格变化检测
- ✅ 自动优化推送

**使用流程**：
1. 连接WebSocket
2. 订阅交易对
3. 接收实时更新
4. 取消订阅

**优势**：
- 比HTTP轮询更高效
- 实时性更好
- 服务器资源占用少
- 支持多交易对

现在可以通过WebSocket接收实时行情推送了！🎉
