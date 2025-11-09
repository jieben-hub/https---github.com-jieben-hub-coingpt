# -*- coding: utf-8 -*-
"""测试 Token 生成和验证"""
from services.web_auth_service import WebAuthService

# 测试创建 token
user_id = 1
token = WebAuthService.create_session_token(user_id)
print(f"生成的 Token: {token[:50]}...")

# 测试验证 token
is_valid, verified_user_id = WebAuthService.verify_session_token(token)
print(f"\nToken 验证结果:")
print(f"  有效: {is_valid}")
print(f"  用户ID: {verified_user_id}")

# 测试无效 token
print(f"\n测试无效 Token:")
is_valid, verified_user_id = WebAuthService.verify_session_token("invalid_token")
print(f"  有效: {is_valid}")
print(f"  用户ID: {verified_user_id}")
