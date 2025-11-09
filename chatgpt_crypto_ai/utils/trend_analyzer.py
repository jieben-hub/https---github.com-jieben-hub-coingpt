# -*- coding: utf-8 -*-
""" 
加密货币趋势分析模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('trend_analyzer')

class TrendAnalyzer:
    """
    负责分析加密货币的趋势和技术指标
    """
    
    @staticmethod
    def analyze_trend(kline_data: pd.DataFrame) -> Dict[str, Any]:
        """
        分析K线数据的趋势和技术指标
        
        Args:
            kline_data: 包含交易对的K线数据的DataFrame
            
        Returns:
            Dict: 包含分析结果的字典
        """
        try:
            if kline_data.empty:
                return {"error": "无法获取币种数据"}
            
            # 确保数据按时间正序排序
            df = kline_data.sort_values('timestamp')
            
            # 计算当前价格和基本信息
            current_price = float(df['close'].iloc[-1])
            price_change = ((current_price / float(df['close'].iloc[0])) - 1) * 100
            
            # 如果有足够数据，计算过去20天的涨跌幅
            change_20d = None
            if len(df) >= 20:
                change_20d = ((current_price / float(df['close'].iloc[-20])) - 1) * 100
            
            # 计算移动平均线
            df['ma7'] = df['close'].rolling(window=7).mean()
            df['ma25'] = df['close'].rolling(window=25).mean()
            df['ma99'] = df['close'].rolling(window=99).mean()
            
            # 判断均线排列趋势
            last_row = df.iloc[-1]
            ma_trend = "不明确"
            if last_row['ma7'] > last_row['ma25'] > last_row['ma99']:
                ma_trend = "多头排列"
            elif last_row['ma7'] < last_row['ma25'] < last_row['ma99']:
                ma_trend = "空头排列"
            elif last_row['ma7'] > last_row['ma25'] and last_row['ma25'] < last_row['ma99']:
                ma_trend = "混合排列"
            
            # 判断整体趋势
            recent_trend = df['close'].iloc[-10:].values
            trend_direction = np.polyfit(range(len(recent_trend)), recent_trend, 1)[0]
            
            if trend_direction > 0:
                overall_trend = "上涨趋势"
            elif trend_direction < 0:
                overall_trend = "下跌趋势"
            else:
                overall_trend = "横盘整理"
            
            # 计算RSI
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = float(rsi.iloc[-1])
            
            # 计算MACD
            exp12 = df['close'].ewm(span=12, adjust=False).mean()
            exp26 = df['close'].ewm(span=26, adjust=False).mean()
            macd = exp12 - exp26
            signal = macd.ewm(span=9, adjust=False).mean()
            hist = macd - signal
            
            macd_signal = "中性"
            if hist.iloc[-1] > 0 and hist.iloc[-2] <= 0:
                macd_signal = "金叉看多"
            elif hist.iloc[-1] < 0 and hist.iloc[-2] >= 0:
                macd_signal = "死叉看空"
            elif hist.iloc[-3:].mean() > 0:
                macd_signal = "偏多"
            elif hist.iloc[-3:].mean() < 0:
                macd_signal = "偏空"
            
            # 计算布林带
            df['20ma'] = df['close'].rolling(window=20).mean()
            df['std'] = df['close'].rolling(window=20).std()
            df['upper_band'] = df['20ma'] + 2 * df['std']
            df['lower_band'] = df['20ma'] - 2 * df['std']
            
            # 判断布林带状态
            last = df.iloc[-1]
            if last['close'] > last['upper_band']:
                bollinger_status = "超买区域"
            elif last['close'] < last['lower_band']:
                bollinger_status = "超卖区域"
            else:
                bollinger_status = "正常区域"
            
            # 计算支撑位和阻力位
            support_levels = []
            resistance_levels = []
            
            # 简化的支撑位和阻力位计算（基于近期价格波动）
            if len(df) >= 20:
                recent_lows = df['low'].iloc[-20:].nsmallest(3).values
                recent_highs = df['high'].iloc[-20:].nlargest(3).values
                
                # 筛选出相对接近的支撑位
                for low in recent_lows:
                    if low < current_price and low not in support_levels:
                        support_levels.append(low)
                
                # 筛选出相对接近的阻力位
                for high in recent_highs:
                    if high > current_price and high not in resistance_levels:
                        resistance_levels.append(high)
            
            # 整合分析结果
            return {
                "price": current_price,
                "price_change_pct_24h": price_change,
                "change_20d": change_20d,
                "overall_trend": overall_trend,
                "ma_trend": ma_trend,
                "rsi": current_rsi,
                "oversold": current_rsi < 30,
                "overbought": current_rsi > 70,
                "macd_signal": macd_signal,
                "bollinger_status": bollinger_status,
                "support_levels": support_levels,
                "resistance_levels": resistance_levels
            }
            
        except Exception as e:
            logger.error(f"趋势分析失败: {str(e)}")
            return {"error": f"趋势分析错误: {str(e)}"}
