# -*- coding: utf-8 -*-
"""
同步Bybit历史交易记录到数据库
包括：已平仓位、订单历史
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from models import db, User, TradingPnlHistory, TradingOrderHistory
from services.trading_service import TradingService

logger = logging.getLogger(__name__)

FETCH_LIMIT = 100


class TradingHistorySync:
    """交易历史同步服务"""
    
    @staticmethod
    def sync_closed_positions(
        user_id: int,
        exchange_name: str = 'bybit',
        days: int = 30,
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        同步已平仓位历史
        
        Args:
            user_id: 用户ID
            exchange_name: 交易所名称
            days: 同步最近多少天的数据
            symbol: 交易对（可选，不指定则同步所有）
            
        Returns:
            Dict: 同步结果
        """
        try:
            logger.info(f"开始同步用户{user_id}的平仓历史，最近{days}天")
            
            # 获取交易所实例
            exchange = TradingService.get_exchange(user_id=user_id, exchange_name=exchange_name)
            
            # Bybit接口仅支持最大7天窗口
            sync_days = min(days, 7)

            # 计算时间范围（UTC）
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=sync_days)

            # 只有在请求小于7天窗口时才传入时间范围参数
            start_param = start_time if sync_days < 7 else None
            end_param = end_time if sync_days < 7 else None
            
            # 从Bybit获取已平仓位
            closed_pnl_list = exchange.get_closed_pnl(
                symbol=symbol,
                start_time=start_param,
                end_time=end_param,
                limit=FETCH_LIMIT
            )
            
            if not closed_pnl_list:
                logger.info(f"用户{user_id}没有平仓记录")
                return {
                    'status': 'success',
                    'message': '没有平仓记录',
                    'synced_count': 0,
                    'skipped_count': 0
                }
            
            synced_count = 0
            skipped_count = 0
            error_count = 0
            
            logger.info(f"开始处理{len(closed_pnl_list)}条平仓记录")
            
            for pnl_data in closed_pnl_list:
                try:
                    # 检查是否已存在（通过order_id去重）
                    order_id = pnl_data.get('orderId') or pnl_data.get('order_id')
                    
                    if order_id:
                        existing = TradingPnlHistory.query.filter_by(
                            user_id=user_id,
                            order_id=order_id
                        ).first()
                        
                        if existing:
                            logger.debug(f"订单{order_id}已存在，跳过")
                            skipped_count += 1
                            continue
                    
                    # 解析数据
                    symbol = pnl_data.get('symbol')
                    side = pnl_data.get('side', '').capitalize()  # Buy/Sell
                    
                    # 价格和数量
                    avg_entry_price = float(pnl_data.get('avgEntryPrice', 0))
                    avg_exit_price = float(pnl_data.get('avgExitPrice', 0))
                    qty = float(pnl_data.get('qty', 0))
                    
                    # 盈亏
                    closed_pnl = float(pnl_data.get('closedPnl', 0))
                    
                    # 计算盈亏百分比
                    if avg_entry_price > 0:
                        pnl_percentage = (closed_pnl / (avg_entry_price * qty)) * 100
                    else:
                        pnl_percentage = 0
                    
                    # 手续费
                    fee = abs(float(pnl_data.get('cumExecFee', 0)))
                    
                    # 净盈亏
                    net_pnl = closed_pnl - fee
                    
                    # 杠杆
                    leverage = float(pnl_data.get('leverage', 1))
                    
                    # 时间
                    created_time = pnl_data.get('createdTime')
                    updated_time = pnl_data.get('updatedTime')
                    
                    if created_time:
                        if isinstance(created_time, (int, float)):
                            # 数字类型的时间戳
                            open_time = datetime.fromtimestamp(int(created_time) / 1000)
                        elif isinstance(created_time, str) and created_time.isdigit():
                            # 字符串格式的数字时间戳
                            open_time = datetime.fromtimestamp(int(created_time) / 1000)
                        else:
                            # ISO格式字符串
                            open_time = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                    else:
                        open_time = datetime.utcnow()
                    
                    if updated_time:
                        if isinstance(updated_time, (int, float)):
                            # 数字类型的时间戳
                            close_time = datetime.fromtimestamp(int(updated_time) / 1000)
                        elif isinstance(updated_time, str) and updated_time.isdigit():
                            # 字符串格式的数字时间戳
                            close_time = datetime.fromtimestamp(int(updated_time) / 1000)
                        else:
                            # ISO格式字符串
                            close_time = datetime.fromisoformat(updated_time.replace('Z', '+00:00'))
                    else:
                        close_time = open_time
                    
                    # 创建记录（使用TradingPnlHistory的字段）
                    pnl_record = TradingPnlHistory(
                        user_id=user_id,
                        exchange=exchange_name,
                        symbol=symbol,
                        side=side,
                        open_time=open_time,
                        open_price=avg_entry_price,
                        open_size=qty,
                        close_time=close_time,
                        close_price=avg_exit_price,
                        close_size=qty,
                        realized_pnl=closed_pnl,
                        pnl_percentage=pnl_percentage,
                        fee=fee,
                        net_pnl=net_pnl,
                        leverage=leverage,
                        order_id=order_id
                    )
                    
                    db.session.add(pnl_record)
                    synced_count += 1
                    
                    logger.info(f"新增平仓: {symbol} {side} PnL={net_pnl} order_id={order_id}")
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"处理平仓记录失败 (order_id={pnl_data.get('orderId', 'unknown')}): {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    continue
            
            # 提交所有记录
            db.session.commit()
            
            logger.info(f"平仓同步完成: 新增{synced_count}条，跳过{skipped_count}条，失败{error_count}条")
            
            return {
                'status': 'success',
                'message': f'同步完成',
                'synced_count': synced_count,
                'skipped_count': skipped_count,
                'total_records': len(closed_pnl_list)
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"同步平仓历史失败: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'synced_count': 0,
                'skipped_count': 0
            }
    
    @staticmethod
    def sync_order_history(
        user_id: int,
        exchange_name: str = 'bybit',
        days: int = 30,
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        同步订单历史
        
        Args:
            user_id: 用户ID
            exchange_name: 交易所名称
            days: 同步最近多少天的数据
            symbol: 交易对（可选）
            
        Returns:
            Dict: 同步结果
        """
        try:
            logger.info(f"开始同步用户{user_id}的订单历史，最近{days}天")
            
            # 获取交易所实例
            exchange = TradingService.get_exchange(user_id=user_id, exchange_name=exchange_name)
            
            # Bybit接口仅支持最大7天窗口
            sync_days = min(days, 7)

            # 计算时间范围（UTC）
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=sync_days)

            start_param = start_time if sync_days < 7 else None
            end_param = end_time if sync_days < 7 else None
            
            # 从Bybit获取订单历史
            orders = exchange.get_order_history(
                symbol=symbol,
                start_time=start_param,
                end_time=end_param,
                limit=FETCH_LIMIT
            )
            
            if not orders:
                logger.info(f"用户{user_id}没有订单记录")
                return {
                    'status': 'success',
                    'message': '没有订单记录',
                    'synced_count': 0,
                    'skipped_count': 0
                }
            
            synced_count = 0
            skipped_count = 0
            error_count = 0
            
            logger.info(f"开始处理{len(orders)}条订单记录")
            
            for order_data in orders:
                try:
                    order_id = order_data.get('orderId') or order_data.get('order_id')
                    
                    if not order_id:
                        logger.warning(f"订单缺少order_id，跳过: {order_data}")
                        continue
                    
                    # 检查是否已存在
                    existing = TradingOrderHistory.query.filter_by(
                        user_id=user_id,
                        order_id=order_id
                    ).first()
                    
                    if existing:
                        # 更新状态
                        existing.status = order_data.get('orderStatus', existing.status)
                        existing.filled_quantity = float(order_data.get('cumExecQty', existing.filled_quantity))
                        existing.avg_price = float(order_data.get('avgPrice', 0)) if order_data.get('avgPrice') else existing.avg_price
                        existing.update_time = datetime.utcnow()
                        skipped_count += 1
                        logger.debug(f"订单{order_id}已存在，更新状态")
                        continue
                    
                    # 解析订单数据
                    symbol = order_data.get('symbol')
                    side = order_data.get('side', '').capitalize()
                    order_type = order_data.get('orderType', 'Market')
                    
                    qty = float(order_data.get('qty', 0))
                    price = float(order_data.get('price', 0)) if order_data.get('price') else None
                    filled_qty = float(order_data.get('cumExecQty', 0))
                    avg_price = float(order_data.get('avgPrice', 0)) if order_data.get('avgPrice') else None
                    
                    status = order_data.get('orderStatus', 'Unknown')
                    
                    # 时间
                    created_time = order_data.get('createdTime')
                    updated_time = order_data.get('updatedTime')
                    
                    if created_time:
                        if isinstance(created_time, (int, float)):
                            # 数字类型的时间戳
                            order_time = datetime.fromtimestamp(int(created_time) / 1000)
                        elif isinstance(created_time, str) and created_time.isdigit():
                            # 字符串格式的数字时间戳
                            order_time = datetime.fromtimestamp(int(created_time) / 1000)
                        else:
                            # ISO格式字符串
                            order_time = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                    else:
                        order_time = datetime.utcnow()
                    
                    if updated_time:
                        if isinstance(updated_time, (int, float)):
                            # 数字类型的时间戳
                            update_time = datetime.fromtimestamp(int(updated_time) / 1000)
                        elif isinstance(updated_time, str) and updated_time.isdigit():
                            # 字符串格式的数字时间戳
                            update_time = datetime.fromtimestamp(int(updated_time) / 1000)
                        else:
                            # ISO格式字符串
                            update_time = datetime.fromisoformat(updated_time.replace('Z', '+00:00'))
                    else:
                        update_time = order_time
                    
                    # 手续费和杠杆
                    fee = abs(float(order_data.get('cumExecFee', 0)))
                    leverage = float(order_data.get('leverage', 1))
                    
                    # 创建订单记录
                    order_record = TradingOrderHistory(
                        user_id=user_id,
                        exchange=exchange_name,
                        order_id=order_id,
                        symbol=symbol,
                        side=side,
                        order_type=order_type,
                        quantity=qty,
                        price=price,
                        filled_quantity=filled_qty,
                        avg_price=avg_price,
                        status=status,
                        order_time=order_time,
                        update_time=update_time,
                        fee=fee,
                        leverage=leverage
                    )
                    
                    db.session.add(order_record)
                    synced_count += 1
                    
                    logger.info(f"新增订单: {order_id} {symbol} {side} {status}")
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"处理订单记录失败 (order_id={order_data.get('orderId', 'unknown')}): {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    continue
            
            # 提交所有记录
            db.session.commit()
            
            logger.info(f"订单同步完成: 新增{synced_count}条，更新{skipped_count}条，失败{error_count}条")
            
            return {
                'status': 'success',
                'message': f'同步完成',
                'synced_count': synced_count,
                'skipped_count': skipped_count,
                'total_records': len(orders)
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"同步订单历史失败: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'synced_count': 0,
                'skipped_count': 0
            }
    
    @staticmethod
    def sync_all_history(
        user_id: int,
        exchange_name: str = 'bybit',
        days: int = 30,
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        同步所有历史记录（平仓+订单）
        
        Args:
            user_id: 用户ID
            exchange_name: 交易所名称
            days: 同步最近多少天的数据
            symbol: 交易对（可选）
            
        Returns:
            Dict: 同步结果
        """
        logger.info(f"开始同步用户{user_id}的所有交易历史")
        result = {
            'status': 'success',
            'message': '所有历史记录同步完成',
            'pnl_sync': None,
            'order_sync': None
        }
        try:
            # 同步平仓历史
            pnl_result = TradingHistorySync.sync_closed_positions(
                user_id=user_id,
                exchange_name=exchange_name,
                days=days,
                symbol=symbol
            )
            result['pnl_sync'] = pnl_result
            
            # 同步订单历史
            order_result = TradingHistorySync.sync_order_history(
                user_id=user_id,
                exchange_name=exchange_name,
                days=days,
                symbol=symbol
            )
            result['order_sync'] = order_result
            
            return result
        except Exception as e:
            result['status'] = 'error'
            result['message'] = str(e)
            return result
        finally:
            db.session.remove()
