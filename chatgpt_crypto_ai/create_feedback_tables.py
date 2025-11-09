# -*- coding: utf-8 -*-
"""
直接创建反馈表的脚本
"""
import os
import sys
from app import create_app
from models import db, SessionFeedback, MessageFeedback

def create_tables():
    """创建反馈表"""
    app = create_app()
    with app.app_context():
        # 创建会话反馈表和消息反馈表
        db.create_all()
        print("反馈表创建完成！")

if __name__ == '__main__':
    create_tables()
