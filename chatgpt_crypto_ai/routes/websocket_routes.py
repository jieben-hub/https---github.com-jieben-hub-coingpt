# -*- coding: utf-8 -*-
"""
WebSocket 路由
处理实时数据推送的WebSocket连接
"""
import logging
import jwt
import time
from datetime import datetime
from flask import request
from flask_socketio import SocketIO, emit, disconnect
from services.websocket_service import get_websocket_service
import config

logger = logging.getLogger(__name__)

def register_websocket_events(socketio: SocketIO):
    """注册WebSocket事件处理器"""
    
    @socketio.on('connect')
    def handle_connect(auth):
        """处理客户端连接"""
        try:
            # 验证认证信息
            token = None
            if auth and 'token' in auth:
                token = auth['token']
            elif request.args.get('token'):
                token = request.args.get('token')
            
            if token:
                # 验证JWT token
                try:
                    payload = jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
                    user_id = payload.get('sub')  # 从token中获取用户ID
                    
                    if user_id:
                        auth_data = {'user_id': int(user_id)}
                        ws_service = get_websocket_service()
                        if ws_service:
                            ws_service.handle_connect(auth_data)
                        else:
                            emit('error', {'message': 'WebSocket服务未启动'})
                    else:
                        emit('error', {'message': 'Token中缺少用户ID'})
                        disconnect()
                except jwt.ExpiredSignatureError:
                    emit('error', {'message': 'Token已过期'})
                    disconnect()
                except jwt.InvalidTokenError:
                    emit('error', {'message': 'Token无效'})
                    disconnect()
            else:
                emit('error', {'message': '缺少认证Token'})
                disconnect()
                
        except Exception as e:
            logger.error(f"WebSocket连接处理失败: {e}")
            emit('error', {'message': '连接失败'})
            disconnect()
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """处理客户端断开连接"""
        try:
            ws_service = get_websocket_service()
            if ws_service:
                ws_service.handle_disconnect()
        except Exception as e:
            logger.error(f"WebSocket断开处理失败: {e}")
    
    @socketio.on('subscribe')
    def handle_subscribe(data):
        """处理订阅请求"""
        try:
            ws_service = get_websocket_service()
            if ws_service:
                ws_service.handle_subscribe(data)
            else:
                emit('error', {'message': 'WebSocket服务未启动'})
        except Exception as e:
            logger.error(f"处理订阅请求失败: {e}")
            emit('error', {'message': '订阅失败'})
    
    @socketio.on('unsubscribe')
    def handle_unsubscribe(data):
        """处理取消订阅请求"""
        try:
            ws_service = get_websocket_service()
            if ws_service:
                ws_service.handle_unsubscribe(data)
            else:
                emit('error', {'message': 'WebSocket服务未启动'})
        except Exception as e:
            logger.error(f"处理取消订阅请求失败: {e}")
            emit('error', {'message': '取消订阅失败'})
    
    @socketio.on('ping')
    def handle_ping():
        """处理心跳包"""
        emit('pong', {'timestamp': str(int(time.time() * 1000))})
    
    @socketio.on('request_data')
    def handle_request_data(data):
        """处理数据请求"""
        try:
            data_type = data.get('type')
            user_id = data.get('user_id')
            
            if not user_id:
                emit('error', {'message': '用户ID缺失'})
                return
            
            # 根据请求类型获取数据
            if data_type == 'balance':
                # 获取余额数据并推送
                from services.trading_service import TradingService
                try:
                    balance = TradingService.get_balance(user_id=user_id)
                    emit('balance_update', {
                        'type': 'balance_update',
                        'data': balance,
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception as e:
                    emit('error', {'message': f'获取余额失败: {str(e)}'})
            
            elif data_type == 'positions':
                # 获取持仓数据并推送
                from services.trading_service import TradingService
                try:
                    positions = TradingService.get_positions(user_id=user_id)
                    emit('position_update', {
                        'type': 'position_update',
                        'data': positions,
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception as e:
                    emit('error', {'message': f'获取持仓失败: {str(e)}'})
            
            elif data_type == 'orders':
                # 获取订单数据并推送
                from services.trading_service import TradingService
                try:
                    orders = TradingService.get_open_orders(user_id=user_id)
                    emit('order_update', {
                        'type': 'order_update',
                        'data': orders,
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception as e:
                    emit('error', {'message': f'获取订单失败: {str(e)}'})
            
            else:
                emit('error', {'message': f'不支持的数据类型: {data_type}'})
                
        except Exception as e:
            logger.error(f"处理数据请求失败: {e}")
            emit('error', {'message': '数据请求失败'})
