# -*- coding: utf-8 -*-
"""
交易历史服务
自动记录交易历史和盈亏数据
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from models.trading_history import TradingPnlHistory, TradingOrderHistory
from services.trading_service import TradingService

logger = logging.getLogger(__name__)

class TradingHistoryService:
    """交易历史服务"""
    
    @staticmethod
    def record_position_close(user_id: int, exchange: str, position_data: Dict[str, Any],
                            close_price: float, close_size: float, close_time: datetime = None) -> Dict[str, Any]:
        """
        记录平仓盈亏
        
        Args:
            user_id: 用户ID
            exchange: 交易所名称
            position_data: 持仓数据
            close_price: 平仓价格
            close_size: 平仓数量
            close_time: 平仓时间，默认当前时间
        """
        try:
            if close_time is None:
                close_time = datetime.utcnow()
            
            # 从持仓数据中提取信息
            symbol = position_data.get('symbol')
            side = position_data.get('side')
            entry_price = float(position_data.get('entry_price', 0))
            size = float(position_data.get('size', 0))
            leverage = float(position_data.get('leverage', 1))
            
            # 计算已实现盈亏
            if side.lower() == 'buy':
                realized_pnl = (close_price - entry_price) * close_size
            else:  # sell
                realized_pnl = (entry_price - close_price) * close_size
            
            # 估算手续费 (通常是成交金额的0.1%)
            fee = close_price * close_size * 0.001
            
            # 记录盈亏历史
            result = TradingPnlHistory.add_pnl_record(
                user_id=user_id,
                exchange=exchange,
                symbol=symbol,
                side=side,
                open_time=datetime.utcnow() - timedelta(hours=1),  # 假设开仓时间
                open_price=entry_price,
                open_size=close_size,
                close_time=close_time,
                close_price=close_price,
                close_size=close_size,
                realized_pnl=realized_pnl,
                fee=fee,
                leverage=leverage,
                position_id=position_data.get('position_id')
            )
            
            logger.info(f"记录用户{user_id}平仓盈亏: {symbol} {side} {realized_pnl}")
            return result
            
        except Exception as e:
            logger.error(f"记录平仓盈亏失败: {e}")
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def record_order_update(user_id: int, exchange: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        记录订单更新
        
        Args:
            user_id: 用户ID
            exchange: 交易所名称
            order_data: 订单数据
        """
        try:
            # 解析订单数据
            order_id = order_data.get('order_id') or order_data.get('orderId')
            symbol = order_data.get('symbol')
            side = order_data.get('side')
            order_type = order_data.get('type') or order_data.get('orderType', 'Unknown')
            quantity = float(order_data.get('quantity') or order_data.get('qty', 0))
            price = order_data.get('price')
            filled_quantity = float(order_data.get('filled_quantity') or order_data.get('executedQty', 0))
            avg_price = order_data.get('avg_price') or order_data.get('avgPrice')
            status = order_data.get('status')
            
            # 时间处理
            order_time = order_data.get('order_time') or order_data.get('time')
            update_time = order_data.get('update_time') or order_data.get('updateTime')
            
            if isinstance(order_time, str):
                order_time = datetime.fromisoformat(order_time.replace('Z', '+00:00'))
            elif isinstance(order_time, (int, float)):
                order_time = datetime.fromtimestamp(order_time / 1000)
            elif order_time is None:
                order_time = datetime.utcnow()
            
            if isinstance(update_time, str):
                update_time = datetime.fromisoformat(update_time.replace('Z', '+00:00'))
            elif isinstance(update_time, (int, float)):
                update_time = datetime.fromtimestamp(update_time / 1000)
            elif update_time is None:
                update_time = datetime.utcnow()
            
            # 记录订单历史
            result = TradingOrderHistory.add_or_update_order(
                user_id=user_id,
                exchange=exchange,
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=float(price) if price else None,
                filled_quantity=filled_quantity,
                avg_price=float(avg_price) if avg_price else None,
                status=status,
                order_time=order_time,
                update_time=update_time,
                fee=float(order_data.get('fee', 0)),
                leverage=float(order_data.get('leverage', 1))
            )
            
            logger.info(f"记录用户{user_id}订单更新: {order_id} {status}")
            return result
            
        except Exception as e:
            logger.error(f"记录订单更新失败: {e}")
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def auto_sync_trading_history(user_id: int, exchange_name: str = None) -> Dict[str, Any]:
        """
        自动同步交易历史
        从交易所API获取最新的交易记录并保存到数据库
        """
        try:
            # 获取用户的持仓变化，检测是否有平仓
            current_positions = TradingService.get_positions(user_id=user_id, exchange_name=exchange_name)
            
            # 获取订单历史并记录
            orders = TradingService.get_open_orders(user_id=user_id, exchange_name=exchange_name)
            
            recorded_orders = 0
            for order in orders:
                result = TradingHistoryService.record_order_update(
                    user_id=user_id,
                    exchange=exchange_name or 'bybit',
                    order_data=order
                )
                if result.get('status') == 'success':
                    recorded_orders += 1
            
            return {
                "status": "success",
                "message": f"同步完成，记录了{recorded_orders}个订单",
                "recorded_orders": recorded_orders
            }
            
        except Exception as e:
            logger.error(f"自动同步交易历史失败: {e}")
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def detect_position_changes(user_id: int, old_positions: List[Dict], new_positions: List[Dict],
                              exchange: str = 'bybit') -> List[Dict[str, Any]]:
        """
        检测持仓变化，识别平仓操作
        
        Args:
            user_id: 用户ID
            old_positions: 旧持仓列表
            new_positions: 新持仓列表
            exchange: 交易所名称
            
        Returns:
            平仓记录列表
        """
        try:
            closed_positions = []
            
            # 创建持仓字典，便于比较
            old_pos_dict = {pos['symbol']: pos for pos in old_positions}
            new_pos_dict = {pos['symbol']: pos for pos in new_positions}
            
            # 检测完全平仓的持仓
            for symbol, old_pos in old_pos_dict.items():
                if symbol not in new_pos_dict:
                    # 持仓完全平仓
                    close_record = TradingHistoryService.record_position_close(
                        user_id=user_id,
                        exchange=exchange,
                        position_data=old_pos,
                        close_price=float(old_pos.get('mark_price', 0)),
                        close_size=float(old_pos.get('size', 0))
                    )
                    closed_positions.append({
                        'symbol': symbol,
                        'action': 'full_close',
                        'record': close_record
                    })
            
            # 检测部分平仓的持仓
            for symbol, new_pos in new_pos_dict.items():
                if symbol in old_pos_dict:
                    old_size = float(old_pos_dict[symbol].get('size', 0))
                    new_size = float(new_pos.get('size', 0))
                    
                    if new_size < old_size:
                        # 持仓减少，可能是部分平仓
                        closed_size = old_size - new_size
                        close_record = TradingHistoryService.record_position_close(
                            user_id=user_id,
                            exchange=exchange,
                            position_data=old_pos_dict[symbol],
                            close_price=float(new_pos.get('mark_price', 0)),
                            close_size=closed_size
                        )
                        closed_positions.append({
                            'symbol': symbol,
                            'action': 'partial_close',
                            'closed_size': closed_size,
                            'record': close_record
                        })
            
            return closed_positions
            
        except Exception as e:
            logger.error(f"检测持仓变化失败: {e}")
            return []
    
    @staticmethod
    def get_user_trading_performance(user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        获取用户交易表现分析
        
        Args:
            user_id: 用户ID
            days: 分析天数
            
        Returns:
            交易表现数据
        """
        try:
            from datetime import timedelta
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # 获取盈亏汇总
            summary = TradingPnlHistory.get_user_pnl_summary(
                user_id=user_id,
                start_date=start_date
            )
            
            # 获取详细记录进行分析
            records = TradingPnlHistory.get_user_pnl_history(
                user_id=user_id,
                limit=1000,
                start_date=start_date
            )
            
            # 分析交易模式
            symbol_stats = {}
            daily_pnl = {}
            
            for record in records:
                symbol = record['symbol']
                close_date = record['close_time'][:10]  # YYYY-MM-DD
                
                # 按币种统计
                if symbol not in symbol_stats:
                    symbol_stats[symbol] = {
                        'trades': 0,
                        'total_pnl': 0,
                        'win_trades': 0,
                        'lose_trades': 0
                    }
                
                symbol_stats[symbol]['trades'] += 1
                symbol_stats[symbol]['total_pnl'] += record['net_pnl']
                
                if record['net_pnl'] > 0:
                    symbol_stats[symbol]['win_trades'] += 1
                else:
                    symbol_stats[symbol]['lose_trades'] += 1
                
                # 按日期统计
                if close_date not in daily_pnl:
                    daily_pnl[close_date] = 0
                daily_pnl[close_date] += record['net_pnl']
            
            # 计算各币种胜率
            for symbol in symbol_stats:
                total = symbol_stats[symbol]['trades']
                wins = symbol_stats[symbol]['win_trades']
                symbol_stats[symbol]['win_rate'] = (wins / total * 100) if total > 0 else 0
            
            return {
                'status': 'success',
                'data': {
                    'summary': summary,
                    'symbol_performance': symbol_stats,
                    'daily_pnl': daily_pnl,
                    'analysis_period': f'{days} days',
                    'total_records': len(records)
                }
            }
            
        except Exception as e:
            logger.error(f"获取交易表现分析失败: {e}")
            return {"status": "error", "message": str(e)}

from datetime import timedelta
