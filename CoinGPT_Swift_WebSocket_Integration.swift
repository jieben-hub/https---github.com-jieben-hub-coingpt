// CoinGPT Swift WebSocket 集成方案
// 完整的iOS客户端WebSocket实现

import Foundation
import SocketIO
import UIKit

// MARK: - WebSocket管理器
class CoinGPTWebSocketManager: ObservableObject {
    
    // MARK: - 属性
    private var manager: SocketManager?
    private var socket: SocketIOClient?
    private let serverURL: String
    private let userId: Int
    private let jwtToken: String
    
    // 连接状态
    @Published var isConnected: Bool = false
    @Published var connectionStatus: String = "未连接"
    
    // 交易数据
    @Published var balance: BalanceData?
    @Published var positions: [PositionData] = []
    @Published var pnlData: PnlData?
    @Published var orders: [OrderData] = []
    
    // 错误处理
    @Published var errorMessage: String?
    @Published var showError: Bool = false
    
    // 重连配置
    private var reconnectAttempts = 0
    private let maxReconnectAttempts = 5
    private var reconnectTimer: Timer?
    
    // MARK: - 初始化
    init(serverURL: String, userId: Int, jwtToken: String) {
        self.serverURL = serverURL
        self.userId = userId
        self.jwtToken = jwtToken
        setupSocketManager()
    }
    
    // MARK: - Socket配置
    private func setupSocketManager() {
        guard let url = URL(string: serverURL) else {
            print("❌ 无效的服务器URL: \(serverURL)")
            return
        }
        
        manager = SocketManager(socketURL: url, config: [
            .log(true),
            .compress,
            .extraHeaders(["Authorization": "Bearer \(jwtToken)"]),
            .forceWebsockets(true),
            .reconnects(true),
            .reconnectAttempts(maxReconnectAttempts),
            .reconnectWait(2)
        ])
        
        socket = manager?.defaultSocket
        setupEventHandlers()
    }
    
    // MARK: - 事件处理
    private func setupEventHandlers() {
        guard let socket = socket else { return }
        
        // 连接事件
        socket.on(clientEvent: .connect) { [weak self] data, ack in
            DispatchQueue.main.async {
                self?.handleConnect()
            }
        }
        
        socket.on(clientEvent: .disconnect) { [weak self] data, ack in
            DispatchQueue.main.async {
                self?.handleDisconnect(reason: data.first as? String ?? "未知原因")
            }
        }
        
        socket.on(clientEvent: .error) { [weak self] data, ack in
            DispatchQueue.main.async {
                self?.handleError(data: data)
            }
        }
        
        // 服务器确认事件
        socket.on("connected") { [weak self] data, ack in
            print("✅ 服务器连接确认: \(data)")
            DispatchQueue.main.async {
                self?.connectionStatus = "已连接"
                self?.subscribeToTradingData()
            }
        }
        
        // 订阅确认事件
        socket.on("subscribed") { [weak self] data, ack in
            print("✅ 订阅成功: \(data)")
            DispatchQueue.main.async {
                self?.connectionStatus = "已订阅交易数据"
            }
        }
        
        // 交易数据更新事件 - 对应服务器端的WebSocket事件
        socket.on("balance_update") { [weak self] data, ack in
            print("📊 收到余额更新事件")
            self?.handleBalanceUpdate(data: data)
        }
        
        socket.on("positions_update") { [weak self] data, ack in
            print("📊 收到持仓更新事件")
            self?.handlePositionsUpdate(data: data)
        }
        
        socket.on("pnl_update") { [weak self] data, ack in
            print("📊 收到盈亏更新事件")
            self?.handlePnlUpdate(data: data)
        }
        
        socket.on("orders_update") { [weak self] data, ack in
            print("📊 收到订单更新事件")
            self?.handleOrdersUpdate(data: data)
        }
        
        // 错误事件
        socket.on("error") { [weak self] data, ack in
            self?.handleServerError(data: data)
        }
    }
    
    // MARK: - 连接管理
    func connect() {
        print("🔄 正在连接WebSocket...")
        connectionStatus = "连接中..."
        socket?.connect()
    }
    
    func disconnect() {
        print("🔌 断开WebSocket连接")
        socket?.disconnect()
        reconnectTimer?.invalidate()
        reconnectTimer = nil
    }
    
