# -*- coding: utf-8 -*-
"""
交易历史同步路由
"""
from flask import Blueprint, request, jsonify, g
from routes.chat_routes import token_required
from services.sync_trading_history import TradingHistorySync
import logging

logger = logging.getLogger(__name__)

sync_bp = Blueprint('sync', __name__, url_prefix='/api/sync')


@sync_bp.route('/trading/pnl', methods=['POST'])
@token_required
def sync_pnl_history():
    """
    同步平仓盈亏历史
    
    Body:
    {
        "exchange": "bybit",
        "days": 30,
        "symbol": "BTCUSDT"  // 可选
    }
    
    Response:
    {
        "status": "success",
        "message": "同步完成",
        "synced_count": 10,
        "skipped_count": 5,
        "total_records": 15
    }
    """
    try:
        user_id = g.user_id
        data = request.get_json() or {}
        
        exchange = data.get('exchange', 'bybit')
        days = data.get('days', 30)
        symbol = data.get('symbol')
        
        logger.info(f"用户{user_id}请求同步平仓历史: exchange={exchange}, days={days}, symbol={symbol}")
        
        result = TradingHistorySync.sync_closed_positions(
            user_id=user_id,
            exchange_name=exchange,
            days=days,
            symbol=symbol
        )
        
        return jsonify(result), 200 if result['status'] == 'success' else 500
        
    except Exception as e:
        logger.error(f"同步平仓历史失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@sync_bp.route('/trading/orders', methods=['POST'])
@token_required
def sync_order_history():
    """
    同步订单历史
    
    Body:
    {
        "exchange": "bybit",
        "days": 30,
        "symbol": "BTCUSDT"  // 可选
    }
    
    Response:
    {
        "status": "success",
        "message": "同步完成",
        "synced_count": 20,
        "skipped_count": 10,
        "total_records": 30
    }
    """
    try:
        user_id = g.user_id
        data = request.get_json() or {}
        
        exchange = data.get('exchange', 'bybit')
        days = data.get('days', 30)
        symbol = data.get('symbol')
        
        logger.info(f"用户{user_id}请求同步订单历史: exchange={exchange}, days={days}, symbol={symbol}")
        
        result = TradingHistorySync.sync_order_history(
            user_id=user_id,
            exchange_name=exchange,
            days=days,
            symbol=symbol
        )
        
        return jsonify(result), 200 if result['status'] == 'success' else 500
        
    except Exception as e:
        logger.error(f"同步订单历史失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@sync_bp.route('/trading/all', methods=['POST'])
@token_required
def sync_all_history():
    """
    同步所有交易历史（平仓+订单）
    
    Body:
    {
        "exchange": "bybit",
        "days": 30,
        "symbol": "BTCUSDT"  // 可选
    }
    
    Response:
    {
        "status": "success",
        "message": "所有历史记录同步完成",
        "pnl_sync": {
            "status": "success",
            "synced_count": 10,
            "skipped_count": 5
        },
        "order_sync": {
            "status": "success",
            "synced_count": 20,
            "skipped_count": 10
        }
    }
    """
    try:
        user_id = g.user_id
        data = request.get_json() or {}
        
        exchange = data.get('exchange', 'bybit')
        days = data.get('days', 30)
        symbol = data.get('symbol')
        
        logger.info(f"用户{user_id}请求同步所有交易历史: exchange={exchange}, days={days}, symbol={symbol}")
        
        result = TradingHistorySync.sync_all_history(
            user_id=user_id,
            exchange_name=exchange,
            days=days,
            symbol=symbol
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"同步所有历史失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
