# -*- coding: utf-8 -*-
"""
订阅管理路由
处理iOS内购验证和订阅管理
"""
from flask import Blueprint, request, jsonify, g
from routes.chat_routes import token_required
from services.iap_service import IAPService
import logging

logger = logging.getLogger(__name__)

subscription_bp = Blueprint('subscription', __name__, url_prefix='/api/subscription')

@subscription_bp.route('/verify', methods=['POST'])
@token_required
def verify_receipt():
    """
    验证App Store收据并激活订阅
    
    请求体:
    {
        "receipt_data": "base64编码的收据数据"
    }
    
    响应:
    {
        "status": "success",
        "message": "订阅激活成功",
        "data": {
            "product_id": "dev.zonekit.coingpt.Premium.year",
            "expires_date": "2026-11-11T14:30:00",
            "membership": "premium"
        }
    }
    """
    try:
        user_id = g.user_id
        data = request.get_json()
        
        if not data or 'receipt_data' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少收据数据'
            }), 400
        
        receipt_data = data['receipt_data']
        
        logger.info(f"用户{user_id}请求验证收据")
        
        # 验证收据
        success, message, subscription_info = IAPService.verify_receipt(receipt_data, user_id)
        
        if not success:
            logger.warning(f"用户{user_id}收据验证失败: {message}")
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
        
        # 激活订阅
        activate_success, activate_message = IAPService.activate_subscription(user_id, subscription_info)
        
        if not activate_success:
            logger.error(f"用户{user_id}订阅激活失败: {activate_message}")
            return jsonify({
                'status': 'error',
                'message': activate_message
            }), 500
        
        logger.info(f"用户{user_id}订阅激活成功")
        
        return jsonify({
            'status': 'success',
            'message': activate_message,
            'data': {
                'product_id': subscription_info['product_id'],
                'transaction_id': subscription_info['transaction_id'],
                'expires_date': subscription_info['expires_date'].isoformat(),
                'is_trial_period': subscription_info['is_trial_period']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"验证收据时发生错误: {e}")
        return jsonify({
            'status': 'error',
            'message': f'服务器错误: {str(e)}'
        }), 500


@subscription_bp.route('/restore', methods=['POST'])
@token_required
def restore_purchases():
    """
    恢复购买
    
    请求体:
    {
        "receipt_data": "base64编码的收据数据"
    }
    
    响应:
    {
        "status": "success",
        "message": "购买已恢复",
        "data": {
            "product_id": "dev.zonekit.coingpt.Premium.year",
            "expires_date": "2026-11-11T14:30:00",
            "membership": "premium"
        }
    }
    """
    try:
        user_id = g.user_id
        data = request.get_json()
        
        if not data or 'receipt_data' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少收据数据'
            }), 400
        
        receipt_data = data['receipt_data']
        
        logger.info(f"用户{user_id}请求恢复购买")
        
        # 恢复购买
        success, message, subscription_info = IAPService.restore_purchases(receipt_data, user_id)
        
        if not success:
            logger.warning(f"用户{user_id}恢复购买失败: {message}")
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
        
        logger.info(f"用户{user_id}购买已恢复")
        
        return jsonify({
            'status': 'success',
            'message': message,
            'data': {
                'product_id': subscription_info['product_id'],
                'transaction_id': subscription_info['transaction_id'],
                'expires_date': subscription_info['expires_date'].isoformat(),
                'is_trial_period': subscription_info['is_trial_period']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"恢复购买时发生错误: {e}")
        return jsonify({
            'status': 'error',
            'message': f'服务器错误: {str(e)}'
        }), 500


@subscription_bp.route('/status', methods=['GET'])
@token_required
def get_subscription_status():
    """
    获取订阅状态
    
    响应:
    {
        "status": "success",
        "data": {
            "user_id": 4,
            "membership": "premium",
            "is_premium": true,
            "is_free": false
        }
    }
    """
    try:
        user_id = g.user_id
        
        result = IAPService.check_subscription_status(user_id)
        
        if result['status'] == 'error':
            return jsonify(result), 404
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"获取订阅状态时发生错误: {e}")
        return jsonify({
            'status': 'error',
            'message': f'服务器错误: {str(e)}'
        }), 500


@subscription_bp.route('/products', methods=['GET'])
def get_products():
    """
    获取可用的订阅产品列表
    
    响应:
    {
        "status": "success",
        "data": {
            "products": [
                {
                    "product_id": "dev.zonekit.coingpt.Premium.year",
                    "type": "yearly",
                    "duration_days": 365,
                    "membership": "premium",
                    "name": "年度会员",
                    "description": "享受无限制使用"
                }
            ]
        }
    }
    """
    try:
        from services.iap_service import PRODUCT_IDS
        
        products = []
        for product_id, config in PRODUCT_IDS.items():
            products.append({
                'product_id': product_id,
                'type': config['type'],
                'duration_days': config['duration_days'],
                'membership': config['membership'],
                'name': '年度会员' if config['type'] == 'yearly' else '月度会员',
                'description': '享受无限制使用CoinGPT的所有功能'
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'products': products
            }
        }), 200
        
    except Exception as e:
        logger.error(f"获取产品列表时发生错误: {e}")
        return jsonify({
            'status': 'error',
            'message': f'服务器错误: {str(e)}'
        }), 500
