import requests
import json

# 基础URL
BASE_URL = "http://192.168.31.127:5000"

# 登录函数
def login(username, password):
    url = f"{BASE_URL}/api/auth/login"
    payload = {
        "username": username,
        "password": password
    }
    response = requests.post(url, json=payload)
    return response.json()

# 获取会话列表
def get_sessions(token):
    url = f"{BASE_URL}/api/auth/sessions"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    return response.json()

# 创建新会话
def create_session(token):
    url = f"{BASE_URL}/api/auth/sessions"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.post(url, headers=headers)
    return response.json()

# 获取用户信息
def get_user_info(token):
    url = f"{BASE_URL}/api/auth/user"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    return response.json()

# 获取用户使用情况
def get_usage_stats(token):
    url = f"{BASE_URL}/api/auth/usage-stats"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    return response.json()

# 主测试函数
def test_session_limit():
    # 登录测试账号
    print("登录测试账号...")
    login_result = login("test", "123123")
    
    if login_result.get("status") != "success":
        print(f"登录失败: {login_result}")
        return
    
    token = login_result["data"]["token"]
    print(f"登录成功，获取到token")
    
    # 获取用户信息
    user_info = get_user_info(token)
    print(f"用户信息: {json.dumps(user_info, indent=2, ensure_ascii=False)}")
    
    # 获取当前会话列表
    sessions = get_sessions(token)
    current_sessions = sessions.get("data", [])
    print(f"当前会话数量: {len(current_sessions)}")
    
    # 获取使用情况
    usage = get_usage_stats(token)
    print(f"使用情况: {json.dumps(usage, indent=2, ensure_ascii=False)}")
    
    # 尝试创建新会话
    print("\n尝试创建新会话...")
    create_result = create_session(token)
    print(f"创建结果: {json.dumps(create_result, indent=2, ensure_ascii=False)}")
    
    # 再次获取会话列表
    sessions = get_sessions(token)
    new_sessions = sessions.get("data", [])
    print(f"创建后会话数量: {len(new_sessions)}")
    
    # 再次获取使用情况
    usage = get_usage_stats(token)
    print(f"创建后使用情况: {json.dumps(usage, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    test_session_limit()
