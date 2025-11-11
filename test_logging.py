#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试日志配置
"""
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'chatgpt_crypto_ai'))

from app import create_app
import requests
import time

def test_logging():
    """测试日志是否正常工作"""
    print("🧪 测试日志配置...")
    
    # 创建应用
    app = create_app()
    
    # 启动应用（非阻塞）
    import threading
    def run_app():
        app.socketio.run(app, host='127.0.0.1', port=5001, debug=False)
    
    server_thread = threading.Thread(target=run_app, daemon=True)
    server_thread.start()
    
    # 等待服务器启动
    time.sleep(3)
    
    print("📡 发送测试请求...")
    
    try:
        # 发送几个测试请求
        test_urls = [
            'http://127.0.0.1:5001/api/version',
            'http://127.0.0.1:5001/api/chat/api/health',
            'http://127.0.0.1:5001/api/trading/balance'
        ]
        
        for url in test_urls:
            try:
                print(f"请求: {url}")
                response = requests.get(url, timeout=5)
                print(f"响应状态: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"请求失败: {e}")
        
        print("\n✅ 测试完成！检查终端是否有日志输出")
        print("如果看不到日志，可能的原因：")
        print("1. 日志级别设置过高")
        print("2. 日志输出被重定向")
        print("3. SocketIO覆盖了Flask的日志配置")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_logging()
