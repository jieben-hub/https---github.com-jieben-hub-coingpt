# CoinGPT Swift WebSocket 集成指南

## 🚀 快速开始

### 1. 安装依赖

在Xcode中添加Socket.IO Swift包：
```
File → Add Package Dependencies
https://github.com/socketio/socket.io-client-swift
```

或在Package.swift中添加：
```swift
dependencies: [
    .package(url: "https://github.com/socketio/socket.io-client-swift", from: "16.0.0")
]
```

### 2. 基础集成

```swift
import SocketIO

class TradingWebSocketManager: ObservableObject {
    private var socket: SocketIOClient?
    @Published var balance: Double = 0.0
    @Published var positions: [Position] = []
    
    init() {
        let manager = SocketManager(
            socketURL: URL(string: "http://192.168.100.173:5000")!
        )
        socket = manager.defaultSocket
        setupEvents()
    }
    
    func connect() {
        socket?.connect()
    }
    
    private func setupEvents() {
        socket?.on("balance_update") { [weak self] data, ack in
            // 处理余额更新
            if let balanceData = data.first as? [String: Any],
               let balance = balanceData["available"] as? Double {
                DispatchQueue.main.async {
                    self?.balance = balance
                }
            }
        }
    }
}
```

### 3. 订阅交易数据

```swift
func subscribeToTradingData(userId: Int) {
    socket?.emit("subscribe_trading", [
        "user_id": userId,
        "types": ["balance", "positions", "pnl", "orders"]
    ])
}
```

## 📊 WebSocket事件映射

### 服务器端API → WebSocket事件对应关系

| HTTP API | 轮询频率 | WebSocket事件 | 优先级 | 说明 |
|----------|----------|---------------|--------|------|
| `/api/trading/positions` | 3-5秒 | `positions_update` | 🔥 高 | 持仓数据，价格波动实时反映 |
| `/api/trading/pnl` | 3-5秒 | `pnl_update` | 🔥 高 | 盈亏数据，用户最关心 |
| `/api/trading/balance` | 5-10秒 | `balance_update` | 🔥 高 | 余额数据，交易后立即更新 |
| `/api/trading/orders` | 10-15秒 | `orders_update` | 🟡 中 | 挂单数据，订单状态变化 |

### Swift中的事件监听
```swift
// 对应服务器端的4个主要WebSocket事件
socket?.on("balance_update") { data, ack in
    // 处理余额更新 - 替代 /api/trading/balance 轮询
}

socket?.on("positions_update") { data, ack in  
    // 处理持仓更新 - 替代 /api/trading/positions 轮询
}

socket?.on("pnl_update") { data, ack in
    // 处理盈亏更新 - 替代 /api/trading/pnl 轮询  
}

socket?.on("orders_update") { data, ack in
    // 处理订单更新 - 替代 /api/trading/orders 轮询
}
```

## 📊 数据结构

### 余额更新
```swift
// 接收到的数据格式
{
    "type": "balance_update",
    "data": {
        "coin": "USDT",
        "available": 1000.50,
        "total": 1200.00,
        "equity": 1150.75
    },
    "timestamp": "2025-11-10T07:29:00.000Z"
}
```

### 持仓更新 (`positions_update`)
```swift
// 接收到的数据格式 - 对应 /api/trading/positions
{
    "type": "positions_update", 
    "data": [
        {
            "symbol": "BTCUSDT",
            "side": "Buy", 
            "size": 0.1,
            "entry_price": 50000.00,
            "mark_price": 50500.00,
            "unrealized_pnl": 50.00,
            "leverage": 10
        }
    ],
    "timestamp": "2025-11-10T07:33:00.000Z",
    "user_id": 4
}
```

### 盈亏更新 (`pnl_update`)
```swift
// 接收到的数据格式 - 对应 /api/trading/pnl
{
    "type": "pnl_update",
    "data": {
        "total_unrealized_pnl": 125.50,
        "position_count": 2,
        "positions": [
            {
                "symbol": "BTCUSDT",
                "side": "Buy",
                "size": 0.1,
                "unrealized_pnl": 75.50,
                "entry_price": 50000.00,
                "mark_price": 50755.00
            }
        ]
    },
    "timestamp": "2025-11-10T07:33:00.000Z",
    "user_id": 4
}
```

