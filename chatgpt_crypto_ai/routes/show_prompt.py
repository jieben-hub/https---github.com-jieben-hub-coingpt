# -*- coding: utf-8 -*-
"""
显示意图提取prompt的路由模�?"""
from flask import Blueprint, request, jsonify, g
import traceback
import config

# 导入服务�?from services.db_service import SessionService, MessageService
from services.auth_service import AppleAuthService
from services.web_auth_service import WebAuthService
from services.limit_service import LimitService

# 导入工具from utils.extract import extract_all_info
from utils.intent_extractor import IntentExtractor
from functools import wraps

# 创建蓝图
show_prompt_bp = Blueprint('show_prompt', __name__, url_prefix='/api/show_prompt')

# Token验证装饰器
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头或会话中获取token
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].replace('Bearer ', '')
        elif request.cookies.get('token'):
            token = request.cookies.get('token')
            
        if not token:
            return jsonify({"status": "error", "message": "缺少认证Token"}), 401
        
        # 先尝试使用Web认证服务验证token
        is_valid, user_id = WebAuthService.verify_session_token(token)
        
        # 如果不是Web登录的token，尝试使用Apple认证服务验证
        if not is_valid or not user_id:
            is_valid, user_id = AppleAuthService.verify_session_token(token)
            
        if not is_valid or not user_id:
            return jsonify({"status": "error", "message": "无效或过期的Token"}), 401
            
        # 设置用户ID到g对象供路由使用
        g.user_id = user_id
        return f(*args, **kwargs)
    return decorated

@show_prompt_bp.route('/', methods=['POST'])
@token_required
def show_intent_prompt():
    """
    仅显示意图提取的prompt，不进行后续处理
    """
    try:
        # 获取请求数据
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', None)
        user_id = g.user_id
        
        if not user_message:
            return jsonify({'status': 'error', 'message': '消息不能为空'}), 400
        
        # 获取会话消息作为上下�?        context = []
        if session_id:
            # 验证会话是否存在并属于当前用�?            session = SessionService.get_session(session_id)
            if not session or session.user_id != user_id:
                return jsonify({'status': 'error', 'message': '无效的会�?ID'}), 400
                
            # 获取会话消息
            context = MessageService.get_messages_for_context(session_id, 10)
        
        # 格式化对话历�?        # context已经是格式化好的字典列表，直接使�?        conversation_history = context
        
        # 构建意图提取prompt
        intent_prompt = IntentExtractor.build_intent_prompt(user_message, conversation_history)
        
        # 运行意图提取
        intent_data = IntentExtractor.extract_intent(user_message, conversation_history)
        
        # 获取传统提取的信息作为补�?        extracted_info = extract_all_info(user_message)
        
        return jsonify({
            'status': 'success',
            'data': {
                'intent_prompt': intent_prompt,
                'intent_result': intent_data,
                'traditional_extraction': extracted_info,
                'user_message': user_message
            }
        })
        
    except Exception as e:
        print(f"Error in show_prompt endpoint: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
