# -*- coding: utf-8 -*-
"""
订阅检查服务
定期检查并处理过期的订阅
"""
import logging
from datetime import datetime
from models import db, User, Subscription

logger = logging.getLogger(__name__)


class SubscriptionChecker:
    """订阅检查器"""
    
    @staticmethod
    def check_expired_subscriptions():
        """
        检查并处理过期的订阅
        将过期订阅标记为expired，并将用户降级为免费用户
        """
        try:
            # 查找所有状态为active但已过期的订阅
            expired_subscriptions = Subscription.query.filter(
                Subscription.status == 'active',
                Subscription.expires_date < datetime.utcnow()
            ).all()
            
            if not expired_subscriptions:
                logger.info("没有过期的订阅")
                return
            
            logger.info(f"发现 {len(expired_subscriptions)} 个过期订阅")
            
            for subscription in expired_subscriptions:
                try:
                    # 更新订阅状态
                    subscription.status = 'expired'
                    subscription.updated_at = datetime.utcnow()
                    
                    # 获取用户
                    user = User.query.get(subscription.user_id)
                    if user:
                        # 检查用户是否还有其他有效订阅
                        other_active_subs = Subscription.query.filter(
                            Subscription.user_id == user.id,
                            Subscription.status == 'active',
                            Subscription.expires_date > datetime.utcnow()
                        ).first()
                        
                        if not other_active_subs:
                            # 没有其他有效订阅，降级为免费用户
                            old_membership = user.membership
                            user.membership = 'free'
                            logger.info(f"用户{user.id}订阅已过期，降级: {old_membership} -> free")
                        else:
                            logger.info(f"用户{user.id}还有其他有效订阅，保持会员状态")
                    
                    db.session.commit()
                    logger.info(f"订阅{subscription.transaction_id}已标记为过期")
                    
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"处理过期订阅{subscription.id}时出错: {e}")
                    continue
            
            logger.info(f"过期订阅检查完成，处理了 {len(expired_subscriptions)} 个订阅")
            
        except Exception as e:
            logger.error(f"检查过期订阅时发生错误: {e}")
    
    @staticmethod
    def get_expiring_soon_subscriptions(days: int = 7):
        """
        获取即将过期的订阅（用于发送提醒）
        
        Args:
            days: 多少天内过期
            
        Returns:
            List[Subscription]: 即将过期的订阅列表
        """
        from datetime import timedelta
        
        try:
            expiry_threshold = datetime.utcnow() + timedelta(days=days)
            
            expiring_soon = Subscription.query.filter(
                Subscription.status == 'active',
                Subscription.expires_date > datetime.utcnow(),
                Subscription.expires_date <= expiry_threshold
            ).all()
            
            logger.info(f"发现 {len(expiring_soon)} 个订阅将在{days}天内过期")
            return expiring_soon
            
        except Exception as e:
            logger.error(f"获取即将过期订阅时发生错误: {e}")
            return []
    
    @staticmethod
    def get_subscription_stats():
        """
        获取订阅统计信息
        
        Returns:
            Dict: 订阅统计数据
        """
        try:
            total_subscriptions = Subscription.query.count()
            active_subscriptions = Subscription.query.filter_by(status='active').count()
            expired_subscriptions = Subscription.query.filter_by(status='expired').count()
            cancelled_subscriptions = Subscription.query.filter_by(status='cancelled').count()
            
            # 统计会员用户
            premium_users = User.query.filter(User.membership != 'free').count()
            free_users = User.query.filter_by(membership='free').count()
            
            return {
                'total_subscriptions': total_subscriptions,
                'active_subscriptions': active_subscriptions,
                'expired_subscriptions': expired_subscriptions,
                'cancelled_subscriptions': cancelled_subscriptions,
                'premium_users': premium_users,
                'free_users': free_users
            }
            
        except Exception as e:
            logger.error(f"获取订阅统计时发生错误: {e}")
            return {}


def init_subscription_checker(app):
    """
    初始化订阅检查器（可选：添加定时任务）
    
    Args:
        app: Flask应用实例
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        
        scheduler = BackgroundScheduler()
        
        # 每天凌晨2点检查过期订阅
        scheduler.add_job(
            func=lambda: app.app_context().push() or SubscriptionChecker.check_expired_subscriptions(),
            trigger='cron',
            hour=2,
            minute=0,
            id='check_expired_subscriptions',
            name='检查过期订阅',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("订阅检查器定时任务已启动")
        
        return scheduler
        
    except ImportError:
        logger.warning("APScheduler未安装，订阅检查器定时任务未启动")
        logger.info("如需启用定时任务，请安装: pip install apscheduler")
        return None
    except Exception as e:
        logger.error(f"初始化订阅检查器时发生错误: {e}")
        return None
