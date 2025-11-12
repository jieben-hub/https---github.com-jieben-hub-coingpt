# -*- coding: utf-8 -*-
"""
活动模型定义
"""
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, DateTime, Integer, Boolean
from models import db

class Activity(db.Model):
    """活动表"""
    __tablename__ = 'activities'
    
    id = Column(BigInteger, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)  # 优先级，数字越大优先级越高
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_active_activities(cls, limit=5):
        """获取当前活跃的活动"""
        now = datetime.utcnow()
        return cls.query.filter_by(is_active=True).filter(
            cls.start_time <= now,
            cls.end_time >= now
        ).order_by(cls.priority.desc(), cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_all_activities(cls):
        """获取所有活动"""
        return cls.query.order_by(cls.priority.desc(), cls.created_at.desc()).all()
    
    @classmethod
    def create_activity(cls, title, description, start_time, end_time, priority=0, is_active=True):
        """创建新活动"""
        try:
            activity = cls(
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                priority=priority,
                is_active=is_active
            )
            db.session.add(activity)
            db.session.commit()
            return {"status": "success", "message": "活动创建成功", "id": activity.id}
        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": f"创建活动失败: {str(e)}"}
    
    @classmethod
    def update_activity(cls, activity_id, title=None, description=None, start_time=None, 
                       end_time=None, priority=None, is_active=None):
        """更新活动"""
        try:
            activity = cls.query.get(activity_id)
            if not activity:
                return {"status": "error", "message": "活动不存在"}
            
            if title is not None:
                activity.title = title
            if description is not None:
                activity.description = description
            if start_time is not None:
                activity.start_time = start_time
            if end_time is not None:
                activity.end_time = end_time
            if priority is not None:
                activity.priority = priority
            if is_active is not None:
                activity.is_active = is_active
                
            db.session.commit()
            return {"status": "success", "message": "活动更新成功"}
        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": f"更新活动失败: {str(e)}"}
    
    @classmethod
    def delete_activity(cls, activity_id):
        """删除活动"""
        try:
            activity = cls.query.get(activity_id)
            if not activity:
                return {"status": "error", "message": "活动不存在"}
            
            db.session.delete(activity)
            db.session.commit()
            return {"status": "success", "message": "活动删除成功"}
        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": f"删除活动失败: {str(e)}"}