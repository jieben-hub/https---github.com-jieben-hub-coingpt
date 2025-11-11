# App端WebSocket集成指南

## 📱 iOS/Swift 集成

### 1️⃣ 安装依赖

在 `Podfile` 中添加：
```ruby
pod 'Socket.IO-Client-Swift', '~> 16.0.1'
```

### 2️⃣ 必需的配置字段

⚠️ **重要：服务器端认证参数要求**
服务器从 `auth` 参数中读取 `token` 字段：
```python
# 服务器端代码
if auth and 'token' in auth:
    token = auth['token']
```

```swift
struct WebSocketConfig {
    let serverURL: String          // WebSocket服务器地址
    let jwtToken: String           // JWT认证令牌（必需！）
    let subscribeTypes: [String]   // 订阅的数据类型
}

// 示例配置
let config = WebSocketConfig(
    serverURL: "http://192.168.100.173:5000",
    jwtToken: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0IiwiaWF0IjoxNzYyNzIxMjA3LCJleHAiOjE3NjMzMjYwMDd9.taqUsvsF4wEh44yOlZG-n5E94jQtdoVHB4l7PLmGEuk",
    subscribeTypes: ["balance", "positions", "pnl", "orders"]
)

// ⚠️ 注意：userId 不需要传递，服务器会从 token 中解析
```

### 3️⃣ WebSocket管理器实现

```swift
import Foundation
import SocketIO
import Combine

class TradingWebSocketManager: ObservableObject {
    // MARK: - 配置
    private let serverURL: String
    private let jwtToken: String
    private let userId: Int
    
    // MARK: - Socket
    private var manager: SocketManager?
    private var socket: SocketIOClient?
    
    // MARK: - 状态
    @Published var isConnected: Bool = false
    @Published var connectionError: String?
    
    // MARK: - 交易数据
    @Published var balance: BalanceData?
    @Published var positions: [PositionData] = []
    @Published var pnlData: PnlData?
    @Published var orders: [OrderData] = []
    
    // MARK: - 初始化
    init(serverURL: String, jwtToken: String) {
        self.serverURL = serverURL
        self.jwtToken = jwtToken
        self.userId = 0  // 将从服务器响应中获取
        setupSocket()
    }
    
    // MARK: - Socket配置
    private func setupSocket() {
        guard let url = URL(string: serverURL) else {
            connectionError = "无效的服务器地址"
            return
        }
        
        // ⚠️ 关键配置：传递JWT token
        // 服务器支持两种方式：
        // 1. Socket.IO的auth参数（推荐）
        // 2. HTTP Authorization Header（备用）
        
        manager = SocketManager(
            socketURL: url,
            config: [
                .log(true),                                    // 开启日志
                .compress,                                     // 启用压缩
                .forceWebsockets(true),                       // 强制使用WebSocket
                .reconnects(true),                            // 自动重连
                .reconnectAttempts(5),                        // 重连次数
                .reconnectWait(2),                            // 重连等待时间
                
                // 方式1: 使用auth参数（推荐）
                .auth(["token": jwtToken]),                   // ⚠️ 推荐方式
                
                // 方式2: 使用HTTP Header（备用）
                .extraHeaders(["Authorization": "Bearer \(jwtToken)"])  // 备用方式
            ]
        )
        
        socket = manager?.defaultSocket
        setupEventHandlers()
    }
    
    // MARK: - 事件处理
    private func setupEventHandlers() {
        guard let socket = socket else { return }
        
        // 连接成功
        socket.on(clientEvent: .connect) { [weak self] data, ack in
            print("✅ WebSocket已连接")
            self?.isConnected = true
            self?.connectionError = nil
        }
        
        // 连接失败
        socket.on(clientEvent: .error) { [weak self] data, ack in
            print("❌ WebSocket错误: \(data)")
            self?.connectionError = "连接错误"
        }
        
        // 连接断开
        socket.on(clientEvent: .disconnect) { [weak self] data, ack in
            print("🔌 WebSocket已断开")
            self?.isConnected = false
        }
        
        // 服务器连接确认
        socket.on("connected") { [weak self] data, ack in
            guard let self = self else { return }
            print("📨 收到连接确认: \(data)")
            
            // 从服务器响应中获取用户ID
            if let responseData = data.first as? [String: Any],
               let userId = responseData["user_id"] as? Int {
                self.userId = userId
                print("👤 用户ID: \(userId)")
            }
            
            // 自动订阅交易数据
            self.subscribeTrading(types: ["balance", "positions", "pnl", "orders"])
        }
        
        // 订阅确认
        socket.on("subscribed") { data, ack in
            print("✅ 订阅成功: \(data)")
        }
        
        // 错误消息
        socket.on("error") { [weak self] data, ack in
            if let errorData = data.first as? [String: Any],
               let message = errorData["message"] as? String {
                print("❌ 服务器错误: \(message)")
                self?.connectionError = message
            }
        }
        
        // 余额更新
        socket.on("balance_update") { [weak self] data, ack in
            self?.handleBalanceUpdate(data: data)
        }
        
        // 持仓更新
        socket.on("positions_update") { [weak self] data, ack in
            self?.handlePositionsUpdate(data: data)
        }
        
        // 盈亏更新
        socket.on("pnl_update") { [weak self] data, ack in
            self?.handlePnlUpdate(data: data)
        }
        
        // 订单更新
        socket.on("orders_update") { [weak self] data, ack in
            self?.handleOrdersUpdate(data: data)
        }
    }
    
    // MARK: - 连接控制
    func connect() {
        socket?.connect()
    }
    
    func disconnect() {
        socket?.disconnect()
    }
    
    // MARK: - 订阅管理
    func subscribeTrading(types: [String]) {
        guard isConnected else {
            print("⚠️ 未连接，无法订阅")
            return
        }
        
        // 服务器支持两种字段名：types 或 subscribeTypes
        socket?.emit("subscribe_trading", [
            "types": types  // 推荐使用 types
            // 或者使用 "subscribeTypes": types  // 也支持
        ])
    }
    
    func unsubscribeTrading(types: [String]) {
        socket?.emit("unsubscribe_trading", [
            "types": types  // 推荐使用 types
        ])
    }
    
    // MARK: - 数据处理
    private func handleBalanceUpdate(data: [Any]) {
        guard let json = data.first as? [String: Any],
              let balanceData = json["data"] as? [String: Any] else {
            return
        }
        
        // 解析余额数据
        DispatchQueue.main.async {
            // 更新UI
            print("💰 收到余额更新: \(balanceData)")
        }
    }
    
    private func handlePositionsUpdate(data: [Any]) {
        guard let json = data.first as? [String: Any],
              let positionsData = json["data"] as? [[String: Any]] else {
            return
        }
        
        DispatchQueue.main.async {
            print("📊 收到持仓更新: \(positionsData.count)个持仓")
        }
    }
    
    private func handlePnlUpdate(data: [Any]) {
        guard let json = data.first as? [String: Any],
              let pnlData = json["data"] as? [String: Any] else {
            return
        }
        
        DispatchQueue.main.async {
            print("📈 收到盈亏更新: \(pnlData)")
        }
    }
    
    private func handleOrdersUpdate(data: [Any]) {
        guard let json = data.first as? [String: Any],
              let ordersData = json["data"] as? [[String: Any]] else {
            return
        }
        
        DispatchQueue.main.async {
            print("📋 收到订单更新: \(ordersData.count)个订单")
        }
    }
}
```

