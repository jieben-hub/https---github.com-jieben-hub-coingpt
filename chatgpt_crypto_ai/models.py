# -*- coding: utf-8 -*-
"""
CoinGPT 数据库模型定义
"""
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class User(db.Model):
    """用户表"""
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String(100), unique=True, nullable=True)  # 添加用户名字段
    password = Column(String(255), nullable=True)  # 添加密码字段
    apple_sub = Column(String(255), unique=True, nullable=True)  # 改为可选，用户可以使用普通登录
    email = Column(String(255), unique=True, nullable=True)  # 新增邮箱字段
    is_active = Column(Integer, default=1, nullable=False)  # 新增激活字段，1为激活，0为未激活
    inviter_id = Column(BigInteger, ForeignKey('users.id'), nullable=True)
    membership = Column(String(50), default='free', nullable=False)
    dialog_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # 关系
    invitees = relationship("User", backref="inviter", remote_side=[id])
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    symbols = relationship("UserSymbol", back_populates="user", cascade="all, delete-orphan")
    exchange_api_keys = relationship("ExchangeApiKey", backref="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")

    def increment_dialog_count(self):
        """增加对话计数"""
        self.dialog_count += 1
        return self.dialog_count

class Session(db.Model):
    """会话表"""
    __tablename__ = 'sessions'
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_symbol = Column(String(50), nullable=True)
    
    # 关系
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    
    def update_last_symbol(self, symbol):
        """更新最后使用的币种"""
        self.last_symbol = symbol
        self.updated_at = datetime.utcnow()

