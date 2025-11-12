# -*- coding: utf-8 -*-
"""
交易所抽象基类
定义所有交易所必须实现的接口
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum


class OrderSide(Enum):
    """订单方向"""
    BUY = "Buy"
    SELL = "Sell"


class OrderType(Enum):
    """订单类型"""
    MARKET = "Market"  # 市价单
    LIMIT = "Limit"    # 限价单


class PositionSide(Enum):
    """持仓方向（合约）"""
    LONG = "Long"   # 做多
    SHORT = "Short"  # 做空


class BaseExchange(ABC):
    """
    交易所基类
    所有交易所适配器必须继承此类并实现所有抽象方法
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        初始化交易所
        
        Args:
            api_key: API Key
            api_secret: API Secret
            testnet: 是否使用测试网
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.client = None
    
    @abstractmethod
    def connect(self) -> bool:
        """
        连接到交易所
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def get_balance(self, coin: str = "USDT") -> Dict[str, Any]:
        """
        获取账户余额
        
        Args:
            coin: 币种，默认 USDT
            
        Returns:
            Dict: {
                'coin': 'USDT',
                'available': 1000.0,
                'total': 1000.0
            }
        """
        pass
    
    @abstractmethod
    def create_market_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        position_side: Optional[PositionSide] = None,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        创建市价单
        
        Args:
            symbol: 交易对，如 "BTCUSDT"
            side: 订单方向 (BUY/SELL)
            quantity: 数量
            position_side: 持仓方向 (LONG/SHORT)，合约必填
            
        Returns:
            Dict: {
                'order_id': '123456',
                'symbol': 'BTCUSDT',
                'side': 'Buy',
                'quantity': 0.001,
                'price': 50000.0,
                'status': 'Filled'
            }
        """
        pass
    
    @abstractmethod
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
        """
        创建限价单
        
        Args:
            symbol: 交易对
            side: 订单方向
            quantity: 数量
            price: 价格
            position_side: 持仓方向（合约）
            
        Returns:
            Dict: 订单信息
        """
        pass
    
    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        取消订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            Dict: 取消结果
        """
        pass
    
    @abstractmethod
    def get_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        查询订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            Dict: 订单详情
        """
        pass
    
    @abstractmethod
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取当前挂单
        
        Args:
            symbol: 交易对，不传则返回所有
            
        Returns:
            List[Dict]: 订单列表
        """
        pass
    
    @abstractmethod
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取持仓（合约）
        
        Args:
            symbol: 交易对，不传则返回所有
            
        Returns:
            List[Dict]: 持仓列表
        """
        pass
    
    @abstractmethod
    def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """
        设置杠杆（合约）
        
        Args:
            symbol: 交易对
            leverage: 杠杆倍数
            
        Returns:
            Dict: 设置结果
        """
        pass
    
    @abstractmethod
    def close_position(
        self,
        symbol: str,
        position_side: PositionSide
    ) -> Dict[str, Any]:
        """
        平仓（合约）
        
        Args:
            symbol: 交易对
            position_side: 持仓方向
            
        Returns:
            Dict: 平仓结果
        """
        pass
    
    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取行情
        
        Args:
            symbol: 交易对
            
        Returns:
            Dict: 行情数据
        """
        pass
    
    def get_exchange_name(self) -> str:
        """
        获取交易所名称
        
        Returns:
            str: 交易所名称
        """
        return self.__class__.__name__.replace('Exchange', '')
