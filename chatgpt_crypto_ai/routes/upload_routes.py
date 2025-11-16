# -*- coding: utf-8 -*-
"""File upload routes."""
from __future__ import annotations

import logging

from flask import Blueprint, request, jsonify

from services.storage_service import R2StorageService
from services.web_auth_service import WebAuthService
from services.auth_service import AppleAuthService

upload_bp = Blueprint('upload', __name__, url_prefix='/api/upload')
logger = logging.getLogger(__name__)


def token_required(f):
    """Reuse the auth logic for uploads."""

    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].replace('Bearer ', '')
        elif request.cookies.get('token'):
            token = request.cookies.get('token')

        if not token:
            return jsonify({"status": "error", "message": "缺少认证Token"}), 401

        is_valid, user_id = WebAuthService.verify_session_token(token)
        if not is_valid or not user_id:
            is_valid, user_id = AppleAuthService.verify_session_token(token)

        if not is_valid or not user_id:
            return jsonify({"status": "error", "message": "无效或过期的Token"}), 401

        return f(user_id, *args, **kwargs)

    return decorated


@upload_bp.route('/image', methods=['POST'])
@token_required
def upload_image(user_id):
    """Receive image upload and forward to Cloudflare R2."""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "缺少文件参数(file)"}), 400

    uploaded = request.files['file']

    if uploaded.filename == '':
        return jsonify({"status": "error", "message": "文件名不能为空"}), 400

    try:
        result = R2StorageService.upload_image(
            uploaded.stream,
            uploaded.filename,
            uploaded.content_type,
        )
        logger.info("用户%d 上传图片成功 key=%s", user_id, result['key'])
        return jsonify({
            "status": "success",
            "data": {
                "url": result['url'],
                "key": result['key'],
                "content_type": result['content_type'],
            }
        })
    except ValueError as ve:
        logger.warning("用户%d 上传失败: %s", user_id, ve)
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as exc:
        logger.exception("上传图片发生错误")
        return jsonify({"status": "error", "message": "上传失败"}), 500
