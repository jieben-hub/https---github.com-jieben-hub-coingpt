#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试交易历史API
"""
import requests
import json
from datetime import datetime

# 配置
BASE_URL = "http://192.168.100.173:5000"
# 需要一个有效的JWT token
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0IiwiaWF0IjoxNzYyNzIxMjA3LCJleHAiOjE3NjMzMjYwMDd9.taqUsvsF4wEh44yOlZG-n5E94jQtdoVHB4l7PLmGEuk"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

def test_add_pnl_record():
    """测试添加盈亏记录"""
    print("🧪 测试添加盈亏记录...")
    
    data = {
        "exchange": "bybit",
        "symbol": "BTCUSDT",
        "side": "Buy",
        "open_time": "2025-11-10T10:00:00Z",
        "open_price": 50000.0,
        "open_size": 0.1,
        "close_time": "2025-11-10T11:00:00Z",
        "close_price": 50500.0,
        "close_size": 0.1,
        "realized_pnl": 50.0,
        "fee": 2.5,
        "leverage": 10.0,
        "order_id": "test_order_123",
        "position_id": "test_position_456"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/trading/history/pnl",
            headers=headers,
            json=data
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 201:
            print("✅ 添加盈亏记录成功")
            return True
        else:
            print("❌ 添加盈亏记录失败")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_get_pnl_history():
    """测试获取盈亏历史"""
    print("\n🧪 测试获取盈亏历史...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/trading/history/pnl?limit=10",
            headers=headers
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            records = result.get('data', {}).get('records', [])
            print(f"✅ 获取盈亏历史成功，共{len(records)}条记录")
            return True
        else:
            print("❌ 获取盈亏历史失败")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_get_pnl_summary():
    """测试获取盈亏汇总"""
    print("\n🧪 测试获取盈亏汇总...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/trading/history/pnl/summary?period=all",
            headers=headers
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            summary = result.get('data', {}).get('summary', {})
            print(f"✅ 获取盈亏汇总成功")
            print(f"   总交易次数: {summary.get('total_trades', 0)}")
            print(f"   总净盈亏: {summary.get('total_net_pnl', 0)}")
            print(f"   胜率: {summary.get('win_rate', 0)}%")
            return True
        else:
            print("❌ 获取盈亏汇总失败")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_get_order_history():
    """测试获取订单历史"""
    print("\n🧪 测试获取订单历史...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/trading/history/orders?limit=10",
            headers=headers
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            records = result.get('data', {}).get('records', [])
            print(f"✅ 获取订单历史成功，共{len(records)}条记录")
            return True
        else:
            print("❌ 获取订单历史失败")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_get_trading_stats():
    """测试获取交易统计"""
    print("\n🧪 测试获取交易统计...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/trading/history/stats",
            headers=headers
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            stats = result.get('data', {}).get('stats', {})
            print(f"✅ 获取交易统计成功")
            for period, data in stats.items():
                print(f"   {period}: {data.get('total_trades', 0)}笔交易, 净盈亏: {data.get('total_net_pnl', 0)}")
            return True
        else:
            print("❌ 获取交易统计失败")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("🚀 开始测试交易历史API")
    print("="*50)
    
    tests = [
        test_add_pnl_record,
        test_get_pnl_history,
        test_get_pnl_summary,
        test_get_order_history,
        test_get_trading_stats
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "="*50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！历史盈亏API正常工作")
    else:
        print("⚠️  部分测试失败，请检查API实现")

if __name__ == "__main__":
    main()
