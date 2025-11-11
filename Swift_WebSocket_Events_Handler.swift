// Swift WebSocket事件处理器
// 专门处理CoinGPT的4个核心交易WebSocket事件

import Foundation
import SocketIO

class CoinGPTTradingWebSocket: ObservableObject {
    
    // MARK: - 属性
    private var socket: SocketIOClient?
    private let userId: Int
    
    // 发布的数据 - 对应4个核心API
    @Published var balance: TradingBalance?          // 对应 /api/trading/balance
    @Published var positions: [TradingPosition] = [] // 对应 /api/trading/positions  
    @Published var pnlData: TradingPnL?             // 对应 /api/trading/pnl
    @Published var orders: [TradingOrder] = []       // 对应 /api/trading/orders
    
    @Published var isConnected = false
    @Published var lastUpdateTime: Date?
    
    // MARK: - 初始化
    init(serverURL: String, userId: Int) {
        self.userId = userId
        setupWebSocket(serverURL: serverURL)
    }
    
    // MARK: - WebSocket设置
    private func setupWebSocket(serverURL: String) {
        guard let url = URL(string: serverURL) else { return }
        
        let manager = SocketManager(socketURL: url, config: [
            .log(false), // 生产环境建议关闭
            .reconnects(true),
            .reconnectAttempts(5)
        ])
        
        socket = manager.defaultSocket
        setupEventHandlers()
    }
    
    // MARK: - 核心事件处理
    private func setupEventHandlers() {
        guard let socket = socket else { return }
        
        // 连接状态
        socket.on(clientEvent: .connect) { [weak self] _, _ in
            DispatchQueue.main.async {
                self?.isConnected = true
                self?.subscribeToTradingData()
            }
        }
        
        socket.on(clientEvent: .disconnect) { [weak self] _, _ in
            DispatchQueue.main.async {
                self?.isConnected = false
            }
        }
        
        // 🔥 核心事件1: 余额更新 (替代 /api/trading/balance 轮询)
        socket.on("balance_update") { [weak self] data, _ in
            self?.handleBalanceUpdate(data)
        }
        
        // 🔥 核心事件2: 持仓更新 (替代 /api/trading/positions 轮询)
        socket.on("positions_update") { [weak self] data, _ in
            self?.handlePositionsUpdate(data)
        }
        
        // 🔥 核心事件3: 盈亏更新 (替代 /api/trading/pnl 轮询)
        socket.on("pnl_update") { [weak self] data, _ in
            self?.handlePnlUpdate(data)
        }
        
        // 🟡 核心事件4: 订单更新 (替代 /api/trading/orders 轮询)
        socket.on("orders_update") { [weak self] data, _ in
            self?.handleOrdersUpdate(data)
        }
    }
    
    // MARK: - 连接和订阅
    func connect() {
        socket?.connect()
    }
    
    func disconnect() {
        socket?.disconnect()
    }
    
    private func subscribeToTradingData() {
        socket?.emit("subscribe_trading", [
            "user_id": userId,
            "types": ["balance", "positions", "pnl", "orders"]
        ])
    }
    
    // MARK: - 数据处理方法
    
    // 处理余额更新 - 替代每5-10秒的HTTP轮询
    private func handleBalanceUpdate(_ data: [Any]) {
        guard let responseData = data.first as? [String: Any],
              let balanceData = responseData["data"] as? [String: Any] else {
            print("❌ 余额数据格式错误")
            return
        }
        
        DispatchQueue.main.async {
            self.balance = TradingBalance(
                coin: balanceData["coin"] as? String ?? "USDT",
                available: balanceData["available"] as? Double ?? 0.0,
                total: balanceData["total"] as? Double ?? 0.0,
                equity: balanceData["equity"] as? Double ?? 0.0
            )
            self.lastUpdateTime = Date()
            print("💰 余额更新: \(self.balance?.available ?? 0)")
        }
    }
    
    // 处理持仓更新 - 替代每3-5秒的HTTP轮询
    private func handlePositionsUpdate(_ data: [Any]) {
        guard let responseData = data.first as? [String: Any],
              let positionsArray = responseData["data"] as? [[String: Any]] else {
            print("❌ 持仓数据格式错误")
            return
        }
        
        DispatchQueue.main.async {
            self.positions = positionsArray.map { posData in
                TradingPosition(
                    symbol: posData["symbol"] as? String ?? "",
                    side: posData["side"] as? String ?? "",
                    size: posData["size"] as? Double ?? 0.0,
                    entryPrice: posData["entry_price"] as? Double ?? 0.0,
                    markPrice: posData["mark_price"] as? Double ?? 0.0,
                    unrealizedPnl: posData["unrealized_pnl"] as? Double ?? 0.0,
                    leverage: posData["leverage"] as? Double ?? 1.0
                )
            }
            self.lastUpdateTime = Date()
            print("📊 持仓更新: \(self.positions.count) 个持仓")
        }
    }
    
    // 处理盈亏更新 - 替代每3-5秒的HTTP轮询
    private func handlePnlUpdate(_ data: [Any]) {
        guard let responseData = data.first as? [String: Any],
              let pnlInfo = responseData["data"] as? [String: Any] else {
            print("❌ 盈亏数据格式错误")
            return
        }
        
        DispatchQueue.main.async {
            self.pnlData = TradingPnL(
                totalUnrealizedPnl: pnlInfo["total_unrealized_pnl"] as? Double ?? 0.0,
                positionCount: pnlInfo["position_count"] as? Int ?? 0
            )
            self.lastUpdateTime = Date()
            print("📈 盈亏更新: \(self.pnlData?.totalUnrealizedPnl ?? 0)")
        }
    }
    