### 订单更新 (`orders_update`)
```swift
// 接收到的数据格式 - 对应 /api/trading/orders
{
    "type": "orders_update",
    "data": [
        {
            "order_id": "12345",
            "symbol": "BTCUSDT", 
            "side": "Buy",
            "type": "Limit",
            "quantity": 0.1,
            "price": 49000.00,
            "status": "PartiallyFilled",
            "filled_quantity": 0.05
        }
    ],
    "timestamp": "2025-11-10T07:33:00.000Z",
    "user_id": 4
}
```

## 🎯 实施步骤

### 阶段1: 基础连接 (1-2天)
1. 集成Socket.IO库
2. 建立WebSocket连接
3. 处理连接状态

### 阶段2: 数据订阅 (2-3天)
1. 实现数据订阅功能
2. 处理实时数据更新
3. 更新UI显示

### 阶段3: 错误处理 (1-2天)
1. 添加重连机制
2. 处理网络异常
3. 回退到HTTP轮询

### 阶段4: 优化 (1-2天)
1. 数据缓存和去重
2. 性能优化
3. 用户体验改进

## 🔧 关键配置

### WebSocket连接配置
```swift
let config: SocketIOClientConfiguration = [
    .log(true),                    // 开启日志
    .compress,                     // 启用压缩
    .reconnects(true),             // 自动重连
    .reconnectAttempts(5),         // 重连次数
    .reconnectWait(2),             // 重连间隔
    .forceWebsockets(true)         // 强制使用WebSocket
]
```

### 错误处理
```swift
socket?.on(clientEvent: .error) { data, ack in
    print("WebSocket错误: \(data)")
    // 回退到HTTP API
    self.fallbackToHTTPPolling()
}
```

## 📱 UI集成示例

### SwiftUI
```swift
struct TradingView: View {
    @StateObject private var wsManager = TradingWebSocketManager()
    
    var body: some View {
        VStack {
            Text("余额: \(wsManager.balance, specifier: "%.2f")")
            
            List(wsManager.positions, id: \.symbol) { position in
                PositionRow(position: position)
            }
        }
        .onAppear {
            wsManager.connect()
        }
    }
}
```

### UIKit
```swift
class TradingViewController: UIViewController {
    private let wsManager = TradingWebSocketManager()
    @IBOutlet weak var balanceLabel: UILabel!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        wsManager.$balance
            .receive(on: DispatchQueue.main)
            .sink { [weak self] balance in
                self?.balanceLabel.text = "余额: \(balance)"
            }
            .store(in: &cancellables)
        
        wsManager.connect()
    }
}
```

## ⚡ 性能优化建议

### 1. 数据去重
```swift
private var lastBalanceUpdate: Date?

func handleBalanceUpdate(_ data: [String: Any]) {
    let now = Date()
    guard lastBalanceUpdate == nil || 
          now.timeIntervalSince(lastBalanceUpdate!) > 1.0 else {
        return // 1秒内不重复处理
    }
    lastBalanceUpdate = now
    // 处理更新...
}
```

### 2. 批量更新UI
```swift
private var pendingUpdates: [String: Any] = [:]
private var updateTimer: Timer?

func scheduleUIUpdate() {
    updateTimer?.invalidate()
    updateTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: false) { _ in
        DispatchQueue.main.async {
            self.applyPendingUpdates()
        }
    }
}
```

### 3. 内存管理
```swift
deinit {
    socket?.disconnect()
    updateTimer?.invalidate()
}
```

## 🛠️ 调试技巧

### 1. 启用详细日志
```swift
let manager = SocketManager(socketURL: url, config: [.log(true)])
```

### 2. 监控连接状态
```swift
socket?.on(clientEvent: .statusChange) { data, ack in
    print("连接状态变化: \(data)")
}
```

### 3. 数据验证
```swift
func validateData(_ data: [String: Any]) -> Bool {
    guard data["type"] != nil,
          data["data"] != nil,
          data["timestamp"] != nil else {
        print("❌ 数据格式无效: \(data)")
        return false
    }
    return true
}
```

## 🔄 回退机制

当WebSocket连接失败时，自动回退到HTTP轮询：

```swift
private func fallbackToHTTPPolling() {
    guard !isUsingHTTPFallback else { return }
    
    isUsingHTTPFallback = true
    startHTTPPolling()
}

private func startHTTPPolling() {
    Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { _ in
        self.fetchDataViaHTTP()
    }
}
```

## 📈 监控指标

跟踪以下指标来优化性能：
- 连接成功率
- 重连频率  
- 数据延迟
- 内存使用
- 电池消耗

这个完整的Swift集成方案可以让你的iOS应用实现实时交易数据推送，大幅提升用户体验！
