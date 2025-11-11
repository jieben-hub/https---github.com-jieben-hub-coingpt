#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试币种列表API
"""
import requests

BASE_URL = "http://192.168.100.173:5000"

def test_symbols_api():
    """测试币种列表API"""
    
    print("=" * 60)
    print("测试币种列表API")
    print("=" * 60)
    
    # 测试1: 获取基础币种
    print("\n1. 测试获取基础币种:")
    try:
        response = requests.get(f"{BASE_URL}/api/trading/symbols?type=base")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                symbols = data['data']['symbols']
                count = data['data']['count']
                print(f"   ✅ 成功获取 {count} 个基础币种")
                print(f"   前10个: {symbols[:10]}")
            else:
                print(f"   ❌ 失败: {data}")
        else:
            print(f"   ❌ HTTP错误: {response.text}")
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 测试2: 获取交易对
    print("\n2. 测试获取交易对:")
    try:
        response = requests.get(f"{BASE_URL}/api/trading/symbols?type=pairs")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                pairs = data['data']['symbols']
                count = data['data']['count']
                print(f"   ✅ 成功获取 {count} 个交易对")
                print(f"   前10个: {pairs[:10]}")
            else:
                print(f"   ❌ 失败: {data}")
        else:
            print(f"   ❌ HTTP错误: {response.text}")
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 测试3: 获取所有信息
    print("\n3. 测试获取所有信息:")
    try:
        response = requests.get(f"{BASE_URL}/api/trading/symbols")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                base_count = data['data']['count']['base_symbols']
                pairs_count = data['data']['count']['trading_pairs']
                print(f"   ✅ 成功获取所有信息")
                print(f"   基础币种: {base_count} 个")
                print(f"   交易对: {pairs_count} 个")
                print(f"   前5个基础币种: {data['data']['base_symbols'][:5]}")
                print(f"   前5个交易对: {data['data']['trading_pairs'][:5]}")
            else:
                print(f"   ❌ 失败: {data}")
        else:
            print(f"   ❌ HTTP错误: {response.text}")
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_symbols_api()
