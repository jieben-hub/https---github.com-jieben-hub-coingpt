#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安装WebSocket依赖
"""
import subprocess
import sys
import os

def install_dependencies():
    """安装WebSocket相关依赖"""
    dependencies = [
        'Flask-SocketIO==5.3.6',
        'websockets>=11.0.3',
        'python-socketio>=5.8.0'
    ]
    
    print("正在安装WebSocket依赖...")
    
    for dep in dependencies:
        try:
            print(f"安装 {dep}...")
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', dep
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {dep} 安装成功")
            else:
                print(f"❌ {dep} 安装失败: {result.stderr}")
                
        except Exception as e:
            print(f"❌ 安装 {dep} 时出错: {e}")
    
    print("\n依赖安装完成！")
    print("现在可以重启应用程序来使用WebSocket功能")

if __name__ == "__main__":
    install_dependencies()
