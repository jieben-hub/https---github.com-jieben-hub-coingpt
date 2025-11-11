#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API健康监控脚本
监控交易所API的健康状态和速率限制情况
"""
import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'chatgpt_crypto_ai'))

from chatgpt_crypto_ai.utils.api_rate_limiter import rate_limiter
from chatgpt_crypto_ai.exchanges.exchange_factory import ExchangeFactory

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIHealthMonitor:
    """API健康监控器"""
    
    def __init__(self):
        self.health_data = {
            'bybit': {
                'last_check': None,
                'status': 'unknown',
                'response_time': 0,
                'error_count': 0,
                'success_count': 0
            }
        }
    
    def check_exchange_health(self, exchange_name: str, test_api_key: str = None, test_secret: str = None) -> dict:
        """
        检查交易所API健康状态
        
        Args:
            exchange_name: 交易所名称
            test_api_key: 测试API密钥
            test_secret: 测试API密钥
            
        Returns:
            dict: 健康状态信息
        """
        start_time = time.time()
        status = {
            'exchange': exchange_name,
            'timestamp': datetime.now().isoformat(),
            'status': 'unknown',
            'response_time': 0,
            'error': None,
            'rate_limit_stats': None
        }
        
        try:
            if not test_api_key or not test_secret:
                logger.warning(f"没有提供{exchange_name}的API密钥，跳过连接测试")
                status['status'] = 'no_credentials'
                return status
            
            # 创建交易所实例
            exchange = ExchangeFactory.create_exchange(
                exchange_name=exchange_name,
                api_key=test_api_key,
                api_secret=test_secret,
                testnet=True  # 使用测试网
            )
            
            # 测试连接
            if exchange.connect():
                # 测试基本API调用
                try:
                    balance = exchange.get_balance('USDT')
                    status['status'] = 'healthy'
                    logger.info(f"{exchange_name} API 健康状态良好")
                except Exception as api_error:
                    if "暂时不可用" in str(api_error) or "Retryable error" in str(api_error):
                        status['status'] = 'rate_limited'
                        status['error'] = 'API rate limited or temporarily unavailable'
                    else:
                        status['status'] = 'api_error'
                        status['error'] = str(api_error)
                    logger.warning(f"{exchange_name} API 调用失败: {api_error}")
            else:
                status['status'] = 'connection_failed'
                status['error'] = 'Failed to connect to exchange'
                logger.error(f"无法连接到{exchange_name}")
                
        except Exception as e:
            status['status'] = 'error'
            status['error'] = str(e)
            logger.error(f"检查{exchange_name}健康状态时出错: {e}")
        
        # 计算响应时间
        status['response_time'] = time.time() - start_time
        
        # 获取速率限制统计
        try:
            status['rate_limit_stats'] = rate_limiter.get_stats(exchange_name)
        except Exception as e:
            logger.warning(f"获取{exchange_name}速率限制统计失败: {e}")
        
        return status
    
    def run_health_check(self, config_file: str = None) -> dict:
        """
        运行完整的健康检查
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            dict: 完整的健康检查报告
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'exchanges': {},
            'overall_status': 'unknown'
        }
        
        # 从配置文件读取API密钥（如果提供）
        test_credentials = {}
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    test_credentials = json.load(f)
            except Exception as e:
                logger.warning(f"读取配置文件失败: {e}")
        
        # 检查各个交易所
        exchanges_to_check = ['bybit']  # 可以扩展到其他交易所
        
        healthy_count = 0
        total_count = len(exchanges_to_check)
        
        for exchange_name in exchanges_to_check:
            creds = test_credentials.get(exchange_name, {})
            api_key = creds.get('api_key')
            api_secret = creds.get('api_secret')
            
            health_status = self.check_exchange_health(exchange_name, api_key, api_secret)
            report['exchanges'][exchange_name] = health_status
            
            if health_status['status'] == 'healthy':
                healthy_count += 1
        
        # 确定整体状态
        if healthy_count == total_count:
            report['overall_status'] = 'healthy'
        elif healthy_count > 0:
            report['overall_status'] = 'partial'
        else:
            report['overall_status'] = 'unhealthy'
        
        return report
    
    def save_report(self, report: dict, output_file: str = None) -> None:
        """保存健康检查报告"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'api_health_report_{timestamp}.json'
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"健康检查报告已保存到: {output_file}")
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
    
    def print_summary(self, report: dict) -> None:
        """打印健康检查摘要"""
        print("\\n" + "="*50)
        print("API 健康检查报告")
        print("="*50)
        print(f"检查时间: {report['timestamp']}")
        print(f"整体状态: {report['overall_status']}")
        print()
        
        for exchange, status in report['exchanges'].items():
            print(f"{exchange.upper()}:")
            print(f"  状态: {status['status']}")
            print(f"  响应时间: {status['response_time']:.2f}秒")
            
            if status['error']:
                print(f"  错误: {status['error']}")
            
            if status['rate_limit_stats']:
                stats = status['rate_limit_stats']
                print(f"  最近1分钟调用: {stats['calls_last_minute']}")
                print(f"  错误计数: {stats['error_count']}")
                print(f"  冷却状态: {'是' if stats['in_cooldown'] else '否'}")
            
            print()
        
        print("="*50)

def main():
    """主函数"""
    monitor = APIHealthMonitor()
    
    # 检查是否提供了配置文件
    config_file = None
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
        if not os.path.exists(config_file):
            logger.warning(f"配置文件不存在: {config_file}")
            config_file = None
    
    logger.info("开始API健康检查...")
    
    # 运行健康检查
    report = monitor.run_health_check(config_file)
    
    # 打印摘要
    monitor.print_summary(report)
    
    # 保存报告
    monitor.save_report(report)
    
    # 提供建议
    print("\\n建议:")
    print("1. 如果API状态为'rate_limited'，请等待几分钟后重试")
    print("2. 如果API状态为'connection_failed'，请检查网络连接和API密钥")
    print("3. 如果API状态为'api_error'，请检查API权限设置")
    print("4. 创建api_test_config.json文件来提供测试API密钥:")
    print("   {")
    print('     "bybit": {')
    print('       "api_key": "your_test_api_key",')
    print('       "api_secret": "your_test_api_secret"')
    print('     }')
    print("   }")

if __name__ == "__main__":
    main()
