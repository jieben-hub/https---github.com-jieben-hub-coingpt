# -*- coding: utf-8 -*-
"""
用户限制服务 - 管理免费用户的使用限制
"""
from typing import Dict, Tuple, Optional
from models import db, User, Session, Message
from services.db_service import UserService, SessionService, MessageService

# 免费用户限制配置
FREE_USER_LIMITS = {
    'max_sessions': 5,  # 免费用户最多可以创建5个会话
    'max_messages_per_session': 10  # 每个会话最多可以发送10条消息
}

class LimitService:
    """用户限制服务"""
    
    @staticmethod
    def check_session_limit(user_id: int) -> Tuple[bool, str]:
        """
        检查用户是否达到会话数量限制
        
        Args:
            user_id: 用户ID
            
        Returns:
            Tuple[bool, str]: (是否可以创建新会话, 错误消息)
        """
        user = UserService.get_user_by_id(user_id)
        if not user:
            return False, "用户不存在"
            
        # 如果是付费会员，不受限制
        if user.membership != 'free':
            return True, ""
            
        # 获取用户当前会话数量
        sessions = Session.query.filter_by(user_id=user_id).all()
        session_count = len(sessions)
        
        if session_count >= FREE_USER_LIMITS['max_sessions']:
            return False, f"免费用户最多只能创建{FREE_USER_LIMITS['max_sessions']}个会话，请删除旧会话或升级会员"
            
        return True, ""
    
    @staticmethod
    def check_message_limit(session_id: int) -> Tuple[bool, str]:
        """
        检查会话是否达到消息数量限制
        
        Args:
            session_id: 会话ID
            
        Returns:
            Tuple[bool, str]: (是否可以发送新消息, 错误消息)
        """
        session = SessionService.get_session(session_id)
        if not session:
            return False, "会话不存在"
            
        # 获取用户信息
        user = UserService.get_user_by_id(session.user_id)
        if not user:
            return False, "用户不存在"
            
        # 如果是付费会员，不受限制
        if user.membership != 'free':
            return True, ""
            
        # 获取会话当前消息数量
        messages = Message.query.filter_by(session_id=session_id).all()
        message_count = len(messages)
        
        if message_count >= FREE_USER_LIMITS['max_messages_per_session']:
            return False, f"免费用户每个会话最多只能发送{FREE_USER_LIMITS['max_messages_per_session']}条消息，请创建新会话或升级会员"
            
        return True, ""
    
    @staticmethod
    def get_user_usage(user_id: int) -> Dict:
        """
        获取用户的使用情况
        Args:
            user_id: 用户ID
        Returns:
            Dict: 用户使用情况统计
        """
        user = UserService.get_user_by_id(user_id)
        if not user:
            return {
                "status": "error",
                "message": "用户不存在"
            }
        # 获取用户当前会话数量
        sessions = Session.query.filter_by(user_id=user_id).all()
        session_count = len(sessions)
        # 获取每个会话的消息数量
        session_stats = []
        for session in sessions:
            messages = Message.query.filter_by(session_id=session.id).all()
            message_count = len(messages)
            session_stats.append({
                "session_id": session.id,
                "message_count": message_count,
                "max_messages": FREE_USER_LIMITS['max_messages_per_session'] if user.membership == 'free' else "无限制",
                "remaining_messages": FREE_USER_LIMITS['max_messages_per_session'] - message_count if user.membership == 'free' else "无限制"
            })
        # 统计总额度和剩余
        reward_count = user.dialog_count if user.membership == 'free' else 0
        FREE_BASE = FREE_USER_LIMITS['max_sessions'] if user.membership == 'free' else 0
        total_quota = FREE_BASE + reward_count if user.membership == 'free' else '无限制'
        print(f"total_quota: {total_quota}")
        remaining_sessions = total_quota - session_count if user.membership == 'free' else '无限制'
        return {
            "status": "success",
            "data": {
                "user_id": user.id,
                "membership": user.membership,
                "session_count": session_count,  # 已用
                "dialog_count": reward_count,     # 奖励累计
                "max_sessions": total_quota,      # 总额度
                "total_quota": total_quota,       # 总额度
                "remaining_sessions": remaining_sessions,
                "sessions": session_stats
            }
        }
    
    @staticmethod
    def generate_invite_code(user_id: int) -> Optional[str]:
        """
        为用户生成邀请码
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[str]: 邀请码，如果用户不存在则返回None
        """
        user = UserService.get_user_by_id(user_id)
        if not user:
            return None
            
        # 简单地使用用户ID作为邀请码的一部分
        invite_code = f"COINGPT-{user.id}-{hash(user.created_at) % 10000:04d}"
        return invite_code

    @staticmethod
    def check_dialog_count(user_id: int) -> Tuple[bool, str]:
        """
        检查用户剩余会话次数（dialog_count>0），会员用户不限制
        """
        user = UserService.get_user_by_id(user_id)
        if not user:
            return False, "用户不存在"
        if user.membership != 'free':
            return True, ""
        if user.dialog_count > 0:
            return True, ""
        return False, "免费用户剩余会话次数已用完，请邀请好友或升级会员"
