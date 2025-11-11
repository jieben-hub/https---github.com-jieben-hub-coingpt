# -*- coding: utf-8 -*-
"""
交易 API 路由
"""
from flask import Blueprint, request, jsonify, g
import logging
import traceback

from services.trading_service import TradingService
from routes.chat_routes import token_required
from utils.symbols_sync import get_all_symbols

logger = logging.getLogger(__name__)

# 创建蓝图
trading_bp = Blueprint('trading', __name__, url_prefix='/api/trading')


@trading_bp.route('/balance', methods=['GET'])
@token_required
def get_balance():
    """
    获取账户余额
    
    Query Parameters:
        coin: 币种，默认 USDT
        exchange: 交易所名称，默认使用配置
    """
    try:
        user_id = g.user_id  # 从 token 中获取用户ID
        coin = request.args.get('coin', 'USDT')
        exchange = request.args.get('exchange')
        
        balance = TradingService.get_balance(user_id=user_id, coin=coin, exchange_name=exchange)
        
        return jsonify({
            'status': 'success',
            'data': balance
        })
        
    except Exception as e:
        logger.error(f"获取余额失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@trading_bp.route('/order', methods=['POST'])
@token_required
def create_order():
    """
    创建订单
    
    Body:
    {
        "symbol": "BTCUSDT",
        "side": "buy",  // buy 或 sell
        "quantity": 0.001,  // 币种数量（quantity_type="coin"时使用）
        "amount": 1000,  // USDT金额（quantity_type="usdt"时使用）
        "quantity_type": "coin",  // "coin"=按币种数量, "usdt"=按USDT金额，默认coin
        "order_type": "market",  // market 或 limit
        "price": 50000,  // 限价单必填
        "position_side": "long",  // long 或 short，合约必填
        "leverage": 10,  // 可选，杠杆倍数，如果提供则自动设置
        "exchange": "bybit"  // 可选
    }
    """
    try:
        user_id = g.user_id  # 从 token 中获取用户ID
        data = request.get_json()
        
        # 获取下单类型
        quantity_type = data.get('quantity_type', 'coin')  # 默认按币种数量
        
        # 验证必填参数
        if quantity_type == 'usdt':
            # 按USDT金额下单，需要amount参数
            required_fields = ['symbol', 'side', 'amount']
        else:
            # 按币种数量下单，需要quantity参数
            required_fields = ['symbol', 'side', 'quantity']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必填参数: {field}'
                }), 400
        
        # 计算实际下单数量
        if quantity_type == 'usdt':
            # 按USDT金额下单，需要计算币种数量
            amount = float(data['amount'])
            
            # 获取当前价格
            if data.get('order_type') == 'limit' and 'price' in data:
                # 限价单使用指定价格
                price = float(data['price'])
            else:
                # 市价单需要获取当前市场价格
                ticker = TradingService.get_ticker(
                    user_id=user_id,
                    symbol=data['symbol'],
                    exchange_name=data.get('exchange')
                )
                price = float(ticker.get('last_price', 0))
                if price == 0:
                    return jsonify({
                        'status': 'error',
                        'message': '无法获取当前价格'
                    }), 400
            
            # 计算币种数量 = USDT金额 / 价格
            quantity = amount / price
            logger.info(f"按USDT金额下单: {amount} USDT / {price} = {quantity} {data['symbol']}")
        else:
            # 按币种数量下单
            quantity = float(data['quantity'])
        
        # 如果提供了杠杆参数，先设置杠杆
        if 'leverage' in data:
            try:
                TradingService.set_leverage(
                    user_id=user_id,
                    symbol=data['symbol'],
                    leverage=int(data['leverage']),
                    exchange_name=data.get('exchange')
                )
                logger.info(f"用户 {user_id} 设置杠杆: {data['symbol']} {data['leverage']}x")
            except Exception as e:
                logger.warning(f"设置杠杆失败，继续下单: {e}")
        
        result = TradingService.create_order(
            user_id=user_id,
            symbol=data['symbol'],
            side=data['side'],
            quantity=quantity,
            order_type=data.get('order_type', 'market'),
            price=float(data['price']) if 'price' in data else None,
            position_side=data.get('position_side'),
            exchange_name=data.get('exchange')
        )
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"创建订单失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@trading_bp.route('/order/<order_id>', methods=['DELETE'])
@token_required
def cancel_order(order_id):
    """
    取消订单
    
    Query Parameters:
        symbol: 交易对（必填）
        exchange: 交易所名称
    """
    try:
        user_id = g.user_id
        symbol = request.args.get('symbol')
        if not symbol:
            return jsonify({
                'status': 'error',
                'message': '缺少参数: symbol'
            }), 400
        
        exchange = request.args.get('exchange')
        
        result = TradingService.cancel_order(
            user_id=user_id,
            symbol=symbol,
            order_id=order_id,
            exchange_name=exchange
        )
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"取消订单失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@trading_bp.route('/orders', methods=['GET'])
@token_required
def get_open_orders():
    """
    获取当前挂单
    
    Query Parameters:
        symbol: 交易对（可选）
        exchange: 交易所名称
    """
    try:
        user_id = g.user_id
        symbol = request.args.get('symbol')
        exchange = request.args.get('exchange')
        
        orders = TradingService.get_open_orders(
            user_id=user_id,
            symbol=symbol,
            exchange_name=exchange
        )
        
        return jsonify({
            'status': 'success',
            'data': orders
        })
        
    except Exception as e:
        logger.error(f"获取挂单失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@trading_bp.route('/positions', methods=['GET'])
@token_required
def get_positions():
    """
    获取持仓
    
    Query Parameters:
        symbol: 交易对（可选）
        exchange: 交易所名称
    """
    try:
        user_id = g.user_id
        symbol = request.args.get('symbol')
        exchange = request.args.get('exchange')
        
        positions = TradingService.get_positions(
            user_id=user_id,
            symbol=symbol,
            exchange_name=exchange
        )
        
        return jsonify({
            'status': 'success',
            'data': positions
        })
        
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@trading_bp.route('/position/close', methods=['POST'])
@token_required
def close_position():
    """
    平仓
    
    Body:
    {
        "symbol": "BTCUSDT",
        "position_side": "long",  // long 或 short
        "exchange": "bybit"  // 可选
    }
    """
    try:
        user_id = g.user_id
        data = request.get_json()
        
        if 'symbol' not in data or 'position_side' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少必填参数: symbol 或 position_side'
            }), 400
        
        result = TradingService.close_position(
            user_id=user_id,
            symbol=data['symbol'],
            position_side=data['position_side'],
            exchange_name=data.get('exchange')
        )
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"平仓失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@trading_bp.route('/leverage', methods=['POST'])
@token_required
def set_leverage():
    """
    设置杠杆
    
    Body:
    {
        "symbol": "BTCUSDT",
        "leverage": 10,
        "exchange": "bybit"  // 可选
    }
    """
    try:
        user_id = g.user_id
        data = request.get_json()
        
        if 'symbol' not in data or 'leverage' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少必填参数: symbol 或 leverage'
            }), 400
        
        result = TradingService.set_leverage(
            user_id=user_id,
            symbol=data['symbol'],
            leverage=int(data['leverage']),
            exchange_name=data.get('exchange')
        )
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"设置杠杆失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@trading_bp.route('/pnl', methods=['GET'])
@token_required
def get_pnl():
    """
    获取盈亏统计
    
    Query Parameters:
        symbol: 交易对（可选，不传则返回所有）
        exchange: 交易所名称
    """
    try:
        user_id = g.user_id
        symbol = request.args.get('symbol')
        exchange = request.args.get('exchange')
        
        # 获取持仓
        try:
            positions = TradingService.get_positions(
                user_id=user_id,
                symbol=symbol,
                exchange_name=exchange
            )
        except Exception as e:
            error_msg = str(e)
            if "暂时不可用" in error_msg or "Retryable error" in error_msg:
                return jsonify({
                    'status': 'error',
                    'message': 'API暂时不可用，请稍后重试',
                    'error_type': 'api_unavailable'
                }), 503
            else:
                raise
        
        # 计算总盈亏
        total_unrealized_pnl = 0.0
        position_details = []
        
        for pos in positions:
            unrealized_pnl = float(pos.get('unrealized_pnl', 0))
            total_unrealized_pnl += unrealized_pnl
            
            # 计算盈亏百分比
            entry_price = float(pos.get('entry_price', 0))
            mark_price = float(pos.get('mark_price', 0))
            size = float(pos.get('size', 0))
            
            if entry_price > 0:
                pnl_percent = ((mark_price - entry_price) / entry_price) * 100
                if pos.get('side') == 'Sell':  # 做空
                    pnl_percent = -pnl_percent
            else:
                pnl_percent = 0.0
            
            position_details.append({
                'symbol': pos.get('symbol'),
                'side': pos.get('side'),
                'size': size,
                'entry_price': entry_price,
                'mark_price': mark_price,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_percent': round(pnl_percent, 2),
                'leverage': float(pos.get('leverage', 1))
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_unrealized_pnl': round(total_unrealized_pnl, 2),
                'total_realized_pnl': 0.0,
                'position_count': len(positions),
                'positions': position_details
            }
        })
        
    except Exception as e:
        logger.error(f"获取盈亏失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@trading_bp.route('/ticker', methods=['GET'])
@token_required
def get_ticker():
    """
    获取交易对实时行情
    
    Query Parameters:
        symbol: 交易对，如 BTCUSDT（必填）
        exchange: 交易所名称，默认使用配置
    
    Returns:
        {
            "status": "success",
            "data": {
                "symbol": "BTCUSDT",
                "last_price": 106333.5,
                "bid_price": 106333.0,
                "ask_price": 106334.0,
                "high_24h": 107000.0,
                "low_24h": 105000.0,
                "volume_24h": 12345.67,
                "change_24h": 2.5,
                "timestamp": "2025-11-10T09:45:00"
            }
        }
    """
    try:
        user_id = g.user_id
        symbol = request.args.get('symbol')
        exchange = request.args.get('exchange')
        
        if not symbol:
            return jsonify({
                'status': 'error',
                'message': '缺少必填参数: symbol'
            }), 400
        
        ticker = TradingService.get_ticker(
            user_id=user_id,
            symbol=symbol,
            exchange_name=exchange
        )
        
        return jsonify({
            'status': 'success',
            'data': ticker
        })
        
    except Exception as e:
        logger.error(f"获取行情失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@trading_bp.route('/symbols', methods=['GET'])
def get_symbols():
    """
    获取所有可交易的币种列表
    
    Query Parameters:
        type: 返回类型，可选值：
            - "base": 只返回基础币种（如BTC, ETH）
            - "pairs": 返回交易对（如BTCUSDT, ETHUSDT）
            - "all": 返回所有信息（默认）
    
    Returns:
        {
            "status": "success",
            "data": {
                "base_symbols": ["BTC", "ETH", ...],  // 基础币种
                "trading_pairs": ["BTCUSDT", "ETHUSDT", ...],  // 交易对
                "count": {
                    "base_symbols": 441,
                    "trading_pairs": 1604
                }
            }
        }
    """
    try:
        return_type = request.args.get('type', 'all')
        
        # 获取基础币种
        base_symbols = get_all_symbols()
        
        # 生成交易对（所有币种 + USDT）
        trading_pairs = [f"{symbol}USDT" for symbol in base_symbols]
        
        # 根据type参数返回不同内容
        if return_type == 'base':
            return jsonify({
                'status': 'success',
                'data': {
                    'symbols': base_symbols,
                    'count': len(base_symbols)
                }
            })
        elif return_type == 'pairs':
            return jsonify({
                'status': 'success',
                'data': {
                    'symbols': trading_pairs,
                    'count': len(trading_pairs)
                }
            })
        else:  # all
            return jsonify({
                'status': 'success',
                'data': {
                    'base_symbols': base_symbols,
                    'trading_pairs': trading_pairs,
                    'count': {
                        'base_symbols': len(base_symbols),
                        'trading_pairs': len(trading_pairs)
                    }
                }
            })
        
    except Exception as e:
        logger.error(f"获取币种列表失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
