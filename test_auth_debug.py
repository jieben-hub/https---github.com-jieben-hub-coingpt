#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试WebSocket认证参数 - 查看服务器端接收到的认证信息
"""
import socketio
import time

def test_with_auth():
    """测试使用auth参数连接"""
    print("=" * 60)
    print("🧪 测试1: 使用 auth 参数传递 token")
    print("=" * 60)
    
    sio = socketio.Client()
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0IiwiaWF0IjoxNzYyNzIxMjA3LCJleHAiOjE3NjMzMjYwMDd9.taqUsvsF4wEh44yOlZG-n5E94jQtdoVHB4l7PLmGEuk"
    
    @sio.event
    def connect():
        print("✅ 客户端：连接成功")
    
    @sio.event
    def connected(data):
        print(f"📨 客户端：收到连接确认 - {data}")
    
    @sio.event
    def connect_error(data):
        print(f"❌ 客户端：连接错误 - {data}")
    
    try:
        print(f"📡 客户端：发送连接请求...")
        print(f"   使用 auth={{'token': '{jwt_token[:30]}...'}}")
        
        # 使用auth参数传递token
        sio.connect(
            'http://192.168.100.173:5000',
            auth={'token': jwt_token}
        )
        
        time.sleep(3)
        sio.disconnect()
        print("✅ 测试1完成\n")
        
    except Exception as e:
        print(f"❌ 测试1失败: {e}\n")

def test_with_query():
    """测试使用URL参数传递token"""
    print("=" * 60)
    print("🧪 测试2: 使用 URL 参数传递 token")
    print("=" * 60)
    
    sio = socketio.Client()
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0IiwiaWF0IjoxNzYyNzIxMjA3LCJleHAiOjE3NjMzMjYwMDd9.taqUsvsF4wEh44yOlZG-n5E94jQtdoVHB4l7PLmGEuk"
    
    @sio.event
    def connect():
        print("✅ 客户端：连接成功")
    
    @sio.event
    def connected(data):
        print(f"📨 客户端：收到连接确认 - {data}")
    
    @sio.event
    def connect_error(data):
        print(f"❌ 客户端：连接错误 - {data}")
    
    try:
        print(f"📡 客户端：发送连接请求...")
        print(f"   使用 URL: http://192.168.100.173:5000?token={jwt_token[:30]}...")
        
        # 使用URL参数传递token
        sio.connect(f'http://192.168.100.173:5000?token={jwt_token}')
        
        time.sleep(3)
        sio.disconnect()
        print("✅ 测试2完成\n")
        
    except Exception as e:
        print(f"❌ 测试2失败: {e}\n")

def test_without_auth():
    """测试不传递任何认证信息"""
    print("=" * 60)
    print("🧪 测试3: 不传递任何认证信息")
    print("=" * 60)
    
    sio = socketio.Client()
    
    @sio.event
    def connect():
        print("✅ 客户端：连接成功")
    
    @sio.event
    def connect_error(data):
        print(f"❌ 客户端：连接错误 - {data}")
    
    try:
        print(f"📡 客户端：发送连接请求...")
        print(f"   不传递任何认证信息")
        
        # 不传递任何认证信息
        sio.connect('http://192.168.100.173:5000')
        
        time.sleep(3)
        sio.disconnect()
        print("✅ 测试3完成\n")
        
    except Exception as e:
        print(f"❌ 测试3失败: {e}\n")

def test_with_wrong_field():
    """测试使用错误的字段名"""
    print("=" * 60)
    print("🧪 测试4: 使用错误的字段名 (jwt 而不是 token)")
    print("=" * 60)
    
    sio = socketio.Client()
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0IiwiaWF0IjoxNzYyNzIxMjA3LCJleHAiOjE3NjMzMjYwMDd9.taqUsvsF4wEh44yOlZG-n5E94jQtdoVHB4l7PLmGEuk"
    
    @sio.event
    def connect():
        print("✅ 客户端：连接成功")
    
    @sio.event
    def connect_error(data):
        print(f"❌ 客户端：连接错误 - {data}")
    
    try:
        print(f"📡 客户端：发送连接请求...")
        print(f"   使用 auth={{'jwt': '{jwt_token[:30]}...'}}")
        
        # 使用错误的字段名
        sio.connect(
            'http://192.168.100.173:5000',
            auth={'jwt': jwt_token}  # 错误：应该是 'token' 不是 'jwt'
        )
        
        time.sleep(3)
        sio.disconnect()
        print("✅ 测试4完成\n")
        
    except Exception as e:
        print(f"❌ 测试4失败: {e}\n")

if __name__ == "__main__":
    print("\n🚀 开始WebSocket认证参数测试")
    print("请观察服务器终端的详细日志输出\n")
    
    # 运行所有测试
    test_with_auth()        # 正确方式
    time.sleep(2)
    
    test_with_query()       # URL参数方式
    time.sleep(2)
    
    test_without_auth()     # 无认证
    time.sleep(2)
    
    test_with_wrong_field() # 错误字段名
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
    print("\n📊 服务器端应该显示以下信息：")
    print("1. Request Headers - HTTP请求头")
    print("2. Request Args - URL参数")
    print("3. 认证参数类型 - auth的类型")
    print("4. 认证参数内容 - auth的完整内容")
    print("5. auth的键 - 所有字段名")
    print("6. token字段 - 如果存在")
    print("\n💡 提示：")
    print("- 测试1应该成功（使用auth参数）")
    print("- 测试2可能成功（使用URL参数）")
    print("- 测试3应该失败（无认证）")
    print("- 测试4应该失败（错误字段名）")
