# -*- coding: utf-8 -*-
"""
对话反馈API路由模块
"""
from flask import Blueprint, request, jsonify, g
import logging
import traceback
from functools import wraps

# 导入服务类
from services.db_service import SessionService
from utils.feedback_system import FeedbackSystem
import config

# 导入Token验证装饰器
from routes.chat_routes import token_required

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('feedback_routes')

# 创建蓝图
feedback_bp = Blueprint('feedback', __name__, url_prefix='/api/feedback')

@feedback_bp.route('/rate', methods=['POST'])
@token_required
def rate_conversation():
    """
    对对话进行评分和提供反馈
    """
    try:
        # 获取请求数据
        data = request.get_json()
        session_id = data.get('session_id')
        conversation_id = data.get('conversation_id', session_id)  # 如果没有提供conversation_id，使用session_id
        rating = data.get('rating')
        feedback_text = data.get('feedback', '')
        context = data.get('context', {})
        user_id = g.user_id
        
        # 验证必要参数
        if not session_id:
            return jsonify({'status': 'error', 'message': '缺少会话ID'}), 400
            
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({'status': 'error', 'message': '评分必须是1-5之间的整数'}), 400
        
        # 验证会话是否属于当前用户
        session = SessionService.get_session(session_id)
        if not session or session.user_id != user_id:
            return jsonify({'status': 'error', 'message': '无权访问此会话或会话不存在'}), 403
        
        # 保存反馈
        result = FeedbackSystem.save_feedback(
            session_id=session_id,
            conversation_id=conversation_id,
            user_id=user_id,
            rating=rating,
            feedback_text=feedback_text,
            context=context
        )
        
        if result['status'] == 'success':
            return jsonify({
                'status': 'success',
                'message': '感谢您的反馈！',
                'data': {
                    'session_id': session_id,
                    'rating': rating
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result['message']
            }), 500
            
    except Exception as e:
        logger.error(f"保存反馈时出错: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@feedback_bp.route('/analytics', methods=['GET'])
@token_required
def get_feedback_analytics():
    """
    获取反馈分析数据
    """
    try:
        # 获取查询参数
        session_id = request.args.get('session_id')
        user_id = g.user_id
        
        # 如果提供了session_id，验证会话是否属于当前用户
        if session_id:
            session = SessionService.get_session(session_id)
            if not session or session.user_id != user_id:
                return jsonify({'status': 'error', 'message': '无权访问此会话或会话不存在'}), 403
        
        # 获取分析数据
        analytics = FeedbackSystem.analyze_feedback(session_id)
        
        return jsonify({
            'status': 'success',
            'data': analytics
        })
            
    except Exception as e:
        logger.error(f"获取反馈分析时出错: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@feedback_bp.route('/suggestions', methods=['GET'])
@token_required
def get_improvement_suggestions():
    """
    获取基于反馈的改进建议
    """
    try:
        # 获取查询参数
        count = request.args.get('count', 10, type=int)
        
        # 获取改进建议
        suggestions = FeedbackSystem.get_improvement_suggestions(count)
        
        return jsonify({
            'status': 'success',
            'data': {
                'suggestions': suggestions,
                'count': len(suggestions)
            }
        })
            
    except Exception as e:
        logger.error(f"获取改进建议时出错: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@feedback_bp.route('/rate_message', methods=['POST'])
@token_required
def rate_message():
    """
    对单条AI回复消息进行评分
    """
    try:
        # 获取请求数据
        data = request.get_json()
        message_id = data.get('message_id')  # 兼容原有参数
        assistant_id = data.get('assistant_id')  # 新增参数
        rating = data.get('rating')
        feedback_text = data.get('feedback', '')
        user_id = g.user_id
        
        # 优先使用assistant_id，如果没有则使用message_id
        actual_id = assistant_id if assistant_id is not None else message_id
        
        # 验证必要参数
        if not actual_id:
            return jsonify({'status': 'error', 'message': '缺少消息ID'}), 400
        
        # 尝试将ID转换为整数
        try:
            actual_id = int(actual_id)
        except (ValueError, TypeError):
            logger.error(f"无效的消息ID格式: {actual_id}，应为整数")
            return jsonify({'status': 'error', 'message': '消息ID必须是整数'}), 400
            
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({'status': 'error', 'message': '评分必须是1-5之间的整数'}), 400
        
        # 验证消息是否属于当前用户的会话
        message = SessionService.get_message_by_id(actual_id)
        if not message:
            logger.warning(f"消息不存在: ID={actual_id}")
            return jsonify({'status': 'error', 'message': '消息不存在'}), 404
            
        # 验证消息是否为AI助手回复
        if message.role != 'assistant':
            logger.warning(f"尝试评分非AI助手消息: ID={actual_id}, 角色={message.role}")
            return jsonify({'status': 'error', 'message': '只能评分AI助手的回复'}), 400
            
        # 获取消息所属的会话
        session = SessionService.get_session(message.session_id)
        if not session or session.user_id != user_id:
            logger.warning(f"用户{user_id}尝试访问无权限的消息: ID={actual_id}, 会话ID={message.session_id}")
            return jsonify({'status': 'error', 'message': '无权访问此消息或消息不存在'}), 403
        
        # 保存单条消息评分
        result = FeedbackSystem.save_message_feedback(
            message_id=str(actual_id),
            user_id=str(user_id),
            rating=rating,
            feedback_text=feedback_text
        )
        
        return jsonify({
            'status': 'success',
            'message': '感谢您的反馈！',
            'data': {
                'message_id': actual_id,
                'rating': rating
            }
        })
            
    except Exception as e:
        logger.error(f"保存消息评分时出错: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@feedback_bp.route('/text', methods=['POST'])
@token_required
def submit_text_feedback():
    """
    用户提交文字反馈（需登录）
    """
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        user_id = g.user_id
        if not content:
            return jsonify({'status': 'error', 'message': '反馈内容不能为空'}), 400
        from models import FeedbackText, db
        feedback = FeedbackText(user_id=user_id, content=content)
        db.session.add(feedback)
        db.session.commit()
        return jsonify({'status': 'success', 'message': '反馈已提交，感谢您的宝贵意见！'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'保存反馈失败: {e}'})
