# -*- coding: utf-8 -*-
"""
自动同步交易历史服务
定期从Bybit同步历史交易记录到数据库
"""
import logging
from datetime import datetime
from models import db, User
from services.sync_trading_history import TradingHistorySync

logger = logging.getLogger(__name__)


class AutoSyncService:
    """自动同步服务"""
    
    @staticmethod
    def sync_all_users_history(days: int = 7):
        """
        同步所有用户的交易历史
        
        Args:
            days: 同步最近多少天的数据
        """
        try:
            logger.info(f"开始自动同步所有用户的交易历史，最近{days}天")
            
            # 获取所有活跃用户 ID，避免持有会话绑定对象
            user_rows = User.query.filter_by(is_active=1).with_entities(User.id).all()
            user_ids = [row.id for row in user_rows]

            if not user_ids:
                logger.info("没有活跃用户需要同步")
                return
            
            # 过滤出配置了API Key的用户
            from models import ExchangeApiKey
            eligible_user_ids = []
            for user_id in user_ids:
                api_key_exists = ExchangeApiKey.query.filter_by(
                    user_id=user_id,
                    exchange='bybit'
                ).with_entities(ExchangeApiKey.id).first()

                if api_key_exists:
                    eligible_user_ids.append(user_id)
                else:
                    logger.debug(f"用户{user_id}未配置API Key，跳过同步")

            if not eligible_user_ids:
                logger.info("没有配置API Key的用户需要同步")
                return
            
            logger.info(f"找到{len(eligible_user_ids)}个配置了API Key的用户")
            
            total_synced = 0
            total_skipped = 0
            success_count = 0
            failed_count = 0
            
            for user_id in eligible_user_ids:
                try:
                    logger.info(f"同步用户{user_id}的交易历史")
                    
                    # 同步该用户的所有历史
                    result = TradingHistorySync.sync_all_history(
                        user_id=user_id,
                        exchange_name='bybit',
                        days=days,
                        symbol=None  # 同步所有交易对
                    )
                    
                    if result['status'] == 'success':
                        pnl_sync = result.get('pnl_sync', {})
                        order_sync = result.get('order_sync', {})
                        
                        pnl_synced = pnl_sync.get('synced_count', 0)
                        pnl_skipped = pnl_sync.get('skipped_count', 0)
                        order_synced = order_sync.get('synced_count', 0)
                        order_skipped = order_sync.get('skipped_count', 0)
                        
                        total_synced += pnl_synced + order_synced
                        total_skipped += pnl_skipped + order_skipped
                        success_count += 1
                        
                        logger.info(f"用户{user_id}同步完成: 平仓{pnl_synced}条, 订单{order_synced}条")
                    else:
                        failed_count += 1
                        logger.error(f"用户{user_id}同步失败: {result.get('message')}")
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"同步用户{user_id}时发生错误: {e}")
                    continue
            
            logger.info(f"自动同步完成: 成功{success_count}个用户, 失败{failed_count}个用户")
            logger.info(f"总计: 新增{total_synced}条记录, 跳过{total_skipped}条记录")
        except Exception as e:
            logger.error(f"自动同步服务发生错误: {e}")
        finally:
            db.session.remove()
    
    @staticmethod
    def sync_user_history(user_id: int, days: int = 7):
        """
        同步单个用户的交易历史
        
        Args:
            user_id: 用户ID
            days: 同步最近多少天的数据
        """
        try:
            logger.info(f"自动同步用户{user_id}的交易历史")
            
            result = TradingHistorySync.sync_all_history(
                user_id=user_id,
                exchange_name='bybit',
                days=days,
                symbol=None
            )
            
            if result['status'] == 'success':
                pnl_sync = result.get('pnl_sync', {})
                order_sync = result.get('order_sync', {})
                
                logger.info(f"用户{user_id}自动同步完成:")
                logger.info(f"  平仓记录: 新增{pnl_sync.get('synced_count', 0)}条, 跳过{pnl_sync.get('skipped_count', 0)}条")
                logger.info(f"  订单记录: 新增{order_sync.get('synced_count', 0)}条, 跳过{order_sync.get('skipped_count', 0)}条")
            else:
                logger.error(f"用户{user_id}自动同步失败: {result.get('message')}")
            
            return result
        except Exception as e:
            logger.error(f"自动同步用户{user_id}时发生错误: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
        finally:
            db.session.remove()
