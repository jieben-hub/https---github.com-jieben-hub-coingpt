# -*- coding: utf-8 -*-
"""
K线数据获取模块，直接通过币安API获取历史K线数据
"""
import requests
import pandas as pd
from typing import Dict, List, Optional, Any
import time
import logging
import json
from datetime import datetime, timedelta
from urllib.parse import urljoin
from utils.symbols_sync import get_trading_pairs

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('kline_fetcher')

class KlineDataFetcher:
    """
    K线数据获取器，直接调用币安API获取加密货币的K线数据
    """
    def __init__(self, api_key: str = '', api_secret: str = ''):
        """
        初始K线数据获取器
        
        Args:
            api_key: 币安API密钥（可选）
            api_secret: 币安API密钥secret（可选）
        """
        # 币安API基础URL
        self.base_url = "https://api.binance.com"
        self.base_url_fallback = "https://api1.binance.com"  # 备用API域名
        
        # 币安API端点
        self.kline_endpoint = "/api/v3/klines"  # K线数据端点
        self.exchange_info_endpoint = "/api/v3/exchangeInfo"  # 交易对信息端点
        self.ticker_price_endpoint = "/api/v3/ticker/price"  # 当前价格端点
        
        # API配置
        self.api_key = api_key
        self.api_secret = api_secret
        
        # 请求配置
        self.request_timeout = 30  # 请求超时时间（秒）
        self.max_retries = 3      # 最大重试次数
        
        # 初始化请求会话
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Content-Type": "application/json"
        })
        
        # 如果提供API密钥，则添加到头部
        if api_key:
            self.session.headers.update({"X-MBX-APIKEY": api_key})
        
        # 优先用本地缓存
        self.available_symbols = get_trading_pairs()
        logger.info(f"币安K线数据获取器初始化完成，成功获取 {len(self.available_symbols)} 个交易对信息（优先本地缓存）")
    
    def _get_available_symbols(self) -> Dict[str, Dict]:
        """
        获取币安所支持的交易对信息
        
        Returns:
            Dict[str, Dict]: 交易对名称到交易对信息的映射
        """
        symbols_info = {}
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                # 选择当前使用的API URL
                url = self.base_url if retry_count == 0 else self.base_url_fallback
                endpoint = urljoin(url, self.exchange_info_endpoint)
                
                # 发送请求获取交易对信息
                response = self.session.get(endpoint, timeout=self.request_timeout)
                response.raise_for_status()
                data = response.json()
                
                # 提取交易对信息
                for symbol_info in data.get('symbols', []):
                    # 只考虑现货交易对并且是正在交易的
                    if symbol_info.get('status') == 'TRADING' and symbol_info.get('isSpotTradingAllowed', False):
                        symbol = symbol_info.get('symbol')
                        base_asset = symbol_info.get('baseAsset')
                        quote_asset = symbol_info.get('quoteAsset')
                        
                        # 保存交易对信息
                        symbols_info[symbol] = {
                            'symbol': symbol,
                            'baseAsset': base_asset,
                            'quoteAsset': quote_asset,
                            'filters': symbol_info.get('filters', []),
                        }
                        
                logger.info(f"成功从币安API获取了 {len(symbols_info)} 个交易对信息")
                return symbols_info
                
            except requests.RequestException as e:
                retry_count += 1
                wait_time = 2 ** retry_count
                logger.warning(f"获取交易对信息失败 (第 {retry_count}/{self.max_retries} 次): {str(e)}, 等待 {wait_time} 秒后重试")
                time.sleep(wait_time)
        
        # 所有重试都失败
        logger.error("无法从币安API获取交易对信息")
        return {}
        
    def _make_api_request(self, endpoint: str, params: Dict = None, use_fallback: bool = False) -> Optional[Any]:
        """
        发送API请求，带自动重试机制
        
        Args:
            endpoint: API端点
            params: 请求参数
            use_fallback: 是否使用备用URL
            
        Returns:
            响应数据或None(如果失败)
        """
        params = params or {}
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                # 选择当前使用的API URL
                base = self.base_url_fallback if use_fallback else self.base_url
                url = urljoin(base, endpoint)
                
                # 发送请求
                response = self.session.get(url, params=params, timeout=self.request_timeout)
                response.raise_for_status()
                return response.json()
                
            except requests.RequestException as e:
                retry_count += 1
                # 如果无法连接主域名并且还有重试次数，切换到备用域名
                if retry_count < self.max_retries:
                    wait_time = 2 ** retry_count
                    use_fallback = retry_count >= 1  # 第二次重试开始使用备用域名
                    logger.warning(f"请求 {endpoint} 失败 (第 {retry_count}/{self.max_retries} 次): {str(e)}")
                    logger.info(f"等待 {wait_time} 秒后使用{'备用' if use_fallback else '主要'}URL重试")
                    time.sleep(wait_time)
                else:
                    logger.error(f"所有重试均失败: {str(e)}")
                    return None
        
        return None

    def get_klines(self, symbol: str, timeframe: str = '1d', limit: int = 100) -> pd.DataFrame:
        """
        使用币安API获取K线数据
        
        Args:
            symbol: 货币对符号，如 'BTC/USDT' 或 'BTC'
            timeframe: 时间周期，如 '1m', '1h', '1d', '1w' 等
            limit: 获取的K线数量，最大为1000
            
        Returns:
            DataFrame: 包含K线数据的DataFrame
        """
        # 币安API的时间周期映射
        binance_intervals = {
            '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h',
            '1d': '1d', '3d': '3d', '1w': '1w', '1M': '1M'
        }
        
        # 标准化时间周期
        if timeframe not in binance_intervals:
            logger.warning(f"不支持的时间周期 {timeframe}，将使用 '1h'")
            interval = '1h'
        else:
            interval = binance_intervals[timeframe]
        
        # 标准化符号，处理不同的币种输入格式
        binance_symbol = self._normalize_symbol(symbol)
        if not binance_symbol:
            logger.error(f"无法找到匹配的交易对: {symbol}")
            return pd.DataFrame()
        
        logger.info(f"获取 {binance_symbol} 的 {interval} K线数据，最大 {limit} 条")
        
        # 准备API请求参数
        params = {
            'symbol': binance_symbol,
            'interval': interval,
            'limit': min(limit, 1000),  # 币安限制最大能查询1000条
        }
        
        # 发送API请求
        response_data = self._make_api_request(self.kline_endpoint, params)
        if not response_data:
            logger.error(f"无法获取 {binance_symbol} 的K线数据")
            return pd.DataFrame()
        
        # 检查数据是否为空
        if len(response_data) == 0:
            logger.warning(f"{binance_symbol} 没有可用的K线数据")
            return pd.DataFrame()
        
        # 币安K线数据格式: [Open time, Open, High, Low, Close, Volume, Close time, Quote asset volume, 
        # Number of trades, Taker buy base, Taker buy quote, Ignore]
        columns = [
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 
            'close_time', 'quote_volume', 'trades_count', 
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ]
        
        # 创建DataFrame
        df = pd.DataFrame(response_data, columns=columns)
        
        # 转换数据类型
        for col in ['open', 'high', 'low', 'close', 'volume', 'quote_volume', 
                   'taker_buy_base', 'taker_buy_quote']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 将时间戳转换为datetime格式
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        
        # 添加额外的信息列
        df['symbol'] = binance_symbol
        df['base_asset'] = self._get_base_asset(binance_symbol)
        df['quote_asset'] = self._get_quote_asset(binance_symbol)
        
        # 计算重要指标
        df['change'] = ((df['close'] - df['open']) / df['open'] * 100).round(2)  # 价格变化百分比
        df['range_percent'] = ((df['high'] - df['low']) / df['low'] * 100).round(2)  # 价格波动范围
        
        # 打印最新价格信息
        if not df.empty:
            latest = df.iloc[-1]
            logger.info(f"成功获取 {len(df)} 条 {binance_symbol} 的K线数据")
            logger.info(f"最新价格 ({binance_symbol}, {latest['timestamp']}): "
                      f"开盘={latest['open']:.4f}, 最高={latest['high']:.4f}, "
                      f"最低={latest['low']:.4f}, 收盘={latest['close']:.4f}, "
                      f"成交量={latest['volume']:.2f}, 价格变化={latest['change']:.2f}%")
        
        return df
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        将不同格式的币种符号标准化为币安API能识别的格式
        
        Args:
            symbol: 原始输入的币种符号，如 'BTC', 'BTC/USDT', 'BTCUSDT'
            
        Returns:
            str: 币安格式的符号，或空字符串（如果找不到）
        """
        # 针对不同格式添加币种匹配策略
        candidates = []
        symbol = symbol.upper()
        
        # 处理情况1: 直接匹配现有交易对
        if symbol in self.available_symbols:
            return symbol
        
        # 处理情况2: 如果包含斜杠，删除斜杠后再尝试
        if '/' in symbol:
            no_slash = symbol.replace('/', '')
            if no_slash in self.available_symbols:
                return no_slash
            # 将带斜杠的符号加入候选
            base, quote = symbol.split('/')
            candidates.append(base + quote)
        
        # 处理情况3: 如果是单一币种，尝试加上不同的计价币
        else:
            # 常见计价币，按优先级排序
            quote_assets = ['USDT', 'BUSD', 'USDC', 'BTC', 'ETH']
            for quote in quote_assets:
                candidate = symbol + quote
                candidates.append(candidate)
        
        # 尝试所有候选符号
        for candidate in candidates:
            if candidate in self.available_symbols:
                return candidate
        
        # 如果还是找不到，尝试全币平台模糊查找（找到包含该基础货币的任何交易对）
        if '/' in symbol:
            base = symbol.split('/')[0]
        else:
            base = symbol
            
        for sym in self.available_symbols:
            # 如果完全匹配或者基础资产匹配
            symbol_info = self.available_symbols[sym]
            if symbol_info['baseAsset'] == base:
                # 优先返回xUSDT交易对
                if symbol_info['quoteAsset'] == 'USDT':
                    return sym
                # 暂存其他匹配
                candidates.append(sym)
        
        # 如果有匹配的其他币种对，返回第一个
        if candidates:
            return candidates[0]
            
        # 完全找不到
        logger.error(f"无法找到匹配的交易对符号: {symbol}")
        return ""
        
    def _get_base_asset(self, symbol: str) -> str:
        """获取交易对的基础资产"""
        if symbol in self.available_symbols:
            return self.available_symbols[symbol]['baseAsset']
        return ""
        
    def _get_quote_asset(self, symbol: str) -> str:
        """获取交易对的计价资产"""
        if symbol in self.available_symbols:
            return self.available_symbols[symbol]['quoteAsset']
        return ""
    
    def get_multiple_klines(self, symbols: List[str], timeframe: str = '1d', limit: int = 100) -> Dict[str, pd.DataFrame]:
        """
        获取多个货币对的K线数据
        
        Args:
            symbols: 货币对符号列表
            timeframe: 时间周期
            limit: 获取的K线数量
            
        Returns:
            Dict[str, DataFrame]: 币种到K线数据的映射
        """
        result = {}
        
        # 记录成功和失败数量供日志
        successful = 0
        failed = 0
        
        logger.info(f"开始获取 {len(symbols)} 个交易对的K线数据")
        
        for symbol in symbols:
            try:
                # 添加适当延迟以尊重币安API限制
                time.sleep(0.3)  # 300ms延迟每个请求，满足币安的限流规则
                
                # 获取单个交易对的K线数据
                df = self.get_klines(symbol, timeframe, limit)
                
                # 如果获取成功，添加到结果字典
                if not df.empty:
                    result[symbol] = df
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"获取 {symbol} 的K线数据时发生错误: {str(e)}")
                failed += 1
        
        logger.info(f"批量获取K线数据完成: 成功 {successful}/{len(symbols)}个交易对")
        if failed > 0:
            logger.warning(f"{failed} 个交易对的数据获取失败")
                
        return result
    
    def get_recent_klines(self, symbol: str, timeframe: str = '1d', days: int = 30) -> pd.DataFrame:
        """
        获取最近一段时间的K线数据
        
        Args:
            symbol: 货币对符号
            timeframe: 时间周期
            days: 获取的天数
            
        Returns:
            DataFrame: 包含K线数据的DataFrame
        """
        # 计算需要多少根K线
        timeframe_in_minutes = self._timeframe_to_minutes(timeframe)
        minutes_in_period = days * 24 * 60
        limit = min(1000, minutes_in_period // timeframe_in_minutes)  # 限制在币安API最大1000条
        
        # 如果需要的数据超过1000条，则使用开始时间和结束时间来进行查询
        if minutes_in_period // timeframe_in_minutes > 1000:
            logger.info(f"要获取 {days} 天的数据需要 {minutes_in_period // timeframe_in_minutes} 条K线，超过币安限制，将只获取最新1000条")
            
        # 使用默认limit参数调用get_klines方法
        return self.get_klines(symbol, timeframe, limit)
    
    def get_current_price(self, symbol: str) -> Dict:
        """
        获取币种当前价格
        
        Args:
            symbol: 货币对符号
            
        Returns:
            Dict: 包含价格信息的字典
        """
        # 标准化符号
        binance_symbol = self._normalize_symbol(symbol)
        if not binance_symbol:
            logger.error(f"无法找到匹配的交易对: {symbol}")
            return {}
            
        # 准备API请求参数
        params = {'symbol': binance_symbol}
        
        # 调用币安的价格接口
        response_data = self._make_api_request(self.ticker_price_endpoint, params)
        
        if not response_data:
            logger.error(f"无法获取 {binance_symbol} 的价格数据")
            return {}
            
        # 使用get_klines获取最近一根K线的更多信息
        kline_df = self.get_klines(binance_symbol, '1d', 1)
        
        result = {
            'symbol': binance_symbol,
            'price': float(response_data.get('price', 0)),
            'baseAsset': self._get_base_asset(binance_symbol),
            'quoteAsset': self._get_quote_asset(binance_symbol),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        # 如果有K线数据，添加更多信息
        if not kline_df.empty:
            latest = kline_df.iloc[-1]
            result.update({
                '24h_change': latest['change'],
                '24h_high': float(latest['high']),
                '24h_low': float(latest['low']),
                '24h_volume': float(latest['volume']),
            })
        
        logger.info(f"{binance_symbol} 当前价格: {result['price']:.4f}")
        return result
    
    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """
        将时间周期字符串转换为分钟数
        
        Args:
            timeframe: 时间周期字符串，如 '1m', '1h', '1d'
            
        Returns:
            int: 对应的分钟数
        """
        # 支持币安的时间周期
        timeframe_map = {
            '1m': 1, '3m': 3, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '2h': 120, '4h': 240, '6h': 360, '8h': 480, '12h': 720,
            '1d': 1440, '3d': 4320, '1w': 10080, '1M': 43200
        }
        
        # 返回对应的分钟数，如果不支持则返回1小时
        if timeframe in timeframe_map:
            return timeframe_map[timeframe]
            
        # 解析自定义格式
        unit = timeframe[-1].lower()
        try:
            value = int(timeframe[:-1])
            
            if unit == 'm':
                return value
            elif unit == 'h':
                return value * 60
            elif unit == 'd':
                return value * 60 * 24
            elif unit == 'w':
                return value * 60 * 24 * 7
            elif unit == 'M':
                return value * 60 * 24 * 30  # 简化处理，挖30天/月
            else:
                logger.warning(f"不支持的时间单位: {unit}，使用默认1小时")
                return 60
        except ValueError:
            logger.warning(f"无效的时间周期格式: {timeframe}，使用默认1小时")
            return 60  # 默认为1小时
