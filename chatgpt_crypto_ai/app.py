# -*- coding: utf-8 -*-
"""
CoinGPT - 区块链行情聊天机器人应用主入口
"""
from flask import Flask, jsonify, render_template, session, request
from datetime import timedelta
from flask_cors import CORS
from flask_migrate import Migrate
from flask_socketio import SocketIO
import os
import logging
import config
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from routes.chat_routes import chat_bp
from routes.auth_routes import auth_bp
from routes.show_prompt import show_prompt_bp
from routes.feedback_routes import feedback_bp
from routes.trading_routes import trading_bp
from routes.exchange_api_routes import exchange_api_bp
from routes.trading_history_routes import trading_history_bp
from routes.subscription_routes import subscription_bp
from routes.admin_subscription_routes import admin_subscription_bp
from routes.upload_routes import upload_bp
from routes.favorite_routes import favorite_bp
from services.trading_websocket_service import init_trading_websocket_service
from models import db


def setup_socketio(app):
    """Configure SocketIO and trading WebSocket services."""
    try:
        import eventlet  # type: ignore
        async_mode = 'eventlet'
        allow_upgrades = True
        eventlet_available = True
    except ImportError:
        async_mode = 'threading'
        allow_upgrades = False
        eventlet_available = False

    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode=async_mode,
        allow_upgrades=allow_upgrades,
        logger=True,
        engineio_logger=True
    )

    if not eventlet_available:
        app.logger.warning(
            "Eventlet 未安装，SocketIO 将退回到长轮询模式，WebSocket 连接会被拒绝"
        )

    trading_ws = init_trading_websocket_service(socketio, app)
    logger = logging.getLogger(__name__)

    @socketio.on('connect')
    def handle_connect(auth):
        """处理WebSocket连接，验证JWT token"""
        print("=" * 60)
        print(f"🔌 WebSocket连接请求 - 来自: {request.remote_addr}")
        print(f"📋 Request Headers: {dict(request.headers)}")
        print(f"📋 Request Args: {dict(request.args)}")
        print(f"📋 认证参数类型: {type(auth)}")
        print(f"📋 认证参数内容: {auth}")
        print("=" * 60)

        try:
            import jwt

            if auth:
                print(f"✅ auth 参数存在")
                print(f"   auth 类型: {type(auth)}")
                print(f"   auth 内容: {auth}")
                if isinstance(auth, dict):
                    print(f"   auth 的键: {list(auth.keys())}")
                    for key, value in auth.items():
                        if key == 'token':
                            print(f"   ✅ 找到 token 字段: {value[:30]}..." if len(value) > 30 else f"   ✅ 找到 token 字段: {value}")
                        else:
                            print(f"   其他字段 {key}: {value}")
            else:
                print(f"❌ auth 参数为空或None")

            token = None

            if auth and 'token' in auth:
                token = auth['token']
                print(f"🔑 从 auth['token'] 获取到token: {token[:30]}...")

            elif 'Authorization' in request.headers:
                auth_header = request.headers.get('Authorization')
                print(f"🔑 从 Authorization Header 获取: {auth_header[:50]}...")
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    print(f"🔑 提取token: {token[:30]}...")
                else:
                    token = auth_header
                    print(f"🔑 直接使用Header值: {token[:30]}...")

            elif hasattr(request, 'args') and request.args.get('token'):
                token = request.args.get('token')
                print(f"🔑 从URL参数获取token: {token[:30]}...")

            if not token:
                print("❌ WebSocket连接被拒绝：缺少token")
                logger.warning("WebSocket连接被拒绝：缺少token")
                return False

            try:
                payload = jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('sub')

                if not user_id:
                    print("❌ WebSocket连接被拒绝：token中缺少用户ID")
                    logger.warning("WebSocket连接被拒绝：token中缺少用户ID")
                    return False

                session['ws_user_id'] = int(user_id)
                session['ws_authenticated'] = True

                print(f"✅ WebSocket连接成功 - 用户ID: {user_id}")
                logger.info(f"WebSocket客户端已连接，用户ID: {user_id}")
                socketio.emit('connected', {
                    'message': '连接成功',
                    'user_id': int(user_id),
                    'authenticated': True
                })
                return True

            except jwt.ExpiredSignatureError:
                print("❌ WebSocket连接被拒绝：token已过期")
                logger.warning("WebSocket连接被拒绝：token已过期")
                return False
            except jwt.InvalidTokenError:
                print("❌ WebSocket连接被拒绝：token无效")
                logger.warning("WebSocket连接被拒绝：token无效")
                return False

        except Exception as e:
            print(f"❌ WebSocket连接验证失败: {e}")
            logger.error(f"WebSocket连接验证失败: {e}")
            return False

    @socketio.on('disconnect')
    def handle_disconnect():
        user_id = session.get('ws_user_id')
        print(f"🔌 WebSocket客户端断开连接 - 来自: {request.remote_addr}")

        try:
            from flask_socketio import leave_room

            if not user_id:
                print("⚠️ 未认证用户断开连接")
                return

            print(f"👤 用户{user_id}退出所有房间")
            all_data_types = ['balance', 'positions', 'pnl', 'orders']

            for data_type in all_data_types:
                room = f"{data_type}_{user_id}"
                try:
                    leave_room(room)
                    print(f"   🚪 退出房间: {room}")
                except Exception:
                    pass

            trading_ws.unsubscribe_user(user_id, all_data_types)

            if trading_ws.ticker_subscribers:
                symbols_to_remove = []
                for symbol, subscribers in list(trading_ws.ticker_subscribers.items()):
                    if user_id in subscribers:
                        symbols_to_remove.append(symbol)
                        room = f"ticker_{symbol}_{user_id}"
                        try:
                            leave_room(room)
                            print(f"   🚪 退出行情房间: {room}")
                        except Exception:
                            pass

                if symbols_to_remove:
                    trading_ws.unsubscribe_ticker(user_id, symbols_to_remove)

            try:
                from services.trading_service import TradingService
                TradingService.clear_user_cache(user_id)
            except Exception as cache_error:
                # 清理缓存失败不应阻断断开逻辑
                logger.debug(f"清理用户{user_id}缓存失败: {cache_error}")

            print(f"✅ 用户{user_id}已退出所有房间并清理订阅")
            logger.info(f"用户{user_id}断开连接并清理所有订阅")

        except AssertionError as assertion_error:
            # 捕获 write() before start_response 等断开异常，避免异常冒泡
            if "write() before start_response" in str(assertion_error):
                print("⚠️ 客户端断开过程中 SocketIO 写入被取消，已忽略")
            else:
                print(f"⚠️ 断开连接处理出错: {assertion_error}")
        except Exception as error:
            if "write() before start_response" in str(error) or "Broken pipe" in str(error):
                print("⚠️ 客户端断开导致写入失败，已忽略")
            else:
                print(f"⚠️ 断开连接处理出错: {error}")

    @socketio.on('subscribe_trading')
    def handle_subscribe_trading(data):
        print(f"📡 收到订阅请求: {data}")
        try:
            if not session.get('ws_authenticated'):
                print("❌ 订阅失败：用户未认证")
                socketio.emit('error', {'message': '未认证，请先连接'})
                return

            user_id = session.get('ws_user_id')
            data_types = data.get('types') or data.get('subscribeTypes', [])

            print(f"👤 用户ID: {user_id}, 请求订阅: {data_types}")
            print(f"📋 原始数据字段: {list(data.keys())}")

            if not user_id:
                print("❌ 订阅失败：用户ID缺失")
                socketio.emit('error', {'message': '用户未认证'})
                return

            if not data_types:
                print("❌ 订阅失败：未指定数据类型")
                socketio.emit('error', {'message': '请指定订阅的数据类型'})
                return

            from flask_socketio import join_room, leave_room
            print(f"🔄 清理用户{user_id}的旧订阅...")

            for data_type in ['balance', 'positions', 'pnl', 'orders']:
                room = f"{data_type}_{user_id}"
                try:
                    leave_room(room)
                except Exception:
                    pass

            trading_ws.unsubscribe_user(user_id, ['balance', 'positions', 'pnl', 'orders'])

            for data_type in data_types:
                room = f"{data_type}_{user_id}"
                join_room(room)
                print(f"🚪 客户端加入房间: {room}")

            trading_ws.subscribe_user(user_id, data_types)
            socketio.emit('subscribed', {
                'user_id': user_id,
                'types': data_types,
                'status': 'success'
            })
            print(f"✅ 订阅成功 - 用户{user_id}订阅了: {data_types}")
            logger.info(f"用户{user_id}订阅了交易数据: {data_types}")

        except Exception as e:
            print(f"❌ 处理订阅失败: {e}")
            logger.error(f"处理交易订阅失败: {e}")
            socketio.emit('error', {'message': '订阅失败'})

    @socketio.on('unsubscribe_trading')
    def handle_unsubscribe_trading(data):
        print(f"📡 收到取消订阅请求: {data}")
        try:
            if not session.get('ws_authenticated'):
                print("❌ 取消订阅失败：用户未认证")
                socketio.emit('error', {'message': '未认证，请先连接'})
                return

            user_id = session.get('ws_user_id')
            data_types = data.get('types') or data.get('subscribeTypes', [])

            print(f"👤 用户ID: {user_id}, 请求取消订阅: {data_types}")
            print(f"📋 原始数据字段: {list(data.keys())}")

            if not user_id:
                print("❌ 取消订阅失败：用户ID缺失")
                socketio.emit('error', {'message': '用户未认证'})
                return

            if not data_types:
                print("❌ 取消订阅失败：未指定数据类型")
                socketio.emit('error', {'message': '请指定要取消订阅的数据类型'})
                return

            from flask_socketio import leave_room
            for data_type in data_types:
                room = f"{data_type}_{user_id}"
                leave_room(room)
                print(f"🚪 客户端离开房间: {room}")

            trading_ws.unsubscribe_user(user_id, data_types)
            socketio.emit('unsubscribed', {
                'user_id': user_id,
                'types': data_types,
                'status': 'success'
            })
            print(f"✅ 取消订阅成功 - 用户{user_id}取消了: {data_types}")
            logger.info(f"用户{user_id}取消订阅了交易数据: {data_types}")

        except Exception as e:
            print(f"❌ 处理取消订阅失败: {e}")
            logger.error(f"处理取消订阅失败: {e}")
            socketio.emit('error', {'message': '取消订阅失败'})

    @socketio.on('subscribe_ticker')
    def handle_subscribe_ticker(data):
        print(f"📊 收到行情订阅请求: {data}")
        try:
            from flask_socketio import join_room, leave_room

            if not session.get('ws_authenticated'):
                print("❌ 订阅失败：用户未认证")
                socketio.emit('error', {'message': '未认证，请先连接'})
                return

            user_id = session.get('ws_user_id')
            symbols = data.get('symbols', [])

            print(f"👤 用户ID: {user_id}, 请求订阅行情: {symbols}")

            if not user_id:
                print("❌ 订阅失败：用户ID缺失")
                socketio.emit('error', {'message': '用户未认证'})
                return

            if not symbols:
                print("❌ 订阅失败：未指定交易对")
                socketio.emit('error', {'message': '请指定要订阅的交易对'})
                return

            print(f"🔄 清理用户{user_id}的旧行情订阅...")

            if trading_ws.ticker_subscribers:
                old_symbols = []
                for symbol, subscribers in list(trading_ws.ticker_subscribers.items()):
                    if user_id in subscribers:
                        old_symbols.append(symbol)
                        room = f"ticker_{symbol}_{user_id}"
                        try:
                            leave_room(room)
                        except Exception:
                            pass

                if old_symbols:
                    trading_ws.unsubscribe_ticker(user_id, old_symbols)

            for symbol in symbols:
                room = f"ticker_{symbol}_{user_id}"
                join_room(room)
                print(f"🚪 客户端加入房间: {room}")

            trading_ws.subscribe_ticker(user_id, symbols)
            socketio.emit('ticker_subscribed', {
                'user_id': user_id,
                'symbols': symbols,
                'status': 'success'
            })
            print(f"✅ 行情订阅成功 - 用户{user_id}订阅了: {symbols}")
            logger.info(f"用户{user_id}订阅了行情: {symbols}")

        except Exception as e:
            print(f"❌ 处理行情订阅失败: {e}")
            logger.error(f"处理行情订阅失败: {e}")
            socketio.emit('error', {'message': '行情订阅失败'})

    @socketio.on('unsubscribe_ticker')
    def handle_unsubscribe_ticker(data):
        print(f"📊 收到取消行情订阅请求: {data}")
        try:
            from flask_socketio import leave_room

            if not session.get('ws_authenticated'):
                print("❌ 取消订阅失败：用户未认证")
                socketio.emit('error', {'message': '未认证，请先连接'})
                return

            user_id = session.get('ws_user_id')
            symbols = data.get('symbols', [])

            print(f"👤 用户ID: {user_id}, 请求取消订阅行情: {symbols}")

            if not user_id:
                print("❌ 取消订阅失败：用户ID缺失")
                socketio.emit('error', {'message': '用户未认证'})
                return

            if not symbols:
                print("❌ 取消订阅失败：未指定交易对")
                socketio.emit('error', {'message': '请指定要取消订阅的交易对'})
                return

            for symbol in symbols:
                room = f"ticker_{symbol}_{user_id}"
                leave_room(room)
                print(f"🚪 客户端离开房间: {room}")

            trading_ws.unsubscribe_ticker(user_id, symbols)
            socketio.emit('ticker_unsubscribed', {
                'user_id': user_id,
                'symbols': symbols,
                'status': 'success'
            })
            print(f"✅ 取消行情订阅成功 - 用户{user_id}取消了: {symbols}")
            logger.info(f"用户{user_id}取消订阅了行情: {symbols}")

        except Exception as e:
            print(f"❌ 处理取消行情订阅失败: {e}")
            logger.error(f"处理取消行情订阅失败: {e}")
            socketio.emit('error', {'message': '取消行情订阅失败'})

    trading_ws.start_service()
    app.socketio = socketio
    app.trading_ws = trading_ws

    return socketio, trading_ws


