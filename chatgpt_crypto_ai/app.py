# -*- coding: utf-8 -*-
"""
CoinGPT - 区块链行情聊天机器人应用主入口
"""
from flask import Flask, jsonify, render_template, session, request
from datetime import timedelta
from flask_cors import CORS
from flask_migrate import Migrate
import os
import config
from routes.chat_routes import chat_bp
from routes.auth_routes import auth_bp
from routes.show_prompt import show_prompt_bp
from routes.feedback_routes import feedback_bp
from models import db

def create_app():
    """创建并配置Flask应用"""
    app = Flask(__name__, instance_relative_config=True)
    
    # 配置应用
    app.config.from_mapping(
        SECRET_KEY=config.SECRET_KEY,
        SESSION_PERMANENT=True,
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        SQLALCHEMY_DATABASE_URI=config.DATABASE_URL,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # 数据库连接池配置
        SQLALCHEMY_ENGINE_OPTIONS={
            'pool_size': 10,
            'pool_recycle': 3600,  # 1小时回收连接
            'pool_pre_ping': True,  # 连接前先ping检查
            'max_overflow': 20,
            'pool_timeout': 30,
        }
    )
    
    # 设置会话存储
    if config.USE_REDIS:
        from redis import Redis
        from flask_session import Session
        
        # 配置Redis连接
        redis_client = Redis.from_url(config.REDIS_URL, password=config.REDIS_PASSWORD)
        app.config['SESSION_TYPE'] = 'redis'
        app.config['SESSION_REDIS'] = redis_client
        Session(app)
    else:
        app.config['SESSION_TYPE'] = 'filesystem'
        from flask_session import Session
        Session(app)
        
    # 初始化数据库
    db.init_app(app)
    
    # 初始化数据库迁移
    migrate = Migrate(app, db)
    
    # 允许跨域请求
    CORS(app)
    
    # 添加请求日志记录
    @app.before_request
    def log_request_info():
        app.logger.info('Headers: %s', request.headers)
        app.logger.info('URL: %s', request.url)
        app.logger.info('Path: %s', request.path)
        app.logger.info('Method: %s', request.method)
        app.logger.info('Blueprint: %s', request.blueprint)
        app.logger.info('Endpoint: %s', request.endpoint)
    
    # 注册路由
    app.register_blueprint(chat_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(show_prompt_bp)
    app.register_blueprint(feedback_bp)
    
    # 打印所有已注册的路由
    app.logger.info('已注册的路由:')
    for rule in app.url_map.iter_rules():
        app.logger.info(f'{rule.endpoint}: {rule.rule} [{", ".join(rule.methods)}]')
        
    # 添加版本号路由
    @app.route('/api/version', methods=['GET'])
    def api_version():
        return jsonify({
            'status': 'ok',
            'version': '0.1.0'
        })
    
    # 首页路由
    @app.route('/')
    def index():
        """返回首页"""
        return render_template('index.html')
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "资源不存在"}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "服务器内部错误"}), 500
    
    return app

# if __name__ == '__main__':
#     app = create_app()
#     port = int(os.environ.get('PORT', 5000))
#     app.run(host='0.0.0.0', port=port, debug=config.DEBUG)
