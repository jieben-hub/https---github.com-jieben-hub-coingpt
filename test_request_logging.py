#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试请求日志是否正常显示
"""
import requests
import time
import threading

def test_requests():
    """发送测试请求"""
    base_url = "http://192.168.100.173:5000"
    
    test_endpoints = [
        "/api/version",
        "/api/chat/api/health", 
        "/api/trading/balance",
        "/api/trading/positions",
        "/api/trading/history/pnl/summary"
    ]
    
    print("🧪 开始测试请求日志...")
    print("请观察终端是否显示请求日志")
    print("-" * 50)
    
    for endpoint in test_endpoints:
        url = base_url + endpoint
        print(f"📡 发送请求: {endpoint}")
        
        try:
            response = requests.get(url, timeout=5)
            print(f"   状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   请求失败: {e}")
        
        time.sleep(1)  # 间隔1秒
    
    print("-" * 50)
    print("✅ 测试完成！")
    print("\n如果你在服务器终端看到类似以下格式的日志，说明日志正常：")
    print("🌐 GET /api/version - 192.168.100.172")
    print("📤 GET /api/version - 200")
    print("\n如果看不到日志，可能的原因：")
    print("1. 服务器没有启动")
    print("2. 日志被重定向或抑制")
    print("3. 终端缓冲问题")

if __name__ == "__main__":
    test_requests()
