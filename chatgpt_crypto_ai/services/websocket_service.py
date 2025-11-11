# -*- coding: utf-8 -*-
"""
WebSocket 实时数据服务
提供交易数据的实时推送，减少API轮询负担
"""
import json
import logging
import asyncio
import websockets
from typing import Dict, Set, Optional, Any
from datetime import datetime
import threading
from flask_socketio import SocketIO, emit, join_room, leave_room
from utils.data_converter import safe_float, safe_str

logger = logging.getLogger(__name__)

class TradingWebSocketService:
    """交易WebSocket服务"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.user_rooms: Dict[int, Set[str]] = {}  # 用户ID -> 房间集合
        self.active_connections: Set[str] = set()  # 活跃连接
        self.bybit_ws = None
        self.running = False
        
        # 订阅的数据类型
        self.subscriptions = {
            'balance': set(),      # 余额订阅
            'positions': set(),    # 持仓订阅
            'orders': set(),       # 订单订阅
            'pnl': set()          # 盈亏订阅
        }
    
    def start_service(self):
        """启动WebSocket服务"""
        if not self.running:
            self.running = True
            # 在后台线程中启动Bybit WebSocket连接
            threading.Thread(target=self._start_bybit_websocket, daemon=True).start()
            logger.info("WebSocket服务已启动")
    
    def stop_service(self):
        """停止WebSocket服务"""
        self.running = False
        if self.bybit_ws:
            asyncio.create_task(self.bybit_ws.close())
        logger.info("WebSocket服务已停止")
    
    def _start_bybit_websocket(self):
        """启动Bybit WebSocket连接"""
        try:
            asyncio.run(self._connect_bybit_websocket())
        except Exception as e:
            logger.error(f"Bybit WebSocket连接失败: {e}")
    
    async def _connect_bybit_websocket(self):
        """连接到Bybit WebSocket"""
        uri = "wss://stream.bybit.com/v5/public/linear"
        
        try:
            async with websockets.connect(uri) as websocket:
                self.bybit_ws = websocket
                logger.info("已连接到Bybit WebSocket")
                
                # 订阅价格数据
                subscribe_msg = {
                    "op": "subscribe",
                    "args": ["tickers.BTCUSDT", "tickers.ETHUSDT"]
                }
                await websocket.send(json.dumps(subscribe_msg))
                
                # 监听消息
                async for message in websocket:
                    if self.running:
                        await self._handle_bybit_message(message)
                    else:
                        break
                        
        except Exception as e:
            logger.error(f"Bybit WebSocket错误: {e}")
            if self.running:
                # 重连机制
                await asyncio.sleep(5)
                await self._connect_bybit_websocket()
    
    async def _handle_bybit_message(self, message: str):
        """处理Bybit WebSocket消息"""
        try:
            data = json.loads(message)
            
            if data.get('topic', '').startswith('tickers.'):
                # 处理价格更新
                ticker_data = data.get('data', {})
                symbol = ticker_data.get('symbol')
                
                if symbol:
                    price_update = {
                        'type': 'price_update',
                        'symbol': symbol,
                        'price': safe_float(ticker_data.get('lastPrice')),
                        'change24h': safe_float(ticker_data.get('price24hPcnt')),
                        'volume24h': safe_float(ticker_data.get('volume24h')),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # 广播价格更新
                    self._broadcast_to_subscribers('price_update', price_update)
                    
        except Exception as e:
            logger.error(f"处理WebSocket消息失败: {e}")
    
    def _broadcast_to_subscribers(self, event_type: str, data: Dict[str, Any]):
        """向订阅者广播数据"""
        try:
            self.socketio.emit(event_type, data)
        except Exception as e:
            logger.error(f"广播数据失败: {e}")
    
    # SocketIO 事件处理
    def handle_connect(self, auth):
        """处理客户端连接"""
        try:
            user_id = auth.get('user_id') if auth else None
            if user_id:
                room = f"user_{user_id}"
                join_room(room)
                
                if user_id not in self.user_rooms:
                    self.user_rooms[user_id] = set()
                self.user_rooms[user_id].add(room)
                
                logger.info(f"用户 {user_id} 已连接WebSocket")
                emit('connected', {'status': 'success', 'message': '连接成功'})
            else:
                emit('error', {'message': '认证失败'})
                
        except Exception as e:
            logger.error(f"处理连接失败: {e}")
            emit('error', {'message': '连接失败'})
    
    def handle_disconnect(self):
        """处理客户端断开连接"""
        # 清理用户房间信息
        # 注意：这里需要根据实际的session信息来清理
        logger.info("客户端已断开连接")
    
    def handle_subscribe(self, data):
        """处理订阅请求"""
        try:
            user_id = data.get('user_id')
            data_types = data.get('types', [])  # ['balance', 'positions', 'orders', 'pnl']
            
            if user_id:
                for data_type in data_types:
                    if data_type in self.subscriptions:
                        self.subscriptions[data_type].add(user_id)
                        join_room(f"{data_type}_{user_id}")
                
                logger.info(f"用户 {user_id} 订阅了: {data_types}")
                emit('subscribed', {'types': data_types, 'status': 'success'})
            else:
                emit('error', {'message': '用户ID缺失'})
                
        except Exception as e:
            logger.error(f"处理订阅失败: {e}")
            emit('error', {'message': '订阅失败'})
    
    def handle_unsubscribe(self, data):
        """处理取消订阅请求"""
        try:
            user_id = data.get('user_id')
            data_types = data.get('types', [])
            
            if user_id:
                for data_type in data_types:
                    if data_type in self.subscriptions:
                        self.subscriptions[data_type].discard(user_id)
                        leave_room(f"{data_type}_{user_id}")
                
                logger.info(f"用户 {user_id} 取消订阅: {data_types}")
                emit('unsubscribed', {'types': data_types, 'status': 'success'})
                
        except Exception as e:
            logger.error(f"处理取消订阅失败: {e}")
            emit('error', {'message': '取消订阅失败'})
    
    # 数据推送方法
    def push_balance_update(self, user_id: int, balance_data: Dict[str, Any]):
        """推送余额更新"""
        if user_id in self.subscriptions['balance']:
            room = f"balance_{user_id}"
            self.socketio.emit('balance_update', {
                'type': 'balance_update',
                'data': balance_data,
                'timestamp': datetime.now().isoformat()
            }, room=room)
    
    def push_position_update(self, user_id: int, positions_data: list):
        """推送持仓更新"""
        if user_id in self.subscriptions['positions']:
            room = f"positions_{user_id}"
            self.socketio.emit('position_update', {
                'type': 'position_update',
                'data': positions_data,
                'timestamp': datetime.now().isoformat()
            }, room=room)
    
    def push_order_update(self, user_id: int, orders_data: list):
        """推送订单更新"""
        if user_id in self.subscriptions['orders']:
            room = f"orders_{user_id}"
            self.socketio.emit('order_update', {
                'type': 'order_update',
                'data': orders_data,
                'timestamp': datetime.now().isoformat()
            }, room=room)
    
    def push_pnl_update(self, user_id: int, pnl_data: Dict[str, Any]):
        """推送盈亏更新"""
        if user_id in self.subscriptions['pnl']:
            room = f"pnl_{user_id}"
            self.socketio.emit('pnl_update', {
                'type': 'pnl_update',
                'data': pnl_data,
                'timestamp': datetime.now().isoformat()
            }, room=room)

# 全局WebSocket服务实例
websocket_service: Optional[TradingWebSocketService] = None

def init_websocket_service(socketio: SocketIO) -> TradingWebSocketService:
    """初始化WebSocket服务"""
    global websocket_service
    websocket_service = TradingWebSocketService(socketio)
    return websocket_service

def get_websocket_service() -> Optional[TradingWebSocketService]:
    """获取WebSocket服务实例"""
    return websocket_service
