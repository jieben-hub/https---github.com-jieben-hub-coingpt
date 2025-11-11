// WebSocket客户端连接示例
// 用于iOS/Android应用集成

class CoinGPTWebSocket {
    constructor(serverUrl, token) {
        this.serverUrl = serverUrl;
        this.token = token;
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        // 事件回调
        this.onBalanceUpdate = null;
        this.onPositionUpdate = null;
        this.onOrderUpdate = null;
        this.onPnlUpdate = null;
        this.onPriceUpdate = null;
        this.onError = null;
        this.onConnected = null;
        this.onDisconnected = null;
    }
    
    connect() {
        try {
            // 使用Socket.IO客户端库
            this.socket = io(this.serverUrl, {
                auth: {
                    token: this.token
                },
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: true
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
            console.log('WebSocket连接成功');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            
            if (this.onConnected) {
                this.onConnected();
            }
        });
        
        // 连接断开
        this.socket.on('disconnect', (reason) => {
            console.log('WebSocket连接断开:', reason);
            this.isConnected = false;
            
            if (this.onDisconnected) {
                this.onDisconnected(reason);
            }
            
            // 自动重连
            if (reason !== 'io client disconnect') {
                this.attemptReconnect();
            }
        });
        
        // 连接确认
        this.socket.on('connected', (data) => {
            console.log('连接确认:', data);
        });
        
        // 余额更新
        this.socket.on('balance_update', (data) => {
            console.log('余额更新:', data);
            if (this.onBalanceUpdate) {
                this.onBalanceUpdate(data);
            }
        });
        
        // 持仓更新
        this.socket.on('position_update', (data) => {
            console.log('持仓更新:', data);
            if (this.onPositionUpdate) {
                this.onPositionUpdate(data);
            }
        });
        
        // 订单更新
        this.socket.on('order_update', (data) => {
            console.log('订单更新:', data);
            if (this.onOrderUpdate) {
                this.onOrderUpdate(data);
            }
        });
        
        // 盈亏更新
        this.socket.on('pnl_update', (data) => {
            console.log('盈亏更新:', data);
            if (this.onPnlUpdate) {
                this.onPnlUpdate(data);
            }
        });
        
        // 价格更新
        this.socket.on('price_update', (data) => {
            console.log('价格更新:', data);
            if (this.onPriceUpdate) {
                this.onPriceUpdate(data);
            }
        });
        
        // 错误处理
        this.socket.on('error', (error) => {
            console.error('WebSocket错误:', error);
            if (this.onError) {
                this.onError('WebSocket错误', error);
            }
        });
        
        // 心跳响应
        this.socket.on('pong', (data) => {
            console.log('心跳响应:', data);
        });
    }
    
    // 订阅数据类型
    subscribe(dataTypes, userId) {
        if (this.isConnected) {
            this.socket.emit('subscribe', {
                user_id: userId,
                types: dataTypes // ['balance', 'positions', 'orders', 'pnl']
            });
        }
    }
    
    // 取消订阅
    unsubscribe(dataTypes, userId) {
        if (this.isConnected) {
            this.socket.emit('unsubscribe', {
                user_id: userId,
                types: dataTypes
            });
        }
    }
    
    // 请求数据
    requestData(dataType, userId) {
        if (this.isConnected) {
            this.socket.emit('request_data', {
                type: dataType,
                user_id: userId
            });
        }
    }
    
    // 发送心跳
    ping() {
        if (this.isConnected) {
            this.socket.emit('ping');
        }
    }
    
    // 断开连接
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.isConnected = false;
        }
    }
    
    // 重连机制
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('重连失败，已达到最大重连次数');
            if (this.onError) {
                this.onError('重连失败', '已达到最大重连次数');
            }
        }
    }
}

// 使用示例
const wsClient = new CoinGPTWebSocket('http://192.168.100.173:5000', 'your_jwt_token');

// 设置事件回调
wsClient.onConnected = () => {
    console.log('WebSocket已连接，开始订阅数据');
    // 订阅所有数据类型
    wsClient.subscribe(['balance', 'positions', 'orders', 'pnl'], userId);
};

wsClient.onBalanceUpdate = (data) => {
    // 更新UI中的余额显示
    updateBalanceUI(data.data);
};

wsClient.onPositionUpdate = (data) => {
    // 更新UI中的持仓显示
    updatePositionsUI(data.data);
};

wsClient.onPnlUpdate = (data) => {
    // 更新UI中的盈亏显示
    updatePnlUI(data.data);
};

wsClient.onError = (message, error) => {
    console.error('WebSocket错误:', message, error);
    // 显示错误提示
};

// 连接WebSocket
wsClient.connect();

// iOS Swift 集成示例 (注释)
/*
import SocketIO

class CoinGPTWebSocketManager {
    private var manager: SocketManager?
    private var socket: SocketIOClient?
    
    func connect(serverURL: String, token: String) {
        guard let url = URL(string: serverURL) else { return }
        
        manager = SocketManager(socketURL: url, config: [
            .log(true),
            .compress,
            .extraHeaders(["Authorization": "Bearer \(token)"])
        ])
        
        socket = manager?.defaultSocket
        
        socket?.on(clientEvent: .connect) { data, ack in
            print("WebSocket连接成功")
            self.subscribeToData()
        }
        
        socket?.on("balance_update") { data, ack in
            // 处理余额更新
            if let balanceData = data[0] as? [String: Any] {
                DispatchQueue.main.async {
                    self.updateBalanceUI(balanceData)
                }
            }
        }
        
        socket?.connect()
    }
    
    private func subscribeToData() {
        socket?.emit("subscribe", [
            "user_id": userId,
            "types": ["balance", "positions", "orders", "pnl"]
        ])
    }
}
*/
