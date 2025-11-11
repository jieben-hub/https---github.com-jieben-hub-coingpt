# -*- coding: utf-8 -*-
"""
API 速率限制器
用于管理交易所 API 调用频率，避免触发速率限制
"""
import time
import threading
from collections import defaultdict, deque
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class APIRateLimiter:
    """API 速率限制器"""
    
    def __init__(self):
        self._locks = defaultdict(threading.Lock)
        self._call_history = defaultdict(deque)
        
        # 不同交易所的速率限制配置
        self._rate_limits = {
            'bybit': {
                'requests_per_second': 10,  # 每秒最多10个请求
                'requests_per_minute': 120,  # 每分钟最多120个请求
                'burst_limit': 5,  # 突发限制
                'cooldown_after_error': 5  # 错误后冷却时间（秒）
            },
            'binance': {
                'requests_per_second': 20,
                'requests_per_minute': 1200,
                'burst_limit': 10,
                'cooldown_after_error': 3
            }
        }
        
        # 错误计数器
        self._error_counts = defaultdict(int)
        self._last_error_time = defaultdict(float)
    
    def wait_if_needed(self, exchange: str, endpoint: str = 'default') -> None:
        """
        如果需要，等待以避免超过速率限制
        
        Args:
            exchange: 交易所名称
            endpoint: API端点名称
        """
        key = f"{exchange}:{endpoint}"
        
        with self._locks[key]:
            now = time.time()
            config = self._rate_limits.get(exchange.lower(), self._rate_limits['bybit'])
            
            # 检查是否在错误冷却期
            if self._should_cooldown(exchange, now, config):
                cooldown_time = config['cooldown_after_error']
                logger.warning(f"{exchange} API 在冷却期，等待 {cooldown_time} 秒")
                time.sleep(cooldown_time)
                self._error_counts[exchange] = 0
            
            # 清理过期的调用记录
            self._cleanup_old_calls(key, now)
            
            # 检查每秒限制
            recent_calls = [t for t in self._call_history[key] if now - t < 1.0]
            if len(recent_calls) >= config['requests_per_second']:
                wait_time = 1.0 - (now - recent_calls[0])
                if wait_time > 0:
                    logger.debug(f"达到每秒限制，等待 {wait_time:.2f} 秒")
                    time.sleep(wait_time)
            
            # 检查每分钟限制
            minute_calls = [t for t in self._call_history[key] if now - t < 60.0]
            if len(minute_calls) >= config['requests_per_minute']:
                wait_time = 60.0 - (now - minute_calls[0])
                if wait_time > 0:
                    logger.warning(f"达到每分钟限制，等待 {wait_time:.2f} 秒")
                    time.sleep(wait_time)
            
            # 记录本次调用
            self._call_history[key].append(time.time())
    
    def record_error(self, exchange: str) -> None:
        """
        记录API错误
        
        Args:
            exchange: 交易所名称
        """
        self._error_counts[exchange] += 1
        self._last_error_time[exchange] = time.time()
        
        logger.warning(f"{exchange} API 错误计数: {self._error_counts[exchange]}")
    
    def record_success(self, exchange: str) -> None:
        """
        记录API成功调用，重置错误计数
        
        Args:
            exchange: 交易所名称
        """
        if self._error_counts[exchange] > 0:
            logger.info(f"{exchange} API 恢复正常，重置错误计数")
            self._error_counts[exchange] = 0
    
    def _should_cooldown(self, exchange: str, now: float, config: Dict) -> bool:
        """检查是否应该进入冷却期"""
        if self._error_counts[exchange] < 3:  # 少于3次错误不需要冷却
            return False
        
        last_error = self._last_error_time.get(exchange, 0)
        return now - last_error < config['cooldown_after_error']
    
    def _cleanup_old_calls(self, key: str, now: float) -> None:
        """清理过期的调用记录"""
        history = self._call_history[key]
        while history and now - history[0] > 60.0:  # 保留最近1分钟的记录
            history.popleft()
    
    def get_stats(self, exchange: str) -> Dict:
        """
        获取速率限制统计信息
        
        Args:
            exchange: 交易所名称
            
        Returns:
            Dict: 统计信息
        """
        now = time.time()
        key = f"{exchange}:default"
        
        recent_calls = [t for t in self._call_history[key] if now - t < 60.0]
        
        return {
            'exchange': exchange,
            'calls_last_minute': len(recent_calls),
            'error_count': self._error_counts[exchange],
            'last_error_time': self._last_error_time.get(exchange, 0),
            'in_cooldown': self._should_cooldown(
                exchange, 
                now, 
                self._rate_limits.get(exchange.lower(), self._rate_limits['bybit'])
            )
        }

# 全局速率限制器实例
rate_limiter = APIRateLimiter()

def with_rate_limit(exchange: str, endpoint: str = 'default'):
    """
    装饰器：为API调用添加速率限制
    
    Args:
        exchange: 交易所名称
        endpoint: API端点名称
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # 等待速率限制
                rate_limiter.wait_if_needed(exchange, endpoint)
                
                # 执行API调用
                result = func(*args, **kwargs)
                
                # 记录成功
                rate_limiter.record_success(exchange)
                
                return result
                
            except Exception as e:
                # 记录错误
                rate_limiter.record_error(exchange)
                
                # 如果是速率限制错误，额外等待
                if any(keyword in str(e).lower() for keyword in ['rate limit', 'too many requests', 'retryable error']):
                    logger.warning(f"{exchange} API 速率限制，额外等待 2 秒")
                    time.sleep(2)
                
                raise e
        
        return wrapper
    return decorator
