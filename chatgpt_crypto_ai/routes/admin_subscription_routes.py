# -*- coding: utf-8 -*-
"""
订阅管理后台路由
仅供管理员使用
"""
from flask import Blueprint, request, jsonify, g
from routes.chat_routes import token_required
from services.subscription_checker import SubscriptionChecker
from models import Subscription, User
import logging

logger = logging.getLogger(__name__)

admin_subscription_bp = Blueprint('admin_subscription', __name__, url_prefix='/api/admin/subscription')


@admin_subscription_bp.route('/check-expired', methods=['POST'])
@token_required
def check_expired():
    """
    手动触发过期订阅检查
    
    响应:
    {
        "status": "success",
        "message": "过期订阅检查完成"
    }
    """
    try:
        # TODO: 添加管理员权限检查
        # if not is_admin(g.user_id):
        #     return jsonify({'status': 'error', 'message': '无权限'}), 403
        
        SubscriptionChecker.check_expired_subscriptions()
        
        return jsonify({
            'status': 'success',
            'message': '过期订阅检查完成'
        }), 200
        
    except Exception as e:
        logger.error(f"检查过期订阅时发生错误: {e}")
        return jsonify({
            'status': 'error',
            'message': f'服务器错误: {str(e)}'
        }), 500


@admin_subscription_bp.route('/stats', methods=['GET'])
@token_required
def get_stats():
    """
    获取订阅统计信息
    
    响应:
    {
        "status": "success",
        "data": {
            "total_subscriptions": 100,
            "active_subscriptions": 80,
            "expired_subscriptions": 15,
            "cancelled_subscriptions": 5,
            "premium_users": 80,
            "free_users": 200
        }
    }
    """
    try:
        # TODO: 添加管理员权限检查
        
        stats = SubscriptionChecker.get_subscription_stats()
        
        return jsonify({
            'status': 'success',
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"获取订阅统计时发生错误: {e}")
        return jsonify({
            'status': 'error',
            'message': f'服务器错误: {str(e)}'
        }), 500


@admin_subscription_bp.route('/expiring-soon', methods=['GET'])
@token_required
def get_expiring_soon():
    """
    获取即将过期的订阅
    
    查询参数:
    - days: 多少天内过期（默认7天）
    
    响应:
    {
        "status": "success",
        "data": [
            {
                "user_id": 4,
                "username": "user@example.com",
                "product_id": "dev.zonekit.coingpt.Premium.year",
                "expires_date": "2025-11-18T14:30:00",
                "days_until_expiry": 7
            }
        ]
    }
    """
    try:
        # TODO: 添加管理员权限检查
        
        days = request.args.get('days', 7, type=int)
        
        expiring_subs = SubscriptionChecker.get_expiring_soon_subscriptions(days)
        
        result = []
        for sub in expiring_subs:
            user = User.query.get(sub.user_id)
            result.append({
                'user_id': sub.user_id,
                'username': user.username if user else None,
                'email': user.email if user else None,
                'product_id': sub.product_id,
                'product_type': sub.product_type,
                'purchase_date': sub.purchase_date.isoformat(),
                'expires_date': sub.expires_date.isoformat(),
                'days_until_expiry': sub.days_until_expiry()
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"获取即将过期订阅时发生错误: {e}")
        return jsonify({
            'status': 'error',
            'message': f'服务器错误: {str(e)}'
        }), 500


@admin_subscription_bp.route('/user/<int:user_id>', methods=['GET'])
@token_required
def get_user_subscriptions(user_id):
    """
    获取指定用户的所有订阅记录
    
    响应:
    {
        "status": "success",
        "data": [
            {
                "id": 1,
                "product_id": "dev.zonekit.coingpt.Premium.year",
                "transaction_id": "1000000123456789",
                "purchase_date": "2024-11-11T14:30:00",
                "expires_date": "2025-11-11T14:30:00",
                "status": "active",
                "is_trial_period": false
            }
        ]
    }
    """
    try:
        # TODO: 添加权限检查（管理员或用户本人）
        
        subscriptions = Subscription.query.filter_by(user_id=user_id).order_by(
            Subscription.created_at.desc()
        ).all()
        
        result = []
        for sub in subscriptions:
            result.append({
                'id': sub.id,
                'product_id': sub.product_id,
                'product_type': sub.product_type,
                'transaction_id': sub.transaction_id,
                'purchase_date': sub.purchase_date.isoformat(),
                'expires_date': sub.expires_date.isoformat(),
                'status': sub.status,
                'is_active': sub.is_active(),
                'days_until_expiry': sub.days_until_expiry(),
                'is_trial_period': sub.is_trial_period,
                'auto_renew_status': sub.auto_renew_status,
                'created_at': sub.created_at.isoformat()
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"获取用户订阅记录时发生错误: {e}")
        return jsonify({
            'status': 'error',
            'message': f'服务器错误: {str(e)}'
        }), 500
