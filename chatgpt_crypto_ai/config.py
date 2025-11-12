# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# API版本配置
API_VERSION = os.getenv('API_VERSION', 'v1')
API_VERSION_PREFIX = f'/api/{API_VERSION}'

# OpenAI API配置
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
OPENAI_TIMEOUT = int(os.getenv('OPENAI_TIMEOUT', '30'))  # API超时时间，默认30秒

# 加密货币API配置
EXCHANGE = os.getenv('EXCHANGE', 'bybit')
EXCHANGE_API_KEY = os.getenv('EXCHANGE_API_KEY', '')
EXCHANGE_SECRET = os.getenv('EXCHANGE_SECRET', '')

# 应用配置
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

# Apple Sign In配置
APPLE_CLIENT_ID = os.getenv('APPLE_CLIENT_ID', '')
APPLE_TEAM_ID = os.getenv('APPLE_TEAM_ID', '')
APPLE_KEY_ID = os.getenv('APPLE_KEY_ID', '')
APPLE_PRIVATE_KEY_PATH = os.getenv('APPLE_PRIVATE_KEY_PATH', '')

# Redis配置（可选）
_raw_redis_url = os.getenv('REDIS_URL', 'redis://104.223.121.217:6379/0')
_redis_password = os.getenv('REDIS_PASSWORD', '')
USE_REDIS = os.getenv('USE_REDIS', 'False').lower() == 'true'

if _redis_password and '@' not in _raw_redis_url.split('://', 1)[-1].split('/', 1)[0]:
    # 注入密码，避免重复包含
    parts = _raw_redis_url.split('://', 1)
    scheme = parts[0]
    remainder = parts[1]
    REDIS_URL = f"{scheme}://:{_redis_password}@{remainder}"
else:
    REDIS_URL = _raw_redis_url

REDIS_PASSWORD = _redis_password
REDIS_SOCKET_TIMEOUT = float(os.getenv('REDIS_SOCKET_TIMEOUT', '5'))
REDIS_SOCKET_CONNECT_TIMEOUT = float(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', '5'))
REDIS_HEALTH_CHECK_INTERVAL = int(os.getenv('REDIS_HEALTH_CHECK_INTERVAL', '30'))
REDIS_MAX_RETRIES = int(os.getenv('REDIS_MAX_RETRIES', '5')) if os.getenv('REDIS_MAX_RETRIES', '').lower() != 'none' else None

# Celery配置
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
CELERY_TIMEZONE = os.getenv('CELERY_TIMEZONE', 'Asia/Shanghai')
CELERY_ENABLE_UTC = os.getenv('CELERY_ENABLE_UTC', 'True').lower() == 'true'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_SYNC_INTERVAL_SECONDS = int(os.getenv('CELERY_SYNC_INTERVAL_SECONDS', '30'))

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///coingpt.db')

# 交易配置
TRADING_EXCHANGE = os.getenv('TRADING_EXCHANGE', 'bybit')  # 默认交易所
TRADING_API_KEY = os.getenv('TRADING_API_KEY', '')
TRADING_API_SECRET = os.getenv('TRADING_API_SECRET', '')
TRADING_TESTNET = os.getenv('TRADING_TESTNET', 'True').lower() == 'true'  # 默认使用测试网

# SQLAlchemy连接池配置
SQLALCHEMY_POOL_SIZE = int(os.getenv('SQLALCHEMY_POOL_SIZE', '10'))
SQLALCHEMY_POOL_RECYCLE = int(os.getenv('SQLALCHEMY_POOL_RECYCLE', '3600'))
SQLALCHEMY_POOL_TIMEOUT = int(os.getenv('SQLALCHEMY_POOL_TIMEOUT', '30'))
SQLALCHEMY_MAX_OVERFLOW = int(os.getenv('SQLALCHEMY_MAX_OVERFLOW', '20'))
SQLALCHEMY_PRE_PING = os.getenv('SQLALCHEMY_PRE_PING', 'True').lower() == 'true'

SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': SQLALCHEMY_POOL_SIZE,
    'pool_recycle': SQLALCHEMY_POOL_RECYCLE,
    'pool_timeout': SQLALCHEMY_POOL_TIMEOUT,
    'max_overflow': SQLALCHEMY_MAX_OVERFLOW,
    'pool_pre_ping': SQLALCHEMY_PRE_PING,
}
