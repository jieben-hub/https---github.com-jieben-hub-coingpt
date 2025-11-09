# -*- coding: utf-8 -*-
"""
从用户输入的自然语言中提取加密货币的相关信息
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple

# 尝试导入币种同步模块
try:
    from utils.symbols_sync import get_all_symbols
    # 从 Bybit API 获取实时币种列表
    BYBIT_SYMBOLS = get_all_symbols()
    logging.info(f"从 Bybit API 加载了 {len(BYBIT_SYMBOLS)} 个币种符号")
except Exception as e:
    logging.error(f"加载 Bybit 币种失败: {str(e)}")
    BYBIT_SYMBOLS = []

# 常见加密货币符号列表 - 确保关键币种始终存在
COMMON_CRYPTO_SYMBOLS = [
    "BTC", "ETH", "USDT", "BNB", "XRP", "ADA", "SOL", "DOGE", "DOT", "AVAX", 
    "SHIB", "MATIC", "LTC", "UNI", "LINK", "XLM", "ATOM", "ETC", "BCH", "FIL", 
    "VET", "TRX", "XMR", "THETA", "XTZ", "ALGO", "EOS", "EGLD", "AAVE", "CAKE",
    "NEO", "QNT", "FTM", "MANA", "AXS", "GRT", "SAND", "LUNA", "GALA", "ONE"
]

# 结合 API 和静态列表生成完整币种列表
ALL_CRYPTO_SYMBOLS = list(set(COMMON_CRYPTO_SYMBOLS + BYBIT_SYMBOLS))

# 特殊处理的加密货币名称与符号映射
CRYPTO_NAME_TO_SYMBOL = {
    "比特币": "BTC",
    "以太坊": "ETH",
    "以太币": "ETH",
    "莱特币": "LTC",
    "狗狗币": "DOGE",
    "柚子": "EOS",
    "波场": "TRX",
    "币安币": "BNB",
    "瑞波币": "XRP",
    "艾达币": "ADA",
    "卡尔达诺": "ADA",
    "波卡": "DOT",
    "索拉纳": "SOL",
    "雪崩": "AVAX",
    "链接": "LINK",
    "恒星币": "XLM",
    "宇宙币": "ATOM",
    "门罗币": "XMR",
    "泰达币": "USDT",
    "柴犬币": "SHIB",
    "多边形": "MATIC",
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "litecoin": "LTC",
    "dogecoin": "DOGE",
    "binance coin": "BNB",
    "ripple": "XRP",
    "cardano": "ADA",
    "polkadot": "DOT",
    "solana": "SOL",
    "avalanche": "AVAX",
    "chainlink": "LINK",
    "stellar": "XLM",
    "cosmos": "ATOM",
    "monero": "XMR",
    "tether": "USDT",
    "shiba inu": "SHIB",
    "polygon": "MATIC",
}

# 常用时间窗口映射
TIME_WINDOW_MAP = {
    "分钟": "1m",
    "小时": "1h",
    "4小时": "4h",
    "天": "1d",
    "日": "1d",
    "周": "1w",
    "月": "1M",
    "minute": "1m",
    "hour": "1h",
    "day": "1d",
    "week": "1w",
    "month": "1M",
}

def extract_crypto_symbols(text: str) -> List[str]:
    """
    从文本中提取加密货币符号
    
    Args:
        text (str): 用户输入的文本
    
    Returns:
        List[str]: 提取出的加密货币符号列表
    """
    # 将文本转换为大写和小写形式
    upper_text = text.upper()
    lower_text = text.lower()
    
    # 直接匹配币种符号
    found_symbols = []
    
    # 预处理文本，添加空格在标点符号前后，以确保正确分词
    processed_text = re.sub(r'([.,!?()\[\]{}:;\'"\s])', r' \1 ', text)
    processed_text = re.sub(r'\s+', ' ', processed_text)  # 将多个空格合并为一个
    tokens = processed_text.split()
    
    # 1. 首先匹配完全相等的词组
    for symbol in ALL_CRYPTO_SYMBOLS:
        if symbol.lower() in [t.lower() for t in tokens] or symbol in [t for t in tokens]:
            if symbol not in found_symbols:
                found_symbols.append(symbol)
    
    # 2. 使用正则表达式匹配单词边界
    for symbol in ALL_CRYPTO_SYMBOLS:
        if symbol in found_symbols:
            continue  # 已经匹配到的跳过
        
        # 匹配完整词边界
        pattern = r'\b' + re.escape(symbol) + r'\b'
        if re.search(pattern, upper_text) or re.search(pattern, lower_text):
            found_symbols.append(symbol)
            continue
        
        # 匹配交易对中的符号（如BTC/USDT中的BTC）
        pattern = r'\b' + re.escape(symbol) + r'/'
        if re.search(pattern, upper_text) or re.search(pattern, lower_text):
            found_symbols.append(symbol)
    
    # 匹配中文或英文名称
    for name, symbol in CRYPTO_NAME_TO_SYMBOL.items():
        if name.lower() in text.lower() and symbol not in found_symbols:
            found_symbols.append(symbol)
    
    return found_symbols

def extract_time_window(text: str) -> Optional[str]:
    """
    提取时间窗口信息
    
    Args:
        text (str): 用户输入的文本
    
    Returns:
        Optional[str]: 提取出的时间窗口，如果未找到则返回None
    """
    # 检查常用时间窗口表达
    for key, value in TIME_WINDOW_MAP.items():
        if key in text.lower():
            return value
            
    # 匹配数字+时间单位的模式
    time_patterns = [
        (r'(\d+)\s*分钟', 'm'),
        (r'(\d+)\s*小时', 'h'),
        (r'(\d+)\s*天', 'd'),
        (r'(\d+)\s*日', 'd'),
        (r'(\d+)\s*周', 'w'),
        (r'(\d+)\s*月', 'M'),
        (r'(\d+)\s*min', 'm'),
        (r'(\d+)\s*hour', 'h'),
        (r'(\d+)\s*day', 'd'),
        (r'(\d+)\s*week', 'w'),
        (r'(\d+)\s*month', 'M'),
    ]
    
    for pattern, unit in time_patterns:
        match = re.search(pattern, text.lower())
        if match:
            return f"{match.group(1)}{unit}"
    
    # 如果未找到特定时间窗口，默认返回None
    return None

def extract_all_info(prompt: str) -> Dict[str, Any]:
    """
    从提示中提取所有相关信息
    
    Args:
        prompt (str): 用户输入的提示
        
    Returns:
        Dict: 包含提取的信息
    """
    symbols = extract_crypto_symbols(prompt)
    time_window = extract_time_window(prompt)
    
    # 默认时间窗口为1天
    if not time_window:
        time_window = "1d"
    
    return {
        "symbols": symbols,
        "time_window": time_window,
    }
