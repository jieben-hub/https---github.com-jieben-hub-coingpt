# -*- coding: utf-8 -*-
"""
用户认证路由 - 处理用户登录、注册和会话管理
"""
from flask import Blueprint, request, jsonify, session, g
from functools import wraps
from services.auth_service import AppleAuthService
from services.web_auth_service import WebAuthService
from services.db_service import UserService, SessionService, MessageService
from services.limit_service import LimitService
from models import Session
import config

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def token_required(f):
    """Token验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头或会话中获取token
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].replace('Bearer ', '')
        elif session.get('token'):
            token = session.get('token')
            
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

@auth_bp.route('/apple/login', methods=['POST'])
def apple_login():
    """处理Apple登录"""
    import json
    import logging
    
    data = request.get_json()
    
    # 详细打印接收到的所有数据
    print("======= Apple登录接收到的完整数据 =======")
    print(f"完整请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    if not data or not data.get('id_token'):
        return jsonify({"status": "error", "message": "缺少ID Token"}), 400
    
    id_token = data.get('id_token')
    user_info = data.get('user_info', {})
    inviter_id = data.get('inviter_id')
    
    # 打印user_info详细信息
    print(f"user_info详细内容: {json.dumps(user_info, ensure_ascii=False, indent=2)}")
    print(f"user_info类型: {type(user_info)}")
    print(f"user_info包含的键: {user_info.keys() if isinstance(user_info, dict) else '非字典类型'}")
    
    # 处理登录
    result = AppleAuthService.process_login(id_token, user_info, inviter_id)
    
    if not result:
        print("登录验证失败")
        return jsonify({"status": "error", "message": "登录验证失败"}), 401
    
    # 创建会话token
    token = AppleAuthService.create_session_token(result['user_id'])
    
    # 存储token到会话
    session['token'] = token
    
    # 打印处理结果
    print(f"登录处理结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    print({
        "status": "success",
        "data": {
            "user": result,
            "token": token
        }
    })
    # 返回用户信息和token
    return jsonify({
        "status": "success",
        "data": {
            "user": result,
            "token": token
        }
    })

@auth_bp.route('/user', methods=['GET'])
@token_required
def get_user_info():
    """获取当前用户信息"""
    user_id = g.user_id
    
    # 从数据库获取用户
    user = UserService.get_user_by_id(user_id)
    
    if not user:
        return jsonify({"status": "error", "message": "用户不存在"}), 404
    
    # 返回用户信息
    return jsonify({
        "status": "success",
        "data": {
            "user_id": user.id,
            "username": user.username,
            "membership": user.membership,
            "dialog_count": user.dialog_count,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
    })

@auth_bp.route('/sessions', methods=['GET'])
@token_required
def get_user_sessions():
    """获取用户的会话列表，支持分页"""
    user_id = g.user_id
    limit = request.args.get('limit', 5, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # 获取用户会话列表
    sessions = SessionService.get_user_sessions(user_id, limit, offset)
    
    # 获取用户会话总数
    total_sessions = Session.query.filter_by(user_id=user_id).count()
    
    # 格式化返回数据
    session_data = []
    for sess in sessions:
        # 获取会话最后一条消息作为预览
        last_message = MessageService.get_session_messages(sess.id, 1)
        preview = last_message[0].content[:50] + "..." if last_message else "空会话"
        
        session_data.append({
            "session_id": sess.id,
            "created_at": sess.created_at.isoformat() if sess.created_at else None,
            "updated_at": sess.updated_at.isoformat() if sess.updated_at else None,
            "last_symbol": sess.last_symbol,
            "preview": preview
        })
    
    return jsonify({
        "status": "success",
        "data": {
            "sessions": session_data,
            "total": total_sessions,
            "limit": limit,
            "offset": offset
        }
    })

@auth_bp.route('/sessions', methods=['POST'])
@token_required
def create_new_session():
    """创建新会话，免费用户有会话数量和次数限制"""
    user_id = g.user_id

    # 检查用户是否达到会话数量限制
    can_create, error_msg = LimitService.check_session_limit(user_id)
    if not can_create:
        return jsonify({
            "status": "error",
            "message": error_msg,
            "code": "SESSION_LIMIT_REACHED"
        }), 403

    # 检查剩余会话次数（总额度-已用）
    from models import User, Session
    user = User.query.get(user_id)
    session_count = Session.query.filter_by(user_id=user_id).count()
    FREE_BASE = 5
    reward_count = user.dialog_count if user.membership == 'free' else 0
    total_quota = FREE_BASE + reward_count if user.membership == 'free' else float('inf')
    remaining_sessions = total_quota - session_count if user.membership == 'free' else float('inf')
    if user.membership == 'free' and remaining_sessions < 1:
        return jsonify({
            "status": "error",
            "message": "免费用户剩余会话次数已用完，请邀请好友或升级会员",
            "code": "DIALOG_COUNT_LIMIT"
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

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"status": "error", "message": "缺少用户名或密码"}), 400
    
    username = data.get('username')
    password = data.get('password')
    inviter_id = data.get('inviter_id')  # 邀请人ID或邀请码，可选

    # 解析邀请码
    if inviter_id and isinstance(inviter_id, str) and inviter_id.startswith('COINGPT-'):
        try:
            inviter_id = int(inviter_id.split('-')[1])
        except Exception:
            inviter_id = None

    # 处理注册
    result = WebAuthService.register_user(username, password, inviter_id)
    
    if not result:
        return jsonify({"status": "error", "message": "注册失败，用户名可能已存在"}), 400
    
    # 创建会话token
    token = WebAuthService.create_session_token(result['user_id'])
    
    # 存储token到会话
    session['token'] = token
    
    # 返回用户信息和token
    return jsonify({
        "status": "success",
        "data": {
            "user": result,
            "token": token
        }
    })

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"status": "error", "message": "缺少用户名或密码"}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    # 处理登录
    result = WebAuthService.login_user(username, password)
    
    if not result:
        return jsonify({"status": "error", "message": "登录失败，用户名或密码错误"}), 401
    
    # 创建会话token
    token = WebAuthService.create_session_token(result['user_id'])
    
    # 存储token到会话
    session['token'] = token
    
    # 返回用户信息和token
    return jsonify({
        "status": "success",
        "data": {
            "user": result,
            "token": token
        }
    })

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """用户登出"""
    # 清除会话
    session.clear()
    
    return jsonify({
        "status": "success",
        "message": "登出成功"
    })


@auth_bp.route('/invite', methods=['GET'])
@token_required
def get_invite_code():
    """获取邀请码"""
    user_id = g.user_id
    
    # 生成邀请码
    invite_code = LimitService.generate_invite_code(user_id)
    
    if not invite_code:
        return jsonify({"status": "error", "message": "生成邀请码失败"}), 400
    
    # 获取已邀请用户数量
    invitee_count = UserService.count_user_invitees(user_id)
    
    return jsonify({
        "status": "success",
        "data": {
            "invite_code": invite_code,
            "invitee_count": invitee_count
        }
    })


@auth_bp.route('/invitees', methods=['GET'])
@token_required
def get_invitees():
    """获取邀请的用户列表"""
    user_id = g.user_id
    
    # 获取邀请的用户列表
    invitees = UserService.get_user_invitees(user_id)
    
    # 格式化返回数据
    invitee_data = []
    for invitee in invitees:
        invitee_data.append({
            "user_id": invitee.id,
            "created_at": invitee.created_at.isoformat() if invitee.created_at else None
        })
    
    return jsonify({
        "status": "success",
        "data": invitee_data
    })


@auth_bp.route('/usage', methods=['GET'])
@token_required
def get_usage():
    """获取用户使用情况"""
    user_id = g.user_id
    
    # 获取用户使用情况
    usage = LimitService.get_user_usage(user_id)
    
    return jsonify(usage)


@auth_bp.route('/usage-stats', methods=['GET'])
@token_required
def get_usage_stats():
    """获取用户使用统计（与/usage接口功能相同）"""
    user_id = g.user_id
    
    # 获取用户使用情况
    usage = LimitService.get_user_usage(user_id)    
    return jsonify(usage)


@auth_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@token_required
def delete_session(session_id):
    """删除指定的会话（仅会员用户可用）"""
    user_id = g.user_id
    
    # 获取用户信息
    user = UserService.get_user_by_id(user_id)
    if not user:
        return jsonify({"status": "error", "message": "用户不存在"}), 404
    
    # 检查用户是否为免费用户
    if user.membership == 'free':
        return jsonify({
            "status": "error",
            "message": "免费用户无法删除会话，请升级会员",
            "code": "PREMIUM_REQUIRED"
        }), 403
    
    # 获取会话
    session = SessionService.get_session(session_id)
    if not session:
        return jsonify({"status": "error", "message": "会话不存在"}), 404
    
    # 检查会话是否属于当前用户
    if session.user_id != user_id:
        return jsonify({"status": "error", "message": "无权删除此会话"}), 403
    
    # 删除会话
    result = SessionService.delete_session(session_id)
    if result:
        return jsonify({
            "status": "success",
            "message": "会话已成功删除"
        })
    else:
        return jsonify({"status": "error", "message": "删除会话失败"}), 500
