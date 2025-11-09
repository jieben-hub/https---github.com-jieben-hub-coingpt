# -*- coding: utf-8 -*-
"""
定时任务脚本：每天18:00自动获取币安币种信息并存储到本地缓存
"""
from utils.symbols_sync import fetch_binance_symbols
import datetime

if __name__ == "__main__":
    print(f"[{datetime.datetime.now()}] 开始同步币安币种信息...")
    fetch_binance_symbols()
    print(f"[{datetime.datetime.now()}] 同步完成！") 