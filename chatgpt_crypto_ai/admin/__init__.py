# -*- coding: utf-8 -*-
"""
管理员模块初始化
"""
from flask import session
from functools import wraps

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            from flask import jsonify
            return jsonify({'status': 'error', 'message': '需要管理员权限'}), 401
        return f(*args, **kwargs)
    return decorated

def init_admin_routes(app):
    """初始化所有管理员路由"""
    # 导入并注册管理员登录相关路由
    from admin.admin_login import create_admin_bp
    admin_bp = create_admin_bp()
    app.register_blueprint(admin_bp)
    
    # 导入并注册公告管理相关路由
    from admin.announcement_management import create_announcement_bp
    announcement_bp = create_announcement_bp(admin_required)
    app.register_blueprint(announcement_bp)
    
    # 导入并注册活动管理相关路由
    from admin.activity_management import create_activity_bp
    activity_bp = create_activity_bp(admin_required)
    app.register_blueprint(activity_bp)
    
    # 导入活动模型到adminmodels包
    from adminmodels.activity import Activity
    
    app.logger.info('管理员路由初始化完成')