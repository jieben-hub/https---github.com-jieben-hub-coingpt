
from pybit.unified_trading import HTTP
import json
# 创建 Bybit 正式网连接
session = HTTP(
    testnet=False,  # ❗️设置为 False 表示连接正式网
    api_key="cNjP4nkl6SUKcmLnMT",
    api_secret="fC1uPDmBBsFlJVB58d6g3Cc6jGdacrTyx1vZ",
)

# 示例：获取最近一条已平仓盈亏记录
response = session.get_closed_pnl(
    category="linear",  # 线性合约
    limit=50
)

print(json.dumps(response))
