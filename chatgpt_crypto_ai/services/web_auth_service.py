# -*- coding: utf-8 -*-
"""
网页用户认证服务
"""
import jwt
import datetime
import os
from models import db, User
from utils.password import hash_password, verify_password
from config import SECRET_KEY

class WebAuthService:
    """
    Web认证服务，用于处理用户名/密码登录和注册
    """
    
    @classmethod
    def register_user(cls, username, password, inviter_id=None):
        """
        注册新用户
        
        Args:
            username (str): 用户名
            password (str): 密码
            inviter_id (int, optional): 邀请人ID
        
        Returns:
            dict: 用户信息或None（如果注册失败）
        """
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return None
        
        # 验证邀请人ID是否有效
        if inviter_id:
            inviter = User.query.get(inviter_id)
            if not inviter:
                inviter_id = None  # 如果邀请人不存在，则设为None
        
        # 创建新用户
        hashed_password = hash_password(password)
        new_user = User(
            username=username,
            password=hashed_password,
            inviter_id=inviter_id,  # 添加邀请人ID
            membership='free',
            dialog_count=0,
            created_at=datetime.datetime.utcnow(),
            last_login=datetime.datetime.utcnow()
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # 邀请奖励：双方各加5次会话
            if inviter_id:
                inviter = User.query.get(inviter_id)
                if inviter:
                    inviter.dialog_count += 5
                    db.session.commit()
            new_user.dialog_count += 5
            db.session.commit()
            
            return {
                'user_id': new_user.id,
                'username': new_user.username,
                'membership': new_user.membership,
                'dialog_count': new_user.dialog_count,
                'inviter_id': new_user.inviter_id,  # 返回邀请人ID
                'created_at': new_user.created_at.isoformat() if new_user.created_at else None
            }
        except Exception as e:
            print(f"Error registering user: {e}")
            db.session.rollback()
            return None
    
    @classmethod
    def login_user(cls, username, password):
        """
        用户登录验证
        
        Args:
            username (str): 用户名
            password (str): 密码
        
        Returns:
            dict: 用户信息或None（如果登录失败）
        """
        # 查找用户
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.password:
            return None
        
        # 验证密码
        if not verify_password(user.password, password):
            return None
        
        # 更新最后登录时间
        user.last_login = datetime.datetime.utcnow()
        db.session.commit()
        
        return {
            'user_id': user.id,
            'username': user.username,
            'membership': user.membership,
            'dialog_count': user.dialog_count,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
    
    @classmethod
    def create_session_token(cls, user_id):
        """
        为用户创建JWT会话令牌
        
        Args:
            user_id (int): 用户ID
        
        Returns:
            str: JWT令牌
        """
        payload = {
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),  # 7天有效期
            'iat': datetime.datetime.utcnow()
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return token
    
    @classmethod
    def verify_session_token(cls, token):
        """
        验证会话令牌
        
        Args:
            token (str): JWT令牌
        
        Returns:
            tuple: (is_valid, user_id)
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            if not user_id:
                print(f"Token payload missing user_id. Payload keys: {list(payload.keys())}")
                return False, None
            return True, user_id
        except jwt.ExpiredSignatureError:
            print("Token expired")
            return False, None
        except jwt.InvalidTokenError as e:
            print(f"Invalid token: {e}")
            return False, None
        except KeyError as e:
            print(f"Token verification error - missing key: {e}")
            return False, None
        except Exception as e:
            print(f"Token verification error: {e}")
            return False, None
