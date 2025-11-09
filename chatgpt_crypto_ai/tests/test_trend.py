# -*- coding: utf-8 -*-
"""
测试趋势分析模块功能
"""
import sys
import os
import unittest
from unittest.mock import patch
import pandas as pd
import numpy as np

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.trend import TrendAnalyzer


class TestTrendAnalyzer(unittest.TestCase):
    """测试趋势分析功能的单元测试类"""

    def setUp(self):
        """创建测试数据"""
        # 创建示例K线数据
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        
        # 模拟一个上涨趋势的价格序列
        close = np.linspace(10000, 15000, 100) + np.random.normal(0, 200, 100)
        
        # 创建OHLCV数据
        self.df_bullish = pd.DataFrame({
            'timestamp': dates,
            'open': close - np.random.normal(0, 100, 100),
            'high': close + np.random.normal(200, 50, 100),
            'low': close - np.random.normal(200, 50, 100),
            'close': close,
            'volume': np.random.normal(1000, 200, 100)
        })
        
        # 模拟一个下跌趋势的价格序列
        close_bearish = np.linspace(15000, 10000, 100) + np.random.normal(0, 200, 100)
        
        # 创建OHLCV数据
        self.df_bearish = pd.DataFrame({
            'timestamp': dates,
            'open': close_bearish - np.random.normal(0, 100, 100),
            'high': close_bearish + np.random.normal(200, 50, 100),
            'low': close_bearish - np.random.normal(200, 50, 100),
            'close': close_bearish,
            'volume': np.random.normal(1000, 200, 100)
        })
        
        # 添加技术指标
        self.df_bullish_indicators = TrendAnalyzer.add_technical_indicators(self.df_bullish)
        self.df_bearish_indicators = TrendAnalyzer.add_technical_indicators(self.df_bearish)

    def test_add_technical_indicators(self):
        """测试添加技术指标功能"""
        # 验证是否成功添加了所有指标列
        expected_columns = [
            'MA5', 'MA10', 'MA20', 'MA50', 
            'RSI', 'MACD', 'MACD_Signal', 'MACD_Histogram',
            'Middle_Band', 'Upper_Band', 'Lower_Band'
        ]
        
        for column in expected_columns:
            self.assertIn(column, self.df_bullish_indicators.columns)
        
        # 验证移动平均线的计算
        # MA5应该是最近5天收盘价的平均值
        last_5_closes = self.df_bullish.iloc[-5:]['close'].mean()
        self.assertAlmostEqual(self.df_bullish_indicators.iloc[-1]['MA5'], last_5_closes, delta=0.001)

    def test_analyze_trend(self):
        """测试趋势分析功能"""
        # 测试上涨趋势分析
        bullish_analysis = TrendAnalyzer.analyze_trend(self.df_bullish_indicators)
        
        # 测试下跌趋势分析
        bearish_analysis = TrendAnalyzer.analyze_trend(self.df_bearish_indicators)
        
        # 验证分析结果中包含所有必要的键
        expected_keys = [
            'overall_trend', 'price', 'price_change_24h', 'price_change_pct_24h',
            'ma_trend', 'rsi', 'overbought', 'oversold', 'macd_signal',
            'bollinger_status', 'change_20d', 'support_levels', 'resistance_levels'
        ]
        
        for key in expected_keys:
            self.assertIn(key, bullish_analysis)
            self.assertIn(key, bearish_analysis)
        
        # 验证上涨趋势分析结果
        self.assertIn("看涨", bullish_analysis['overall_trend'])
        
        # 验证下跌趋势分析结果
        self.assertIn("看跌", bearish_analysis['overall_trend'])

    def test_calculate_support_resistance(self):
        """测试支撑阻力位计算功能"""
        # 测试上涨趋势的支撑阻力位
        sr_bullish = TrendAnalyzer.calculate_support_resistance(self.df_bullish)
        
        # 验证结果中包含支撑位和阻力位
        self.assertIn('support', sr_bullish)
        self.assertIn('resistance', sr_bullish)
        
        # 支撑位应该在当前价格之下
        current_price = self.df_bullish.iloc[-1]['close']
        for level in sr_bullish['support']:
            self.assertLess(level, current_price)


if __name__ == "__main__":
    unittest.main()
