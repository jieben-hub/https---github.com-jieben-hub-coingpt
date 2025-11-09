# -*- coding: utf-8 -*-
"""
公告模型定义
"""
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, DateTime, Integer, Boolean
from models import db

class Announcement(db.Model):
    """公告表"""
    __tablename__ = 'announcements'
    
    id = Column(BigInteger, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)  # 优先级，数字越大优先级越高
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_active_announcements(cls, limit=5):
        """获取活跃的公告"""
        return cls.query.filter_by(is_active=True).order_by(cls.priority.desc(), cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_all_announcements(cls):
        """获取所有公告"""
        return cls.query.order_by(cls.priority.desc(), cls.created_at.desc()).all()
    
    @classmethod
    def create_announcement(cls, title, content, priority=0, is_active=True):
        """创建新公告"""
        try:
            announcement = cls(
                title=title,
                content=content,
                priority=priority,
                is_active=is_active
            )
            db.session.add(announcement)
            db.session.commit()
            return {"status": "success", "message": "公告创建成功", "id": announcement.id}
        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": f"创建公告失败: {str(e)}"}
    
    @classmethod
    def update_announcement(cls, announcement_id, title=None, content=None, priority=None, is_active=None):
        """更新公告"""
        try:
            announcement = cls.query.get(announcement_id)
            if not announcement:
                return {"status": "error", "message": "公告不存在"}
            
            if title is not None:
                announcement.title = title
            if content is not None:
                announcement.content = content
            if priority is not None:
                announcement.priority = priority
            if is_active is not None:
                announcement.is_active = is_active
                
            db.session.commit()
            return {"status": "success", "message": "公告更新成功"}
        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": f"更新公告失败: {str(e)}"}
    
    @classmethod
    def delete_announcement(cls, announcement_id):
        """删除公告"""
        try:
            announcement = cls.query.get(announcement_id)
            if not announcement:
                return {"status": "error", "message": "公告不存在"}
            
            db.session.delete(announcement)
            db.session.commit()
            return {"status": "success", "message": "公告删除成功"}
        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": f"删除公告失败: {str(e)}"}
