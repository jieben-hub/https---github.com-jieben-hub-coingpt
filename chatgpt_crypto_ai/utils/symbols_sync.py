# -*- coding: utf-8 -*-
"""
直接从币安API获取并同步最新币种信息
"""
import json
import os
import time
import requests
from typing import List, Dict, Any, Optional
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('symbols_sync')

# API设置
BINANCE_API_BASE = 'https://api.binance.com'
BINANCE_API_FALLBACK = 'https://api1.binance.com'  # 备用API地址
BINANCE_EXCHANGE_INFO_ENDPOINT = '/api/v3/exchangeInfo'

# 缓存文件路径
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")
SYMBOLS_CACHE_FILE = os.path.join(CACHE_DIR, "binance_symbols.json")

# 缓存有效期（24小时）
CACHE_TTL = 86400  # 秒


def ensure_cache_dir():
    """确保缓存目录存在"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def fetch_binance_symbols() -> Dict[str, Dict]:
    """
    直接从币安API获取所有支持的交易对信息
    
    Returns:
        Dict[str, Dict]: 交易对信息字典，键为交易对符号，值为详细信息
    """
    try:
        logger.info("正在从币安API获取交易对信息...")
        
        # 首先尝试主API地址
        response = None
        api_urls = [BINANCE_API_BASE, BINANCE_API_FALLBACK]
        
        for api_url in api_urls:
            try:
                full_url = f"{api_url}{BINANCE_EXCHANGE_INFO_ENDPOINT}"
                logger.info(f"请求币安API: {full_url}")
                
                response = requests.get(
                    full_url,
                    headers={'User-Agent': 'CoinGPT/1.0'},
                    timeout=10  # 设置超时时间
                )
                
                if response.status_code == 200:
                    break  # 成功获取数据，跳出循环
                else:
                    logger.warning(f"请求币安API失败，状态码: {response.status_code}，尝试备用URL")
            
            except Exception as e:
                logger.warning(f"请求币安API {api_url} 失败: {str(e)}，尝试备用URL")
        
        # 检查是否成功获取数据
        if not response or response.status_code != 200:
            logger.error("所有币安API请求都失败")
            return {}
        
        # 解析响应数据
        data = response.json()
        symbols_data = data.get('symbols', [])
        
        # 处理交易对信息
        symbols_dict = {}
        base_coins = set()  # 用于存储基础币种
        
        for symbol_info in symbols_data:
            symbol = symbol_info.get('symbol')
            status = symbol_info.get('status')
            base_asset = symbol_info.get('baseAsset')
            quote_asset = symbol_info.get('quoteAsset')
            
            # 只保留状态为TRADING的交易对
            if status == 'TRADING' and symbol and base_asset and quote_asset:
                symbols_dict[symbol] = {
                    'baseAsset': base_asset,
                    'quoteAsset': quote_asset,
                    'status': status
                }
                base_coins.add(base_asset)
        
        # 转换基础币种为排序列表
        base_coin_list = sorted(list(base_coins))
        
        logger.info(f"从币安API获取到 {len(symbols_dict)} 个交易对和 {len(base_coin_list)} 个基础币种")
        
        # 保存到缓存
        save_symbols_cache(symbols_dict, base_coin_list)
        
        return symbols_dict
    
    except Exception as e:
        logger.error(f"获取币安交易对信息失败: {str(e)}")
        return {}


def save_symbols_cache(symbols_dict: Dict[str, Dict], base_coins: List[str]):
    """保存交易对和币种信息到缓存文件"""
    ensure_cache_dir()
    
    cache_data = {
        "timestamp": int(time.time()),
        "symbols_dict": symbols_dict,
        "base_coins": base_coins
    }
    
    try:
        with open(SYMBOLS_CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
        logger.info(f"交易对和币种信息已缓存到 {SYMBOLS_CACHE_FILE}")
    except Exception as e:
        logger.error(f"保存交易对缓存失败: {str(e)}")


def load_symbols_cache() -> Optional[Dict]:
    """从缓存加载交易对和币种信息，如果缓存有效的话"""
    if not os.path.exists(SYMBOLS_CACHE_FILE):
        return None
    
    try:
        with open(SYMBOLS_CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
        
        timestamp = cache_data.get("timestamp", 0)
        symbols_dict = cache_data.get("symbols_dict", {})
        base_coins = cache_data.get("base_coins", [])
        
        # 检查缓存是否过期
        if int(time.time()) - timestamp > CACHE_TTL:
            logger.info("交易对缓存已过期")
            return None
        
        logger.info(f"从缓存加载了 {len(symbols_dict)} 个交易对和 {len(base_coins)} 个基础币种")
        return {
            "symbols_dict": symbols_dict,
            "base_coins": base_coins
        }
    
    except Exception as e:
        logger.error(f"加载交易对缓存失败: {str(e)}")
        return None


def get_all_symbols() -> List[str]:
    """
    获取所有基础币种符号，优先使用缓存，缓存无效则从API获取
    
    Returns:
        List[str]: 基础币种符号列表
    """
    # 尝试从缓存加载
    cache_data = load_symbols_cache()
    
    # 如果缓存无效或不存在，从API获取
    if not cache_data:
        symbols_dict = fetch_binance_symbols()
        # 从交易对中提取基础币种
        base_coins = set()
        for symbol_info in symbols_dict.values():
            base_coins.add(symbol_info.get('baseAsset'))
        return sorted(list(base_coins))
    else:
        return cache_data.get("base_coins", [])


def get_trading_pairs() -> Dict[str, Dict]:
    """
    获取所有交易对信息，优先使用缓存，缓存无效则从API获取
    
    Returns:
        Dict[str, Dict]: 交易对信息字典，键为交易对符号，值为详细信息
    """
    # 尝试从缓存加载
    cache_data = load_symbols_cache()
    
    # 如果缓存无效或不存在，从API获取
    if not cache_data:
        return fetch_binance_symbols()
    else:
        return cache_data.get("symbols_dict", {})


if __name__ == "__main__":
    # 测试基础币种获取
    base_coins = get_all_symbols()
    print(f"获取到 {len(base_coins)} 个基础币种")
    print("前20个基础币种:", base_coins[:20])
    
    # 测试交易对获取
    trading_pairs = get_trading_pairs()
    print(f"获取到 {len(trading_pairs)} 个交易对")
    sample_pairs = list(trading_pairs.keys())[:5]
    for pair in sample_pairs:
        info = trading_pairs[pair]
        print(f"{pair}: 基础资产={info['baseAsset']}, 计价资产={info['quoteAsset']}")
        
    # 测试常见币种的交易对
    common_coins = ['BTC', 'ETH', 'SOL', 'XRP']
    for coin in common_coins:
        matching_pairs = [p for p in trading_pairs.keys() if trading_pairs[p]['baseAsset'] == coin and trading_pairs[p]['quoteAsset'] == 'USDT']
        if matching_pairs:
            print(f"{coin}的主要交易对: {matching_pairs[0]}")
        else:
            print(f"{coin}没有USDT交易对")
