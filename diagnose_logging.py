#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
诊断日志问题
"""
import sys
import os
import logging

def diagnose_logging():
    """诊断日志配置"""
    print("🔍 诊断日志配置...")
    print("=" * 50)
    
    # 1. 检查Python版本
    print(f"Python版本: {sys.version}")
    
    # 2. 检查日志配置
    root_logger = logging.getLogger()
    print(f"根日志器级别: {root_logger.level}")
    print(f"根日志器处理器数量: {len(root_logger.handlers)}")
    
    for i, handler in enumerate(root_logger.handlers):
        print(f"  处理器 {i}: {type(handler).__name__} - 级别: {handler.level}")
    
    # 3. 检查Flask相关日志器
    flask_logger = logging.getLogger('flask')
    print(f"Flask日志器级别: {flask_logger.level}")
    print(f"Flask日志器处理器数量: {len(flask_logger.handlers)}")
    
    werkzeug_logger = logging.getLogger('werkzeug')
    print(f"Werkzeug日志器级别: {werkzeug_logger.level}")
    print(f"Werkzeug日志器处理器数量: {len(werkzeug_logger.handlers)}")
    
    # 4. 测试日志输出
    print("\n📝 测试日志输出:")
    print("这是print输出")
    logging.info("这是logging.info输出")
    
    # 5. 检查环境变量
    print(f"\n🌍 环境变量:")
    print(f"PYTHONUNBUFFERED: {os.environ.get('PYTHONUNBUFFERED', '未设置')}")
    print(f"FLASK_ENV: {os.environ.get('FLASK_ENV', '未设置')}")
    print(f"FLASK_DEBUG: {os.environ.get('FLASK_DEBUG', '未设置')}")
    
    # 6. 建议
    print(f"\n💡 建议:")
    print("1. 确保终端支持UTF-8编码")
    print("2. 检查是否有其他程序重定向了输出")
    print("3. 尝试设置环境变量 PYTHONUNBUFFERED=1")
    print("4. 检查IDE或终端的日志过滤设置")
    
    print("\n🧪 运行测试:")
    print("1. 重启应用: python run.py")
    print("2. 发送测试请求: python test_request_logging.py")
    print("3. 观察终端是否显示请求日志")

if __name__ == "__main__":
    diagnose_logging()
