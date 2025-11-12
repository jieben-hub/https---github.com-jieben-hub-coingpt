# -*- coding: utf-8 -*-
"""
iOS内购验证服务
处理App Store的收据验证和订阅管理
"""
import requests
import logging
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from models import db, User, Subscription

logger = logging.getLogger(__name__)

# App Store验证URL
SANDBOX_URL = "https://sandbox.itunes.apple.com/verifyReceipt"
PRODUCTION_URL = "https://buy.itunes.apple.com/verifyReceipt"

# 产品ID配置
PRODUCT_IDS = {
    'dev.zonekit.coingpt.Premium.year': {
        'type': 'yearly',
        'duration_days': 365,
        'membership': 'premium'
    }
}

class IAPService:
    """iOS内购服务"""
    
    @staticmethod
    def verify_receipt(receipt_data: str, user_id: int, use_sandbox: bool = False) -> Tuple[bool, str, Optional[Dict]]:
        """
        验证App Store收据
        
        Args:
            receipt_data: Base64编码的收据数据
            user_id: 用户ID
            use_sandbox: 是否使用沙盒环境
            
        Returns:
            Tuple[bool, str, Optional[Dict]]: (验证是否成功, 消息, 订阅信息)
        """
        try:
            # 选择验证URL
            verify_url = SANDBOX_URL if use_sandbox else PRODUCTION_URL
            
            # 构建验证请求
            import os
            shared_secret = os.getenv('APP_STORE_SHARED_SECRET', '')
            
            payload = {
                'receipt-data': receipt_data,
                'password': shared_secret,  # 从环境变量读取共享密钥
                'exclude-old-transactions': True
            }
            
            # 发送验证请求
            logger.info(f"验证用户{user_id}的收据，环境: {'沙盒' if use_sandbox else '生产'}")
            response = requests.post(verify_url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            status = result.get('status', -1)
            
            # 状态码说明
            # 0: 成功
            # 21007: 沙盒收据发送到生产环境
            # 21008: 生产收据发送到沙盒环境
            
            # 如果是沙盒收据发到了生产环境，自动切换到沙盒重试
            if status == 21007 and not use_sandbox:
                logger.info("检测到沙盒收据，切换到沙盒环境重试")
                return IAPService.verify_receipt(receipt_data, user_id, use_sandbox=True)
            
            # 如果是生产收据发到了沙盒环境，切换到生产重试
            if status == 21008 and use_sandbox:
                logger.info("检测到生产收据，切换到生产环境重试")
                return IAPService.verify_receipt(receipt_data, user_id, use_sandbox=False)
            
            if status != 0:
                error_messages = {
                    21000: "App Store无法读取提供的JSON数据",
                    21002: "收据数据属性格式错误",
                    21003: "收据无法验证",
                    21004: "提供的共享密钥不匹配",
                    21005: "收据服务器当前不可用",
                    21006: "收据有效但订阅已过期",
                    21010: "此收据无法验证，可能是伪造的"
                }
                error_msg = error_messages.get(status, f"未知错误，状态码: {status}")
                logger.error(f"收据验证失败: {error_msg}")
                return False, error_msg, None
            
            # 解析收据信息
            receipt = result.get('receipt', {})
            latest_receipt_info = result.get('latest_receipt_info', [])
            
            if not latest_receipt_info:
                logger.warning("收据中没有订阅信息")
                return False, "收据中没有订阅信息", None
            
            # 获取最新的订阅信息
            latest_transaction = latest_receipt_info[-1]
            product_id = latest_transaction.get('product_id')
            
            # 验证产品ID
            if product_id not in PRODUCT_IDS:
                logger.error(f"未知的产品ID: {product_id}")
                return False, f"未知的产品ID: {product_id}", None
            
            # 解析订阅时间
            expires_date_ms = latest_transaction.get('expires_date_ms')
            if not expires_date_ms:
                logger.error("收据中没有过期时间")
                return False, "收据中没有过期时间", None
            
            expires_date = datetime.fromtimestamp(int(expires_date_ms) / 1000)
            
            # 检查订阅是否过期
            if expires_date < datetime.now():
                logger.warning(f"订阅已过期: {expires_date}")
                return False, "订阅已过期", None
            
            # 构建订阅信息
            subscription_info = {
                'product_id': product_id,
                'transaction_id': latest_transaction.get('transaction_id'),
                'original_transaction_id': latest_transaction.get('original_transaction_id'),
                'purchase_date': datetime.fromtimestamp(int(latest_transaction.get('purchase_date_ms', 0)) / 1000),
                'expires_date': expires_date,
                'is_trial_period': latest_transaction.get('is_trial_period') == 'true',
                'is_in_intro_offer_period': latest_transaction.get('is_in_intro_offer_period') == 'true'
            }
            
            logger.info(f"收据验证成功，产品: {product_id}, 过期时间: {expires_date}")
            return True, "验证成功", subscription_info
            
        except requests.RequestException as e:
            logger.error(f"验证收据时网络错误: {e}")
            return False, f"网络错误: {str(e)}", None
        except Exception as e:
            logger.error(f"验证收据时发生错误: {e}")
            return False, f"验证失败: {str(e)}", None
    
    @staticmethod
    def activate_subscription(user_id: int, subscription_info: Dict) -> Tuple[bool, str]:
        """
        激活用户订阅
        
        Args:
            user_id: 用户ID
            subscription_info: 订阅信息
            
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "用户不存在"
            
            product_id = subscription_info['product_id']
            product_config = PRODUCT_IDS.get(product_id)
            
            if not product_config:
                return False, f"未知的产品ID: {product_id}"
            
            transaction_id = subscription_info['transaction_id']
            
            # 检查是否已存在该交易记录
            existing_sub = Subscription.query.filter_by(transaction_id=transaction_id).first()
            
            if existing_sub:
                # 更新现有订阅
                existing_sub.expires_date = subscription_info['expires_date']
                existing_sub.status = 'active'
                existing_sub.updated_at = datetime.utcnow()
                logger.info(f"更新现有订阅记录: {transaction_id}")
            else:
                # 创建新的订阅记录
                new_subscription = Subscription(
                    user_id=user_id,
                    product_id=product_id,
                    product_type=product_config['type'],
                    transaction_id=transaction_id,
                    original_transaction_id=subscription_info['original_transaction_id'],
                    purchase_date=subscription_info['purchase_date'],
                    expires_date=subscription_info['expires_date'],
                    status='active',
                    is_trial_period=subscription_info['is_trial_period'],
                    is_in_intro_offer_period=subscription_info['is_in_intro_offer_period']
                )
                db.session.add(new_subscription)
                logger.info(f"创建新订阅记录: {transaction_id}")
            
            # 更新用户会员状态
            old_membership = user.membership
            user.membership = product_config['membership']
            
            db.session.commit()
            
            logger.info(f"用户{user_id}订阅已激活: {old_membership} -> {user.membership}")
            logger.info(f"订阅过期时间: {subscription_info['expires_date']}")
            
            return True, f"订阅激活成功，会员有效期至 {subscription_info['expires_date'].strftime('%Y-%m-%d')}"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"激活订阅时发生错误: {e}")
            return False, f"激活失败: {str(e)}"
    
    @staticmethod
    def restore_purchases(receipt_data: str, user_id: int) -> Tuple[bool, str, Optional[Dict]]:
        """
        恢复购买
        
        Args:
            receipt_data: Base64编码的收据数据
            user_id: 用户ID
            
        Returns:
            Tuple[bool, str, Optional[Dict]]: (是否成功, 消息, 订阅信息)
        """
        logger.info(f"用户{user_id}请求恢复购买")
        
        # 验证收据
        success, message, subscription_info = IAPService.verify_receipt(receipt_data, user_id)
        
        if not success:
            return False, message, None
        
        # 激活订阅
        activate_success, activate_message = IAPService.activate_subscription(user_id, subscription_info)
        
        if not activate_success:
            return False, activate_message, None
        
        return True, "购买已恢复", subscription_info
    
    @staticmethod
    def check_subscription_status(user_id: int) -> Dict:
        """
        检查用户订阅状态
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 订阅状态信息
        """
        user = User.query.get(user_id)
        if not user:
            return {
                'status': 'error',
                'message': '用户不存在'
            }
        
        is_premium = user.membership != 'free'
        
        # 获取最新的有效订阅
        active_subscription = Subscription.query.filter_by(
            user_id=user_id,
            status='active'
        ).order_by(Subscription.expires_date.desc()).first()
        
        subscription_data = None
        if active_subscription:
            subscription_data = {
                'product_id': active_subscription.product_id,
                'product_type': active_subscription.product_type,
                'purchase_date': active_subscription.purchase_date.isoformat(),
                'expires_date': active_subscription.expires_date.isoformat(),
                'days_until_expiry': active_subscription.days_until_expiry(),
                'is_active': active_subscription.is_active(),
                'is_trial_period': active_subscription.is_trial_period,
                'auto_renew_status': active_subscription.auto_renew_status
            }
        
        return {
            'status': 'success',
            'data': {
                'user_id': user.id,
                'membership': user.membership,
                'is_premium': is_premium,
                'is_free': not is_premium,
                'subscription': subscription_data
            }
        }
