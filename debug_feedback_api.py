#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.stdout.reconfigure(encoding='utf-8')  # 设置标准输出编码为UTF-8

"""
CoinGPT API调试脚本
用于测试/api/feedback/rate_message接口
"""

import requests
import json
import sys

# 服务器地址
BASE_URL = "http://localhost:5000"

def print_separator():
    """打印分隔线"""
    print("\n" + "="*50 + "\n")

def login(username, password):
    """登录并获取token"""
    print(f"尝试登录账号: {username}")
    
    url = f"{BASE_URL}/api/auth/login"
    payload = {
        "username": username,
        "password": password
    }
    
    print(f"请求URL: {url}")
    print(f"请求数据: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and response.json().get("status") == "success":
            token = response.json().get("data", {}).get("token")
            print(f"登录成功，获取到token: {token[:10]}...")
            return token
        else:
            print("登录失败")
            return None
    except Exception as e:
        print(f"登录请求异常: {e}")
        return None

def get_user_sessions(token):
    """获取用户会话列表"""
    print("获取用户会话列表")
    
    url = f"{BASE_URL}/api/auth/sessions"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"请求URL: {url}")
    print(f"请求头: {headers}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and response.json().get("status") == "success":
            sessions = response.json().get("data", {}).get("sessions", [])
            if sessions:
                print(f"获取到 {len(sessions)} 个会话")
                return sessions[0].get("session_id")  # 返回第一个会话的ID
            else:
                print("没有找到任何会话")
                return None
        else:
            print("获取会话列表失败")
            return None
    except Exception as e:
        print(f"获取会话列表请求异常: {e}")
        return None

def get_session_messages(token, session_id):
    """获取会话消息"""
    print(f"\n==================================================\n")
    print(f"获取会话 {session_id} 的消息")
    url = f"{BASE_URL}/api/chat/session/{session_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"请求URL: {url}")
    print(f"请求头: {headers}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        message_id = 1  # 默认消息ID
        
        if response.status_code == 200 and response.json().get("status") == "success":
            messages = response.json().get("data", {}).get("messages", [])
            if messages:
                print(f"获取到 {len(messages)} 条消息")
                
                # 筛选出AI助手(role=assistant)的消息
                assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]
                if assistant_messages:
                    # 使用最新的AI回复消息ID
                    message_id = assistant_messages[0].get("id")
                    print(f"找到AI助手消息，使用ID: {message_id}")
                else:
                    print("未找到AI助手消息，使用默认ID 1")
            else:
                print("未获取到任何消息，使用默认ID 1")
        else:
            print(f"获取会话消息失败: {response.status_code}")
    except Exception as e:
        print(f"获取会话消息时出错: {e}")
    
    return message_id

def rate_message(token, message_id):
    """对消息进行评分"""
    print(f"\n==================================================\n")
    print(f"尝试对消息 {message_id} 进行评分")
    url = f"{BASE_URL}/api/feedback/rate_message"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "assistant_id": message_id,  # 使用新的assistant_id字段
        "rating": 5,
        "feedback": "测试反馈"
    }
    
    print(f"请求URL: {url}")
    print(f"请求头: {headers}")
    # 修改前
    print(f"请求数据: {json.dumps(data, ensure_ascii=False)}")

    # 打印完整的curl命令，方便手动测试
    curl_command = f'curl -X POST "{url}" -H "Authorization: Bearer {token}" -H "Content-Type: application/json" -d \'{json.dumps(data, ensure_ascii=False)}\''

    print(f"等效的curl命令: {curl_command}")
    
    # 尝试不同的请求方式
    print("\n尝试方式1: 使用requests.post")
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"响应状态码: {response.status_code}")
        try:
            print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        except:
            print(f"响应内容: {response.text}")
        
        # 如果第一种方式失败，尝试第二种方式
        if response.status_code == 404:
            print("\n尝试方式2: 使用不同的URL格式")
            alt_url = f"{BASE_URL}/api/feedback/rate_message/"
            print(f"请求URL: {alt_url} (添加了尾部斜杠)")
            response = requests.post(alt_url, json=payload, headers=headers)
            print(f"响应状态码: {response.status_code}")
            try:
                print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
            except:
                print(f"响应内容: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"评分请求异常: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) < 3:
        username = "test"
        password = "123123"
        print(f"使用默认账号: {username}/{password}")
    else:
        username = sys.argv[1]
        password = sys.argv[2]
    
    print_separator()
    
    # 1. 登录
    token = login(username, password)
    if not token:
        print("登录失败，无法继续测试")
        return
    
    print_separator()
    
    # 2. 获取会话列表
    session_id = get_user_sessions(token)
    if not session_id:
        print("获取会话失败，无法继续测试")
        return
    
    print_separator()
    
    # 3. 获取会话消息
    message_id = get_session_messages(token, session_id)
    if not message_id:
        print("获取消息失败，无法继续测试")
        return
    
    print_separator()
    
    # 4. 对消息进行评分
    success = rate_message(token, message_id)
    
    print_separator()
    
    if success:
        print("测试成功完成！")
    else:
        print("测试失败，请检查日志")

if __name__ == "__main__":
    main()
