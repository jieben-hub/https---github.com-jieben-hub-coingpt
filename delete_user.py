#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
删除指定邮箱的用户脚本
"""
import sys
import os
import io

# 设置标准输出编码为UTF-8，解决中文输出问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加当前目录到路径，确保可以导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入必要的模块
from chatgpt_crypto_ai.models import db, User
from chatgpt_crypto_ai.config import DATABASE_URL
from flask import Flask
from sqlalchemy import or_

def create_mini_app():
    """创建一个最小化的Flask应用用于数据库操作"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def find_users(search_term=None):
    """
    查找用户，支持邮箱、用户名和Apple ID查询
    如果search_term为None，则返回所有用户
    
    Args:
        search_term: 搜索关键词（邮箱、用户名或Apple ID），可选
    
    Returns:
        list: 匹配的用户列表
    """
    app = create_mini_app()
    with app.app_context():
        if search_term:
            # 使用多条件查询
            users = User.query.filter(
                or_(
                    User.email == search_term,  # 精确匹配邮箱
                    User.apple_sub == search_term,  # 精确匹配 Apple ID
                    User.email.contains(search_term),  # 邮箱包含搜索关键词
                    User.apple_sub.contains(search_term),  # Apple ID 包含搜索关键词
                    User.username.contains(search_term)  # 用户名包含搜索关键词
                )
            ).all()
            
            if users:
                print(f"找到 {len(users)} 个匹配用户:")
            else:
                print(f"未找到匹配搜索条件 '{search_term}' 的用户")
                return []
        else:
            # 查询所有用户
            users = User.query.order_by(User.id).all()
            print(f"共有 {len(users)} 个用户:")
        
        # 显示用户信息
        for i, user in enumerate(users, 1):
            print(f"\n--- 用户 {i} ---")
            print(f"ID: {user.id}")
            print(f"用户名: {user.username or '(无)'}")
            print(f"邮箱: {user.email or '(无)'}")
            print(f"Apple ID: {user.apple_sub or '(无)'}")
            print(f"创建时间: {user.created_at}")
            print(f"最后登录: {user.last_login or '(无)'}")
            print(f"会员类型: {user.membership}")
            print(f"对话数量: {user.dialog_count}")
        
        return users

def list_all_users():
    """查询并显示所有用户"""
    return find_users(None)

def delete_user_by_id(user_id):
    """
    通过用户ID删除用户
    
    Args:
        user_id: 用户ID
    
    Returns:
        bool: 是否成功删除用户
    """
    app = create_mini_app()
    with app.app_context():
        # 查找用户
        user = User.query.get(user_id)
        
        if user:
            print(f"\n准备删除用户: ID={user.id}, 用户名={user.username or '(无)'}, 邮箱={user.email or '(无)'}")
            
            # 确认删除
            confirm = input(f"\n确认删除该用户? (y/n): ")
            if confirm.lower() != 'y':
                print("取消删除操作")
                return False
            
            # 删除用户
            try:
                db.session.delete(user)
                db.session.commit()
                print(f"成功删除用户: ID={user_id}")
                return True
            except Exception as e:
                db.session.rollback()
                print(f"删除用户失败: {str(e)}")
                return False
        else:
            print(f"未找到ID为 {user_id} 的用户")
            return False

if __name__ == "__main__":
    import sys
    
    print("\n===== 用户管理工具 =====\n")
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        # 默认查询所有用户
        command = 'list'
    
    if command == 'list':
        # 查询所有用户
        print("\n正在查询所有用户...\n")
        users = list_all_users()
        print("\n查询完成。如需删除用户，请运行: python delete_user.py delete <用户ID>")
    
    elif command == 'search' and len(sys.argv) > 2:
        # 搜索特定用户
        search_term = sys.argv[2]
        print(f"\n正在查询包含 '{search_term}' 的用户...\n")
        users = find_users(search_term)
        if not users:
            print("未找到用户，无法执行删除操作")
        print("\n查询完成。如需删除用户，请运行: python delete_user.py delete <用户ID>")
    
    elif command == 'delete' and len(sys.argv) > 2:
        # 删除用户
        try:
            user_id = int(sys.argv[2])
            print(f"\n尝试删除用户 ID: {user_id}")
            # 首先查询用户信息
            app = create_mini_app()
            with app.app_context():
                user = User.query.get(user_id)
                if user:
                    print(f"\n找到用户: ID={user.id}, 用户名={user.username or '(无)'}, 邮箱={user.email or '(无)'}")
                    print(f"Apple ID: {user.apple_sub or '(无)'}")
                    
                    # 自动删除用户
                    try:
                        db.session.delete(user)
                        db.session.commit()
                        print(f"\n成功删除用户: ID={user_id}")
                    except Exception as e:
                        db.session.rollback()
                        print(f"\n删除用户失败: {str(e)}")
                else:
                    print(f"\n未找到ID为 {user_id} 的用户")
        except ValueError:
            print("\n无效的用户ID，应为整数")
    
    else:
        # 显示使用帮助
        print("用法:")
        print("  python delete_user.py                 - 查询所有用户")
        print("  python delete_user.py list           - 查询所有用户")
        print("  python delete_user.py search <关键词>  - 搜索特定用户")
        print("  python delete_user.py delete <用户ID> - 删除指定用户")
    
    print("\n操作完成")

