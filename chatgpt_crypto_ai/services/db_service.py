# -*- coding: utf-8 -*-
"""
数据库服务模块 - 提供数据库操作的高级API
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from models import db, User, Session, Message, UserSymbol

class UserService:
    """用户相关服务"""
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """根据用户ID获取用户"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_apple_sub(apple_sub: str) -> Optional[User]:
        """根据Apple唯一标识获取用户"""
        return User.query.filter_by(apple_sub=apple_sub).first()
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def create_user(apple_sub: str = None, username: str = None, password: str = None, email: str = None, inviter_id: Optional[int] = None) -> Optional[User]:
        """
        创建新用户
        
        Args:
            apple_sub: Apple唯一标识（可选）
            username: 用户名（可选）
            password: 密码（可选，但如果提供了用户名则必须提供）
            email: 电子邮箱（可选）
            inviter_id: 邀请人ID（可选）
            
        Returns:
            User: 创建的用户对象，如果创建失败则返回None
        """
        # 检查参数有效性
        if not apple_sub and not username:
            print("错误: 创建用户时需要提供apple_sub或username")
            return None
            
        # 如果是Apple登录（有apple_sub），则允许没有密码
        # 如果是普通注册（没有apple_sub），则要求有密码
        if not apple_sub and username and not password:
            print("错误: 普通注册需要提供密码")
            return None
            
        # 检查用户名是否已存在
        if username and UserService.get_user_by_username(username):
            return None
            
        # 创建用户
        user = User(
            apple_sub=apple_sub,
            username=username,
            password=password,  # 实际应用中应该对密码进行哈希处理
            email=email,  # 添加email字段
            inviter_id=inviter_id,
            membership='free',
            dialog_count=0,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @staticmethod
    def get_or_create_user(apple_sub: str, username: str = None, email: str = None, inviter_id: Optional[int] = None) -> User:
        """获取用户，不存在则创建
        
        Args:
            apple_sub: Apple唯一标识
            username: 用户名（可选，仅在创建新用户时使用）
            email: 电子邮箱（可选，仅在创建新用户时使用）
            inviter_id: 邀请人ID（可选）
            
        Returns:
            User: 获取或创建的用户对象
        """
        user = UserService.get_user_by_apple_sub(apple_sub)
        if not user:
            user = UserService.create_user(apple_sub=apple_sub, username=username, email=email, inviter_id=inviter_id)
        return user
    
    @staticmethod
    def update_last_login(user_id: int) -> None:
        """更新最后登录时间"""
        user = User.query.get(user_id)
        if user:
            user.last_login = datetime.utcnow()
            db.session.commit()
    
    @staticmethod
    def increment_dialog_count(user_id: int) -> int:
        """增加对话计数并返回最新值"""
        user = User.query.get(user_id)
        if user:
            user.dialog_count += 1
            db.session.commit()
            return user.dialog_count
        return 0
    
    @staticmethod
    def update_membership(user_id: int, membership: str) -> bool:
        """更新用户会员级别"""
        user = User.query.get(user_id)
        if user:
            user.membership = membership
            db.session.commit()
            return True
        return False
        
    @staticmethod
    def get_user_invitees(user_id: int) -> List[User]:
        """获取用户邀请的所有用户"""
        return User.query.filter_by(inviter_id=user_id).all()
        
    @staticmethod
    def count_user_invitees(user_id: int) -> int:
        """统计用户邀请的用户数量"""
        return User.query.filter_by(inviter_id=user_id).count()
        
    @staticmethod
    def verify_password(username: str, password: str) -> Optional[User]:
        """验证用户名和密码"""
        user = UserService.get_user_by_username(username)
        if user and user.password == password:  # 实际应用中应该比较哈希值
            return user
        return None


class SessionService:
    """会话相关服务"""
    
    @staticmethod
    def create_session(user_id: int) -> Session:
        """创建新会话"""
        session = Session(
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(session)
        db.session.commit()
        return session
    
    @staticmethod
    def get_session(session_id: int) -> Optional[Session]:
        """获取会话"""
        return Session.query.get(session_id)
    
    @staticmethod
    def get_user_sessions(user_id: int, limit: int = 5, offset: int = 0) -> List[Session]:
        """获取用户最近的会话，支持分页
        
        Args:
            user_id: 用户ID
            limit: 每页数量，默认5
            offset: 偏移量，默认0
            
        Returns:
            会话列表
        """
        return Session.query.filter_by(user_id=user_id).order_by(Session.updated_at.desc()).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_message_by_id(message_id: int) -> Optional[Message]:
        """根据ID获取消息"""
        return Message.query.get(message_id)
    
    @staticmethod
    def update_session_symbol(session_id: int, symbol: str) -> bool:
        """更新会话最后使用的币种"""
        session = Session.query.get(session_id)
        if session:
            session.last_symbol = symbol
            session.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def touch_session(session_id: int) -> bool:
        """更新会话时间"""
        session = Session.query.get(session_id)
        if session:
            session.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
        
    @staticmethod
    def delete_session(session_id: int) -> bool:
        """删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否删除成功
        """
        session = Session.query.get(session_id)
        if session:
            db.session.delete(session)
            db.session.commit()
            return True
        return False


class MessageService:
    """消息相关服务"""
    
    @staticmethod
    def create_message(session_id: int, role: str, content: str) -> Message:
        """创建新消息"""
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            created_at=datetime.utcnow()
        )
        db.session.add(message)
        db.session.commit()
        return message
    
    @staticmethod
    def get_session_messages(session_id: int, limit: int = 10) -> List[Message]:
        """获取会话的最近消息"""
        return Message.query.filter_by(session_id=session_id).order_by(Message.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_messages_for_context(session_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取会话的最近消息，格式化为OpenAI API的上下文格式"""
        messages = Message.query.filter_by(session_id=session_id).order_by(Message.created_at.asc()).limit(limit).all()
        return [{"role": msg.role, "content": msg.content} for msg in messages]
    
    @staticmethod
    def get_all_session_messages(session_id: int) -> List[Message]:
        """获取会话的所有历史消息，按创建时间升序排列"""
        return Message.query.filter_by(session_id=session_id).order_by(Message.created_at.asc()).all()
        
    @staticmethod
    def get_message_by_id(message_id: int) -> Optional[Message]:
        """根据ID获取单条消息"""
        return Message.query.get(message_id)


class SymbolService:
    """用户币种偏好服务"""
    
    @staticmethod
    def add_symbol_for_user(user_id: int, symbol: str) -> None:
        """为用户添加币种偏好"""
        UserSymbol.add_symbol_for_user(user_id, symbol)
    
    @staticmethod
    def get_user_symbols(user_id: int, limit: int = 5) -> List[str]:
        """获取用户最近使用的币种"""
        symbols = UserSymbol.query.filter_by(user_id=user_id).order_by(UserSymbol.added_at.desc()).limit(limit).all()
        return [symbol.symbol for symbol in symbols]