### 4️⃣ 在SwiftUI中使用

```swift
import SwiftUI

struct TradingView: View {
    @StateObject private var wsManager: TradingWebSocketManager
    
    init(jwtToken: String, userId: Int) {
        _wsManager = StateObject(wrappedValue: TradingWebSocketManager(
            serverURL: "http://192.168.100.173:5000",
            jwtToken: jwtToken,
            userId: userId
        ))
    }
    
    var body: some View {
        VStack {
            // 连接状态
            HStack {
                Circle()
                    .fill(wsManager.isConnected ? Color.green : Color.red)
                    .frame(width: 10, height: 10)
                Text(wsManager.isConnected ? "已连接" : "未连接")
            }
            
            // 余额显示
            if let balance = wsManager.balance {
                Text("余额: \(balance.total)")
            }
            
            // 持仓列表
            List(wsManager.positions) { position in
                PositionRow(position: position)
            }
        }
        .onAppear {
            wsManager.connect()
        }
        .onDisappear {
            wsManager.disconnect()
        }
    }
}
```

### 5️⃣ 获取JWT Token

在登录成功后保存JWT token：

```swift
class AuthManager {
    static let shared = AuthManager()
    
    private let tokenKey = "jwt_token"
    private let userIdKey = "user_id"
    
    // 保存登录信息
    func saveLoginInfo(token: String, userId: Int) {
        UserDefaults.standard.set(token, forKey: tokenKey)
        UserDefaults.standard.set(userId, forKey: userIdKey)
    }
    
    // 获取JWT Token
    func getJWTToken() -> String? {
        return UserDefaults.standard.string(forKey: tokenKey)
    }
    
    // 获取用户ID
    func getUserId() -> Int? {
        let userId = UserDefaults.standard.integer(forKey: userIdKey)
        return userId > 0 ? userId : nil
    }
    
    // 清除登录信息
    func logout() {
        UserDefaults.standard.removeObject(forKey: tokenKey)
        UserDefaults.standard.removeObject(forKey: userIdKey)
    }
}
```

