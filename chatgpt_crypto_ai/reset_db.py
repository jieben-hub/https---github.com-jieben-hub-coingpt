# -*- coding: utf-8 -*-
"""
数据库重置脚本
此脚本用于删除并重建数据库表结构
"""
from app import create_app
from models import db

def reset_database():
    """重置数据库，删除并重建所有表"""
    app = create_app()
    with app.app_context():
        db.drop_all()  # 删除所有表
        db.create_all()  # 重新创建所有表
        print("数据库表已重置!")

if __name__ == "__main__":
    # 开发环境中直接重置数据库
    reset_database()
