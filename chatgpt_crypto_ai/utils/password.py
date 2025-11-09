# -*- coding: utf-8 -*-
"""
密码哈希和验证工具
"""
import hashlib
import os
import binascii

def hash_password(password):
    """
    对密码进行安全哈希处理
    
    Args:
        password (str): 原始密码
        
    Returns:
        str: 哈希后的密码字符串，格式为 salt:hashed_value
    """
    # 生成随机盐值
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    # 使用盐值和密码计算哈希
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), 
                                   salt, 100000, 64)
    pwdhash = binascii.hexlify(pwdhash)
    # 返回盐值:哈希值的格式
    return (salt + pwdhash).decode('ascii')

def verify_password(stored_password, provided_password):
    """
    验证提供的密码是否与存储的哈希值匹配
    
    Args:
        stored_password (str): 存储的密码哈希值
        provided_password (str): 待验证的密码
        
    Returns:
        bool: 如果密码匹配则返回True，否则False
    """
    try:
        # 从存储的字符串中提取盐值
        salt = stored_password[:64]
        # 从存储的字符串中提取哈希值
        stored_hash = stored_password[64:]
        # 使用相同的盐值和提供的密码计算哈希
        pwdhash = hashlib.pbkdf2_hmac('sha512', 
                                       provided_password.encode('utf-8'), 
                                       salt.encode('ascii'), 
                                       100000, 64)
        pwdhash = binascii.hexlify(pwdhash).decode('ascii')
        # 比较计算得到的哈希值与存储的哈希值
        return pwdhash == stored_hash
    except Exception as e:
        print(f"Password verification error: {e}")
        return False
