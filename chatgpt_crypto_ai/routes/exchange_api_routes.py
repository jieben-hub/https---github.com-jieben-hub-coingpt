# -*- coding: utf-8 -*-
"""
交易所 API Key 管理路由
"""
from flask import Blueprint, request, jsonify, g
import logging
import traceback
from cryptography.fernet import Fernet
import os

from models import db, ExchangeApiKey
from routes.chat_routes import token_required

logger = logging.getLogger(__name__)

# 创建蓝图
exchange_api_bp = Blueprint('exchange_api', __name__, url_prefix='/api/exchange-api')


@exchange_api_bp.route('/keys', methods=['GET'])
@token_required
def get_api_keys():
    """
    获取用户的所有 API Key 配置
    """
    try:
        user_id = g.user_id
        
        keys = ExchangeApiKey.query.filter_by(user_id=user_id).all()
        
        # 解密并返回（不返回完整的 secret）
        result = []
        encryption_key = os.getenv('ENCRYPTION_KEY', Fernet.generate_key().decode()).encode()
        f = Fernet(encryption_key)
        
        for key in keys:
            api_key_decrypted = f.decrypt(key.api_key.encode()).decode()
            result.append({
                'id': key.id,
                'exchange': key.exchange,
                'testnet': bool(key.testnet),
                'is_active': bool(key.is_active),
                'nickname': key.nickname,
                'api_key_preview': api_key_decrypted[:10] + '...' if len(api_key_decrypted) > 10 else api_key_decrypted,
                'created_at': key.created_at.isoformat() if key.created_at else None
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"获取 API Key 列表失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@exchange_api_bp.route('/keys', methods=['POST'])
@token_required
def add_api_key():
    """
    添加新的 API Key
    
    Body:
    {
        "exchange": "bybit",
        "api_key": "your_api_key",
        "api_secret": "your_api_secret",
        "testnet": true,
        "nickname": "我的主账户"
    }
    """
    try:
        user_id = g.user_id
        data = request.get_json()
        
        # 验证必填参数
        required_fields = ['exchange', 'api_key', 'api_secret']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必填参数: {field}'
                }), 400
        
        # 加密 API Key 和 Secret
        encryption_key = os.getenv('ENCRYPTION_KEY', Fernet.generate_key().decode()).encode()
        f = Fernet(encryption_key)
        
        encrypted_api_key = f.encrypt(data['api_key'].encode()).decode()
        encrypted_api_secret = f.encrypt(data['api_secret'].encode()).decode()
        
        # 创建记录
        new_key = ExchangeApiKey(
            user_id=user_id,
            exchange=data['exchange'],
            api_key=encrypted_api_key,
            api_secret=encrypted_api_secret,
            testnet=1 if data.get('testnet', True) else 0,
            nickname=data.get('nickname')
        )
        
        db.session.add(new_key)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'API Key 添加成功',
            'data': {
                'id': new_key.id,
                'exchange': new_key.exchange,
                'testnet': bool(new_key.testnet),
                'nickname': new_key.nickname
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加 API Key 失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@exchange_api_bp.route('/keys/<int:key_id>', methods=['PUT'])
@token_required
def update_api_key(key_id):
    """
    更新 API Key
    
    Body:
    {
        "api_key": "new_api_key",  // 可选
        "api_secret": "new_api_secret",  // 可选
        "testnet": false,  // 可选
        "is_active": true,  // 可选
        "nickname": "新昵称"  // 可选
    }
    """
    try:
        user_id = g.user_id
        data = request.get_json()
        
        # 查询记录
        key = ExchangeApiKey.query.filter_by(id=key_id, user_id=user_id).first()
        if not key:
            return jsonify({
                'status': 'error',
                'message': 'API Key 不存在或无权访问'
            }), 404
        
        # 更新字段
        encryption_key = os.getenv('ENCRYPTION_KEY', Fernet.generate_key().decode()).encode()
        f = Fernet(encryption_key)
        
        if 'api_key' in data:
            key.api_key = f.encrypt(data['api_key'].encode()).decode()
        
        if 'api_secret' in data:
            key.api_secret = f.encrypt(data['api_secret'].encode()).decode()
        
        if 'testnet' in data:
            key.testnet = 1 if data['testnet'] else 0
        
        if 'is_active' in data:
            key.is_active = 1 if data['is_active'] else 0
        
        if 'nickname' in data:
            key.nickname = data['nickname']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'API Key 更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新 API Key 失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@exchange_api_bp.route('/keys/<int:key_id>', methods=['DELETE'])
@token_required
def delete_api_key(key_id):
    """删除 API Key"""
    try:
        user_id = g.user_id
        
        # 查询记录
        key = ExchangeApiKey.query.filter_by(id=key_id, user_id=user_id).first()
        if not key:
            return jsonify({
                'status': 'error',
                'message': 'API Key 不存在或无权访问'
            }), 404
        
        db.session.delete(key)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'API Key 删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除 API Key 失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
