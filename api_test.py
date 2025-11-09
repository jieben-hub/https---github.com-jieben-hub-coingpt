#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import sys

# 基础URL
BASE_URL = "http://127.0.0.1:5000"  # 本地测试环境
# BASE_URL = "http://192.168.31.127:5000"  # 如果需要测试其他环境，取消注释此行

# 测试账号
USERNAME = "test"
PASSWORD = "123123"

# 存储token
token = None

# 颜色输出
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_result(endpoint, status_code, response_text=None, error=None):
    """打印测试结果"""
    if 200 <= status_code < 300:
        status = f"{Colors.OKGREEN}[成功]{Colors.ENDC}"
    elif status_code == 404:
        status = f"{Colors.FAIL}[404 未找到]{Colors.ENDC}"
    else:
        status = f"{Colors.WARNING}[{status_code}]{Colors.ENDC}"
    
    print(f"{status} {endpoint}")
    
    if response_text and (200 <= status_code < 300):
        try:
            pretty_json = json.dumps(json.loads(response_text), ensure_ascii=False, indent=2)
            print(f"{Colors.OKBLUE}响应内容:{Colors.ENDC}\n{pretty_json}\n")
        except:
            print(f"{Colors.WARNING}响应内容 (非JSON):{Colors.ENDC}\n{response_text}\n")
    
    if error:
        print(f"{Colors.FAIL}错误:{Colors.ENDC} {error}\n")

def login():
    """登录并获取token"""
    global token
    endpoint = "/api/auth/login"
    url = BASE_URL + endpoint
    
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(url, json=data)
        print_result(endpoint, response.status_code, response.text)
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("status") == "success":
                token = response_data.get("data", {}).get("token")
                print(f"{Colors.OKGREEN}登录成功，获取到token{Colors.ENDC}\n")
                return True
    except Exception as e:
        print_result(endpoint, 500, error=str(e))
    
    print(f"{Colors.FAIL}登录失败，无法继续测试{Colors.ENDC}\n")
    return False

def test_endpoint(method, endpoint, data=None, auth_required=True):
    """测试单个API端点"""
    url = BASE_URL + endpoint
    headers = {}
    
    if auth_required and token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            print(f"{Colors.FAIL}不支持的HTTP方法: {method}{Colors.ENDC}")
            return
        
        print_result(endpoint, response.status_code, response.text)
    except Exception as e:
        print_result(endpoint, 500, error=str(e))

def main():
    """主函数，测试所有API端点"""
    print(f"{Colors.HEADER}开始测试CoinGPT API端点...{Colors.ENDC}\n")
    
    # 首先登录获取token
    if not login():
        return
    
    # 测试认证相关API
    print(f"\n{Colors.HEADER}测试认证相关API...{Colors.ENDC}")
    test_endpoint("GET", "/api/auth/user")
    test_endpoint("GET", "/api/auth/usage-stats")
    test_endpoint("GET", "/api/auth/invite")  # 正确的邀请码API
    test_endpoint("GET", "/api/auth/invite-code")  # 文档中错误的API路径
    test_endpoint("GET", "/api/auth/invited-users")
    
    # 测试会话相关API
    print(f"\n{Colors.HEADER}测试会话相关API...{Colors.ENDC}")
    test_endpoint("GET", "/api/auth/sessions")
    
    # 测试聊天相关API
    print(f"\n{Colors.HEADER}测试聊天相关API...{Colors.ENDC}")
    test_endpoint("GET", "/api/chat/api/health", auth_required=False)
    
    # 测试反馈相关API
    print(f"\n{Colors.HEADER}测试反馈相关API...{Colors.ENDC}")
    test_endpoint("GET", "/api/feedback/analytics")
    
    print(f"\n{Colors.HEADER}API测试完成{Colors.ENDC}")

if __name__ == "__main__":
    main()