    private func handleConnect() {
        print("✅ WebSocket连接成功")
        isConnected = true
        connectionStatus = "已连接"
        reconnectAttempts = 0
        
        // 发送连接确认
        socket?.emit("ping")
    }
    
    private func handleDisconnect(reason: String) {
        print("❌ WebSocket连接断开: \(reason)")
        isConnected = false
        connectionStatus = "连接断开: \(reason)"
        
        // 自动重连
        if reason != "io client disconnect" {
            attemptReconnect()
        }
    }
    
    private func attemptReconnect() {
        guard reconnectAttempts < maxReconnectAttempts else {
            connectionStatus = "重连失败"
            showErrorMessage("WebSocket重连失败，请检查网络连接")
            return
        }
        
        reconnectAttempts += 1
        let delay = min(pow(2.0, Double(reconnectAttempts)), 30.0) // 指数退避，最大30秒
        
        connectionStatus = "重连中... (\(reconnectAttempts)/\(maxReconnectAttempts))"
        
        reconnectTimer = Timer.scheduledTimer(withTimeInterval: delay, repeats: false) { [weak self] _ in
            self?.connect()
        }
    }
    
    // MARK: - 数据订阅
    private func subscribeToTradingData() {
        let subscriptionData: [String: Any] = [
            "user_id": userId,
            "types": ["balance", "positions", "pnl", "orders"]
        ]
        
        socket?.emit("subscribe_trading", subscriptionData)
        print("📡 发送交易数据订阅请求")
    }
    
    func unsubscribeFromTradingData() {
        let unsubscriptionData: [String: Any] = [
            "user_id": userId,
            "types": ["balance", "positions", "pnl", "orders"]
        ]
        
        socket?.emit("unsubscribe_trading", unsubscriptionData)
        print("🚫 取消交易数据订阅")
    }
    
    // MARK: - 数据处理
    private func handleBalanceUpdate(data: [Any]) {
        guard let responseData = data.first as? [String: Any],
              let balanceInfo = responseData["data"] as? [String: Any] else {
            print("❌ 余额数据格式错误")
            return
        }
        
        DispatchQueue.main.async {
            self.balance = BalanceData(from: balanceInfo)
            print("💰 余额更新: \(self.balance?.available ?? 0)")
        }
    }
    
    private func handlePositionsUpdate(data: [Any]) {
        guard let responseData = data.first as? [String: Any],
              let positionsArray = responseData["data"] as? [[String: Any]] else {
            print("❌ 持仓数据格式错误")
            return
        }
        
        DispatchQueue.main.async {
            self.positions = positionsArray.compactMap { PositionData(from: $0) }
            print("📊 持仓更新: \(self.positions.count) 个持仓")
        }
    }
    
    private func handlePnlUpdate(data: [Any]) {
        guard let responseData = data.first as? [String: Any],
              let pnlInfo = responseData["data"] as? [String: Any] else {
            print("❌ 盈亏数据格式错误")
            return
        }
        
        DispatchQueue.main.async {
            self.pnlData = PnlData(from: pnlInfo)
            print("📈 盈亏更新: \(self.pnlData?.totalUnrealizedPnl ?? 0)")
        }
    }
    
    private func handleOrdersUpdate(data: [Any]) {
        guard let responseData = data.first as? [String: Any],
              let ordersArray = responseData["data"] as? [[String: Any]] else {
            print("❌ 订单数据格式错误")
            return
        }
        
        DispatchQueue.main.async {
            self.orders = ordersArray.compactMap { OrderData(from: $0) }
            print("📋 订单更新: \(self.orders.count) 个订单")
        }
    }
    
    // MARK: - 错误处理
    private func handleError(data: [Any]) {
        let errorInfo = data.first as? String ?? "未知错误"
        print("❌ WebSocket错误: \(errorInfo)")
        showErrorMessage("连接错误: \(errorInfo)")
    }
    
    private func handleServerError(data: [Any]) {
        guard let errorData = data.first as? [String: Any],
              let message = errorData["message"] as? String else {
            showErrorMessage("服务器错误")
            return
        }
        
        print("❌ 服务器错误: \(message)")
        showErrorMessage(message)
    }
    
    private func showErrorMessage(_ message: String) {
        DispatchQueue.main.async {
            self.errorMessage = message
            self.showError = true
        }
    }
    