### 6️⃣ 完整的使用流程

```swift
// 1. 用户登录，获取JWT token
func login(username: String, password: String) async {
    let loginURL = "http://192.168.100.173:5000/api/auth/login"
    
    // 发送登录请求
    let response = try await performLogin(url: loginURL, username: username, password: password)
    
    // 保存token和用户ID
    if let token = response["token"] as? String,
       let userId = response["user_id"] as? Int {
        AuthManager.shared.saveLoginInfo(token: token, userId: userId)
    }
}

// 2. 使用token连接WebSocket
func connectWebSocket() {
    guard let token = AuthManager.shared.getJWTToken(),
          let userId = AuthManager.shared.getUserId() else {
        print("❌ 未登录")
        return
    }
    
    let wsManager = TradingWebSocketManager(
        serverURL: "http://192.168.100.173:5000",
        jwtToken: token,
        userId: userId
    )
    
    wsManager.connect()
}
```

## 🔑 **关键配置总结**

### ⚠️⚠️⚠️ 认证参数（最重要）

**服务器端支持3种认证方式：**
```python
# 方式1: 从 auth 参数读取（推荐）
if auth and 'token' in auth:
    token = auth['token']

# 方式2: 从 Authorization Header 读取（备用）
elif 'Authorization' in request.headers:
    auth_header = request.headers.get('Authorization')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]  # 移除 'Bearer ' 前缀

# 方式3: 从 URL 参数读取
elif request.args.get('token'):
    token = request.args.get('token')
```

**客户端配置方式：**
```swift
// ✅ 方式1: 使用 .auth() 配置项（推荐）
manager = SocketManager(
    socketURL: url,
    config: [
        .auth(["token": jwtToken])  // ⚠️ 推荐方式
    ]
)

// ✅ 方式2: 使用 HTTP Header（备用）
manager = SocketManager(
    socketURL: url,
    config: [
        .extraHeaders(["Authorization": "Bearer \(jwtToken)"])  // 备用方式
    ]
)

// ✅ 方式3: 同时使用两种方式（最保险）
manager = SocketManager(
    socketURL: url,
    config: [
        .auth(["token": jwtToken]),
        .extraHeaders(["Authorization": "Bearer \(jwtToken)"])
    ]
)

// ❌ 错误方式：
// .connectParams(["token": jwtToken])  // 这个不会传递到 auth 参数
```

### 必需字段：
1. **serverURL**: `"http://192.168.100.173:5000"`
2. **jwtToken**: 从登录API获取的JWT令牌（必需！）
3. **userId**: 不需要传递，服务器会从token中自动解析

### 完整的Socket.IO配置：
```swift
manager = SocketManager(
    socketURL: URL(string: "http://192.168.100.173:5000")!,
    config: [
        .log(true),                      // 开启日志便于调试
        .forceWebsockets(true),          // 强制使用WebSocket
        .reconnects(true),               // 自动重连
        .auth(["token": jwtToken])       // ⚠️⚠️⚠️ 最关键：认证token
    ]
)
```

### 订阅数据类型：
- `"balance"` - 余额数据
- `"positions"` - 持仓数据
- `"pnl"` - 盈亏数据
- `"orders"` - 订单数据

## 🧪 测试连接

```swift
// 测试代码
let testToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
let wsManager = TradingWebSocketManager(
    serverURL: "http://192.168.100.173:5000",
    jwtToken: testToken,
    userId: 4
)
wsManager.connect()
```

## ⚠️ 注意事项

1. **Token有效期** - JWT token会过期，需要定期刷新
2. **网络切换** - App切换网络时需要重连
3. **后台运行** - iOS后台限制，需要处理断线重连
4. **错误处理** - 处理各种连接错误和超时
5. **数据同步** - 确保WebSocket数据与REST API数据一致

## 🔐 安全建议

1. 使用HTTPS/WSS加密传输
2. Token安全存储（使用Keychain）
3. 定期刷新token
4. 验证服务器证书
5. 处理认证失败情况
