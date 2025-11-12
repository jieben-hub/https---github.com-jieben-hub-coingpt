# -*- coding: utf-8 -*-
"""
活动管理相关功能
"""
from flask import Blueprint, request, jsonify
from adminmodels.activity import Activity
from models import db
from datetime import datetime

def create_activity_bp(admin_required):
    """创建活动管理蓝图"""
    activity_bp = Blueprint('activity', __name__, url_prefix='/admin/activities')
    
    @activity_bp.route('/', methods=['GET'])
    @admin_required
    def get_activities():
        """获取活动列表"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        only_active = request.args.get('only_active', False, type=bool)
        current_only = request.args.get('current_only', False, type=bool)
        
        query = Activity.query
        
        if only_active:
            query = query.filter_by(is_active=True)
        
        if current_only:
            now = datetime.utcnow()
            query = query.filter(
                Activity.start_time <= now,
                Activity.end_time >= now
            )
        
        activities = query.order_by(
            Activity.priority.desc(), 
            Activity.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        activity_list = []
        for activity in activities.items:
            activity_list.append({
                'id': activity.id,
                'title': activity.title,
                'description': activity.description,
                'start_time': activity.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': activity.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'is_active': activity.is_active,
                'priority': activity.priority,
                'created_at': activity.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': activity.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'status': 'success',
            'data': activity_list,
            'total': activities.total,
            'page': page,
            'pages': activities.pages
        })
    
    @activity_bp.route('/<int:activity_id>', methods=['GET'])
    @admin_required
    def get_activity(activity_id):
        """获取单个活动详情"""
        activity = Activity.query.get(activity_id)
        if not activity:
            return jsonify({'status': 'error', 'message': '活动不存在'}), 404
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': activity.id,
                'title': activity.title,
                'description': activity.description,
                'start_time': activity.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': activity.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'is_active': activity.is_active,
                'priority': activity.priority,
                'created_at': activity.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': activity.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    
    @activity_bp.route('/', methods=['POST'])
    @admin_required
    def create_activity():
        """创建新活动"""
        data = request.get_json()
        
        title = data.get('title')
        description = data.get('description')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        priority = data.get('priority', 0)
        is_active = data.get('is_active', True)
        
        if not title or not description or not start_time_str or not end_time_str:
            return jsonify({'status': 'error', 'message': '缺少必要参数'}), 400
        
        try:
            # 转换时间字符串为datetime对象
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            
            if start_time >= end_time:
                return jsonify({'status': 'error', 'message': '开始时间必须早于结束时间'}), 400
            
            activity = Activity(
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                priority=priority,
                is_active=is_active
            )
            db.session.add(activity)
            db.session.commit()
            
            return jsonify({
                'status': 'success', 
                'message': '活动创建成功',
                'data': {
                    'id': activity.id,
                    'title': activity.title
                }
            })
        except ValueError as e:
            return jsonify({'status': 'error', 'message': f'时间格式错误: {str(e)}'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'创建失败: {str(e)}'})
    
    @activity_bp.route('/<int:activity_id>', methods=['PUT'])
    @admin_required
    def update_activity(activity_id):
        """更新活动"""
        activity = Activity.query.get(activity_id)
        if not activity:
            return jsonify({'status': 'error', 'message': '活动不存在'}), 404
        
        data = request.get_json()
        
        # 更新字段
        if 'title' in data:
            activity.title = data['title']
        if 'description' in data:
            activity.description = data['description']
        if 'priority' in data:
            activity.priority = data['priority']
        if 'is_active' in data:
            activity.is_active = data['is_active']
        
        # 处理时间字段
        if 'start_time' in data:
            try:
                start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
                activity.start_time = start_time
            except ValueError:
                return jsonify({'status': 'error', 'message': '开始时间格式错误'}), 400
        
        if 'end_time' in data:
            try:
                end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
                activity.end_time = end_time
            except ValueError:
                return jsonify({'status': 'error', 'message': '结束时间格式错误'}), 400
        
        # 验证时间逻辑
        if activity.start_time >= activity.end_time:
            return jsonify({'status': 'error', 'message': '开始时间必须早于结束时间'}), 400
        
        try:
            db.session.commit()
            return jsonify({'status': 'success', 'message': '活动更新成功'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'更新失败: {str(e)}'})
    
    @activity_bp.route('/<int:activity_id>', methods=['DELETE'])
    @admin_required
    def delete_activity(activity_id):
        """删除活动"""
        activity = Activity.query.get(activity_id)
        if not activity:
            return jsonify({'status': 'error', 'message': '活动不存在'}), 404
        
        try:
            db.session.delete(activity)
            db.session.commit()
            return jsonify({'status': 'success', 'message': '活动删除成功'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'删除失败: {str(e)}'})
    
    return activity_bp