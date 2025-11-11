# -*- coding: utf-8 -*-
"""
用户交易所 API Key 模型
"""
from datetime import datetime
from models import db
from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Boolean, Text
from cryptography.fernet import Fernet
import os


class ExchangeApiKey(db.Model):
    """用户交易所 API Key 表"""
    __tablename__ = 'exchange_api_keys'
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    exchange = Column(String(50), nullable=False)  # bybit, binance, huobi
    api_key = Column(Text, nullable=False)  # 加密存储
    api_secret = Column(Text, nullable=False)  # 加密存储
    testnet = Column(Boolean, default=True, nullable=False)  # 是否测试网
    is_active = Column(Boolean, default=True, nullable=False)  # 是否启用
    nickname = Column(String(100), nullable=True)  # 用户自定义昵称，如"我的主账户"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 加密密钥（应该从环境变量读取）
    _encryption_key = None
    
    @classmethod
    def get_encryption_key(cls):
        """获取加密密钥"""
        if cls._encryption_key is None:
            key = os.getenv('ENCRYPTION_KEY')
            if not key:
                # 如果没有配置，生成一个新的（仅用于开发）
                key = Fernet.generate_key().decode()
                print(f"⚠️  警告：未配置 ENCRYPTION_KEY，使用临时密钥: {key}")
            cls._encryption_key = key.encode() if isinstance(key, str) else key
        return cls._encryption_key
    
    def encrypt_value(self, value: str) -> str:
        """加密值"""
        f = Fernet(self.get_encryption_key())
        return f.encrypt(value.encode()).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """解密值"""
        f = Fernet(self.get_encryption_key())
        return f.decrypt(encrypted_value.encode()).decode()
    
    def set_api_key(self, api_key: str):
        """设置 API Key（自动加密）"""
        self.api_key = self.encrypt_value(api_key)
    
    def get_api_key(self) -> str:
        """获取 API Key（自动解密）"""
        return self.decrypt_value(self.api_key)
    
    def set_api_secret(self, api_secret: str):
        """设置 API Secret（自动加密）"""
        self.api_secret = self.encrypt_value(api_secret)
    
    def get_api_secret(self) -> str:
        """获取 API Secret（自动解密）"""
        return self.decrypt_value(self.api_secret)
    
    def to_dict(self):
        """转换为字典（不包含敏感信息）"""
        return {
            'id': self.id,
            'exchange': self.exchange,
            'testnet': self.testnet,
            'is_active': self.is_active,
            'nickname': self.nickname,
            'api_key_preview': self.get_api_key()[:10] + '...' if self.api_key else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
