# -*- coding: utf-8 -*-
"""
更新Bybit币种信息脚本
"""
from symbols_sync import fetch_bybit_symbols
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("开始同步Bybit币种信息...")
    symbols = fetch_bybit_symbols()
    print(f"成功同步 {len(symbols)} 个币种")
    print("前20个币种示例:", symbols[:20] if len(symbols) >= 20 else symbols)
    print("同步完成！")
