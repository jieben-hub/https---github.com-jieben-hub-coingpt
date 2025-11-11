#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速测试WebSocket连接
"""
import socketio
import time

def test_connection():
    """测试WebSocket连接"""
    sio = socketio.Client()
    
    # 有效的JWT token
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0IiwiaWF0IjoxNzYyNzIxMjA3LCJleHAiOjE3NjMzMjYwMDd9.taqUsvsF4wEh44yOlZG-n5E94jQtdoVHB4l7PLmGEuk"
    
    @sio.event
    def connect():
        print("✅ 连接成功")
    
    @sio.event
    def connected(data):
        print(f"📨 收到连接确认: {data}")
        # 订阅数据
        sio.emit('subscribe_trading', {'types': ['balance', 'pnl']})
    
    @sio.event
    def subscribed(data):
        print(f"✅ 订阅成功: {data}")
    
    @sio.event
    def error(data):
        print(f"❌ 错误: {data}")
    
    try:
        print("🔌 连接到服务器...")
        sio.connect('http://192.168.100.173:5000', auth={'token': jwt_token})
        
        print("⏳ 等待10秒...")
        time.sleep(10)
        
        print("🔌 断开连接...")
        sio.disconnect()
        print("✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_connection()
