# -*- coding: utf-8 -*-
from utils.kline import KlineDataFetcher
import pandas as pd
import time

# 测试配置
symbols_to_test = [
    'BTC',      # 简单符号
    'BTC/USDT', # 标准斜杠格式
    'BTCUSDT',  # 无斜杠格式
    'ETH',      # 另一个常见币种
    'SOL',      # 第三代区块链
    'AAVE',     # DeFi代币
    'XRP',      # 另一种主流币
    'PEPE'      # 流行迷因币测试
]

timeframes = ['1h', '4h', '1d']

# 初始化K线获取器
print("初始化币安K线数据获取器...")
kline_fetcher = KlineDataFetcher()  # 新API不需要传递exchange_id参数

# 测试函数
def test_symbol(symbol, timeframe='1h', limit=10):
    print(f"\n{'='*50}")
    print(f"测试获取 {symbol} 的 {timeframe} K线数据 (最近{limit}条)")
    
    start_time = time.time()
    df = kline_fetcher.get_klines(symbol, timeframe, limit)
    duration = time.time() - start_time
    
    if not df.empty:
        print(f"[成功] 成功获取到 {len(df)} 条数据，耗时 {duration:.2f} 秒")
        print(f"交易对: {df['symbol'].iloc[0]}")
        
        # 显示基础资产和计价资产
        if 'base_asset' in df.columns and 'quote_asset' in df.columns:
            print(f"基础资产: {df['base_asset'].iloc[0]}, 计价资产: {df['quote_asset'].iloc[0]}")
            
        print("\n最新价格数据:")
        latest = df.iloc[-1]
        print(f"时间: {latest['timestamp']}")
        print(f"开盘: {latest['open']:.2f}, 收盘: {latest['close']:.2f}")
        print(f"最高: {latest['high']:.2f}, 最低: {latest['low']:.2f}")
        print(f"成交量: {latest['volume']:.2f}")
        
        # 显示额外计算的指标
        if 'change' in df.columns:
            print(f"价格变化: {latest['change']:.2f}%")
        if 'range_percent' in df.columns:
            print(f"波动范围: {latest['range_percent']:.2f}%")
        
        # 如果有其他币安特有的字段，也显示它们
        if 'quote_volume' in df.columns:
            print(f"计价资产成交量: {latest['quote_volume']:.2f}")
        if 'trades_count' in df.columns:
            print(f"交易次数: {latest['trades_count']}")
    else:
        print(f"[失败] 获取 {symbol} 数据失败，耗时 {duration:.2f} 秒")
    return not df.empty

# 执行测试
print("开始测试常用币种的K线数据获取...")
print("使用1小时时间框架")

successful = 0
failed = 0

# 测试所有币种
for symbol in symbols_to_test:
    if test_symbol(symbol):
        successful += 1
    else:
        failed += 1
    # 简单延迟避免API限制
    time.sleep(1)

# 测试不同时间框架
if successful > 0:
    print("\n测试不同时间框架...")
    test_coin = symbols_to_test[0]  # 使用第一个成功的币种
    
    for tf in timeframes:
        test_symbol(test_coin, tf, 5)
        time.sleep(1)
        
    # 测试较长历史数据
    print("\n测试获取更多历史数据...")
    test_symbol(test_coin, '1d', 30)

# 结果统计
print(f"\n{'='*50}")
print(f"测试完成: 成功 {successful}/{len(symbols_to_test)} 币种")
if failed > 0:
    print(f"失败: {failed}/{len(symbols_to_test)} 币种")
print("""注意: 
1. 如果测试成功，说明币安API直接连接正常工作
2. 如果特定币种失败，可能是因为该币种在币安不可用或符号格式不匹配
3. K线数据包含额外的计算字段如变化百分比(change)和波动范围(range_percent)
4. 数据中还包括币安特有的字段如计价资产成交量(quote_volume)和交易次数(trades_count)
""")