    // MARK: - 手动数据请求
    func requestLatestData() {
        guard isConnected else {
            showErrorMessage("WebSocket未连接")
            return
        }
        
        // 可以请求最新数据
        socket?.emit("request_data", [
            "user_id": userId,
            "type": "all"
        ])
    }
}

// MARK: - 数据模型
struct BalanceData {
    let coin: String
    let available: Double
    let total: Double
    let equity: Double
    
    init(from dict: [String: Any]) {
        self.coin = dict["coin"] as? String ?? ""
        self.available = dict["available"] as? Double ?? 0.0
        self.total = dict["total"] as? Double ?? 0.0
        self.equity = dict["equity"] as? Double ?? 0.0
    }
}

struct PositionData: Identifiable {
    let id = UUID()
    let symbol: String
    let side: String
    let size: Double
    let entryPrice: Double
    let markPrice: Double
    let unrealizedPnl: Double
    let leverage: Double
    
    init(from dict: [String: Any]) {
        self.symbol = dict["symbol"] as? String ?? ""
        self.side = dict["side"] as? String ?? ""
        self.size = dict["size"] as? Double ?? 0.0
        self.entryPrice = dict["entry_price"] as? Double ?? 0.0
        self.markPrice = dict["mark_price"] as? Double ?? 0.0
        self.unrealizedPnl = dict["unrealized_pnl"] as? Double ?? 0.0
        self.leverage = dict["leverage"] as? Double ?? 1.0
    }
    
    var pnlColor: UIColor {
        return unrealizedPnl >= 0 ? .systemGreen : .systemRed
    }
    
    var pnlText: String {
        let sign = unrealizedPnl >= 0 ? "+" : ""
        return "\(sign)\(String(format: "%.2f", unrealizedPnl))"
    }
}

struct PnlData {
    let totalUnrealizedPnl: Double
    let positionCount: Int
    let positions: [PositionData]
    
    init(from dict: [String: Any]) {
        self.totalUnrealizedPnl = dict["total_unrealized_pnl"] as? Double ?? 0.0
        self.positionCount = dict["position_count"] as? Int ?? 0
        
        if let positionsArray = dict["positions"] as? [[String: Any]] {
            self.positions = positionsArray.compactMap { PositionData(from: $0) }
        } else {
            self.positions = []
        }
    }
    
    var totalPnlColor: UIColor {
        return totalUnrealizedPnl >= 0 ? .systemGreen : .systemRed
    }
    
    var totalPnlText: String {
        let sign = totalUnrealizedPnl >= 0 ? "+" : ""
        return "\(sign)\(String(format: "%.2f", totalUnrealizedPnl))"
    }
}

struct OrderData: Identifiable {
    let id = UUID()
    let orderId: String
    let symbol: String
    let side: String
    let type: String
    let quantity: Double
    let price: Double
    let status: String
    let filledQuantity: Double
    
    init(from dict: [String: Any]) {
        self.orderId = dict["order_id"] as? String ?? ""
        self.symbol = dict["symbol"] as? String ?? ""
        self.side = dict["side"] as? String ?? ""
        self.type = dict["type"] as? String ?? ""
        self.quantity = dict["quantity"] as? Double ?? 0.0
        self.price = dict["price"] as? Double ?? 0.0
        self.status = dict["status"] as? String ?? ""
        self.filledQuantity = dict["filled_quantity"] as? Double ?? 0.0
    }
    
    var statusColor: UIColor {
        switch status.lowercased() {
        case "filled": return .systemGreen
        case "partiallyfilled": return .systemOrange
        case "cancelled": return .systemRed
        default: return .systemBlue
        }
    }
}

// MARK: - SwiftUI视图示例
import SwiftUI

struct TradingDashboardView: View {
    @StateObject private var webSocketManager = CoinGPTWebSocketManager(
        serverURL: "http://192.168.100.173:5000",
        userId: 4
    )
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // 连接状态
                    ConnectionStatusView(manager: webSocketManager)
                    
                    // 余额信息
                    if let balance = webSocketManager.balance {
                        BalanceCardView(balance: balance)
                    }
                    
                    // 盈亏信息
                    if let pnlData = webSocketManager.pnlData {
                        PnlCardView(pnlData: pnlData)
                    }
                    
