# -*- coding: utf-8 -*-
"""
Bybit 交易所适配器
使用 pybit 库实现
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal, ROUND_DOWN
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
        self._instrument_info_cache: Dict[str, Dict[str, Decimal]] = {}
    
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

    @staticmethod
    def _to_decimal(value: Any, default: str) -> Decimal:
        try:
            if value in (None, ""):
                return Decimal(default)
            return Decimal(str(value))
        except (ArithmeticError, ValueError, TypeError):
            return Decimal(default)

    @staticmethod
    def _decimal_to_string(value: Decimal) -> str:
        normalized = value.normalize()
        text = format(normalized, 'f')
        if '.' in text:
            text = text.rstrip('0').rstrip('.')
        return text or '0'

    def _get_symbol_filters(self, symbol: str) -> Dict[str, Decimal]:
        symbol_key = symbol.upper()
        if symbol_key in self._instrument_info_cache:
            return self._instrument_info_cache[symbol_key]

        try:
            response = self.client.get_instruments_info(
                category="linear",
                symbol=symbol_key
            )
        except Exception as exc:
            logger.error(f"获取 {symbol_key} 交易规则失败: {exc}")
            raise

        if response.get('retCode') != 0 or not response.get('result', {}).get('list'):
            raise Exception(f"获取 {symbol_key} 交易规则失败: {response.get('retMsg')}")

        info = response['result']['list'][0]
        lot_filter = info.get('lotSizeFilter', {}) or {}
        price_filter = info.get('priceFilter', {}) or {}

        qty_step = self._to_decimal(lot_filter.get('qtyStep'), '1')
        if qty_step <= 0:
            qty_step = Decimal('1')

        tick_size = self._to_decimal(price_filter.get('tickSize'), '0.1')
        if tick_size <= 0:
            tick_size = Decimal('0.1')

        filters: Dict[str, Decimal] = {
            'qty_step': qty_step,
            'min_qty': self._to_decimal(lot_filter.get('minOrderQty'), '0'),
            'max_qty': self._to_decimal(lot_filter.get('maxOrderQty'), '0'),
            'tick_size': tick_size,
            'min_price': self._to_decimal(price_filter.get('minPrice'), '0'),
            'max_price': self._to_decimal(price_filter.get('maxPrice'), '0'),
        }

        self._instrument_info_cache[symbol_key] = filters
        return filters

    def _normalize_to_step(
        self,
        symbol: str,
        value: Decimal,
        step: Decimal,
        min_value: Decimal,
        max_value: Decimal,
        label: str
    ) -> Decimal:
        if value is None:
            raise ValueError(f"{label}不能为空")

        if step <= 0:
            step = Decimal('1')

        if value <= 0:
            raise ValueError(f"{label}必须大于0")

        normalized = (value / step).to_integral_value(rounding=ROUND_DOWN) * step
        normalized = normalized.quantize(step, rounding=ROUND_DOWN)

        if min_value > 0 and normalized < min_value:
            raise ValueError(f"{symbol} {label} {normalized} 小于最小允许值 {min_value}")

        if max_value > 0 and normalized > max_value:
            raise ValueError(f"{symbol} {label} {normalized} 超过最大允许值 {max_value}")

        if normalized <= 0:
            raise ValueError(f"{label}归一化后必须大于0")

        if normalized != value:
            logger.info(f"{symbol} {label} 调整: 原始 {value} -> {normalized}")

        return normalized

    def _format_quantity(self, symbol: str, quantity: float) -> (str, float):
        filters = self._get_symbol_filters(symbol)
        normalized = self._normalize_to_step(
            symbol,
            Decimal(str(quantity)),
            filters['qty_step'],
            filters['min_qty'],
            filters['max_qty'],
            "数量"
        )
        return self._decimal_to_string(normalized), float(normalized)

    def _format_price(self, symbol: str, price: float) -> (str, float):
        filters = self._get_symbol_filters(symbol)
        normalized = self._normalize_to_step(
            symbol,
            Decimal(str(price)),
            filters['tick_size'],
            filters['min_price'],
            filters['max_price'],
            "价格"
        )
        return self._decimal_to_string(normalized), float(normalized)

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
        position_side: Optional[PositionSide] = None,
        position_idx: Optional[int] = None,
        reduce_only: bool = False,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None
    ) -> Dict[str, Any]:
        """创建市价单"""
        try:
            qty_str, normalized_qty = self._format_quantity(symbol, quantity)
            # Bybit 参数映射
            order_params = {
                "category": "linear",  # 线性合约
                "symbol": symbol,
                "side": side.value,
                "orderType": "Market",
                "qty": qty_str,
            }
            
            # 根据模式设置 positionIdx
            if position_idx is not None:
                order_params["positionIdx"] = position_idx
            elif position_side is not None:
                # 如果没有明确提供，根据方向推断（默认单向持仓）
                order_params["positionIdx"] = 1 if position_side == PositionSide.LONG else 2

            if reduce_only:
                order_params["reduceOnly"] = True

            if take_profit is not None:
                tp_str, _ = self._format_price(symbol, take_profit)
                order_params["takeProfit"] = tp_str
                order_params["tpTriggerBy"] = "LastPrice"

            if stop_loss is not None:
                sl_str, _ = self._format_price(symbol, stop_loss)
                order_params["stopLoss"] = sl_str
                order_params["slTriggerBy"] = "LastPrice"
            
            result = self.client.place_order(**order_params)
            
            if result['retCode'] == 0:
                order_data = result['result']
                return {
                    'order_id': order_data['orderId'],
                    'symbol': symbol,
                    'side': side.value,
                    'quantity': normalized_qty,
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
        position_side: Optional[PositionSide] = None,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None
    ) -> Dict[str, Any]:
        """创建限价单"""
        try:
            qty_str, normalized_qty = self._format_quantity(symbol, quantity)
            price_str, normalized_price = self._format_price(symbol, price)
            order_params = {
                "category": "linear",
                "symbol": symbol,
                "side": side.value,
                "orderType": "Limit",
                "qty": qty_str,
                "price": price_str,
            }

            if take_profit is not None:
                tp_str, _ = self._format_price(symbol, take_profit)
                order_params["takeProfit"] = tp_str
                order_params["tpTriggerBy"] = "LastPrice"

            if stop_loss is not None:
                sl_str, _ = self._format_price(symbol, stop_loss)
                order_params["stopLoss"] = sl_str
                order_params["slTriggerBy"] = "LastPrice"

            result = self.client.place_order(**order_params)

            if result['retCode'] == 0:
                order_data = result['result']
                return {
                    'order_id': order_data['orderId'],
                    'symbol': symbol,
                    'side': side.value,
                    'quantity': normalized_qty,
                    'price': normalized_price,
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
                            'leverage': safe_float(pos.get('leverage')),
                            'position_idx': int(pos.get('positionIdx', 0))
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
            
            side_key = 'Buy' if position_side == PositionSide.LONG else 'Sell'
            position = next((pos for pos in positions if pos.get('side') == side_key), None)

            if not position:
                raise Exception(f"未找到 {symbol} 的{side_key}持仓")
            size = position['size']
            
            # 平仓方向与持仓方向相反
            close_side = OrderSide.SELL if position_side == PositionSide.LONG else OrderSide.BUY
            position_idx = position.get('position_idx')
            
            # 使用市价单平仓
            return self.create_market_order(
                symbol=symbol,
                side=close_side,
                quantity=size,
                position_side=position_side,
                position_idx=position_idx,
                reduce_only=True
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
    
    def get_closed_pnl(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[Any] = None,
        end_time: Optional[Any] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取已平仓盈亏记录
        
        Args:
            symbol: 交易对（可选）
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
            
        Returns:
            List[Dict]: 平仓记录列表
        """
        try:
            from datetime import datetime
            
            params = {
                "category": "linear",
                "limit": limit
            }
            
            if symbol:
                params["symbol"] = symbol
            
            # 转换时间为毫秒时间戳
            if start_time:
                if isinstance(start_time, datetime):
                    params["startTime"] = int(start_time.timestamp() * 1000)
                else:
                    params["startTime"] = int(start_time)
            
            if end_time:
                if isinstance(end_time, datetime):
                    params["endTime"] = int(end_time.timestamp() * 1000)
                else:
                    params["endTime"] = int(end_time)
            
            logger.info(f"获取已平仓盈亏记录: {params}")
            
            # 分页获取所有记录
            all_pnl_list = []
            cursor = None
            
            while True:
                if cursor:
                    params["cursor"] = cursor
                
                response = self.client.get_closed_pnl(**params)
                
                if response["retCode"] != 0:
                    raise Exception(f"获取平仓记录失败: {response['retMsg']}")
                
                result = response["result"]
                pnl_list = result.get("list", [])
                all_pnl_list.extend(pnl_list)
                
                # 检查是否还有更多数据
                cursor = result.get("nextPageCursor")
                if not cursor or len(pnl_list) == 0:
                    break
                
                logger.debug(f"继续获取下一页，cursor={cursor}")
            
            logger.info(f"获取到{len(all_pnl_list)}条平仓记录")
            
            return all_pnl_list
            
        except Exception as e:
            logger.error(f"获取平仓记录失败: {e}")
            raise
    
    def get_order_history(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[Any] = None,
        end_time: Optional[Any] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取订单历史
        
        Args:
            symbol: 交易对（可选）
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
            
        Returns:
            List[Dict]: 订单列表
        """
        try:
            from datetime import datetime
            
            params = {
                "category": "linear",
                "limit": limit
            }
            
            if symbol:
                params["symbol"] = symbol
            
            # 转换时间为毫秒时间戳
            if start_time:
                if isinstance(start_time, datetime):
                    params["startTime"] = int(start_time.timestamp() * 1000)
                else:
                    params["startTime"] = int(start_time)
            
            if end_time:
                if isinstance(end_time, datetime):
                    params["endTime"] = int(end_time.timestamp() * 1000)
                else:
                    params["endTime"] = int(end_time)
            
            logger.info(f"获取订单历史: {params}")
            
            # 分页获取所有记录
            all_orders = []
            cursor = None
            
            while True:
                if cursor:
                    params["cursor"] = cursor
                
                response = self.client.get_order_history(**params)
                
                if response["retCode"] != 0:
                    raise Exception(f"获取订单历史失败: {response['retMsg']}")
                
                result = response["result"]
                orders = result.get("list", [])
                all_orders.extend(orders)
                
                # 检查是否还有更多数据
                cursor = result.get("nextPageCursor")
                if not cursor or len(orders) == 0:
                    break
                
                logger.debug(f"继续获取下一页订单，cursor={cursor}")
            
            logger.info(f"获取到{len(all_orders)}条订单记录")
            
            return all_orders
            
        except Exception as e:
            logger.error(f"获取订单历史失败: {e}")
            raise
