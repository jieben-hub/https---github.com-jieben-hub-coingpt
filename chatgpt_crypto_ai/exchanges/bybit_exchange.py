# -*- coding: utf-8 -*-
"""
Bybit 交易所适配器
使用 pybit 库实现
"""
from typing import Dict, List, Optional, Any
from pybit.unified_trading import HTTP
import logging
import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from utils.api_rate_limiter import with_rate_limit, rate_limiter
from utils.data_converter import safe_float, safe_str

from .base_exchange import (
    BaseExchange,
    OrderSide,
    OrderType,
    PositionSide
)

logger = logging.getLogger(__name__)


class BybitExchange(BaseExchange):
    """Bybit 交易所实现"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        self.client = None
        self.time_offset = 0  # 与服务器的时间偏移量
    
    def _sync_server_time(self) -> bool:
        """同步服务器时间"""
        try:
            # 获取Bybit服务器时间
            base_url = "https://api-testnet.bybit.com" if self.testnet else "https://api.bybit.com"
            response = requests.get(f"{base_url}/v5/market/time", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('retCode') == 0:
                    server_time = int(data['result']['timeSecond']) * 1000  # 转换为毫秒
                    local_time = int(time.time() * 1000)
                    self.time_offset = server_time - local_time
                    
                    logger.info(f"时间同步成功，偏移量: {self.time_offset}ms")
                    return True
            
            logger.warning("无法获取服务器时间，使用本地时间")
            return False
            
        except Exception as e:
            logger.warning(f"时间同步失败: {e}，使用本地时间")
            return False
    
    def connect(self) -> bool:
        """连接到 Bybit"""
        try:
            # 先同步时间
            self._sync_server_time()
            
            # 创建客户端时设置更大的recv_window
            self.client = HTTP(
                testnet=self.testnet,
                api_key=self.api_key,
                api_secret=self.api_secret,
                recv_window=10000  # 增加到10秒
            )
            
            # 测试连接
            result = self.client.get_wallet_balance(accountType="UNIFIED")
            
            if result['retCode'] == 0:
                logger.info(f"成功连接到 Bybit {'测试网' if self.testnet else '主网'}")
                return True
            else:
                logger.error(f"连接 Bybit 失败: {result['retMsg']}")
                return False
                
        except Exception as e:
            logger.error(f"连接 Bybit 异常: {e}")
            # 如果是时间戳错误，尝试重新同步时间
            if "timestamp" in str(e).lower() or "recv_window" in str(e).lower():
                logger.info("检测到时间戳问题，尝试重新同步...")
                self._sync_server_time()
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    @with_rate_limit('bybit', 'get_wallet_balance')
    def _get_wallet_balance_with_retry(self, account_type: str, coin: str) -> Dict[str, Any]:
        """带重试的获取钱包余额内部方法"""
        try:
            result = self.client.get_wallet_balance(
                accountType=account_type,
                coin=coin
            )
            return result
        except Exception as e:
            if "Retryable error occurred" in str(e):
                logger.warning(f"Bybit API 重试错误，等待重试: {e}")
                time.sleep(1)
            raise e
    
    def get_balance(self, coin: str = "USDT") -> Dict[str, Any]:
        """获取账户余额"""
        try:
            result = self._get_wallet_balance_with_retry("UNIFIED", coin)
            
            if result['retCode'] == 0:
                coins = result['result']['list'][0]['coin']
                for c in coins:
                    if c['coin'] == coin:
                        return {
                            'coin': coin,
                            'available': safe_float(c.get('availableToWithdraw')),
                            'total': safe_float(c.get('walletBalance')),
                            'equity': safe_float(c.get('equity'))
                        }
            
            return {'coin': coin, 'available': 0.0, 'total': 0.0}
            
        except Exception as e:
            logger.error(f"获取余额失败: {e}")
            if "Retryable error occurred" in str(e):
                raise Exception("Bybit API 暂时不可用，请稍后重试")
            raise
    
    def create_market_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        position_side: Optional[PositionSide] = None
    ) -> Dict[str, Any]:
        """创建市价单"""
        try:
            # Bybit 参数映射
            order_params = {
                "category": "linear",  # 线性合约
                "symbol": symbol,
                "side": side.value,
                "orderType": "Market",
                "qty": str(quantity),
            }
            
            # 不设置positionIdx，让Bybit根据账户设置自动处理
            # 这样可以兼容单向持仓和双向持仓两种模式
            # if position_side:
            #     order_params["positionIdx"] = 1 if position_side == PositionSide.LONG else 2
            
            result = self.client.place_order(**order_params)
            
            if result['retCode'] == 0:
                order_data = result['result']
                return {
                    'order_id': order_data['orderId'],
                    'symbol': symbol,
                    'side': side.value,
                    'quantity': quantity,
                    'order_type': 'Market',
                    'status': 'Created',
                    'position_side': position_side.value if position_side else None
                }
            else:
                raise Exception(f"下单失败: {result['retMsg']}")
                
        except Exception as e:
            logger.error(f"创建市价单失败: {e}")
            raise
    
    def create_limit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: float,
        position_side: Optional[PositionSide] = None
    ) -> Dict[str, Any]:
        """创建限价单"""
        try:
            order_params = {
                "category": "linear",
                "symbol": symbol,
                "side": side.value,
                "orderType": "Limit",
                "qty": str(quantity),
                "price": str(price),
            }
            
            # 不设置positionIdx，让Bybit根据账户设置自动处理
            # if position_side:
            #     order_params["positionIdx"] = 1 if position_side == PositionSide.LONG else 2
            
            result = self.client.place_order(**order_params)
            
            if result['retCode'] == 0:
                order_data = result['result']
                return {
                    'order_id': order_data['orderId'],
                    'symbol': symbol,
                    'side': side.value,
                    'quantity': quantity,
                    'price': price,
                    'order_type': 'Limit',
                    'status': 'Created',
                    'position_side': position_side.value if position_side else None
                }
            else:
                raise Exception(f"下单失败: {result['retMsg']}")
                
        except Exception as e:
            logger.error(f"创建限价单失败: {e}")
            raise
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """取消订单"""
        try:
            result = self.client.cancel_order(
                category="linear",
                symbol=symbol,
                orderId=order_id
            )
            
            if result['retCode'] == 0:
                return {
                    'order_id': order_id,
                    'status': 'Cancelled'
                }
            else:
                raise Exception(f"取消订单失败: {result['retMsg']}")
                
        except Exception as e:
            logger.error(f"取消订单失败: {e}")
            raise
    
    def get_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """查询订单"""
        try:
            result = self.client.get_order_history(
                category="linear",
                symbol=symbol,
                orderId=order_id
            )
            
            if result['retCode'] == 0 and result['result']['list']:
                order = result['result']['list'][0]
                return {
                    'order_id': order['orderId'],
                    'symbol': order['symbol'],
                    'side': order['side'],
                    'quantity': float(order['qty']),
                    'price': float(order['price']) if order['price'] else None,
                    'status': order['orderStatus'],
                    'filled_quantity': float(order['cumExecQty']),
                    'avg_price': float(order['avgPrice']) if order['avgPrice'] else None
                }
            else:
                raise Exception(f"查询订单失败: {result['retMsg']}")
                
        except Exception as e:
            logger.error(f"查询订单失败: {e}")
            raise
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取当前挂单"""
        try:
            params = {"category": "linear"}
            if symbol:
                params["symbol"] = symbol
            else:
                # Bybit要求必须提供symbol、settleCoin或baseCoin之一
                # 如果没有指定symbol，使用settleCoin=USDT获取所有USDT合约的挂单
                params["settleCoin"] = "USDT"
            
            result = self.client.get_open_orders(**params)
            
            if result['retCode'] == 0:
                orders = []
                for order in result['result']['list']:
                    orders.append({
                        'order_id': order['orderId'],
                        'symbol': order['symbol'],
                        'side': order['side'],
                        'quantity': float(order['qty']),
                        'price': float(order['price']) if order['price'] else None,
                        'status': order['orderStatus']
                    })
                return orders
            else:
                raise Exception(f"获取挂单失败: {result['retMsg']}")
                
        except Exception as e:
            logger.error(f"获取挂单失败: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    @with_rate_limit('bybit', 'get_positions')
    def _get_positions_with_retry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """带重试的获取持仓内部方法"""
        try:
            result = self.client.get_positions(**params)
            return result
        except Exception as e:
            if "Retryable error occurred" in str(e):
                logger.warning(f"Bybit API 重试错误，等待重试: {e}")
                time.sleep(1)  # 额外等待
            raise e
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取持仓"""
        try:
            params = {"category": "linear", "settleCoin": "USDT"}
            if symbol:
                params["symbol"] = symbol
            
            result = self._get_positions_with_retry(params)
            
            if result['retCode'] == 0:
                positions = []
                for pos in result['result']['list']:
                    # 只返回有持仓的
                    size = safe_float(pos.get('size'))
                    if size > 0:
                        positions.append({
                            'symbol': safe_str(pos.get('symbol')),
                            'side': safe_str(pos.get('side')),
                            'size': size,
                            'entry_price': safe_float(pos.get('avgPrice')),
                            'mark_price': safe_float(pos.get('markPrice')),
                            'unrealized_pnl': safe_float(pos.get('unrealisedPnl')),
                            'leverage': safe_float(pos.get('leverage'))
                        })
                return positions
            else:
                raise Exception(f"获取持仓失败: {result['retMsg']}")
                
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            # 如果是重试错误，提供更友好的错误信息
            if "Retryable error occurred" in str(e):
                raise Exception("Bybit API 暂时不可用，请稍后重试")
            raise
    
    def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """设置杠杆"""
        try:
            result = self.client.set_leverage(
                category="linear",
                symbol=symbol,
                buyLeverage=str(leverage),
                sellLeverage=str(leverage)
            )
            
            if result['retCode'] == 0:
                return {
                    'symbol': symbol,
                    'leverage': leverage,
                    'status': 'Success'
                }
            else:
                raise Exception(f"设置杠杆失败: {result['retMsg']}")
                
        except Exception as e:
            logger.error(f"设置杠杆失败: {e}")
            raise
    
    def close_position(
        self,
        symbol: str,
        position_side: PositionSide
    ) -> Dict[str, Any]:
        """平仓"""
        try:
            # 先获取持仓信息
            positions = self.get_positions(symbol)
            
            if not positions:
                raise Exception(f"没有找到 {symbol} 的持仓")
            
            position = positions[0]
            size = position['size']
            
            # 平仓方向与持仓方向相反
            close_side = OrderSide.SELL if position_side == PositionSide.LONG else OrderSide.BUY
            
            # 使用市价单平仓
            return self.create_market_order(
                symbol=symbol,
                side=close_side,
                quantity=size,
                position_side=position_side
            )
                
        except Exception as e:
            logger.error(f"平仓失败: {e}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取行情
        
        Args:
            symbol: 交易对，如 BTCUSDT
            
        Returns:
            Dict: 行情数据
        """
        try:
            response = self.client.get_tickers(
                category="linear",
                symbol=symbol
            )
            
            if response["retCode"] != 0:
                raise Exception(f"获取行情失败: {response['retMsg']}")
            
            ticker_list = response["result"]["list"]
            if not ticker_list:
                raise Exception(f"未找到{symbol}的行情数据")
            
            ticker = ticker_list[0]
            
            # 使用当前时间作为时间戳
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            
            return {
                "symbol": ticker["symbol"],
                "last_price": float(ticker["lastPrice"]),
                "bid_price": float(ticker["bid1Price"]),
                "ask_price": float(ticker["ask1Price"]),
                "high_24h": float(ticker["highPrice24h"]),
                "low_24h": float(ticker["lowPrice24h"]),
                "volume_24h": float(ticker["volume24h"]),
                "change_24h": float(ticker["price24hPcnt"]) * 100,  # 转换为百分比
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"获取行情失败: {e}")
            raise
