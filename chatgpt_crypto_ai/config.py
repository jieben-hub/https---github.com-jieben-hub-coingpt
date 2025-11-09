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
REDIS_URL = os.getenv('REDIS_URL', 'redis://104.223.121.217:6379/0')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
USE_REDIS = os.getenv('USE_REDIS', 'False').lower() == 'true'

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///coingpt.db')
