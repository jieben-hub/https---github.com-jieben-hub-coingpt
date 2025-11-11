// 交易数据WebSocket客户端示例
// 专门用于交易数据的实时推送

class TradingWebSocketClient {
    constructor(serverUrl, jwtToken) {
        this.serverUrl = serverUrl;
        this.jwtToken = jwtToken;
        this.socket = null;
        this.isConnected = false;
        this.userId = null; // 将从token中获取
        
        // 数据回调函数
        this.onBalanceUpdate = null;
        this.onPositionUpdate = null;
        this.onPnlUpdate = null;
        this.onOrderUpdate = null;
        this.onError = null;
        this.onConnected = null;
        
        // 当前订阅的数据类型
        this.subscribedTypes = [];
    }
    
    connect() {
        try {
            // 使用JWT token进行认证连接
            this.socket = io(this.serverUrl, {
                auth: {
                    token: this.jwtToken
                },
                transports: ['websocket', 'polling']
            });
            this.setupEventHandlers();
        } catch (error) {
            console.error('WebSocket连接失败:', error);
            if (this.onError) {
                this.onError('连接失败', error);
            }
        }
    }
    
    setupEventHandlers() {
        // 连接成功
        this.socket.on('connect', () => {
            console.log('交易WebSocket连接成功');
            this.isConnected = true;
            
            if (this.onConnected) {
                this.onConnected();
            }
        });
        
        // 连接断开
        this.socket.on('disconnect', (reason) => {
            console.log('交易WebSocket连接断开:', reason);
            this.isConnected = false;
        });
        
        // 连接确认
        this.socket.on('connected', (data) => {
            console.log('服务器连接确认:', data);
            // 从服务器响应中获取用户ID
            if (data.user_id) {
                this.userId = data.user_id;
            }
        });
        
        // 订阅确认
        this.socket.on('subscribed', (data) => {
            console.log('订阅成功:', data);
            this.subscribedTypes = data.types;
        });
        
        // 取消订阅确认
        this.socket.on('unsubscribed', (data) => {
            console.log('取消订阅成功:', data);
            this.subscribedTypes = this.subscribedTypes.filter(
                type => !data.types.includes(type)
            );
        });
        
        // 余额更新
        this.socket.on('balance_update', (data) => {
            console.log('余额更新:', data);
            if (this.onBalanceUpdate) {
                this.onBalanceUpdate(data);
            }
        });
        
        // 持仓更新
        this.socket.on('positions_update', (data) => {
            console.log('持仓更新:', data);
            if (this.onPositionUpdate) {
                this.onPositionUpdate(data);
            }
        });
        
        // 盈亏更新
        this.socket.on('pnl_update', (data) => {
            console.log('盈亏更新:', data);
            if (this.onPnlUpdate) {
                this.onPnlUpdate(data);
            }
        });
        
        // 订单更新
        this.socket.on('orders_update', (data) => {
            console.log('订单更新:', data);
            if (this.onOrderUpdate) {
                this.onOrderUpdate(data);
            }
        });
        
        // 错误处理
        this.socket.on('error', (error) => {
            console.error('WebSocket错误:', error);
            if (this.onError) {
                this.onError('WebSocket错误', error);
            }
        });
    }
    
    // 订阅交易数据 - 不需要传递user_id，服务器从session获取
    subscribeTrading(dataTypes = ['balance', 'positions', 'pnl', 'orders']) {
        if (this.isConnected) {
            this.socket.emit('subscribe_trading', {
                types: dataTypes
            });
        } else {
            console.warn('WebSocket未连接，无法订阅');
        }
    }
    
    // 取消订阅交易数据 - 不需要传递user_id
    unsubscribeTrading(dataTypes) {
        if (this.isConnected) {
            this.socket.emit('unsubscribe_trading', {
                types: dataTypes || this.subscribedTypes
            });
        }
    }
    
    // 断开连接
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.isConnected = false;
        }
    }
    
    // 获取连接状态
    getStatus() {
        return {
            connected: this.isConnected,
            subscribedTypes: this.subscribedTypes,
            userId: this.userId
        };
    }
}

// 使用示例 - 需要提供JWT token
const jwtToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0IiwiaWF0IjoxNzYyNzIxMjA3LCJleHAiOjE3NjMzMjYwMDd9.taqUsvsF4wEh44yOlZG-n5E94jQtdoVHB4l7PLmGEuk";
const tradingWS = new TradingWebSocketClient('http://192.168.100.173:5000', jwtToken);

// 设置回调函数
tradingWS.onConnected = () => {
    console.log('交易WebSocket已连接，开始订阅数据');
    // 订阅所有交易数据
    tradingWS.subscribeTrading(['balance', 'positions', 'pnl', 'orders']);
};

tradingWS.onBalanceUpdate = (data) => {
    console.log('收到余额更新:', data.data);
    // 更新UI中的余额显示
    updateBalanceUI(data.data);
};

tradingWS.onPositionUpdate = (data) => {
    console.log('收到持仓更新:', data.data);
    // 更新UI中的持仓显示
    updatePositionsUI(data.data);
};

