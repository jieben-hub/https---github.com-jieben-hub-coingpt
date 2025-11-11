#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建交易历史相关数据库表
"""
import os
import sys

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'chatgpt_crypto_ai'))

from app import create_app
from models import db

def create_trading_history_tables():
    """创建交易历史相关的数据库表"""
    
    app = create_app()
    
    with app.app_context():
        # 直接创建表
        db.create_all()
        print("✅ 交易历史数据库表创建成功！")
        print("📊 已创建的表:")
        print("   - trading_pnl_history (历史盈亏记录)")
        print("   - trading_order_history (订单历史记录)")
        return
        

if __name__ == "__main__":
    try:
        create_trading_history_tables()
    except Exception as e:
        print(f"❌ 创建数据库表失败: {e}")
        import traceback
        traceback.print_exc()
