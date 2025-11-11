# -*- coding: utf-8 -*-
"""
交易数据WebSocket推送服务
专门处理交易相关的实时数据推送
"""
import logging
import threading
import time
from typing import Dict, Set, Any, Optional
from datetime import datetime
from flask_socketio import SocketIO
from services.trading_service import TradingService

logger = logging.getLogger(__name__)

class TradingWebSocketService:
    """交易数据WebSocket推送服务"""
    
    def __init__(self, socketio, app=None):
        self.socketio = socketio
        self.app = app  # 保存Flask app实例
        self.running = False
        self.subscribers: Dict[str, Set[int]] = {
            'balance': set(),
            'positions': set(), 
            'pnl': set(),
            'orders': set()
        }
        
        # 行情订阅：{symbol: set(user_ids)}
        self.ticker_subscribers: Dict[str, Set[int]] = {}
        
        # 数据缓存，避免重复推送相同数据
        self.data_cache: Dict[int, Dict[str, Any]] = {}
        
        # 推送频率控制 (秒)
        self.push_intervals = {
            'balance': 10,      # 余额每10秒检查一次
            'positions': 5,     # 持仓每5秒检查一次
            'pnl': 5,          # 盈亏每5秒检查一次  
            'orders': 15,      # 订单每15秒检查一次
            'ticker': 2        # 行情每2秒更新一次
        }
        
        # 行情缓存：{symbol: {price, timestamp}}
        self.ticker_cache: Dict[str, Dict[str, Any]] = {}
        
        # 线程控制
        self.threads: Dict[str, threading.Thread] = {}
    
    def start_service(self):
        """启动WebSocket推送服务"""
        if self.running:
            return
            
        self.running = True
        print("🚀 启动交易数据WebSocket推送服务")
        logger.info("启动交易数据WebSocket推送服务")
        
        # 启动各类数据推送线程
        for data_type in self.push_intervals.keys():
            thread = threading.Thread(
                target=self._data_push_loop,
                args=(data_type,),
                daemon=True,
                name=f"ws_push_{data_type}"
            )
            thread.start()
            self.threads[data_type] = thread
            print(f"🔄 启动{data_type}数据推送线程 - 推送间隔: {self.push_intervals[data_type]}秒")
            logger.info(f"启动{data_type}数据推送线程")
    
    def stop_service(self):
        """停止WebSocket推送服务"""
        self.running = False
        logger.info("停止交易数据WebSocket推送服务")
        
        # 等待线程结束
        for thread in self.threads.values():
            if thread.is_alive():
                thread.join(timeout=2)
    
    def subscribe_user(self, user_id: int, data_types: list):
        """用户订阅数据类型"""
        for data_type in data_types:
            if data_type in self.subscribers:
                self.subscribers[data_type].add(user_id)
                # 加入Socket.IO房间
                room = f"{data_type}_{user_id}"
                print(f"📋 用户{user_id}订阅{data_type}数据")
                print(f"   加入房间: {room}")
                print(f"   当前订阅者: {len(self.subscribers[data_type])}")
                logger.info(f"用户{user_id}订阅{data_type}数据")
    
    def unsubscribe_user(self, user_id: int, data_types: list):
        """用户取消订阅数据类型"""
        for data_type in data_types:
            if data_type in self.subscribers:
                self.subscribers[data_type].discard(user_id)
                print(f"📋 用户{user_id}取消订阅{data_type}数据 - 剩余订阅者: {len(self.subscribers[data_type])}")
                logger.info(f"用户{user_id}取消订阅{data_type}数据")
        
        # 清除该用户的数据缓存
        if user_id in self.data_cache:
            del self.data_cache[user_id]
            print(f"🗑️ 清除用户{user_id}的数据缓存")
            logger.info(f"清除用户{user_id}的数据缓存")
    
    def subscribe_ticker(self, user_id: int, symbols: list):
        """订阅行情数据"""
        for symbol in symbols:
            if symbol not in self.ticker_subscribers:
                self.ticker_subscribers[symbol] = set()
            
            self.ticker_subscribers[symbol].add(user_id)
            print(f"📊 用户{user_id}订阅{symbol}行情")
            print(f"   当前订阅{symbol}的用户: {len(self.ticker_subscribers[symbol])}")
            logger.info(f"用户{user_id}订阅{symbol}行情")
    
    def unsubscribe_ticker(self, user_id: int, symbols: list):
        """取消订阅行情数据"""
        for symbol in symbols:
            if symbol in self.ticker_subscribers:
                self.ticker_subscribers[symbol].discard(user_id)
                print(f"📊 用户{user_id}取消订阅{symbol}行情 - 剩余订阅者: {len(self.ticker_subscribers[symbol])}")
                
                # 如果没有订阅者了，删除该symbol
                if not self.ticker_subscribers[symbol]:
                    del self.ticker_subscribers[symbol]
                    print(f"   {symbol}无订阅者，移除")
                
                logger.info(f"用户{user_id}取消订阅{symbol}行情")
    
    def _data_push_loop(self, data_type: str):
        """数据推送循环"""
        interval = self.push_intervals[data_type]
        
        while self.running:
            try:
                if data_type == 'ticker':
                    # 行情推送逻辑
                    self._push_ticker_data()
                else:
                    # 获取订阅该数据类型的用户
                    subscribers = self.subscribers[data_type].copy()
                    
                    if subscribers:
                        print(f"🔄 [{data_type}] 开始推送，订阅者: {subscribers}")
                        # 为每个订阅用户推送数据
                        for user_id in subscribers:
                            self._push_user_data(user_id, data_type)
                    # else:
                    #     print(f"⏸️ [{data_type}] 无订阅者，跳过推送")
                
                # 等待下一次推送
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"{data_type}数据推送循环出错: {e}")
                print(f"❌ [{data_type}] 推送循环出错: {e}")
                time.sleep(interval)
    
    def _push_user_data(self, user_id: int, data_type: str):
        """为特定用户推送特定类型的数据"""
        try:
            # 使用Flask应用上下文
            if self.app:
                with self.app.app_context():
                    # 获取最新数据
                    new_data = self._fetch_user_data(user_id, data_type)
                    
                    if new_data is None:
                        print(f"⚠️ [{data_type}] 用户{user_id}数据为空，跳过推送")
                        return
                    
                    # 检查数据是否有变化
                    has_changed = self._has_data_changed(user_id, data_type, new_data)
                    print(f"🔍 [{data_type}] 用户{user_id}数据变化: {has_changed}")
                    
                    if has_changed:
                        # 更新缓存
                        self._update_cache(user_id, data_type, new_data)
                        
                        # 推送数据
                        self._emit_data_update(user_id, data_type, new_data)
                    else:
                        print(f"⏭️ [{data_type}] 用户{user_id}数据无变化，跳过推送")
            else:
                print(f"⚠️ 无Flask app实例")
                # 如果没有app实例，直接获取（可能会失败）
                new_data = self._fetch_user_data(user_id, data_type)
                
                if new_data is None:
                    return
                
                # 检查数据是否有变化
                if self._has_data_changed(user_id, data_type, new_data):
                    # 更新缓存
                    self._update_cache(user_id, data_type, new_data)
                    
                    # 推送数据
                    self._emit_data_update(user_id, data_type, new_data)
                
                logger.debug(f"推送{data_type}数据给用户{user_id}")
            
        except Exception as e:
            logger.error(f"推送{data_type}数据给用户{user_id}失败: {e}")
            print(f"❌ [{data_type}] 推送给用户{user_id}失败: {e}")
    
    def _fetch_user_data(self, user_id: int, data_type: str) -> Optional[Any]:
        """获取用户的特定类型数据"""
        try:
            if data_type == 'balance':
                return TradingService.get_balance(user_id=user_id, coin='USDT')
            
            elif data_type == 'positions':
                return TradingService.get_positions(user_id=user_id)
            
            elif data_type == 'pnl':
                positions = TradingService.get_positions(user_id=user_id)
                # 计算总盈亏
                total_unrealized_pnl = 0.0
                position_details = []
                
                for pos in positions:
                    unrealized_pnl = float(pos.get('unrealized_pnl', 0))
                    total_unrealized_pnl += unrealized_pnl
                    
                    position_details.append({
                        'symbol': pos.get('symbol'),
                        'side': pos.get('side'),
                        'size': pos.get('size'),
                        'unrealized_pnl': unrealized_pnl,
                        'entry_price': pos.get('entry_price'),
                        'mark_price': pos.get('mark_price')
                    })
                
                return {
                    'total_unrealized_pnl': total_unrealized_pnl,
                    'position_count': len(positions),
                    'positions': position_details
                }
            
            elif data_type == 'orders':
                return TradingService.get_open_orders(user_id=user_id)
            
            return None
            
        except Exception as e:
            logger.error(f"获取用户{user_id}的{data_type}数据失败: {e}")
            return None
    
    def _push_ticker_data(self):
        """推送行情数据"""
        if not self.ticker_subscribers:
            return
        
        # 获取所有需要推送的交易对
        symbols = list(self.ticker_subscribers.keys())
        
        for symbol in symbols:
            try:
                # 获取订阅该交易对的用户
                subscribers = self.ticker_subscribers.get(symbol, set()).copy()
                
                if not subscribers:
                    continue
                
                # 使用第一个用户的ID获取行情（行情数据对所有用户相同）
                user_id = next(iter(subscribers))
                
                if self.app:
                    with self.app.app_context():
                        ticker = TradingService.get_ticker(user_id=user_id, symbol=symbol)
                else:
                    ticker = TradingService.get_ticker(user_id=user_id, symbol=symbol)
                
                if ticker:
                    # 检查价格是否有变化
                    last_price = float(ticker.get('last_price', 0))
                    cached = self.ticker_cache.get(symbol, {})
                    cached_price = cached.get('last_price', 0)
                    
                    # 价格变化或超过5秒未更新，则推送
                    if last_price != cached_price or time.time() - cached.get('timestamp', 0) > 5:
                        # 更新缓存
                        self.ticker_cache[symbol] = {
                            'last_price': last_price,
                            'timestamp': time.time()
                        }
                        
                        # 推送给所有订阅该交易对的用户
                        for user_id in subscribers:
                            self._emit_ticker_update(user_id, symbol, ticker)
                
            except Exception as e:
                logger.error(f"推送{symbol}行情失败: {e}")
    
    def _emit_ticker_update(self, user_id: int, symbol: str, ticker: Dict[str, Any]):
        """发送行情更新事件"""
        try:
            room = f"ticker_{symbol}_{user_id}"
            event_name = "ticker_update"
            
            payload = {
                'type': event_name,
                'symbol': symbol,
                'data': ticker,
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id
            }
            
            print(f"📊 推送{symbol}行情给用户{user_id}")
            print(f"   价格: {ticker.get('last_price')}")
            print(f"   房间: {room}")
            
            try:
                self.socketio.emit(event_name, payload, room=room)
            except Exception as emit_error:
                if "write() before start_response" in str(emit_error) or "Broken pipe" in str(emit_error):
                    print(f"⚠️ 客户端可能已断开，跳过推送")
                else:
                    raise
            
        except Exception as e:
            if "write() before start_response" not in str(e) and "Broken pipe" not in str(e):
                print(f"❌ 发送{symbol}行情更新失败: {e}")
                logger.error(f"发送{symbol}行情更新失败: {e}")
    
    def _has_data_changed(self, user_id: int, data_type: str, new_data: Any) -> bool:
        """检查数据是否有变化"""
        if user_id not in self.data_cache:
            return True
        
        if data_type not in self.data_cache[user_id]:
            return True
        
        old_data = self.data_cache[user_id][data_type]
        
        # 简单的数据比较
        return str(new_data) != str(old_data)
    
    def _update_cache(self, user_id: int, data_type: str, data: Any):
        """更新数据缓存"""
        if user_id not in self.data_cache:
            self.data_cache[user_id] = {}
        
        self.data_cache[user_id][data_type] = data
    
    def _emit_data_update(self, user_id: int, data_type: str, data: Any):
        """发送数据更新事件"""
        try:
            room = f"{data_type}_{user_id}"
            event_name = f"{data_type}_update"
            
            payload = {
                'type': event_name,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id
            }
            
            print(f"📤 推送{data_type}数据给用户{user_id}")
            print(f"   数据内容: {payload}")
            print(f"   房间: {room}")
            
            try:
                self.socketio.emit(event_name, payload, room=room)
            except Exception as emit_error:
                # 客户端可能已断开，忽略此错误
                if "write() before start_response" in str(emit_error) or "Broken pipe" in str(emit_error):
                    print(f"⚠️ 客户端可能已断开，跳过推送")
                else:
                    raise
            
        except Exception as e:
            # 只记录非断开连接的错误
            if "write() before start_response" not in str(e) and "Broken pipe" not in str(e):
                print(f"❌ 发送{data_type}更新事件失败: {e}")
                logger.error(f"发送{data_type}更新事件失败: {e}")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            'running': self.running,
            'subscribers': {
                data_type: len(users) 
                for data_type, users in self.subscribers.items()
            },
            'cached_users': len(self.data_cache),
            'active_threads': len([t for t in self.threads.values() if t.is_alive()])
        }

# 全局交易WebSocket服务实例
trading_ws_service: Optional[TradingWebSocketService] = None

def init_trading_websocket_service(socketio: SocketIO, app=None) -> TradingWebSocketService:
    """初始化交易WebSocket服务"""
    global trading_ws_service
    trading_ws_service = TradingWebSocketService(socketio, app)
    return trading_ws_service

def get_trading_websocket_service() -> Optional[TradingWebSocketService]:
    """获取交易WebSocket服务实例"""
    return trading_ws_service
