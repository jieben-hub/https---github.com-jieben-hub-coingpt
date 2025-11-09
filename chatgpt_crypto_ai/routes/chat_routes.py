# -*- coding: utf-8 -*-
"""
核心聊天API接口模块
"""
from flask import Blueprint, request, jsonify, session, g, Response
import time
import json
import os
import logging
import traceback
from functools import wraps
from openai import OpenAI

# 导入配置和数据库模型
import config
from models import db

# 导入服务类
from services.db_service import UserService, SessionService, MessageService, SymbolService
from services.auth_service import AppleAuthService
from services.web_auth_service import WebAuthService
from services.limit_service import LimitService

# 导入工具类
from utils.extract import extract_all_info
from utils.kline import KlineDataFetcher
from utils.trend_analyzer import TrendAnalyzer
from utils.prompt import PromptConstructor
from utils.intent_extractor import IntentExtractor

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('chat_routes')

# 创建蓝图
chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

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

@chat_bp.route('/show_prompt', methods=['POST'])
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
        
        # 获取会话消息作为上下文
        context = []
        if session_id:
            # 验证会话是否存在并属于当前用户
            session = SessionService.get_session(session_id)
            if not session or session.user_id != user_id:
                return jsonify({'status': 'error', 'message': '无效的会话 ID'}), 400
                
            # 检查会话是否达到消息数量限制
            can_send, error_msg = LimitService.check_message_limit(session_id)
            if not can_send:
                return jsonify({
                    'status': 'error',
                    'message': error_msg,
                    'code': 'MESSAGE_LIMIT_REACHED'
                }), 403
            
            # 获取会话消息
            context = MessageService.get_messages_for_context(session_id, 10)
        
        # 格式化对话历史
        conversation_history = []
        for msg in context:
            conversation_history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # 构建意图提取prompt
        intent_prompt = IntentExtractor.build_intent_prompt(user_message, conversation_history)
        
        # 运行意图提取
        intent_data = IntentExtractor.extract_intent(user_message, conversation_history)
        
        # 获取传统提取的信息作为补充
        extracted_info = extract_all_info(user_message)
        
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

