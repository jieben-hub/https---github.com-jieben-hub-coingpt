# -*- coding: utf-8 -*-
"""
管理员登录相关功能
"""
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from models import db, User
import os
from datetime import datetime, timedelta

def check_admin_credentials(username, password):
    """检查管理员凭证"""
    # 从环境变量或配置中获取管理员账号密码
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    return username == admin_username and password == admin_password

def create_admin_bp():
    """创建管理员蓝图"""
    admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
    
    @admin_bp.route('/login', methods=['GET', 'POST'])
    def admin_login():
        """管理员登录"""
        if request.method == 'GET':
            # 对于GET请求，渲染登录页面
            from flask import render_template
            return render_template('admin/login.html')
        else:  # POST
            # 支持表单提交和JSON提交
            if request.is_json:
                data = request.get_json()
                username = data.get('username')
                password = data.get('password')
            else:
                # 表单提交
                username = request.form.get('username')
                password = request.form.get('password')
            
            if not username or not password:
                return jsonify({'status': 'error', 'message': '用户名和密码不能为空'}), 400
            
            if check_admin_credentials(username, password):
                # 设置会话
                session['admin_logged_in'] = True
                session['admin_username'] = username
                # 如果是API请求返回JSON，否则重定向到dashboard
                if request.is_json:
                    return jsonify({'status': 'success', 'message': '登录成功'})
                else:
                    return redirect(url_for('admin.dashboard'))
            else:
                # 如果是API请求返回JSON，否则渲染登录页面并显示错误
                if request.is_json:
                    return jsonify({'status': 'error', 'message': '用户名或密码错误'}), 401
                else:
                    return render_template('admin/login.html', error='用户名或密码错误')
    
    @admin_bp.route('/logout', methods=['GET', 'POST'])
    def admin_logout():
        """管理员登出"""
        session.pop('admin_logged_in', None)
        session.pop('admin_username', None)
        # 如果是API请求返回JSON，否则重定向到登录页面
        if request.is_json or request.method == 'POST' and request.content_type == 'application/json':
            return jsonify({'status': 'success', 'message': '登出成功'})
        else:
            return redirect(url_for('admin.admin_login'))
    
    def admin_required(f):
        """管理员权限装饰器"""
        from functools import wraps
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get('admin_logged_in'):
                # 检查是否是API请求
                if request.is_json or request.content_type == 'application/json':
                    return jsonify({'status': 'error', 'message': '需要管理员权限'}), 401
                else:
                    # 非API请求重定向到登录页面
                    return redirect(url_for('admin.admin_login'))
            return f(*args, **kwargs)
        return decorated
    
    # 用户管理路由
    @admin_bp.route('/users', methods=['GET'])
    @admin_required
    def get_users():
        """获取用户列表"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        users = User.query.paginate(page=page, per_page=per_page, error_out=False)
        
        user_list = []
        for user in users.items:
            user_list.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'apple_sub': user.apple_sub,
                'membership': user.membership,
                'is_active': user.is_active,
                'dialog_count': user.dialog_count,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None,
                'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None
            })
        
        return jsonify({
            'status': 'success',
            'data': user_list,
            'total': users.total,
            'page': page,
            'pages': users.pages
        })
    
    @admin_bp.route('/users/<int:user_id>', methods=['GET'])
    @admin_required
    def get_user(user_id):
        """获取单个用户信息"""
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'apple_sub': user.apple_sub,
                'membership': user.membership,
                'is_active': user.is_active,
                'dialog_count': user.dialog_count,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None,
                'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None
            }
        })
    
    @admin_bp.route('/users/<int:user_id>', methods=['PUT'])
    @admin_required
    def update_user(user_id):
        """更新用户信息"""
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        data = request.get_json()
        
        # 只允许更新特定字段
        if 'membership' in data:
            user.membership = data['membership']
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        
        try:
            db.session.commit()
            return jsonify({'status': 'success', 'message': '用户信息更新成功'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'更新失败: {str(e)}'})
    
    @admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
    @admin_required
    def delete_user(user_id):
        """删除用户"""
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        try:
            db.session.delete(user)
            db.session.commit()
            return jsonify({'status': 'success', 'message': '用户删除成功'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'删除失败: {str(e)}'})
    
    # 会员管理路由
    @admin_bp.route('/memberships', methods=['GET'])
    @admin_required
    def get_membership_stats():
        """获取会员统计信息"""
        # 统计不同会员等级的用户数量
        membership_stats = db.session.query(
            User.membership,
            db.func.count(User.id).label('count')
        ).group_by(User.membership).all()
        
        stats = {}
        for membership, count in membership_stats:
            stats[membership] = count
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
    
    @admin_bp.route('/users/upgrade', methods=['POST'])
    @admin_required
    def upgrade_user_membership():
        """升级用户会员等级"""
        data = request.get_json()
        user_id = data.get('user_id')
        new_membership = data.get('membership')
        
        if not user_id or not new_membership:
            return jsonify({'status': 'error', 'message': '缺少必要参数'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        try:
            user.membership = new_membership
            db.session.commit()
            return jsonify({'status': 'success', 'message': '会员等级更新成功'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'更新失败: {str(e)}'})
    
    # 页面视图函数
    @admin_bp.route('/')
    @admin_bp.route('/dashboard')
    @admin_required
    def dashboard():
        """管理员仪表盘"""
        # 获取用户统计数据
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=1).count()
        
        # 获取不同会员等级的用户数
        from sqlalchemy import func
        membership_stats = db.session.query(
            User.membership,
            func.count(User.id).label('count')
        ).group_by(User.membership).all()
        
        return render_template('admin/dashboard.html', 
                             total_users=total_users,
                             active_users=active_users,
                             membership_stats=membership_stats,
                             admin_username=session.get('admin_username'))
    
    @admin_bp.route('/users/page', methods=['GET'])
    @admin_required
    def users_page():
        """用户管理页面"""
        return render_template('admin/users.html', admin_username=session.get('admin_username'))
    
    @admin_bp.route('/activities', methods=['GET'])
    @admin_required
    def activities_page():
        """活动管理页面"""
        return render_template('admin/activities.html', admin_username=session.get('admin_username'))
    
    @admin_bp.route('/announcements', methods=['GET'])
    @admin_required
    def announcements_page():
        """公告管理页面"""
        return render_template('admin/announcements.html', admin_username=session.get('admin_username'))
    
    # 全局错误处理 - 页面不存在
    @admin_bp.app_errorhandler(404)
    def page_not_found(e):
        return render_template('admin/404.html'), 404
    
    return admin_bp