class Message(db.Model):
    """消息表"""
    __tablename__ = 'messages'
    
    id = Column(BigInteger, primary_key=True)
    session_id = Column(BigInteger, ForeignKey('sessions.id'), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    session = relationship("Session", back_populates="messages")
    
    @classmethod
    def get_session_messages(cls, session_id, limit=10):
        """获取会话的最近消息"""
        return cls.query.filter_by(session_id=session_id).order_by(cls.created_at.desc()).limit(limit).all()

class UserSymbol(db.Model):
    """用户币种偏好表"""
    __tablename__ = 'user_symbols'
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    symbol = Column(String(50), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="symbols")
    
    @classmethod
    def add_symbol_for_user(cls, user_id, symbol):
        """为用户添加币种偏好，如果已存在则忽略"""
        exists = cls.query.filter_by(user_id=user_id, symbol=symbol).first()
        if not exists:
            new_symbol = cls(user_id=user_id, symbol=symbol)
            db.session.add(new_symbol)
            db.session.commit()
    
    @classmethod
    def get_user_symbols(cls, user_id, limit=5):
        """获取用户最近使用的币种"""
        return cls.query.filter_by(user_id=user_id).order_by(cls.added_at.desc()).limit(limit).all()


class SessionFeedback(db.Model):
    """会话评分表 - 存储用户对整个会话的评分"""
    __tablename__ = 'session_feedbacks'
    
    id = Column(BigInteger, primary_key=True)
    session_id = Column(BigInteger, ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5星评分
    feedback_text = Column(Text, nullable=True)  # 文字反馈，可选
    context = Column(Text, nullable=True)  # 存储为JSON字符串的上下文信息
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    session = relationship("Session")
    user = relationship("User")
    
    @classmethod
    def save_feedback(cls, session_id, user_id, rating, feedback_text=None, context=None):
        """保存会话评分到数据库"""
        try:
            # 验证评分范围
            if rating < 1 or rating > 5:
                return {"status": "error", "message": "评分必须在1-5之间"}
                
            # 将context转换为JSON字符串
            context_json = json.dumps(context) if context else None
            
            # 创建新的评分记录
            feedback = cls(
                session_id=session_id,
                user_id=user_id,
                rating=rating,
                feedback_text=feedback_text,
                context=context_json
            )
            
            db.session.add(feedback)
            db.session.commit()
            
            return {"status": "success", "message": "会话评分已保存", "id": feedback.id}
            
        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": f"保存会话评分失败: {e}"}


class MessageFeedback(db.Model):
    """消息评分表 - 存储用户对单条AI回复的评分"""
    __tablename__ = 'message_feedbacks'
    
    id = Column(BigInteger, primary_key=True)
    message_id = Column(BigInteger, ForeignKey('messages.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5星评分
    feedback_text = Column(Text, nullable=True)  # 文字反馈，可选
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    message = relationship("Message")
    user = relationship("User")
    
    @classmethod
    def save_feedback(cls, message_id, user_id, rating, feedback_text=None):
        """保存消息评分到数据库"""
        try:
            # 验证评分范围
            if rating < 1 or rating > 5:
                return {"status": "error", "message": "评分必须在1-5之间"}
            
            # 创建新的评分记录
            feedback = cls(
                message_id=message_id,
                user_id=user_id,
                rating=rating,
                feedback_text=feedback_text
            )
            
            db.session.add(feedback)
            db.session.commit()
            
            return {"status": "success", "message": "消息评分已保存", "id": feedback.id}
            
        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": f"保存消息评分失败: {e}"}


class FeedbackText(db.Model):
    """用户文字反馈表"""
    __tablename__ = 'feedback_texts'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class ExchangeApiKey(db.Model):
    """用户交易所 API Key 表"""
    __tablename__ = 'exchange_api_keys'
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    exchange = Column(String(50), nullable=False)  # bybit, binance, huobi
    api_key = Column(Text, nullable=False)  # 加密存储
    api_secret = Column(Text, nullable=False)  # 加密存储
    testnet = Column(Integer, default=1, nullable=False)  # 是否测试网，1=是，0=否
    is_active = Column(Integer, default=1, nullable=False)  # 是否启用，1=是，0=否
    nickname = Column(String(100), nullable=True)  # 用户自定义昵称
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TradingPnlHistory(db.Model):
    """历史盈亏记录表 - 记录每次平仓的盈亏情况"""
    __tablename__ = 'trading_pnl_history'
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)
    
    # 开仓信息
    open_time = Column(DateTime, nullable=False)
    open_price = Column(Float, nullable=False)
    open_size = Column(Float, nullable=False)
    
    # 平仓信息
    close_time = Column(DateTime, nullable=False)
    close_price = Column(Float, nullable=False)
    close_size = Column(Float, nullable=False)
    
    # 盈亏信息
    realized_pnl = Column(Float, nullable=False)
    pnl_percentage = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)
    net_pnl = Column(Float, nullable=False)
    
    # 其他信息
    leverage = Column(Float, default=1.0)
    order_id = Column(String(100), nullable=True)
    position_id = Column(String(100), nullable=True)
    
    # 记录创建时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User")


class TradingOrderHistory(db.Model):
    """交易订单历史记录表 - 记录所有订单的详细信息"""
    __tablename__ = 'trading_order_history'
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    exchange = Column(String(50), nullable=False)
    
    # 订单基本信息
    order_id = Column(String(100), nullable=False, unique=True)
    symbol = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)
    order_type = Column(String(20), nullable=False)
    
    # 价格和数量
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    filled_quantity = Column(Float, default=0.0)
    avg_price = Column(Float, nullable=True)
    
    # 订单状态
    status = Column(String(20), nullable=False)
    
    # 时间信息
    order_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)
    
    # 其他信息
    fee = Column(Float, default=0.0)
    leverage = Column(Float, default=1.0)
    
    # 记录创建时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User")


class Subscription(db.Model):
    """订阅记录表 - 记录用户的订阅信息"""
    __tablename__ = 'subscriptions'
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    
    # 产品信息
    product_id = Column(String(255), nullable=False)  # 如: dev.zonekit.coingpt.Premium.year
    product_type = Column(String(50), nullable=False)  # yearly, monthly
    
    # 交易信息
    transaction_id = Column(String(255), nullable=False, unique=True)  # App Store交易ID
    original_transaction_id = Column(String(255), nullable=False)  # 原始交易ID（用于识别同一订阅）
    
    # 时间信息
    purchase_date = Column(DateTime, nullable=False)  # 购买时间
    expires_date = Column(DateTime, nullable=False)   # 过期时间
    
    # 订阅状态
    status = Column(String(20), default='active', nullable=False)  # active, expired, cancelled
    is_trial_period = Column(Boolean, default=False)  # 是否试用期
    is_in_intro_offer_period = Column(Boolean, default=False)  # 是否优惠期
    
    # 自动续期
    auto_renew_status = Column(Boolean, default=True)  # 是否自动续期
    
    # 记录时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="subscriptions")
    
    def is_active(self):
        """检查订阅是否有效"""
        return self.status == 'active' and self.expires_date > datetime.utcnow()
    
    def days_until_expiry(self):
        """距离过期还有多少天"""
        if self.expires_date > datetime.utcnow():
            return (self.expires_date - datetime.utcnow()).days
        return 0
