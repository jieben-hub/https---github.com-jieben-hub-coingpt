# -*- coding: utf-8 -*-
"""
认证服务模块 - 处理用户登录认证和令牌验证
"""
import time
import json
from typing import Dict, Any, Optional, Tuple
import jwt
import requests
from jose import jwk, jwt as jose_jwt
from jose.utils import base64url_decode
import config
from services.db_service import UserService

class AppleAuthService:
    """Apple认证服务"""
    
    @staticmethod
    def verify_apple_token(id_token: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        验证Apple ID令牌
        
        参数:
            id_token: 从Apple获取的ID令牌
        
        返回:
            (验证是否成功, 用户标识符(sub), 完整的用户信息)
        """
        try:
            print(f"开始验证Apple ID令牌: {id_token[:10]}...")
            print(f"当前配置的APPLE_CLIENT_ID: {config.APPLE_CLIENT_ID}")
            
            # 获取Apple公钥
            apple_public_keys_url = "https://appleid.apple.com/auth/keys"
            print(f"正在获取Apple公钥: {apple_public_keys_url}")
            response = requests.get(apple_public_keys_url)
            if response.status_code != 200:
                print(f"获取Apple公钥失败: HTTP {response.status_code}")
                return False, None, None
                
            apple_public_keys = response.json()
            print(f"成功获取Apple公钥: {len(apple_public_keys.get('keys', []))}个密钥")
                
            # 解码JWT头部以获取kid(密钥ID)
            try:
                header = jose_jwt.get_unverified_header(id_token)
                kid = header['kid']
                print(f"解析JWT头部成功，获取到kid: {kid}")
            except Exception as e:
                print(f"解析JWT头部失败: {str(e)}")
                return False, None, None
                
            # 找到对应的公钥
            public_key = None
            for key_info in apple_public_keys['keys']:
                if key_info['kid'] == kid:
                    try:
                        public_key = jwk.construct(key_info)
                        print(f"找到匹配的公钥并成功构造")
                        break
                    except Exception as e:
                        print(f"构造公钥失败: {str(e)}")
                        return False, None, None
            
            if not public_key:
                print(f"未找到匹配的公钥，kid: {kid}")
                return False, None, None
                
            # 验证令牌
            try:
                message, encoded_signature = id_token.rsplit('.', 1)
                decoded_signature = base64url_decode(encoded_signature.encode())
                
                if not public_key.verify(message.encode(), decoded_signature):
                    print("签名验证失败")
                    return False, None, None
                    
                print("签名验证成功")
            except Exception as e:
                print(f"签名验证过程异常: {str(e)}")
                return False, None, None
                
            # 解码并验证声明
            try:
                claims = jose_jwt.get_unverified_claims(id_token)
                print(f"成功解析JWT声明: {claims.keys()}")
                
                # 验证iss, aud和过期时间
                if claims['iss'] != 'https://appleid.apple.com':
                    print(f"iss验证失败: {claims['iss']} != https://appleid.apple.com")
                    return False, None, None
                
                if claims['aud'] != config.APPLE_CLIENT_ID:
                    print(f"aud验证失败: {claims['aud']} != {config.APPLE_CLIENT_ID}")
                    return False, None, None
                
                current_time = time.time()
                if current_time > claims['exp']:
                    print(f"令牌已过期: 当前时间 {current_time} > 过期时间 {claims['exp']}")
                    return False, None, None
                    
                print("所有声明验证通过")
            except Exception as e:
                print(f"验证声明过程异常: {str(e)}")
                return False, None, None
                
            # 返回验证结果和用户标识
            print(f"验证成功，用户标识: {claims['sub'][:5]}...")
            return True, claims['sub'], claims
            
        except Exception as e:
            import traceback
            print(f"Apple令牌验证异常: {str(e)}")
            print(f"异常详情: {traceback.format_exc()}")
            return False, None, None
    
    @staticmethod
    def process_login(id_token: str, user_info: Optional[Dict[str, Any]] = None, inviter_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        处理Apple登录流程
        
        参数:
            id_token: 从Apple获取的ID令牌
            user_info: 用户附加信息(可选)
            inviter_id: 邀请人ID(可选)
            
        返回:
            用户信息字典，失败则返回None
        """
        import json
        
        print("======= 开始处理Apple登录 =======")
        print(f"收到的user_info: {json.dumps(user_info, ensure_ascii=False) if user_info else 'None'}")
        
        # 验证令牌
        is_valid, sub, claims = AppleAuthService.verify_apple_token(id_token)
        if not is_valid or not sub:
            print("令牌验证失败，无法处理登录")
            return None
        
        # 打印完整的claims信息
        print("======= JWT令牌解析结果 =======")
        print(f"完整claims数据: {json.dumps(claims, ensure_ascii=False, indent=2)}")
        
        # 从user_info中提取姓名信息，用于创建用户名
        username = None
        if user_info and isinstance(user_info, dict) and 'name' in user_info:
            name_info = user_info.get('name', {})
            first_name = name_info.get('firstName', '')
            last_name = name_info.get('lastName', '')
            if first_name or last_name:
                # 中文习惯是姓在前，名在后
                username = f"{last_name}{first_name}"
                print(f"从user_info中提取姓名并生成用户名: {username}")
            else:
                print("user_info中的姓名信息为空")
        else:
            print("user_info中不包含姓名信息，无法生成用户名")
        
        # 提取email信息
        email = None
        if 'email' in claims:
            email = claims['email']
            print(f"JWT中包含email: {email}")
            print(f"email_verified: {claims.get('email_verified', False)}")
            
            # 如果没有从姓名生成用户名，可以考虑使用email的前缀作为备选
            if not username and email:
                email_prefix = email.split('@')[0]
                if email_prefix:
                    username = email_prefix
                    print(f"使用email前缀作为用户名: {username}")
        else:
            print("JWT中不包含email信息")
        
        # 获取或创建用户，传入生成的用户名和email
        user = UserService.get_or_create_user(sub, username, email, inviter_id)
        
        # 检查用户是否成功创建
        if not user:
            print(f"错误: 无法获取或创建用户，apple_sub={sub}, username={username}")
            return None
            
        print(f"用户信息: ID={user.id}, apple_sub={user.apple_sub}, username={user.username}")
        
        # 更新登录时间
        UserService.update_last_login(user.id)
        
        # 返回用户信息
        result = {
            "user_id": user.id,
            "sub": user.apple_sub,
            "username": user.username,  # 添加用户名到返回结果
            "membership": user.membership,
            "dialog_count": user.dialog_count,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
        
        print(f"登录处理完成，返回结果: {json.dumps(result, ensure_ascii=False)}")
        return result
    
    @staticmethod
    def create_session_token(user_id: int) -> str:
        """
        创建会话令牌
        
        参数:
            user_id: 用户ID
            
        返回:
            JWT会话令牌
        """
        payload = {
            "sub": str(user_id),
            "iat": int(time.time()),
            "exp": int(time.time()) + 7 * 24 * 60 * 60  # 7天过期
        }
        
        token = jwt.encode(payload, config.SECRET_KEY, algorithm="HS256")
        return token
    
    @staticmethod
    def verify_session_token(token: str) -> Tuple[bool, Optional[int]]:
        """
        验证会话令牌
        
        参数:
            token: JWT会话令牌
            
        返回:
            (验证是否成功, 用户ID)
        """
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
            return True, int(payload["sub"])
        except:
            return False, None