                    // 持仓列表
                    PositionsListView(positions: webSocketManager.positions)
                    
                    // 订单列表
                    OrdersListView(orders: webSocketManager.orders)
                }
                .padding()
            }
            .navigationTitle("交易面板")
            .onAppear {
                webSocketManager.connect()
            }
            .onDisappear {
                webSocketManager.disconnect()
            }
            .alert("错误", isPresented: $webSocketManager.showError) {
                Button("确定") {
                    webSocketManager.showError = false
                }
            } message: {
                Text(webSocketManager.errorMessage ?? "")
            }
        }
    }
}

struct ConnectionStatusView: View {
    @ObservedObject var manager: CoinGPTWebSocketManager
    
    var body: some View {
        HStack {
            Circle()
                .fill(manager.isConnected ? Color.green : Color.red)
                .frame(width: 10, height: 10)
            
            Text(manager.connectionStatus)
                .font(.caption)
            
            Spacer()
            
            Button("重连") {
                manager.connect()
            }
            .disabled(manager.isConnected)
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(8)
    }
}

struct BalanceCardView: View {
    let balance: BalanceData
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("账户余额")
                .font(.headline)
            
            HStack {
                VStack(alignment: .leading) {
                    Text("可用余额")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text("\(balance.available, specifier: "%.2f") \(balance.coin)")
                        .font(.title2)
                        .bold()
                }
                
                Spacer()
                
                VStack(alignment: .trailing) {
                    Text("总余额")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text("\(balance.total, specifier: "%.2f") \(balance.coin)")
                        .font(.title3)
                }
            }
        }
        .padding()
        .background(Color.blue.opacity(0.1))
        .cornerRadius(12)
    }
}

struct PnlCardView: View {
    let pnlData: PnlData
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("总盈亏")
                .font(.headline)
            
            HStack {
                Text(pnlData.totalPnlText)
                    .font(.title)
                    .bold()
                    .foregroundColor(Color(pnlData.totalPnlColor))
                
                Spacer()
                
                Text("\(pnlData.positionCount) 个持仓")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(pnlData.totalUnrealizedPnl >= 0 ? Color.green.opacity(0.1) : Color.red.opacity(0.1))
        .cornerRadius(12)
    }
}

struct PositionsListView: View {
    let positions: [PositionData]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("持仓")
                .font(.headline)
            
            if positions.isEmpty {
                Text("暂无持仓")
                    .foregroundColor(.secondary)
                    .padding()
            } else {
                ForEach(positions) { position in
                    PositionRowView(position: position)
                }
            }
        }
        .padding()
        .background(Color.gray.opacity(0.05))
        .cornerRadius(12)
    }
}

struct PositionRowView: View {
    let position: PositionData
    
    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text(position.symbol)
                    .font(.headline)
                Text("\(position.side) \(position.size, specifier: "%.4f")")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            VStack(alignment: .trailing) {
                Text(position.pnlText)
                    .font(.headline)
                    .foregroundColor(Color(position.pnlColor))
                Text("\(position.markPrice, specifier: "%.2f")")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

struct OrdersListView: View {
    let orders: [OrderData]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("挂单")
                .font(.headline)
            
            if orders.isEmpty {
                Text("暂无挂单")
                    .foregroundColor(.secondary)
                    .padding()
            } else {
                ForEach(orders) { order in
                    OrderRowView(order: order)
                }
            }
        }
        .padding()
        .background(Color.gray.opacity(0.05))
        .cornerRadius(12)
    }
}

struct OrderRowView: View {
    let order: OrderData
    
    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text(order.symbol)
                    .font(.headline)
                Text("\(order.side) \(order.quantity, specifier: "%.4f")")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            VStack(alignment: .trailing) {
                Text(order.status)
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(Color(order.statusColor).opacity(0.2))
                    .cornerRadius(4)
                Text("\(order.price, specifier: "%.2f")")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - 使用示例
/*
在你的App中使用:

1. 添加依赖到Package.swift或通过Xcode添加:
   https://github.com/socketio/socket.io-client-swift

2. 在ContentView中使用:
   TradingDashboardView()

3. 或者在UIKit中使用:
   let webSocketManager = CoinGPTWebSocketManager(
       serverURL: "http://192.168.100.173:5000", 
       userId: 4
   )
   webSocketManager.connect()
*/
