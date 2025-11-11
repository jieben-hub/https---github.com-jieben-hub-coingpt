#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试WebSocket日志输出
"""
import socketio
import time
import threading

def test_websocket_logging():
    """测试WebSocket连接和日志"""
    print("🧪 测试WebSocket日志输出...")
    print("请观察服务器终端的WebSocket日志")
    print("-" * 50)
    
    # 创建SocketIO客户端
    sio = socketio.Client()
    
    # JWT token (需要替换为有效的token)
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0IiwiaWF0IjoxNzYyNzIxMjA3LCJleHAiOjE3NjMzMjYwMDd9.taqUsvsF4wEh44yOlZG-n5E94jQtdoVHB4l7PLmGEuk"
    
    # 事件处理器
    @sio.event
    def connect():
        print("✅ 客户端：连接成功")
    
    @sio.event
    def disconnect():
        print("🔌 客户端：连接断开")
    
    @sio.event
    def connected(data):
        print(f"📨 客户端：收到连接确认 - {data}")
        
        # 订阅交易数据
        print("📡 客户端：发送订阅请求...")
        sio.emit('subscribe_trading', {
            'types': ['balance', 'positions', 'pnl', 'orders']
        })
    
    @sio.event
    def subscribed(data):
        print(f"📨 客户端：订阅成功 - {data}")
    
    @sio.event
    def error(data):
        print(f"❌ 客户端：收到错误 - {data}")
    
    @sio.event
    def balance_update(data):
        print(f"💰 客户端：收到余额更新 - {data}")
    
    @sio.event
    def positions_update(data):
        print(f"📊 客户端：收到持仓更新 - {data}")
    
    @sio.event
    def pnl_update(data):
        print(f"📈 客户端：收到盈亏更新 - {data}")
    
    @sio.event
    def orders_update(data):
        print(f"📋 客户端：收到订单更新 - {data}")
    
    try:
        # 连接到服务器
        print("🔌 客户端：尝试连接...")
        sio.connect('http://192.168.100.173:5000', auth={'token': jwt_token})
        
        # 等待一段时间接收数据
        print("⏳ 等待30秒接收数据...")
        time.sleep(30)
        
        # 测试取消订阅
        print("📡 客户端：发送取消订阅请求...")
        sio.emit('unsubscribe_trading', {
            'types': ['balance', 'positions']
        })
        
        time.sleep(5)
        
        # 断开连接
        print("🔌 客户端：断开连接...")
        sio.disconnect()
        
    except Exception as e:
        print(f"❌ 客户端：连接失败 - {e}")
    
    print("-" * 50)
    print("✅ 测试完成！")
    print("\n在服务器终端应该看到类似以下日志：")
    print("🔌 WebSocket连接请求 - 来自: 192.168.100.172")
    print("🔑 收到认证token: eyJhbGciOiJIUzI1NiIsInR5...")
    print("✅ WebSocket连接成功 - 用户ID: 4")
    print("📡 收到订阅请求: {'types': ['balance', 'positions', 'pnl', 'orders']}")
    print("👤 用户ID: 4, 请求订阅: ['balance', 'positions', 'pnl', 'orders']")
    print("📋 用户4订阅balance数据 - 当前订阅者: 1")
    print("✅ 订阅成功 - 用户4订阅了: ['balance', 'positions', 'pnl', 'orders']")
    print("📤 推送balance数据给用户4")
    print("🔌 WebSocket客户端断开连接 - 来自: 192.168.100.172")

if __name__ == "__main__":
    test_websocket_logging()
