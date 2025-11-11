#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Bybit修复效果
"""
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'chatgpt_crypto_ai'))

from chatgpt_crypto_ai.utils.data_converter import safe_float, safe_str

def test_data_converter():
    """测试数据转换器"""
    print("测试数据转换器...")
    
    # 测试各种边界情况
    test_cases = [
        ('', 0.0),
        (None, 0.0),
        ('null', 0.0),
        ('123.45', 123.45),
        ('0', 0.0),
        ('  456.78  ', 456.78),
        ('invalid', 0.0),
        ([], 0.0),
        ({}, 0.0)
    ]
    
    print("safe_float 测试:")
    for value, expected in test_cases:
        result = safe_float(value)
        status = "✅" if result == expected else "❌"
        print(f"  {status} safe_float({repr(value)}) = {result} (期望: {expected})")
    
    print("\nsafe_str 测试:")
    str_cases = [
        ('', ''),
        (None, ''),
        ('null', ''),
        ('hello', 'hello'),
        ('  world  ', 'world'),
        (123, '123'),
        ([], '[]')
    ]
    
    for value, expected in str_cases:
        result = safe_str(value)
        status = "✅" if result == expected else "❌"
        print(f"  {status} safe_str({repr(value)}) = {repr(result)} (期望: {repr(expected)})")

def test_bybit_response_simulation():
    """模拟Bybit API响应并测试处理"""
    print("\n模拟Bybit API响应测试...")
    
    # 模拟可能出现问题的API响应
    mock_balance_response = {
        'retCode': 0,
        'result': {
            'list': [{
                'coin': [{
                    'coin': 'USDT',
                    'availableToWithdraw': '',  # 空字符串
                    'walletBalance': '1000.50',
                    'equity': None  # None值
                }]
            }]
        }
    }
    
    mock_position_response = {
        'retCode': 0,
        'result': {
            'list': [
                {
                    'symbol': 'BTCUSDT',
                    'side': 'Buy',
                    'size': '0.1',
                    'avgPrice': '',  # 空字符串
                    'markPrice': '50000.00',
                    'unrealisedPnl': 'null',  # 字符串null
                    'leverage': '10'
                },
                {
                    'symbol': 'ETHUSDT',
                    'side': 'Sell',
                    'size': '',  # 空字符串，应该被过滤
                    'avgPrice': '3000.00',
                    'markPrice': '3050.00',
                    'unrealisedPnl': '-50.00',
                    'leverage': '5'
                }
            ]
        }
    }
    
    # 测试余额处理
    print("余额数据处理:")
    coins = mock_balance_response['result']['list'][0]['coin']
    for c in coins:
        if c['coin'] == 'USDT':
            balance_data = {
                'coin': 'USDT',
                'available': safe_float(c.get('availableToWithdraw')),
                'total': safe_float(c.get('walletBalance')),
                'equity': safe_float(c.get('equity'))
            }
            print(f"  处理结果: {balance_data}")
    
    # 测试持仓处理
    print("\n持仓数据处理:")
    positions = []
    for pos in mock_position_response['result']['list']:
        size = safe_float(pos.get('size'))
        if size > 0:  # 只处理有持仓的
            position_data = {
                'symbol': safe_str(pos.get('symbol')),
                'side': safe_str(pos.get('side')),
                'size': size,
                'entry_price': safe_float(pos.get('avgPrice')),
                'mark_price': safe_float(pos.get('markPrice')),
                'unrealized_pnl': safe_float(pos.get('unrealisedPnl')),
                'leverage': safe_float(pos.get('leverage'))
            }
            positions.append(position_data)
            print(f"  处理结果: {position_data}")
    
    print(f"\n总共处理了 {len(positions)} 个有效持仓")

def main():
    """主函数"""
    print("Bybit 数据处理修复测试")
    print("="*50)
    
    test_data_converter()
    test_bybit_response_simulation()
    
    print("\n" + "="*50)
    print("测试完成！修复应该能解决以下问题:")
    print("1. ✅ 空字符串转换为浮点数的错误")
    print("2. ✅ None值的安全处理")
    print("3. ✅ 'null'字符串的处理")
    print("4. ✅ 无效数据的默认值处理")
    print("\n现在可以重启应用程序测试修复效果！")

if __name__ == "__main__":
    main()
