# -*- coding: utf-8 -*-
"""
趋势分析模块，用于分析加密货币的价格走势
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

class TrendAnalyzer:
    """
    趋势分析工具，提供各种技术指标计算和趋势判断功能
    """
    
    @staticmethod
    def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        向K线数据添加常用技术指标
        
        Args:
            df: K线数据DataFrame，包含OHLCV数据
            
        Returns:
            DataFrame: 添加了技术指标的DataFrame
        """
        # 创建副本避免修改原始数据
        result = df.copy()
        
        # 计算常用移动平均线
        result['MA5'] = result['close'].rolling(window=5).mean()
        result['MA10'] = result['close'].rolling(window=10).mean()
        result['MA20'] = result['close'].rolling(window=20).mean()
        result['MA50'] = result['close'].rolling(window=50).mean()
        
        # 计算RSI (相对强弱指标)
        delta = result['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        
        rs = avg_gain / avg_loss
        result['RSI'] = 100 - (100 / (1 + rs))
        
        # 计算MACD
        exp1 = result['close'].ewm(span=12, adjust=False).mean()
        exp2 = result['close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        result['MACD'] = macd
        result['MACD_Signal'] = signal
        result['MACD_Histogram'] = macd - signal
        
        # 布林带
        result['Middle_Band'] = result['close'].rolling(window=20).mean()
        std = result['close'].rolling(window=20).std()
        result['Upper_Band'] = result['Middle_Band'] + (std * 2)
        result['Lower_Band'] = result['Middle_Band'] - (std * 2)
        
        return result
    
    @staticmethod
    def analyze_trend(df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析K线数据的趋势
        
        Args:
            df: 包含技术指标的K线数据
            
        Returns:
            Dict: 包含趋势分析结果的字典
        """
        if df.empty or len(df) < 50:
            return {"error": "数据不足以进行趋势分析"}
            
        # 获取最新的几个收盘价和指标
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 价格和均线的相对位置
        price_vs_ma5 = latest['close'] > latest['MA5']
        price_vs_ma10 = latest['close'] > latest['MA10']
        price_vs_ma20 = latest['close'] > latest['MA20']
        price_vs_ma50 = latest['close'] > latest['MA50']
        
        # 价格是上涨还是下跌
        price_change = latest['close'] - prev['close']
        price_change_pct = price_change / prev['close'] * 100
        
        # 均线排列趋势
        ma_trend = "看涨" if latest['MA5'] > latest['MA10'] > latest['MA20'] > latest['MA50'] else (
                   "看跌" if latest['MA5'] < latest['MA10'] < latest['MA20'] < latest['MA50'] else "震荡")
        
        # 判断是否超买超卖
        overbought = latest['RSI'] > 70
        oversold = latest['RSI'] < 30
        
        # MACD分析
        macd_crossover = prev['MACD'] < prev['MACD_Signal'] and latest['MACD'] > latest['MACD_Signal']
        macd_crossunder = prev['MACD'] > prev['MACD_Signal'] and latest['MACD'] < latest['MACD_Signal']
        
        # 布林带分析
        bollinger_squeeze = (latest['Upper_Band'] - latest['Lower_Band']) / latest['Middle_Band'] < 0.1
        price_above_upper = latest['close'] > latest['Upper_Band']
        price_below_lower = latest['close'] < latest['Lower_Band']
        
        # 计算20日涨跌幅
        if len(df) >= 21:
            price_20d_ago = df.iloc[-21]['close']
            change_20d = (latest['close'] - price_20d_ago) / price_20d_ago * 100
        else:
            change_20d = None
        
        # 整体趋势判断
        bullish_signals = sum([
            price_vs_ma5, price_vs_ma10, price_vs_ma20, price_vs_ma50,
            ma_trend == "看涨", oversold, macd_crossover
        ])
        
        bearish_signals = sum([
            not price_vs_ma5, not price_vs_ma10, not price_vs_ma20, not price_vs_ma50,
            ma_trend == "看跌", overbought, macd_crossunder
        ])
        
        if bullish_signals > bearish_signals + 2:
            overall_trend = "强烈看涨"
        elif bullish_signals > bearish_signals:
            overall_trend = "偏向看涨"
        elif bearish_signals > bullish_signals + 2:
            overall_trend = "强烈看跌"
        elif bearish_signals > bullish_signals:
            overall_trend = "偏向看跌"
        else:
            overall_trend = "区间震荡"
        
        # 计算支撑和阻力位
        support_resistance = TrendAnalyzer.calculate_support_resistance(df)
        
        # 汇总分析结果
        analysis = {
            "overall_trend": overall_trend,
            "price": latest['close'],
            "price_change_24h": price_change,
            "price_change_pct_24h": price_change_pct,
            "ma_trend": ma_trend,
            "rsi": latest['RSI'],
            "overbought": overbought,
            "oversold": oversold,
            "macd_signal": "金叉" if macd_crossover else ("死叉" if macd_crossunder else "无明显信号"),
            "bollinger_status": "挤压" if bollinger_squeeze else ("突破上轨" if price_above_upper else ("跌破下轨" if price_below_lower else "区间内")),
            "change_20d": change_20d,
            "support_levels": support_resistance["support"],
            "resistance_levels": support_resistance["resistance"],
        }
        
        return analysis
    
    @staticmethod
    def calculate_support_resistance(df: pd.DataFrame, window: int = 10) -> Dict[str, List[float]]:
        """
        计算支撑位和阻力位
        
        Args:
            df: K线数据
            window: 寻找局部极值的窗口大小
            
        Returns:
            Dict: 包含支撑位和阻力位的字典
        """
        # 寻找局部低点和局部高点
        local_min = []
        local_max = []
        
        if len(df) < window * 2:
            # 数据不足，返回最低价和最高价
            return {
                "support": [df['low'].min()],
                "resistance": [df['high'].max()]
            }
        
        for i in range(window, len(df) - window):
            # 前后窗口的切片
            prev_window = df.iloc[i-window:i]
            next_window = df.iloc[i+1:i+window+1]
            current = df.iloc[i]
            
            # 如果当前点的低价是前后窗口中的最低，则为支撑位
            if current['low'] <= prev_window['low'].min() and current['low'] <= next_window['low'].min():
                local_min.append(current['low'])
            
            # 如果当前点的高价是前后窗口中的最高，则为阻力位
            if current['high'] >= prev_window['high'].max() and current['high'] >= next_window['high'].max():
                local_max.append(current['high'])
        
        # 对支撑位和阻力位进行聚类，避免太多太近的位置
        support = TrendAnalyzer._cluster_price_levels(local_min)
        resistance = TrendAnalyzer._cluster_price_levels(local_max)
        
        # 根据当前价格过滤支撑位和阻力位
        current_price = df.iloc[-1]['close']
        support = [s for s in support if s < current_price]
        resistance = [r for r in resistance if r > current_price]
        
        # 返回前3个最接近当前价格的支撑位和阻力位
        support.sort(reverse=True)  # 从高到低排序支撑位
        resistance.sort()  # 从低到高排序阻力位
        
        return {
            "support": support[:3],
            "resistance": resistance[:3]
        }
    
    @staticmethod
    def _cluster_price_levels(levels: List[float], threshold_pct: float = 0.01) -> List[float]:
        """
        对价格水平进行聚类，合并相近的价位
        
        Args:
            levels: 价格水平列表
            threshold_pct: 合并阈值，相差小于这个百分比的价位会被合并
            
        Returns:
            List[float]: 聚类后的价格水平
        """
        if not levels:
            return []
            
        # 排序
        sorted_levels = sorted(levels)
        clusters = []
        current_cluster = [sorted_levels[0]]
        
        for i in range(1, len(sorted_levels)):
            current = sorted_levels[i]
            cluster_avg = sum(current_cluster) / len(current_cluster)
            
            # 如果当前价位与聚类平均值相差小于阈值，则添加到当前聚类
            if abs(current - cluster_avg) / cluster_avg < threshold_pct:
                current_cluster.append(current)
            else:
                # 否则完成当前聚类并开始新聚类
                clusters.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [current]
                
        # 添加最后一个聚类
        if current_cluster:
            clusters.append(sum(current_cluster) / len(current_cluster))
            
        return clusters
