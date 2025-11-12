# -*- coding: utf-8 -*-
"""
交易服务层
提供统一的交易接口，管理交易所连接
"""
from typing import Dict, List, Optional, Any
import logging
from exchanges.exchange_factory import ExchangeFactory
from exchanges.base_exchange import BaseExchange, OrderSide, PositionSide
import config

logger = logging.getLogger(__name__)


class TradingService:
    """交易服务"""
    
    # 缓存交易所实例（按用户ID缓存）
    _exchange_instances: Dict[str, BaseExchange] = {}
    
    @classmethod
    def clear_user_cache(cls, user_id: int, exchange_name: str = None):
        """
        清除用户的交易所实例缓存
        
        Args:
            user_id: 用户ID
            exchange_name: 交易所名称，如果为None则清除该用户的所有缓存
        """
        if exchange_name:
            # 清除特定交易所的缓存
            for testnet in [True, False]:
                cache_key = f"{user_id}_{exchange_name}_{testnet}"
                if cache_key in cls._exchange_instances:
                    del cls._exchange_instances[cache_key]
                    logger.info(f"清除用户{user_id}的{exchange_name}交易所缓存")
        else:
            # 清除该用户的所有缓存
            keys_to_remove = [k for k in cls._exchange_instances.keys() if k.startswith(f"{user_id}_")]
            for key in keys_to_remove:
                del cls._exchange_instances[key]
                logger.info(f"清除缓存: {key}")
    
    @classmethod
    def get_user_api_key(cls, user_id: int, exchange_name: str = 'bybit'):
        """
        获取用户的 API Key 配置
        
        Args:
            user_id: 用户ID
            exchange_name: 交易所名称
            
        Returns:
            ExchangeApiKey 或 None
        """
        from models import ExchangeApiKey
        
        return ExchangeApiKey.query.filter_by(
            user_id=user_id,
            exchange=exchange_name,
            is_active=1
        ).first()
    
    @classmethod
    def get_exchange(
        cls,
        user_id: int = None,
        exchange_name: str = None,
        api_key: str = None,
        api_secret: str = None,
        testnet: bool = None
    ) -> BaseExchange:
        """
        获取交易所实例
        
        Args:
            user_id: 用户ID（优先从数据库读取用户的 API Key）
            exchange_name: 交易所名称
            api_key: API Key（如果不提供，从数据库读取）
            api_secret: API Secret（如果不提供，从数据库读取）
            testnet: 是否测试网
            
        Returns:
            BaseExchange: 交易所实例
        """
        from models import ExchangeApiKey
        from cryptography.fernet import Fernet
        import os
        
        exchange_name = exchange_name or 'bybit'
        
        # 如果提供了 user_id，从数据库读取
        if user_id and not (api_key and api_secret):
            user_api_config = cls.get_user_api_key(user_id, exchange_name)
            if not user_api_config:
                raise Exception(f"用户未配置 {exchange_name} API Key，请先在设置中添加")
            
            # 解密 API Key
            encryption_key = os.getenv('ENCRYPTION_KEY', Fernet.generate_key().decode()).encode()
            f = Fernet(encryption_key)
            
            api_key = f.decrypt(user_api_config.api_key.encode()).decode()
            api_secret = f.decrypt(user_api_config.api_secret.encode()).decode()
            testnet = bool(user_api_config.testnet)
        
        # 如果没有提供任何参数，使用系统配置（仅用于测试）
        if not api_key or not api_secret:
            api_key = getattr(config, 'TRADING_API_KEY', '')
            api_secret = getattr(config, 'TRADING_API_SECRET', '')
            testnet = testnet if testnet is not None else getattr(config, 'TRADING_TESTNET', False)
            
            if not api_key or not api_secret:
                raise Exception("未配置 API Key，请提供 user_id 或配置系统级 API Key")
        
        # 缓存键（包含用户ID）
        cache_key = f"{user_id}_{exchange_name}_{testnet}" if user_id else f"system_{exchange_name}_{testnet}"
        
        # 如果已有实例，检查连接是否有效
        if cache_key in cls._exchange_instances:
            existing_instance = cls._exchange_instances[cache_key]
            # 验证连接是否仍然有效
            try:
                # 简单测试：尝试获取余额（如果失败说明连接已失效）
                if hasattr(existing_instance, 'client') and existing_instance.client:
                    logger.debug(f"使用缓存的交易所实例: {cache_key}")
                    return existing_instance
                else:
                    logger.info(f"缓存的交易所实例无效，重新创建: {cache_key}")
                    del cls._exchange_instances[cache_key]
            except Exception as e:
                logger.warning(f"缓存的交易所实例验证失败，重新创建: {e}")
                del cls._exchange_instances[cache_key]
        
        # 创建新实例
        exchange = ExchangeFactory.create_exchange(
            exchange_name=exchange_name,
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet
        )
        
        # 连接交易所
        if exchange.connect():
            cls._exchange_instances[cache_key] = exchange
            logger.info(f"用户 {user_id} 成功连接到 {exchange_name}")
            return exchange
        else:
            raise Exception(f"无法连接到 {exchange_name}")
    
    @classmethod
    def create_order(
        cls,
        user_id: int,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None,
        position_side: Optional[str] = None,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None,
        exchange_name: str = None
    ) -> Dict[str, Any]:
        """
        创建订单
        
        Args:
            user_id: 用户ID
            symbol: 交易对，如 "BTCUSDT"
            side: 方向 ("buy" 或 "sell")
            quantity: 数量
            order_type: 订单类型 ("market" 或 "limit")
            price: 价格（限价单必填）
            position_side: 持仓方向 ("long" 或 "short")，合约必填
            exchange_name: 交易所名称
            
        Returns:
            Dict: 订单信息
        """
        try:
            exchange = cls.get_exchange(user_id=user_id, exchange_name=exchange_name)
            
            # 转换参数
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
            pos_side = None
            if position_side:
                pos_side = PositionSide.LONG if position_side.lower() == "long" else PositionSide.SHORT
            
            # 根据订单类型调用不同方法
            if order_type.lower() == "market":
                result = exchange.create_market_order(
                    symbol=symbol,
                    side=order_side,
                    quantity=quantity,
                    position_side=pos_side,
                    take_profit=take_profit,
                    stop_loss=stop_loss
                )
            elif order_type.lower() == "limit":
                if price is None:
                    raise ValueError("限价单必须指定价格")
                result = exchange.create_limit_order(
                    symbol=symbol,
                    side=order_side,
                    quantity=quantity,
                    price=price,
                    position_side=pos_side,
                    take_profit=take_profit,
                    stop_loss=stop_loss
                )
            else:
                raise ValueError(f"不支持的订单类型: {order_type}")
            
            logger.info(f"创建订单成功: {result}")
            return result
            
        except Exception as e:
            logger.error(f"创建订单失败: {e}")
            raise
    
    @classmethod
    def cancel_order(
        cls,
        user_id: int,
        symbol: str,
        order_id: str,
        exchange_name: str = None
    ) -> Dict[str, Any]:
        """取消订单"""
        try:
            exchange = cls.get_exchange(user_id=user_id, exchange_name=exchange_name)
            result = exchange.cancel_order(symbol, order_id)
            logger.info(f"取消订单成功: {order_id}")
            return result
        except Exception as e:
            logger.error(f"取消订单失败: {e}")
            raise
    
    @classmethod
    def get_balance(
        cls,
        user_id: int,
        coin: str = "USDT",
        exchange_name: str = None
    ) -> Dict[str, Any]:
        """获取余额"""
        try:
            exchange = cls.get_exchange(user_id=user_id, exchange_name=exchange_name)
            return exchange.get_balance(coin)
        except Exception as e:
            logger.error(f"获取余额失败: {e}")
            raise
    
    @classmethod
    def get_positions(
        cls,
        user_id: int,
        symbol: Optional[str] = None,
        exchange_name: str = None
    ) -> List[Dict[str, Any]]:
        """获取持仓"""
        try:
            exchange = cls.get_exchange(user_id=user_id, exchange_name=exchange_name)
            return exchange.get_positions(symbol)
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            raise
    
    @classmethod
    def close_position(
        cls,
        user_id: int,
        symbol: str,
        position_side: str,
        exchange_name: str = None
    ) -> Dict[str, Any]:
        """平仓"""
        try:
            exchange = cls.get_exchange(user_id=user_id, exchange_name=exchange_name)
            
            # 获取平仓前的持仓信息
            positions = exchange.get_positions(symbol)
            position_data = None
            for pos in positions:
                if pos.get('side', '').lower() == position_side.lower():
                    position_data = pos
                    break
            
            # 执行平仓
            pos_side = PositionSide.LONG if position_side.lower() == "long" else PositionSide.SHORT
            result = exchange.close_position(symbol, pos_side)
            
            # 记录平仓到数据库
            if position_data and result.get('status') == 'success':
                try:
                    from services.trading_history_service import TradingHistoryService
                    from datetime import datetime
                    
                    close_price = float(result.get('price', 0))
                    close_size = float(position_data.get('size', 0))
                    
                    TradingHistoryService.record_position_close(
                        user_id=user_id,
                        exchange=exchange_name or 'bybit',
                        position_data=position_data,
                        close_price=close_price,
                        close_size=close_size,
                        close_time=datetime.utcnow()
                    )
                    logger.info(f"平仓记录已保存到数据库: {symbol} {position_side}")
                except Exception as e:
                    logger.error(f"保存平仓记录失败: {e}")
                    # 不影响平仓操作的成功返回
            
            logger.info(f"平仓成功: {symbol} {position_side}")
            return result
        except Exception as e:
            logger.error(f"平仓失败: {e}")
            raise
    
    @classmethod
    def set_leverage(
        cls,
        user_id: int,
        symbol: str,
        leverage: int,
        exchange_name: str = None
    ) -> Dict[str, Any]:
        """设置杠杆"""
        try:
            exchange = cls.get_exchange(user_id=user_id, exchange_name=exchange_name)
            result = exchange.set_leverage(symbol, leverage)
            logger.info(f"设置杠杆成功: {symbol} {leverage}x")
            return result
        except Exception as e:
            logger.error(f"设置杠杆失败: {e}")
            raise
    
    @classmethod
    def get_open_orders(
        cls,
        user_id: int,
        symbol: Optional[str] = None,
        exchange_name: str = None
    ) -> List[Dict[str, Any]]:
        """获取挂单"""
        try:
            exchange = cls.get_exchange(user_id=user_id, exchange_name=exchange_name)
            return exchange.get_open_orders(symbol)
        except Exception as e:
            logger.error(f"获取挂单失败: {e}")
            raise
    
    @classmethod
    def get_ticker(
        cls,
        user_id: int,
        symbol: str,
        exchange_name: str = None
    ) -> Dict[str, Any]:
        """获取行情"""
        try:
            exchange = cls.get_exchange(user_id=user_id, exchange_name=exchange_name)
            return exchange.get_ticker(symbol)
        except Exception as e:
            logger.error(f"获取行情失败: {e}")
            raise
