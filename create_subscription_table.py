# -*- coding: utf-8 -*-
"""
直接创建订阅表的脚本
如果Flask-Migrate有问题，可以使用这个脚本直接创建表
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'chatgpt_crypto_ai'))

from app import create_app
from models import db, Subscription

def create_subscription_table():
    """创建订阅表"""
    app = create_app()
    
    with app.app_context():
        # 检查表是否已存在
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        if 'subscriptions' in inspector.get_table_names():
            print("✅ subscriptions 表已存在")
            return
        
        print("📊 开始创建 subscriptions 表...")
        
        # 创建表
        Subscription.__table__.create(db.engine)
        
        print("✅ subscriptions 表创建成功！")
        
        # 验证表结构
        print("\n📋 表结构：")
        columns = inspector.get_columns('subscriptions')
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")

if __name__ == '__main__':
    create_subscription_table()
