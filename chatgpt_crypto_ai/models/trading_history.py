# -*- coding: utf-8 -*-
"""
交易历史相关数据库模型
包括历史盈亏、平仓记录等
"""
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, Float, Integer
from sqlalchemy.orm import relationship
from models import db

class TradingPnlHistory(db.Model):
    """历史盈亏记录表 - 记录每次平仓的盈亏情况"""
    __tablename__ = 'trading_pnl_history'
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    exchange = Column(String(50), nullable=False)  # bybit, binance等
    symbol = Column(String(50), nullable=False)    # BTCUSDT等
    side = Column(String(10), nullable=False)      # Buy, Sell
    
    # 开仓信息
    open_time = Column(DateTime, nullable=False)   # 开仓时间
    open_price = Column(Float, nullable=False)     # 开仓价格
    open_size = Column(Float, nullable=False)      # 开仓数量
    
    # 平仓信息
    close_time = Column(DateTime, nullable=False)  # 平仓时间
    close_price = Column(Float, nullable=False)    # 平仓价格
    close_size = Column(Float, nullable=False)     # 平仓数量
    
    # 盈亏信息
    realized_pnl = Column(Float, nullable=False)   # 已实现盈亏
    pnl_percentage = Column(Float, nullable=False) # 盈亏百分比
    fee = Column(Float, default=0.0)               # 手续费
    net_pnl = Column(Float, nullable=False)        # 净盈亏(扣除手续费)
    
    # 其他信息
    leverage = Column(Float, default=1.0)          # 杠杆倍数
    order_id = Column(String(100), nullable=True)  # 订单ID
    position_id = Column(String(100), nullable=True) # 持仓ID
    
    # 记录创建时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User")
    
    @classmethod
    def add_pnl_record(cls, user_id: int, exchange: str, symbol: str, side: str,
                      open_time: datetime, open_price: float, open_size: float,
                      close_time: datetime, close_price: float, close_size: float,
                      realized_pnl: float, fee: float = 0.0, leverage: float = 1.0,
                      order_id: str = None, position_id: str = None):
        """添加历史盈亏记录"""
        try:
            # 计算盈亏百分比
            if side.lower() == 'buy':
                pnl_percentage = ((close_price - open_price) / open_price) * 100 * leverage
            else:  # sell
                pnl_percentage = ((open_price - close_price) / open_price) * 100 * leverage
            
            # 计算净盈亏
            net_pnl = realized_pnl - fee
            
            record = cls(
                user_id=user_id,
                exchange=exchange,
                symbol=symbol,
                side=side,
                open_time=open_time,
                open_price=open_price,
                open_size=open_size,
                close_time=close_time,
                close_price=close_price,
                close_size=close_size,
                realized_pnl=realized_pnl,
                pnl_percentage=pnl_percentage,
                fee=fee,
                net_pnl=net_pnl,
                leverage=leverage,
                order_id=order_id,
                position_id=position_id
            )
            
            db.session.add(record)
            db.session.commit()
            
            return {"status": "success", "message": "盈亏记录已保存", "id": record.id}
            
        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": f"保存盈亏记录失败: {e}"}
    
    @classmethod
    def get_user_pnl_history(cls, user_id: int, limit: int = 50, offset: int = 0,
                            symbol: str = None, exchange: str = None,
                            start_date: datetime = None, end_date: datetime = None):
        """获取用户历史盈亏记录"""
        query = cls.query.filter_by(user_id=user_id)
        
        # 添加筛选条件
        if symbol:
            query = query.filter_by(symbol=symbol)
        if exchange:
            query = query.filter_by(exchange=exchange)
        if start_date:
            query = query.filter(cls.close_time >= start_date)
        if end_date:
            query = query.filter(cls.close_time <= end_date)
        
        # 按平仓时间倒序排列
        records = query.order_by(cls.close_time.desc()).offset(offset).limit(limit).all()
        
        return [cls._to_dict(record) for record in records]
    
    @classmethod
    def get_user_pnl_summary(cls, user_id: int, exchange: str = None, 
                           start_date: datetime = None, end_date: datetime = None):
        """获取用户盈亏汇总统计"""
        query = cls.query.filter_by(user_id=user_id)
        
        if exchange:
            query = query.filter_by(exchange=exchange)
        if start_date:
            query = query.filter(cls.close_time >= start_date)
        if end_date:
            query = query.filter(cls.close_time <= end_date)
        
        records = query.all()
        
        if not records:
            return {
                'total_trades': 0,
                'total_realized_pnl': 0.0,
                'total_net_pnl': 0.0,
                'total_fees': 0.0,
                'win_trades': 0,
                'lose_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'best_trade': 0.0,
                'worst_trade': 0.0
            }
        
        # 计算统计数据
        total_trades = len(records)
        total_realized_pnl = sum(r.realized_pnl for r in records)
        total_net_pnl = sum(r.net_pnl for r in records)
        total_fees = sum(r.fee for r in records)
        
        win_trades = [r for r in records if r.net_pnl > 0]
        lose_trades = [r for r in records if r.net_pnl < 0]
        
        win_count = len(win_trades)
        lose_count = len(lose_trades)
        win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0
        
        avg_win = sum(r.net_pnl for r in win_trades) / win_count if win_count > 0 else 0
        avg_loss = sum(r.net_pnl for r in lose_trades) / lose_count if lose_count > 0 else 0
        
        best_trade = max(r.net_pnl for r in records) if records else 0
        worst_trade = min(r.net_pnl for r in records) if records else 0
        
        return {
            'total_trades': total_trades,
            'total_realized_pnl': round(total_realized_pnl, 2),
            'total_net_pnl': round(total_net_pnl, 2),
            'total_fees': round(total_fees, 2),
            'win_trades': win_count,
            'lose_trades': lose_count,
            'win_rate': round(win_rate, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'best_trade': round(best_trade, 2),
            'worst_trade': round(worst_trade, 2)
        }
    
    @staticmethod
    def _to_dict(record):
        """将记录转换为字典"""
        return {
            'id': record.id,
            'exchange': record.exchange,
            'symbol': record.symbol,
            'side': record.side,
            'open_time': record.open_time.isoformat(),
            'open_price': record.open_price,
            'open_size': record.open_size,
            'close_time': record.close_time.isoformat(),
            'close_price': record.close_price,
            'close_size': record.close_size,
            'realized_pnl': record.realized_pnl,
            'pnl_percentage': round(record.pnl_percentage, 2),
            'fee': record.fee,
            'net_pnl': record.net_pnl,
            'leverage': record.leverage,
            'order_id': record.order_id,
            'position_id': record.position_id,
            'created_at': record.created_at.isoformat()
        }


class TradingOrderHistory(db.Model):
    """交易订单历史记录表 - 记录所有订单的详细信息"""
    __tablename__ = 'trading_order_history'
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    exchange = Column(String(50), nullable=False)
    
    # 订单基本信息
    order_id = Column(String(100), nullable=False, unique=True)
    symbol = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)      # Buy, Sell
    order_type = Column(String(20), nullable=False) # Market, Limit, Stop等
    
    # 价格和数量
    quantity = Column(Float, nullable=False)       # 订单数量
    price = Column(Float, nullable=True)           # 订单价格(市价单可为空)
    filled_quantity = Column(Float, default=0.0)   # 已成交数量
    avg_price = Column(Float, nullable=True)       # 平均成交价格
    
    # 订单状态
    status = Column(String(20), nullable=False)    # New, PartiallyFilled, Filled, Cancelled等
    
    # 时间信息
    order_time = Column(DateTime, nullable=False)  # 下单时间
    update_time = Column(DateTime, nullable=False) # 最后更新时间
    
    # 其他信息
    fee = Column(Float, default=0.0)               # 手续费
    leverage = Column(Float, default=1.0)          # 杠杆倍数
    
    # 记录创建时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User")
    
    @classmethod
    def add_or_update_order(cls, user_id: int, exchange: str, order_id: str,
                           symbol: str, side: str, order_type: str, quantity: float,
                           price: float = None, filled_quantity: float = 0.0,
                           avg_price: float = None, status: str = 'New',
                           order_time: datetime = None, update_time: datetime = None,
                           fee: float = 0.0, leverage: float = 1.0):
        """添加或更新订单记录"""
        try:
            # 查找是否已存在该订单
            existing_order = cls.query.filter_by(order_id=order_id).first()
            
            if existing_order:
                # 更新现有订单
                existing_order.filled_quantity = filled_quantity
                existing_order.avg_price = avg_price
                existing_order.status = status
                existing_order.update_time = update_time or datetime.utcnow()
                existing_order.fee = fee
                existing_order.updated_at = datetime.utcnow()
            else:
                # 创建新订单记录
                new_order = cls(
                    user_id=user_id,
                    exchange=exchange,
                    order_id=order_id,
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    price=price,
                    filled_quantity=filled_quantity,
                    avg_price=avg_price,
                    status=status,
                    order_time=order_time or datetime.utcnow(),
                    update_time=update_time or datetime.utcnow(),
                    fee=fee,
                    leverage=leverage
                )
                db.session.add(new_order)
            
            db.session.commit()
            return {"status": "success", "message": "订单记录已保存"}
            
        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": f"保存订单记录失败: {e}"}
    
    @classmethod
    def get_user_order_history(cls, user_id: int, limit: int = 50, offset: int = 0,
                              symbol: str = None, exchange: str = None, status: str = None):
        """获取用户订单历史"""
        query = cls.query.filter_by(user_id=user_id)
        
        if symbol:
            query = query.filter_by(symbol=symbol)
        if exchange:
            query = query.filter_by(exchange=exchange)
        if status:
            query = query.filter_by(status=status)
        
        records = query.order_by(cls.order_time.desc()).offset(offset).limit(limit).all()
        
        return [cls._to_dict(record) for record in records]
    
    @staticmethod
    def _to_dict(record):
        """将记录转换为字典"""
        return {
            'id': record.id,
            'exchange': record.exchange,
            'order_id': record.order_id,
            'symbol': record.symbol,
            'side': record.side,
            'order_type': record.order_type,
            'quantity': record.quantity,
            'price': record.price,
            'filled_quantity': record.filled_quantity,
            'avg_price': record.avg_price,
            'status': record.status,
            'order_time': record.order_time.isoformat(),
            'update_time': record.update_time.isoformat(),
            'fee': record.fee,
            'leverage': record.leverage,
            'created_at': record.created_at.isoformat()
        }
