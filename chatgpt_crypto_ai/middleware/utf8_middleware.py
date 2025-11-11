# -*- coding: utf-8 -*-
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
