# 修复行情API问题

## 🐛 问题描述

用户访问 `/api/trading/ticker` 时遇到两个错误：

### 1. Token payload 问题
```
Token payload missing user_id. Payload keys: ['sub', 'iat', 'exp']
```

### 2. 方法不存在
```
AttributeError: type object 'TradingService' has no attribute 'get_ticker'
```

## ✅ 解决方案

### 问题1：Token解析

**原因**：JWT token中使用的是`sub`字段存储用户ID，而不是`user_id`

**解决**：无需修改，`token_required`装饰器已经正确处理：
```python
# auth_service.py
payload = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
return True, int(payload["sub"])  # 使用sub字段
```

### 问题2：缺少get_ticker方法

**修复步骤**：

#### 1. 在BaseExchange添加抽象方法
```python
@abstractmethod
def get_ticker(self, symbol: str) -> Dict[str, Any]:
    """获取行情"""
    pass
```

#### 2. 在BybitExchange实现方法
```python
def get_ticker(self, symbol: str) -> Dict[str, Any]:
    """获取行情"""
    response = self.client.get_tickers(
        category="linear",
        symbol=symbol
    )
    
    ticker = response["result"]["list"][0]
    
    return {
        "symbol": ticker["symbol"],
        "last_price": float(ticker["lastPrice"]),
        "bid_price": float(ticker["bid1Price"]),
        "ask_price": float(ticker["ask1Price"]),
        "high_24h": float(ticker["highPrice24h"]),
        "low_24h": float(ticker["lowPrice24h"]),
        "volume_24h": float(ticker["volume24h"]),
        "change_24h": float(ticker["price24hPcnt"]) * 100,
        "timestamp": ticker["time"]
    }
```

#### 3. 在TradingService添加方法
```python
@classmethod
def get_ticker(
    cls,
    user_id: int,
    symbol: str,
    exchange_name: str = None
) -> Dict[str, Any]:
    """获取行情"""
    exchange = cls.get_exchange(user_id=user_id, exchange_name=exchange_name)
    return exchange.get_ticker(symbol)
```

## 📊 修改的文件

1. ✅ `exchanges/base_exchange.py` - 添加get_ticker抽象方法
2. ✅ `exchanges/bybit_exchange.py` - 实现get_ticker方法
3. ✅ `services/trading_service.py` - 添加get_ticker方法

## 🧪 测试

### HTTP API测试
```bash
curl -X GET "http://192.168.100.173:5000/api/trading/ticker?symbol=BTCUSDT" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 预期响应
```json
{
    "status": "success",
    "data": {
        "symbol": "BTCUSDT",
        "last_price": 106333.5,
        "bid_price": 106333.0,
        "ask_price": 106334.0,
        "high_24h": 107000.0,
        "low_24h": 105000.0,
        "volume_24h": 12345.67,
        "change_24h": 2.5,
        "timestamp": "1699600000000"
    }
}
```

## 📝 API使用说明

### 请求
```
GET /api/trading/ticker?symbol=BTCUSDT
Authorization: Bearer {jwt_token}
```

### 参数
- `symbol` (必需) - 交易对符号，如BTCUSDT
- `exchange` (可选) - 交易所名称，默认bybit

### 响应字段
| 字段 | 类型 | 说明 |
|------|------|------|
| symbol | string | 交易对符号 |
| last_price | float | 最新成交价 |
| bid_price | float | 买一价 |
| ask_price | float | 卖一价 |
| high_24h | float | 24小时最高价 |
| low_24h | float | 24小时最低价 |
| volume_24h | float | 24小时成交量 |
| change_24h | float | 24小时涨跌幅(%) |
| timestamp | string | 时间戳 |

## ✅ 验证清单

- [x] BaseExchange添加get_ticker抽象方法
- [x] BybitExchange实现get_ticker方法
- [x] TradingService添加get_ticker方法
- [x] API路由已存在 (routes/trading_routes.py)
- [x] Token解析正确处理sub字段

## 🎉 完成

现在重启服务器，行情API应该可以正常工作了！

### 使用示例

```swift
// Swift客户端
func fetchTicker(symbol: String) async throws -> TickerData {
    let url = URL(string: "http://192.168.100.173:5000/api/trading/ticker?symbol=\(symbol)")!
    var request = URLRequest(url: url)
    request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
    
    let (data, _) = try await URLSession.shared.data(for: request)
    let response = try JSONDecoder().decode(TickerResponse.self, from: data)
    
    return response.data
}

// 使用
let ticker = try await fetchTicker(symbol: "BTCUSDT")
print("BTC价格: $\(ticker.lastPrice)")
```

## 🔄 WebSocket推送

除了HTTP API，还可以使用WebSocket实时推送：

```swift
// 订阅行情
socket.emit("subscribe_ticker", ["symbols": ["BTCUSDT"]])

// 接收更新
socket.on("ticker_update") { data, ack in
    // 每2秒自动推送
}
```

详见：`WebSocket_Ticker_Guide.md`