@chat_bp.route('/', methods=['POST'])
@token_required
def chat():
    """
    处理聊天请求的API端点
    """
    try:
        # 获取请求数据
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', None)
        stream = data.get('stream', False)  # 新增流式输出参数
        user_id = g.user_id
        
        if not user_message:
            return jsonify({'status': 'error', 'message': '消息不能为空'}), 400
        
        try:
            # 从用户输入提取币种和时间范围
            crypto_info = extract_all_info(user_message)
            
            # 获取或创建会话
            if not session_id:
                # 检查用户是否达到会话数量限制
                can_create, error_msg = LimitService.check_session_limit(user_id)
                if not can_create:
                    return jsonify({
                        "status": "error",
                        "message": error_msg,
                        "code": "SESSION_LIMIT_REACHED"
                    }), 403
                    
                new_session = SessionService.create_session(user_id)
                session_id = new_session.id
            else:
                # 检查会话是否存在并属于当前用户
                session = SessionService.get_session(session_id)
                if not session or session.user_id != user_id:
                    return jsonify({'status': 'error', 'message': '无效的会话 ID'}), 400
            
            # 检查会话是否达到消息数量限制
            can_send, error_msg = LimitService.check_message_limit(session_id)
            if not can_send:
                return jsonify({
                    'status': 'error',
                    'message': error_msg,
                    'code': 'MESSAGE_LIMIT_REACHED'
                }), 403
            
            # 保存用户消息
            MessageService.create_message(session_id, "user", user_message)
            
            # 更新会话
            SessionService.touch_session(session_id)
            
            # 如果检测到币种，更新会话最后使用的币种并添加到用户币种偏好
            if crypto_info['symbols']:
                symbol = crypto_info['symbols'][0]  # 取第一个作为主要币种
                SessionService.update_session_symbol(session_id, symbol)
                SymbolService.add_symbol_for_user(user_id, symbol)
            
            # 获取会话消息作为上下文
            context = MessageService.get_messages_for_context(session_id, 10)
            
            # 增加用户对话计数
            UserService.increment_dialog_count(user_id)
            
            # 格式化对话历史用于意图提取
            # context已经是格式化好的字典列表，直接使用
            conversation_history = context
            
            # 使用意图提取器获取更精确的意图和参数，传入对话历史以支持上下文理解
            intent_data = IntentExtractor.extract_intent(user_message, conversation_history)

            # 自动补全逻辑
            # 补全币种
            if not intent_data.get('coin') or intent_data.get('coin') in [None, '', 'null', 'none']:
                try:
                    from utils.symbols_sync import get_all_symbols
                    cached_coins = set(get_all_symbols())
                except Exception:
                    cached_coins = set()
                for msg in reversed(conversation_history):
                    if msg['role'] == 'user':
                        # 用缓存币种信息智能提取
                        for coin in cached_coins:
                            if coin and coin.upper() in msg['content'].upper():
                                intent_data['coin'] = coin.upper()
                                break
                        if intent_data.get('coin'):
                            break
            # 补全时间框架
            if not intent_data.get('timeframe') or intent_data.get('timeframe') in [None, '', 'null', 'none']:
                intent_data['timeframe'] = '1h'
            # 补全意图
            if not intent_data.get('intent') or intent_data.get('intent') in [None, '', 'null', 'none']:
                intent_data['intent'] = 'chat'
            
            # 获取传统提取的信息作为补充
            extracted_info = extract_all_info(user_message)
            
            # 合并两种方法提取的信息
            symbols = []
            if intent_data.get('coin') and intent_data.get('coin').lower() not in ['null', 'none']:
                symbols.append(intent_data.get('coin').upper())
            if not symbols:  # 如果意图提取器没有找到币种，使用传统提取结果
                symbols = extracted_info.get('symbols', [])
            
            # 获取意图和时间框架
            intent = intent_data.get('intent', 'chat')
            timeframe = IntentExtractor.map_timeframe_to_system(intent_data.get('timeframe'))
            
            # 记录最终确定的处理信息
            logger.info(f"最终确定的币种: {symbols}, 时间窗口: {timeframe}, 意图: {intent}")
            
            # 整合提取的信息
            final_extracted_info = {
                "symbols": symbols,
                "time_window": timeframe,
                "intent": intent,
                "original_extraction": extracted_info,
                "context_based_extraction": intent_data  # 添加上下文感知的提取结果
            }
            
            # 收集每个币种的K线数据和分析结果
            price_data = {}
            analysis_results = {}
            
            # 检查是否为普通聊天模式
            is_chat_mode = intent == "chat" or not symbols
            
            # 只有当非聊天模式且检测到币种时才执行分析
            if not is_chat_mode and symbols:
                for symbol in symbols:
                    # 确保币种符号格式正确
                    if '/' not in symbol:
                        symbol_key = f"{symbol}/USDT"
                    else:
                        symbol_key = symbol
                        
                    # 初始化K线数据获取器
                    kline_fetcher = KlineDataFetcher()
                    # 获取K线数据
                    kline_data = kline_fetcher.get_klines(symbol_key, timeframe)
                    
                    if not kline_data.empty:
                        # 分析趋势
                        analysis = TrendAnalyzer.analyze_trend(kline_data)
                        
                        # 存储结果
                        price_data[symbol_key] = kline_data
                        analysis_results[symbol] = analysis
            
            # 构造GPT消息
            gpt_messages = PromptConstructor.construct_messages(
                user_message, 
                final_extracted_info,  # 使用合并后的提取信息
                analysis_results, 
                price_data,
                context
            )
            
            # 调用OpenAI API
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            
            # 如果请求流式输出
            if stream:
                # 使用流式输出模式调用API
                def generate():
                    full_response = ""
                    stream_response = client.chat.completions.create(
                        model=config.OPENAI_MODEL,
                        messages=gpt_messages,
                        stream=True
                    )
                    for chunk in stream_response:
                        content = chunk.choices[0].delta.content
                        if content is not None:
                            full_response += content
                            # 返回SSE格式数据
                            yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"
                    
                    # 完成后保存到数据库
                    message = MessageService.create_message(session_id, "assistant", full_response)
                    
                    # 发送完成信号，包含消息ID
                    yield f"data: {json.dumps({'content': '', 'done': True, 'message_id': message.id})}\n\n"
                
                # 返回流式响应
                return Response(generate(), mimetype='text/event-stream')
            
            # 非流式输出模式
            else:
                response = client.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    messages=gpt_messages
                )
                
                # 将AI回复添加到上下文并保存到数据库
                ai_message = response.choices[0].message.content
                MessageService.create_message(session_id, "assistant", ai_message)
                
                # 返回AI回复
                return jsonify({
                    'status': 'success',
                    'message': ai_message,
                    'session_id': session_id
                })
        
        except Exception as e:
            print(f"Error in chat endpoint: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
        

@chat_bp.route('/sessions', methods=['POST'])
@token_required
def create_new_session():
    """
    创建新会话
    """
    user_id = g.user_id
    
    # 检查用户是否达到会话数量限制
    can_create, error_msg = LimitService.check_session_limit(user_id)
    if not can_create:
        return jsonify({
            "status": "error",
            "message": error_msg,
            "code": "SESSION_LIMIT_REACHED"
        }), 403
    
    # 创建新会话
    new_session = SessionService.create_session(user_id)
    
    return jsonify({
        "status": "success",
        "data": {
            "session_id": new_session.id,
            "created_at": new_session.created_at.isoformat()
        }
    })


@chat_bp.route('/session/<session_id>', methods=['GET'])
@token_required
def get_session_messages(session_id):
    """
    获取指定会话的历史消息
    """
    try:
        # 验证会话是否属于当前用户
        user_id = g.user_id
        session = SessionService.get_session(session_id)
        
        if not session or session.user_id != user_id:
            return jsonify({'status': 'error', 'message': '无权访问此会话或会话不存在'}), 403
        
        # 获取会话所有历史消息
        messages = MessageService.get_all_session_messages(session_id)
        
        # 格式化消息数据
        formatted_messages = []
        for msg in messages:
            message_data = {
                'role': msg.role,
                'content': msg.content,
                'created_at': msg.created_at.isoformat()
            }
            
            # 根据角色使用不同的ID字段名
            if msg.role == 'assistant':
                message_data['assistant_id'] = msg.id  # AI回复使用assistant_id
            else:
                message_data['user_message_id'] = msg.id  # 用户消息使用user_message_id
            
            # 保留原始id字段以兼容现有代码
            message_data['id'] = msg.id
            
            formatted_messages.append(message_data)
        
        return jsonify({
            'status': 'success',
            'data': {
                'session_id': session_id,
                'messages': formatted_messages
            }
        })
    
    except Exception as e:
        print(f"Error getting session messages: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
        
@chat_bp.route('/api/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    """
    return jsonify({
        'status': 'ok',
        'version': '0.1.0',
    })