tradingWS.onPnlUpdate = (data) => {
    console.log('收到盈亏更新:', data.data);
    // 更新UI中的盈亏显示
    updatePnlUI(data.data);
};

tradingWS.onOrderUpdate = (data) => {
    console.log('收到订单更新:', data.data);
    // 更新UI中的订单显示
    updateOrdersUI(data.data);
};

tradingWS.onError = (message, error) => {
    console.error('交易WebSocket错误:', message, error);
    // 显示错误提示，可能需要回退到轮询模式
    showErrorMessage('实时数据连接异常，切换到轮询模式');
};

// 连接WebSocket
tradingWS.connect();

// UI更新函数示例
function updateBalanceUI(balanceData) {
    // 更新余额显示
    document.getElementById('balance-available').textContent = balanceData.available;
    document.getElementById('balance-total').textContent = balanceData.total;
}

function updatePositionsUI(positionsData) {
    // 更新持仓列表
    const positionsList = document.getElementById('positions-list');
    positionsList.innerHTML = '';
    
    positionsData.forEach(position => {
        const positionElement = document.createElement('div');
        positionElement.innerHTML = `
            <div class="position-item">
                <span>${position.symbol}</span>
                <span>${position.side}</span>
                <span>${position.size}</span>
                <span class="${position.unrealized_pnl >= 0 ? 'profit' : 'loss'}">
                    ${position.unrealized_pnl}
                </span>
            </div>
        `;
        positionsList.appendChild(positionElement);
    });
}

function updatePnlUI(pnlData) {
    // 更新总盈亏显示
    const totalPnl = document.getElementById('total-pnl');
    totalPnl.textContent = pnlData.total_unrealized_pnl;
    totalPnl.className = pnlData.total_unrealized_pnl >= 0 ? 'profit' : 'loss';
}

function updateOrdersUI(ordersData) {
    // 更新订单列表
    const ordersList = document.getElementById('orders-list');
    ordersList.innerHTML = '';
    
    ordersData.forEach(order => {
        const orderElement = document.createElement('div');
        orderElement.innerHTML = `
            <div class="order-item">
                <span>${order.symbol}</span>
                <span>${order.side}</span>
                <span>${order.type}</span>
                <span>${order.quantity}</span>
                <span>${order.price}</span>
                <span>${order.status}</span>
            </div>
        `;
        ordersList.appendChild(orderElement);
    });
}

function showErrorMessage(message) {
    // 显示错误消息
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    // 3秒后隐藏
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 3000);
}

// iOS Swift 集成示例 (注释)
/*
import SocketIO

class TradingWebSocketManager {
    private var manager: SocketManager?
    private var socket: SocketIOClient?
    private let userId: Int
    
    init(serverURL: String, userId: Int) {
        self.userId = userId
        guard let url = URL(string: serverURL) else { return }
        
        manager = SocketManager(socketURL: url, config: [
            .log(true),
            .compress
        ])
        
        socket = manager?.defaultSocket
        setupEventHandlers()
    }
    
    private func setupEventHandlers() {
        socket?.on(clientEvent: .connect) { data, ack in
            print("交易WebSocket连接成功")
            self.subscribeTrading()
        }
        
        socket?.on("balance_update") { data, ack in
            if let balanceData = data[0] as? [String: Any] {
                DispatchQueue.main.async {
                    self.handleBalanceUpdate(balanceData)
                }
            }
        }
        
        socket?.on("positions_update") { data, ack in
            if let positionsData = data[0] as? [String: Any] {
                DispatchQueue.main.async {
                    self.handlePositionsUpdate(positionsData)
                }
            }
        }
        
        socket?.on("pnl_update") { data, ack in
            if let pnlData = data[0] as? [String: Any] {
                DispatchQueue.main.async {
                    self.handlePnlUpdate(pnlData)
                }
            }
        }
    }
    
    func connect() {
        socket?.connect()
    }
    
    func disconnect() {
        socket?.disconnect()
    }
    
    private func subscribeTrading() {
        socket?.emit("subscribe_trading", [
            "user_id": userId,
            "types": ["balance", "positions", "pnl", "orders"]
        ])
    }
    
    private func handleBalanceUpdate(_ data: [String: Any]) {
        // 处理余额更新
        NotificationCenter.default.post(name: .balanceUpdated, object: data)
    }
    
    private func handlePositionsUpdate(_ data: [String: Any]) {
        // 处理持仓更新
        NotificationCenter.default.post(name: .positionsUpdated, object: data)
    }
    
    private func handlePnlUpdate(_ data: [String: Any]) {
        // 处理盈亏更新
        NotificationCenter.default.post(name: .pnlUpdated, object: data)
    }
}

extension Notification.Name {
    static let balanceUpdated = Notification.Name("balanceUpdated")
    static let positionsUpdated = Notification.Name("positionsUpdated")
    static let pnlUpdated = Notification.Name("pnlUpdated")
}
*/