    // 处理订单更新 - 替代每10-15秒的HTTP轮询
    private func handleOrdersUpdate(_ data: [Any]) {
        guard let responseData = data.first as? [String: Any],
              let ordersArray = responseData["data"] as? [[String: Any]] else {
            print("❌ 订单数据格式错误")
            return
        }
        
        DispatchQueue.main.async {
            self.orders = ordersArray.map { orderData in
                TradingOrder(
                    orderId: orderData["order_id"] as? String ?? "",
                    symbol: orderData["symbol"] as? String ?? "",
                    side: orderData["side"] as? String ?? "",
                    type: orderData["type"] as? String ?? "",
                    quantity: orderData["quantity"] as? Double ?? 0.0,
                    price: orderData["price"] as? Double ?? 0.0,
                    status: orderData["status"] as? String ?? "",
                    filledQuantity: orderData["filled_quantity"] as? Double ?? 0.0
                )
            }
            self.lastUpdateTime = Date()
            print("📋 订单更新: \(self.orders.count) 个订单")
        }
    }
}

// MARK: - 数据模型 (对应服务器端API返回的数据结构)

struct TradingBalance {
    let coin: String
    let available: Double
    let total: Double
    let equity: Double
}

struct TradingPosition: Identifiable {
    let id = UUID()
    let symbol: String
    let side: String
    let size: Double
    let entryPrice: Double
    let markPrice: Double
    let unrealizedPnl: Double
    let leverage: Double
    
    var isProfitable: Bool {
        return unrealizedPnl >= 0
    }
    
    var pnlText: String {
        let sign = unrealizedPnl >= 0 ? "+" : ""
        return "\(sign)\(String(format: "%.2f", unrealizedPnl))"
    }
}

struct TradingPnL {
    let totalUnrealizedPnl: Double
    let positionCount: Int
    
    var isProfitable: Bool {
        return totalUnrealizedPnl >= 0
    }
    
    var totalPnlText: String {
        let sign = totalUnrealizedPnl >= 0 ? "+" : ""
        return "\(sign)\(String(format: "%.2f", totalUnrealizedPnl))"
    }
}

struct TradingOrder: Identifiable {
    let id = UUID()
    let orderId: String
    let symbol: String
    let side: String
    let type: String
    let quantity: Double
    let price: Double
    let status: String
    let filledQuantity: Double
    
    var isActive: Bool {
        return !["Filled", "Cancelled", "Rejected"].contains(status)
    }
}

// MARK: - 使用示例

/*
// 在你的SwiftUI View中使用
struct TradingView: View {
    @StateObject private var tradingWS = CoinGPTTradingWebSocket(
        serverURL: "http://192.168.100.173:5000",
        userId: 4
    )
    
    var body: some View {
        VStack {
            // 连接状态
            HStack {
                Circle()
                    .fill(tradingWS.isConnected ? Color.green : Color.red)
                    .frame(width: 8, height: 8)
                Text(tradingWS.isConnected ? "已连接" : "未连接")
            }
            
            // 余额显示 - 实时更新，无需轮询
            if let balance = tradingWS.balance {
                Text("余额: \(balance.available, specifier: "%.2f") \(balance.coin)")
            }
            
            // 总盈亏 - 实时更新，无需轮询
            if let pnl = tradingWS.pnlData {
                Text("总盈亏: \(pnl.totalPnlText)")
                    .foregroundColor(pnl.isProfitable ? .green : .red)
            }
            
            // 持仓列表 - 实时更新，无需轮询
            List(tradingWS.positions) { position in
                HStack {
                    Text(position.symbol)
                    Spacer()
                    Text(position.pnlText)
                        .foregroundColor(position.isProfitable ? .green : .red)
                }
            }
        }
        .onAppear {
            tradingWS.connect()
        }
        .onDisappear {
            tradingWS.disconnect()
        }
    }
}

// 在UIKit中使用
class TradingViewController: UIViewController {
    private let tradingWS = CoinGPTTradingWebSocket(
        serverURL: "http://192.168.100.173:5000",
        userId: 4
    )
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // 监听余额变化 - 替代定时器轮询
        tradingWS.$balance
            .compactMap { $0 }
            .receive(on: DispatchQueue.main)
            .sink { [weak self] balance in
                self?.updateBalanceUI(balance)
            }
            .store(in: &cancellables)
        
        // 监听持仓变化 - 替代定时器轮询
        tradingWS.$positions
            .receive(on: DispatchQueue.main)
            .sink { [weak self] positions in
                self?.updatePositionsUI(positions)
            }
            .store(in: &cancellables)
        
        tradingWS.connect()
    }
    
    private func updateBalanceUI(_ balance: TradingBalance) {
        // 更新余额UI - 实时数据，无延迟
        balanceLabel.text = "\(balance.available) \(balance.coin)"
    }
    
    private func updatePositionsUI(_ positions: [TradingPosition]) {
        // 更新持仓UI - 实时数据，无延迟
        positionsTableView.reloadData()
    }
}
*/
