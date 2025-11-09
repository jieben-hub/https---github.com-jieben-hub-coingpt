# -*- coding: utf-8 -*-
"""
数据库模型包
"""
from flask_sqlalchemy import SQLAlchemy

# 创建数据库实例
db = SQLAlchemy()

# 导入所有模型，确保它们被注册到SQLAlchemy
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 从根目录导入User模型
from models import User
from models.announcement import Announcement
