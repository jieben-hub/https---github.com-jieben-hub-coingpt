# -*- coding: utf-8 -*-
"""
交易历史 API 路由
包括历史盈亏、订单历史等
"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
import logging
import traceback

from routes.chat_routes import token_required
from models import db, TradingPnlHistory, TradingOrderHistory

logger = logging.getLogger(__name__)

# 创建蓝图
trading_history_bp = Blueprint('trading_history', __name__, url_prefix='/api/trading/history')


@trading_history_bp.route('/pnl', methods=['GET'])
@token_required
def get_pnl_history():
    """
    获取历史盈亏记录
    
    Query Parameters:
        limit: 返回记录数量，默认50，最大100
        offset: 偏移量，默认0
        symbol: 币种筛选，可选
        exchange: 交易所筛选，可选
        start_date: 开始日期 (YYYY-MM-DD)，可选
        end_date: 结束日期 (YYYY-MM-DD)，可选
    """
    try:
        user_id = g.user_id
        
        # 获取查询参数
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        symbol = request.args.get('symbol')
        exchange = request.args.get('exchange')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # 解析日期
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # 设置为当天结束时间
            end_date = end_date.replace(hour=23, minute=59, second=59)
        
        # 获取历史盈亏记录
        query = TradingPnlHistory.query.filter_by(user_id=user_id)
        
        # 添加筛选条件
        if symbol:
            query = query.filter_by(symbol=symbol)
        if exchange:
            query = query.filter_by(exchange=exchange)
        if start_date:
            query = query.filter(TradingPnlHistory.close_time >= start_date)
        if end_date:
            query = query.filter(TradingPnlHistory.close_time <= end_date)
        
        # 按平仓时间倒序排列
        records = query.order_by(TradingPnlHistory.close_time.desc()).offset(offset).limit(limit).all()
        
        # 转换为字典格式
        pnl_records = []
        for record in records:
            pnl_records.append({
                'id': record.id,
                'exchange': record.exchange,
                'symbol': record.symbol,
                'side': record.side,
                'open_time': record.open_time.isoformat(),
                'open_price': record.open_price,
                'open_size': record.open_size,
                'close_time': record.close_time.isoformat(),
                'close_price': record.close_price,
                'close_size': record.close_size,
                'realized_pnl': record.realized_pnl,
                'pnl_percentage': round(record.pnl_percentage, 2),
                'fee': record.fee,
                'net_pnl': record.net_pnl,
                'leverage': record.leverage,
                'order_id': record.order_id,
                'position_id': record.position_id,
                'created_at': record.created_at.isoformat()
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'records': pnl_records,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'has_more': len(pnl_records) == limit
                }
            }
        })
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': f'参数格式错误: {str(e)}'
        }), 400
        
    except Exception as e:
        logger.error(f"获取历史盈亏失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@trading_history_bp.route('/pnl/summary', methods=['GET'])
@token_required
def get_pnl_summary():
    """
    获取盈亏汇总统计
    
    Query Parameters:
        exchange: 交易所筛选，可选
        start_date: 开始日期 (YYYY-MM-DD)，可选
        end_date: 结束日期 (YYYY-MM-DD)，可选
        period: 统计周期 (today, week, month, quarter, year, all)，默认all
    """
    try:
        user_id = g.user_id
        
        # 获取查询参数
        exchange = request.args.get('exchange')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        period = request.args.get('period', 'all')
        
        # 根据period设置日期范围
        start_date = None
        end_date = None
        
        if period != 'all':
            now = datetime.now()
            if period == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now
            elif period == 'week':
                start_date = now - timedelta(days=7)
                end_date = now
            elif period == 'month':
                start_date = now - timedelta(days=30)
                end_date = now
            elif period == 'quarter':
                start_date = now - timedelta(days=90)
                end_date = now
            elif period == 'year':
                start_date = now - timedelta(days=365)
                end_date = now
        
        # 如果提供了具体日期，优先使用
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)
        
        # 获取盈亏汇总 - 简化实现
        query = TradingPnlHistory.query.filter_by(user_id=user_id)
        
        if exchange:
            query = query.filter_by(exchange=exchange)
        if start_date:
            query = query.filter(TradingPnlHistory.close_time >= start_date)
        if end_date:
            query = query.filter(TradingPnlHistory.close_time <= end_date)
        
        records = query.all()
        
        # 计算统计数据
        if not records:
            summary = {
                'total_trades': 0,
                'total_realized_pnl': 0.0,
                'total_net_pnl': 0.0,
                'total_fees': 0.0,
                'win_trades': 0,
                'lose_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'best_trade': 0.0,
                'worst_trade': 0.0
            }
        else:
            total_trades = len(records)
            total_realized_pnl = sum(r.realized_pnl for r in records)
            total_net_pnl = sum(r.net_pnl for r in records)
            total_fees = sum(r.fee for r in records)
            
            win_trades = [r for r in records if r.net_pnl > 0]
            lose_trades = [r for r in records if r.net_pnl < 0]
            
            win_count = len(win_trades)
            lose_count = len(lose_trades)
            win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0
            
            avg_win = sum(r.net_pnl for r in win_trades) / win_count if win_count > 0 else 0
            avg_loss = sum(r.net_pnl for r in lose_trades) / lose_count if lose_count > 0 else 0
            
            best_trade = max(r.net_pnl for r in records) if records else 0
            worst_trade = min(r.net_pnl for r in records) if records else 0
            
            summary = {
                'total_trades': total_trades,
                'total_realized_pnl': round(total_realized_pnl, 2),
                'total_net_pnl': round(total_net_pnl, 2),
                'total_fees': round(total_fees, 2),
                'win_trades': win_count,
                'lose_trades': lose_count,
                'win_rate': round(win_rate, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'best_trade': round(best_trade, 2),
                'worst_trade': round(worst_trade, 2)
            }
        
        return jsonify({
            'status': 'success',
            'data': {
                'summary': summary,
                'period': period,
                'date_range': {
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                }
            }
        })
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': f'参数格式错误: {str(e)}'
        }), 400
        
    except Exception as e:
        logger.error(f"获取盈亏汇总失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@trading_history_bp.route('/orders', methods=['GET'])
@token_required
def get_order_history():
    """
    获取订单历史记录
    
    Query Parameters:
        limit: 返回记录数量，默认50，最大100
        offset: 偏移量，默认0
        symbol: 币种筛选，可选
        exchange: 交易所筛选，可选
        status: 订单状态筛选，可选
    """
    try:
        user_id = g.user_id
        
        # 获取查询参数
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        symbol = request.args.get('symbol')
        exchange = request.args.get('exchange')
        status = request.args.get('status')
        
        # 获取订单历史记录
        query = TradingOrderHistory.query.filter_by(user_id=user_id)
        
        if symbol:
            query = query.filter_by(symbol=symbol)
        if exchange:
            query = query.filter_by(exchange=exchange)
        if status:
            query = query.filter_by(status=status)
        
        records = query.order_by(TradingOrderHistory.order_time.desc()).offset(offset).limit(limit).all()
        
        # 转换为字典格式
        order_records = []
        for record in records:
            order_records.append({
                'id': record.id,
                'exchange': record.exchange,
                'order_id': record.order_id,
                'symbol': record.symbol,
                'side': record.side,
                'order_type': record.order_type,
                'quantity': record.quantity,
                'price': record.price,
                'filled_quantity': record.filled_quantity,
                'avg_price': record.avg_price,
                'status': record.status,
                'order_time': record.order_time.isoformat(),
                'update_time': record.update_time.isoformat(),
                'fee': record.fee,
                'leverage': record.leverage,
                'created_at': record.created_at.isoformat()
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'records': order_records,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'has_more': len(order_records) == limit
                }
            }
        })
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': f'参数格式错误: {str(e)}'
        }), 400
        
    except Exception as e:
        logger.error(f"获取订单历史失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@trading_history_bp.route('/pnl', methods=['POST'])
@token_required
def add_pnl_record():
    """
    手动添加历史盈亏记录
    (通常由系统自动调用，也可手动添加)
    
    Request Body:
    {
        "exchange": "bybit",
        "symbol": "BTCUSDT",
        "side": "Buy",
        "open_time": "2025-11-10T10:00:00Z",
        "open_price": 50000.0,
        "open_size": 0.1,
        "close_time": "2025-11-10T11:00:00Z",
        "close_price": 50500.0,
        "close_size": 0.1,
        "realized_pnl": 50.0,
        "fee": 2.5,
        "leverage": 10.0,
        "order_id": "12345",
        "position_id": "67890"
    }
    """
    try:
        user_id = g.user_id
        data = request.get_json()
        
        # 验证必需字段
        required_fields = [
            'exchange', 'symbol', 'side', 'open_time', 'open_price', 'open_size',
            'close_time', 'close_price', 'close_size', 'realized_pnl'
        ]
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必需字段: {field}'
                }), 400
        
        # 解析时间
        open_time = datetime.fromisoformat(data['open_time'].replace('Z', '+00:00'))
        close_time = datetime.fromisoformat(data['close_time'].replace('Z', '+00:00'))
        
        # 计算盈亏百分比
        open_price = float(data['open_price'])
        close_price = float(data['close_price'])
        side = data['side']
        leverage = float(data.get('leverage', 1.0))
        
        if side.lower() == 'buy':
            pnl_percentage = ((close_price - open_price) / open_price) * 100 * leverage
        else:  # sell
            pnl_percentage = ((open_price - close_price) / open_price) * 100 * leverage
        
        # 计算净盈亏
        realized_pnl = float(data['realized_pnl'])
        fee = float(data.get('fee', 0.0))
        net_pnl = realized_pnl - fee
        
        # 创建新记录
        record = TradingPnlHistory(
            user_id=user_id,
            exchange=data['exchange'],
            symbol=data['symbol'],
            side=side,
            open_time=open_time,
            open_price=open_price,
            open_size=float(data['open_size']),
            close_time=close_time,
            close_price=close_price,
            close_size=float(data['close_size']),
            realized_pnl=realized_pnl,
            pnl_percentage=pnl_percentage,
            fee=fee,
            net_pnl=net_pnl,
            leverage=leverage,
            order_id=data.get('order_id'),
            position_id=data.get('position_id')
        )
        
        try:
            db.session.add(record)
            db.session.commit()
            result = {"status": "success", "message": "盈亏记录已保存", "id": record.id}
        except Exception as e:
            db.session.rollback()
            result = {"status": "error", "message": f"保存盈亏记录失败: {e}"}
        
        if result['status'] == 'success':
            return jsonify(result), 201
        else:
            return jsonify(result), 500
            
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': f'数据格式错误: {str(e)}'
        }), 400
        
    except Exception as e:
        logger.error(f"添加盈亏记录失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@trading_history_bp.route('/stats', methods=['GET'])
@token_required
def get_trading_stats():
    """
    获取交易统计数据
    包括今日、本周、本月的盈亏统计
    """
    try:
        user_id = g.user_id
        exchange = request.args.get('exchange')
        
        now = datetime.now()
        
        # 获取不同时间段的统计
        stats = {}
        
        periods = {
            'today': now.replace(hour=0, minute=0, second=0, microsecond=0),
            'week': now - timedelta(days=7),
            'month': now - timedelta(days=30),
            'quarter': now - timedelta(days=90),
            'year': now - timedelta(days=365)
        }
        
        for period_name, start_date in periods.items():
            # 简化统计计算
            query = TradingPnlHistory.query.filter_by(user_id=user_id)
            if exchange:
                query = query.filter_by(exchange=exchange)
            query = query.filter(TradingPnlHistory.close_time >= start_date)
            query = query.filter(TradingPnlHistory.close_time <= now)
            
            records = query.all()
            total_trades = len(records)
            total_net_pnl = sum(r.net_pnl for r in records) if records else 0
            win_trades = len([r for r in records if r.net_pnl > 0])
            win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
            
            stats[period_name] = {
                'total_trades': total_trades,
                'total_net_pnl': round(total_net_pnl, 2),
                'win_trades': win_trades,
                'win_rate': round(win_rate, 2)
            }
        
        # 获取总体统计
        all_query = TradingPnlHistory.query.filter_by(user_id=user_id)
        if exchange:
            all_query = all_query.filter_by(exchange=exchange)
        all_records = all_query.all()
        all_total_trades = len(all_records)
        all_total_net_pnl = sum(r.net_pnl for r in all_records) if all_records else 0
        all_win_trades = len([r for r in all_records if r.net_pnl > 0])
        all_win_rate = (all_win_trades / all_total_trades * 100) if all_total_trades > 0 else 0
        
        stats['all_time'] = {
            'total_trades': all_total_trades,
            'total_net_pnl': round(all_total_net_pnl, 2),
            'win_trades': all_win_trades,
            'win_rate': round(all_win_rate, 2)
        }
        
        return jsonify({
            'status': 'success',
            'data': {
                'stats': stats,
                'generated_at': now.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"获取交易统计失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