def create_app(enable_socketio: bool = True):
    """创建并配置Flask应用"""
    app = Flask(__name__, instance_relative_config=True)
    
    # 配置日志 - 确保能看到请求日志
    import logging
    
    # 只在没有配置过的情况下配置日志
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            force=True  # 强制重新配置
        )
    
    # 确保Flask和Werkzeug日志可见
    app.logger.setLevel(logging.INFO)
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    
    # 添加控制台处理器确保日志输出到终端
    if not app.logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        app.logger.addHandler(console_handler)
    
    # 配置应用
    app.config.from_mapping(
        SECRET_KEY=config.SECRET_KEY,
        SESSION_PERMANENT=True,
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        SQLALCHEMY_DATABASE_URI=config.DATABASE_URL,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS=config.SQLALCHEMY_ENGINE_OPTIONS,
    )
    
    # 设置会话存储
    if config.USE_REDIS:
        from redis import Redis
        from flask_session import Session

        retry_strategy = Retry(
            ExponentialBackoff(cap=max(2, config.REDIS_HEALTH_CHECK_INTERVAL // 2 or 1), base=1),
            retries=config.REDIS_MAX_RETRIES,
        )

        # 配置Redis连接
        redis_client = Redis.from_url(
            config.REDIS_URL,
            password=config.REDIS_PASSWORD,
            socket_timeout=config.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=config.REDIS_SOCKET_CONNECT_TIMEOUT,
            health_check_interval=config.REDIS_HEALTH_CHECK_INTERVAL,
            socket_keepalive=True,
            retry_on_timeout=True,
            retry=retry_strategy,
        )
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
    
    # 添加请求日志记录 - 简化版本
    @app.before_request
    def log_request_info():
        # 简化日志，只记录关键信息
        print(f"🌐 {request.method} {request.path} - {request.remote_addr}")
        app.logger.info(f"{request.method} {request.path} from {request.remote_addr}")
    
    @app.after_request
    def log_response_info(response):
        print(f"📤 {request.method} {request.path} - {response.status_code}")
        app.logger.info(f"Response: {response.status_code} for {request.method} {request.path}")
        return response
    
    # 注册路由
    app.register_blueprint(chat_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(show_prompt_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(trading_bp)
    app.register_blueprint(exchange_api_bp)
    app.register_blueprint(trading_history_bp)
    app.register_blueprint(subscription_bp)
    app.register_blueprint(admin_subscription_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(favorite_bp)
    
    # 初始化管理员模块
    try:
        from admin import init_admin_routes
        init_admin_routes(app)
        app.logger.info('管理员模块初始化成功')
    except Exception as e:
        app.logger.error(f'管理员模块初始化失败: {str(e)}')
    
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

    if enable_socketio:
        socketio, trading_ws = setup_socketio(app)
        app.socketio = socketio
        app.trading_ws = trading_ws
    else:
        app.socketio = None
        app.trading_ws = None

    return app

# if __name__ == '__main__':
#     app = create_app()
#     port = int(os.environ.get('PORT', 5000))
#     app.run(host='0.0.0.0', port=port, debug=config.DEBUG)
