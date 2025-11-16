# -*- coding: utf-8 -*-
"""User favorite symbols routes."""
from __future__ import annotations

from functools import wraps

from flask import Blueprint, jsonify, request

from services.db_service import SymbolService
from services.auth_service import AppleAuthService
from services.web_auth_service import WebAuthService

favorite_bp = Blueprint('favorites', __name__, url_prefix='/api/favorites')


def token_required(func):
    """Shared auth decorator for favorites endpoints."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].replace('Bearer ', '')
        elif request.cookies.get('token'):
            token = request.cookies.get('token')

        if not token:
            return jsonify({'status': 'error', 'message': '缺少认证Token'}), 401

        is_valid, user_id = WebAuthService.verify_session_token(token)
        if not is_valid or not user_id:
            is_valid, user_id = AppleAuthService.verify_session_token(token)

        if not is_valid or not user_id:
            return jsonify({'status': 'error', 'message': '无效或过期的Token'}), 401

        return func(user_id, *args, **kwargs)

    return wrapper


@favorite_bp.route('', methods=['GET'])
@token_required
def list_favorites(user_id: int):
    limit_arg = request.args.get('limit')
    limit = int(limit_arg) if limit_arg else None
    symbols = SymbolService.get_user_symbols(user_id=user_id, limit=limit)
    return jsonify({'status': 'success', 'data': {'symbols': symbols}})


@favorite_bp.route('', methods=['POST'])
@token_required
def add_favorite(user_id: int):
    data = request.get_json() or {}
    symbol = data.get('symbol')
    if not symbol:
        return jsonify({'status': 'error', 'message': '缺少必填参数: symbol'}), 400

    SymbolService.add_symbol_for_user(user_id=user_id, symbol=symbol.upper())
    return jsonify({'status': 'success', 'message': '已收藏该币种'})


@favorite_bp.route('/<symbol>', methods=['DELETE'])
@token_required
def remove_favorite(user_id: int, symbol: str):
    if not symbol:
        return jsonify({'status': 'error', 'message': '缺少必填参数: symbol'}), 400

    SymbolService.remove_symbol_for_user(user_id=user_id, symbol=symbol.upper())
    return jsonify({'status': 'success', 'message': '已取消收藏该币种'})
