#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复CoinGPT应用中的UTF-8编码问题
"""
import os
import sys
import json
import logging
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'chatgpt_crypto_ai'))

from chatgpt_crypto_ai.utils.utf8_validator import UTF8Validator

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_debug_log():
    """修复debug.log文件的UTF-8问题"""
    debug_log_path = os.path.join(os.path.dirname(__file__), 'debug.log')
    
    if not os.path.exists(debug_log_path):
        logger.info("debug.log文件不存在，跳过")
        return
    
    try:
        logger.info("正在修复debug.log文件...")
        if UTF8Validator.fix_file_encoding(debug_log_path):
            logger.info("debug.log文件修复成功")
        else:
            logger.warning("debug.log文件修复失败")
    except Exception as e:
        logger.error(f"修复debug.log时出错: {e}")

def fix_json_files():
    """修复JSON文件的UTF-8问题"""
    json_dirs = [
        'chatgpt_crypto_ai/cache',
        'chatgpt_crypto_ai/data/feedback'
    ]
    
    for json_dir in json_dirs:
        dir_path = os.path.join(os.path.dirname(__file__), json_dir)
        if not os.path.exists(dir_path):
            continue
            
        logger.info(f"正在检查目录: {dir_path}")
        
        for file_path in Path(dir_path).glob('**/*.json'):
            try:
                # 读取JSON文件
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    data = json.load(f)
                
                # 验证和清理数据
                cleaned_data = UTF8Validator.validate_json_data(data)
                
                # 重新保存
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"已修复JSON文件: {file_path}")
                
            except Exception as e:
                logger.error(f"修复JSON文件失败: {file_path}, 错误: {e}")

def check_database_connection():
    """检查数据库连接和UTF-8设置"""
    try:
        from chatgpt_crypto_ai.models import db
        from chatgpt_crypto_ai.app import create_app
        
        app = create_app()
        with app.app_context():
            # 测试数据库连接
            result = db.engine.execute("SELECT version();")
            version = result.fetchone()[0]
            logger.info(f"数据库连接正常: {version}")
            
            # 检查数据库编码设置
            result = db.engine.execute("SHOW SERVER_ENCODING;")
            encoding = result.fetchone()[0]
            logger.info(f"数据库编码: {encoding}")
            
            if encoding.upper() != 'UTF8':
                logger.warning(f"数据库编码不是UTF8: {encoding}")
                logger.info("建议设置数据库编码为UTF8")
            
    except Exception as e:
        logger.error(f"检查数据库时出错: {e}")

def create_utf8_middleware():
    """创建UTF-8中间件来处理请求和响应"""
    middleware_path = os.path.join(
        os.path.dirname(__file__), 
        'chatgpt_crypto_ai', 
        'middleware', 
        'utf8_middleware.py'
    )
    
    # 确保目录存在
    os.makedirs(os.path.dirname(middleware_path), exist_ok=True)
    
    middleware_code = '''# -*- coding: utf-8 -*-
"""
UTF-8编码中间件
确保所有HTTP请求和响应都正确处理UTF-8编码
"""
import json
import logging
from flask import request, Response, g
from functools import wraps
from utils.utf8_validator import UTF8Validator

logger = logging.getLogger(__name__)

def utf8_middleware(app):
    """
    UTF-8编码中间件
    在请求处理前后确保UTF-8编码正确
    """
    
    @app.before_request
    def before_request():
        """请求前处理"""
        try:
            # 检查请求数据的UTF-8编码
            if request.is_json and request.get_json():
                json_data = request.get_json()
                if isinstance(json_data, dict):
                    # 验证和清理JSON数据
                    cleaned_data = UTF8Validator.validate_json_data(json_data)
                    g.cleaned_json = cleaned_data
        except Exception as e:
            logger.warning(f"请求预处理UTF-8验证失败: {e}")
    
    @app.after_request
    def after_request(response):
        """响应后处理"""
        try:
            # 确保响应头设置正确的编码
            if response.content_type and 'application/json' in response.content_type:
                if 'charset' not in response.content_type:
                    response.content_type = 'application/json; charset=utf-8'
            
            # 验证响应数据
            if response.is_json and response.get_json():
                json_data = response.get_json()
                if isinstance(json_data, dict):
                    cleaned_data = UTF8Validator.validate_json_data(json_data)
                    response.data = UTF8Validator.safe_json_dumps(cleaned_data)
                    
        except Exception as e:
            logger.warning(f"响应后处理UTF-8验证失败: {e}")
        
        return response

def safe_jsonify(data, **kwargs):
    """
    安全的JSON响应函数
    确保UTF-8编码正确
    """
    try:
        cleaned_data = UTF8Validator.validate_json_data(data) if isinstance(data, dict) else data
        json_str = UTF8Validator.safe_json_dumps(cleaned_data, **kwargs)
        
        response = Response(
            json_str,
            mimetype='application/json; charset=utf-8'
        )
        return response
        
    except Exception as e:
        logger.error(f"安全JSON响应失败: {e}")
        error_response = {"status": "error", "message": "encoding_error"}
        return Response(
            json.dumps(error_response),
            mimetype='application/json; charset=utf-8',
            status=500
        )
'''
    
    try:
        with open(middleware_path, 'w', encoding='utf-8') as f:
            f.write(middleware_code)
        logger.info(f"已创建UTF-8中间件: {middleware_path}")
    except Exception as e:
        logger.error(f"创建UTF-8中间件失败: {e}")

def main():
    """主函数"""
    logger.info("开始修复CoinGPT应用的UTF-8编码问题...")
    
    # 1. 修复debug.log文件
    fix_debug_log()
    
    # 2. 修复JSON文件
    fix_json_files()
    
    # 3. 检查数据库连接
    check_database_connection()
    
    # 4. 创建UTF-8中间件
    create_utf8_middleware()
    
    logger.info("UTF-8编码问题修复完成!")
    
    # 提供使用建议
    print("\\n" + "="*50)
    print("UTF-8编码修复建议:")
    print("="*50)
    print("1. 在app.py中添加UTF-8中间件:")
    print("   from middleware.utf8_middleware import utf8_middleware, safe_jsonify")
    print("   utf8_middleware(app)")
    print()
    print("2. 替换所有jsonify调用为safe_jsonify:")
    print("   return safe_jsonify({'status': 'success', 'data': data})")
    print()
    print("3. 在处理用户输入时使用UTF8Validator:")
    print("   from utils.utf8_validator import UTF8Validator")
    print("   cleaned_text = UTF8Validator.clean_string(user_input)")
    print()
    print("4. 确保数据库连接使用UTF-8编码:")
    print("   在DATABASE_URL中添加: ?charset=utf8mb4")
    print("="*50)

if __name__ == "__main__":
    main()
