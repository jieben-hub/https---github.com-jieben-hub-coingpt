# -*- coding: utf-8 -*-
"""
测试从用户输入中提取加密货币信息的功能
"""
import sys
import os
import unittest
from unittest.mock import patch
import pandas as pd

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.extract import extract_crypto_symbols, extract_time_window, extract_all_info


class TestExtractFunctions(unittest.TestCase):
    """测试提取功能的单元测试类"""

    def test_extract_crypto_symbols(self):
        """测试从文本中提取加密货币符号"""
        # 测试直接符号提取
        text1 = "BTC和ETH的价格走势如何？"
        result1 = extract_crypto_symbols(text1)
        self.assertEqual(set(result1), {"BTC", "ETH"})
        
        # 测试中文名称提取
        text2 = "比特币和以太坊哪个投资价值更高？"
        result2 = extract_crypto_symbols(text2)
        self.assertEqual(set(result2), {"BTC", "ETH"})
        
        # 测试英文名称提取
        text3 = "Compare bitcoin and ethereum performance."
        result3 = extract_crypto_symbols(text3)
        self.assertEqual(set(result3), {"BTC", "ETH"})
        
        # 测试混合提取
        text4 = "SOL、ADA和波卡的技术面分析"
        result4 = extract_crypto_symbols(text4)
        self.assertEqual(set(result4), {"SOL", "ADA", "DOT"})
        
        # 测试不包含任何加密货币的文本
        text5 = "今天天气真好"
        result5 = extract_crypto_symbols(text5)
        self.assertEqual(result5, [])

    def test_extract_time_window(self):
        """测试从文本中提取时间窗口"""
        # 测试常用时间窗口
        text1 = "BTC的1小时图分析"
        result1 = extract_time_window(text1)
        self.assertEqual(result1, "1h")
        
        # 测试数字+时间单位模式
        text2 = "请看一下ETH 4小时的走势"
        result2 = extract_time_window(text2)
        self.assertEqual(result2, "4h")
        
        # 测试日/天/周期
        text3 = "BTC最近7天的表现如何？"
        result3 = extract_time_window(text3)
        self.assertEqual(result3, "7d")
        
        # 测试英文时间单位
        text4 = "Show me the 15min chart of BTC"
        result4 = extract_time_window(text4)
        self.assertEqual(result4, "15m")
        
        # 测试不包含时间窗口的文本
        text5 = "比特币是什么？"
        result5 = extract_time_window(text5)
        self.assertIsNone(result5)

    def test_extract_all_info(self):
        """测试从提示中提取所有相关信息"""
        # 测试完整提取
        prompt1 = "分析一下BTC和ETH在4小时图上的表现"
        result1 = extract_all_info(prompt1)
        self.assertEqual(set(result1["symbols"]), {"BTC", "ETH"})
        self.assertEqual(result1["time_window"], "4h")
        
        # 测试只有币种没有时间窗口
        prompt2 = "比较一下SOL和ADA"
        result2 = extract_all_info(prompt2)
        self.assertEqual(set(result2["symbols"]), {"SOL", "ADA"})
        self.assertEqual(result2["time_window"], "1d")  # 默认为1d
        
        # 测试既没有币种也没有时间窗口
        prompt3 = "加密货币市场总体趋势如何？"
        result3 = extract_all_info(prompt3)
        self.assertEqual(result3["symbols"], ["BTC"])  # 默认为BTC
        self.assertEqual(result3["time_window"], "1d")  # 默认为1d


if __name__ == "__main__":
    unittest.main()
