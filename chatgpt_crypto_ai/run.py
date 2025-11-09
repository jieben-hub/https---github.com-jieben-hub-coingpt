# -*- coding: utf-8 -*-
"""
CoinGPT 启动脚本
此脚本用于启动CoinGPT应用
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
