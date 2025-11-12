# -*- coding: utf-8 -*-
"""
公告管理相关功能
"""
from flask import Blueprint, request, jsonify
from adminmodels.announcement import Announcement
from models import db

def create_announcement_bp(admin_required):
    """创建公告管理蓝图"""
    announcement_bp = Blueprint('announcement', __name__, url_prefix='/admin/announcements')
    
    @announcement_bp.route('/', methods=['GET'])
    @admin_required
    def get_announcements():
        """获取公告列表"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        only_active = request.args.get('only_active', False, type=bool)
        
        query = Announcement.query
        if only_active:
            query = query.filter_by(is_active=True)
        
        announcements = query.order_by(
            Announcement.priority.desc(), 
            Announcement.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        announcement_list = []
        for announcement in announcements.items:
            announcement_list.append({
                'id': announcement.id,
                'title': announcement.title,
                'content': announcement.content,
                'is_active': announcement.is_active,
                'priority': announcement.priority,
                'created_at': announcement.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': announcement.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'status': 'success',
            'data': announcement_list,
            'total': announcements.total,
            'page': page,
            'pages': announcements.pages
        })
    
    @announcement_bp.route('/<int:announcement_id>', methods=['GET'])
    @admin_required
    def get_announcement(announcement_id):
        """获取单个公告详情"""
        announcement = Announcement.query.get(announcement_id)
        if not announcement:
            return jsonify({'status': 'error', 'message': '公告不存在'}), 404
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': announcement.id,
                'title': announcement.title,
                'content': announcement.content,
                'is_active': announcement.is_active,
                'priority': announcement.priority,
                'created_at': announcement.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': announcement.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    
    @announcement_bp.route('/', methods=['POST'])
    @admin_required
    def create_announcement():
        """创建新公告"""
        data = request.get_json()
        
        title = data.get('title')
        content = data.get('content')
        priority = data.get('priority', 0)
        is_active = data.get('is_active', True)
        
        if not title or not content:
            return jsonify({'status': 'error', 'message': '标题和内容不能为空'}), 400
        
        try:
            announcement = Announcement(
                title=title,
                content=content,
                priority=priority,
                is_active=is_active
            )
            db.session.add(announcement)
            db.session.commit()
            
            return jsonify({
                'status': 'success', 
                'message': '公告创建成功',
                'data': {
                    'id': announcement.id,
                    'title': announcement.title
                }
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'创建失败: {str(e)}'})
    
    @announcement_bp.route('/<int:announcement_id>', methods=['PUT'])
    @admin_required
    def update_announcement(announcement_id):
        """更新公告"""
        announcement = Announcement.query.get(announcement_id)
        if not announcement:
            return jsonify({'status': 'error', 'message': '公告不存在'}), 404
        
        data = request.get_json()
        
        # 更新字段
        if 'title' in data:
            announcement.title = data['title']
        if 'content' in data:
            announcement.content = data['content']
        if 'priority' in data:
            announcement.priority = data['priority']
        if 'is_active' in data:
            announcement.is_active = data['is_active']
        
        try:
            db.session.commit()
            return jsonify({'status': 'success', 'message': '公告更新成功'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'更新失败: {str(e)}'})
    
    @announcement_bp.route('/<int:announcement_id>', methods=['DELETE'])
    @admin_required
    def delete_announcement(announcement_id):
        """删除公告"""
        announcement = Announcement.query.get(announcement_id)
        if not announcement:
            return jsonify({'status': 'error', 'message': '公告不存在'}), 404
        
        try:
            db.session.delete(announcement)
            db.session.commit()
            return jsonify({'status': 'success', 'message': '公告删除成功'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'删除失败: {str(e)}'})
    
    return announcement_bp