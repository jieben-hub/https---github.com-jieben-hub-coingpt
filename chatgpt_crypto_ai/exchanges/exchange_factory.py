# -*- coding: utf-8 -*-
"""
交易所工厂类
根据配置创建对应的交易所实例
"""
from typing import Optional
from .base_exchange import BaseExchange
from .bybit_exchange import BybitExchange
import logging

logger = logging.getLogger(__name__)


class ExchangeFactory:
    """交易所工厂"""
    
    # 支持的交易所映射
    EXCHANGES = {
        'bybit': BybitExchange,
        # 'binance': BinanceExchange,  # 未来添加
        # 'huobi': HuobiExchange,      # 未来添加
        # 'okx': OKXExchange,          # 未来添加
    }
    
    @classmethod
    def create_exchange(
        cls,
        exchange_name: str,
        api_key: str,
        api_secret: str,
        testnet: bool = False
    ) -> BaseExchange:
        """
        创建交易所实例
        
        Args:
            exchange_name: 交易所名称 ('bybit', 'binance', 'huobi')
            api_key: API Key
            api_secret: API Secret
            testnet: 是否使用测试网
            
        Returns:
            BaseExchange: 交易所实例
            
        Raises:
            ValueError: 不支持的交易所
        """
        exchange_name = exchange_name.lower()
        
        if exchange_name not in cls.EXCHANGES:
            supported = ', '.join(cls.EXCHANGES.keys())
            raise ValueError(
                f"不支持的交易所: {exchange_name}。"
                f"支持的交易所: {supported}"
            )
        
        exchange_class = cls.EXCHANGES[exchange_name]
        exchange = exchange_class(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet
        )
        
        logger.info(f"创建 {exchange_name} 交易所实例")
        return exchange
    
    @classmethod
    def get_supported_exchanges(cls) -> list:
        """
        获取支持的交易所列表
        
        Returns:
            list: 交易所名称列表
        """
        return list(cls.EXCHANGES.keys())
    
    @classmethod
    def is_supported(cls, exchange_name: str) -> bool:
        """
        检查是否支持该交易所
        
        Args:
            exchange_name: 交易所名称
            
        Returns:
            bool: 是否支持
        """
        return exchange_name.lower() in cls.EXCHANGES
