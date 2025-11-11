# -*- coding: utf-8 -*-
"""
CoinGPT 启动脚本
此脚本用于启动CoinGPT应用
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    import os
    import sys
    
    # 确保标准输出不被缓冲
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🚀 启动CoinGPT服务器，端口: {port}")
    print(f"📡 WebSocket地址: ws://0.0.0.0:{port}")
    print(f"🌐 HTTP地址: http://0.0.0.0:{port}")
    print("-" * 50)
    
    # 使用SocketIO运行应用
    app.socketio.run(
        app, 
        host='0.0.0.0', 
        port=port, 
        debug=True,
        use_reloader=False,  # 避免重复启动
        log_output=True      # 确保日志输出
    )
