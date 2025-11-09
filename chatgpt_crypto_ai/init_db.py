# -*- coding: utf-8 -*-
"""
数据库初始化脚本
此脚本用于创建数据库表结构
"""
from app import create_app
from models import db

def init_database():
    """初始化数据库，创建所有表"""
    app = create_app()
    with app.app_context():
        db.create_all()
        print("数据库表已创建!")

if __name__ == "__main__":
    init_database()
