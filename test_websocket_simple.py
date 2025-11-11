#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的WebSocket测试
"""
from flask import Flask
from flask_socketio import SocketIO, emit
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test_secret_key'

# 初始化SocketIO
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',
    logger=True
)

@socketio.on('connect')
def handle_connect():
    """处理客户端连接"""
    logger.info("客户端已连接")
    emit('connected', {'message': '连接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开连接"""
    logger.info("客户端已断开连接")

@socketio.on('ping')
def handle_ping():
    """处理心跳包"""
    emit('pong', {'timestamp': str(int(time.time() * 1000))})

@socketio.on('test_message')
def handle_test_message(data):
    """处理测试消息"""
    logger.info(f"收到测试消息: {data}")
    emit('test_response', {'received': data, 'status': 'ok'})

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket测试</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    </head>
    <body>
        <h1>WebSocket测试页面</h1>
        <div id="messages"></div>
        <button onclick="sendTest()">发送测试消息</button>
        
        <script>
            const socket = io();
            
            socket.on('connect', function() {
                console.log('WebSocket连接成功');
                document.getElementById('messages').innerHTML += '<p>✅ WebSocket连接成功</p>';
            });
            
            socket.on('connected', function(data) {
                console.log('连接确认:', data);
                document.getElementById('messages').innerHTML += '<p>✅ 服务器确认: ' + data.message + '</p>';
            });
            
            socket.on('test_response', function(data) {
                console.log('测试响应:', data);
                document.getElementById('messages').innerHTML += '<p>📨 测试响应: ' + JSON.stringify(data) + '</p>';
            });
            
            socket.on('disconnect', function() {
                console.log('WebSocket连接断开');
                document.getElementById('messages').innerHTML += '<p>❌ WebSocket连接断开</p>';
            });
            
            function sendTest() {
                socket.emit('test_message', {message: 'Hello WebSocket!', timestamp: Date.now()});
            }
        </script>
    </body>
    </html>
    '''

import time

if __name__ == '__main__':
    print("启动简单WebSocket测试服务器...")
    print("访问 http://localhost:5001 进行测试")
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
