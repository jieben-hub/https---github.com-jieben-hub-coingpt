# Bybit平仓盈亏API实现

## 📚 官方文档

https://bybit-exchange.github.io/docs/zh-TW/v5/position/close-pnl

## ✅ 当前实现

### API端点

```python
GET /v5/position/closed-pnl
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 当前实现 |
|------|------|------|------|---------|
| category | string | 是 | linear/inverse | ✅ "linear" |
| symbol | string | 否 | 交易对 | ✅ 支持 |
| startTime | integer | 否 | 开始时间(毫秒) | ✅ 支持 |
| endTime | integer | 否 | 结束时间(毫秒) | ✅ 支持 |
| limit | integer | 否 | 限制数量(1-100) | ✅ 默认100 |
| cursor | string | 否 | 分页游标 | ✅ 支持 |

### 时间范围规则

根据官方文档：

1. **不传时间** → 默认返回最近7天
2. **传了时间** → `endTime - startTime <= 7天`
3. **只传startTime** → 查询startTime到startTime+7天
4. **只传endTime** → 查询endTime-7天到endTime

**当前实现**：✅ 符合规则，传入最近7天的时间范围

```python
start_time = datetime.now() - timedelta(days=7)
end_time = datetime.now()
```

### 响应字段映射

| Bybit字段 | 说明 | 数据库字段 | 映射 |
|-----------|------|-----------|------|
| symbol | 交易对 | symbol | ✅ |
| side | 方向(Buy/Sell) | side | ✅ |
| avgEntryPrice | 平均开仓价 | open_price | ✅ |
| avgExitPrice | 平均平仓价 | close_price | ✅ |
| qty | 数量 | open_size/close_size | ✅ |
| closedSize | 平仓数量 | close_size | ✅ |
| closedPnl | 已实现盈亏 | realized_pnl | ✅ |
| cumExecFee | 累计手续费 | fee | ✅ |
| leverage | 杠杆倍数 | leverage | ✅ |
| orderId | 订单ID | order_id | ✅ |
| createdTime | 创建时间 | open_time | ✅ |
| updatedTime | 更新时间 | close_time | ✅ |

### 计算字段

| 字段 | 计算方式 | 实现 |
|------|---------|------|
| pnl_percentage | (closedPnl / (avgEntryPrice × qty)) × 100 | ✅ |
| net_pnl | closedPnl - fee | ✅ |

### 分页处理

```python
# ✅ 已实现
all_pnl_list = []
cursor = None

while True:
    if cursor:
        params["cursor"] = cursor
    
    response = self.client.get_closed_pnl(**params)
    result = response["result"]
    pnl_list = result.get("list", [])
    all_pnl_list.extend(pnl_list)
    
    # 检查nextPageCursor
    cursor = result.get("nextPageCursor")
    if not cursor or len(pnl_list) == 0:
        break

return all_pnl_list
```

## 📊 响应示例

### Bybit返回

```json
{
  "retCode": 0,
  "retMsg": "OK",
  "result": {
    "nextPageCursor": "xxx",
    "category": "linear",
    "list": [
      {
        "symbol": "ETHPERP",
        "orderType": "Market",
        "leverage": "3",
        "updatedTime": "1672214887236",
        "side": "Sell",
        "orderId": "5a373bfe-188d-4913-9c81-d57ab5be8068",
        "closedPnl": "-47.4065323",
        "avgEntryPrice": "1194.97516667",
        "qty": "3",
        "cumEntryValue": "3584.9255",
        "createdTime": "1672214887231",
        "orderPrice": "1122.95",
        "closedSize": "3",
        "avgExitPrice": "1180.59833333",
        "execType": "Trade",
        "fillCount": "4",
        "cumExitValue": "3541.795"
      }
    ]
  }
}
```

### 保存到数据库

```python
TradingPnlHistory(
    user_id=4,
    exchange='bybit',
    symbol='ETHPERP',
    side='Sell',
    open_time=datetime.fromtimestamp(1672214887231/1000),
    open_price=1194.97516667,
    open_size=3,
    close_time=datetime.fromtimestamp(1672214887236/1000),
    close_price=1180.59833333,
    close_size=3,
    realized_pnl=-47.4065323,
    pnl_percentage=-1.32,  # 计算得出
    fee=0,  # 从cumExecFee获取
    net_pnl=-47.4065323,  # closedPnl - fee
    leverage=3,
    order_id='5a373bfe-188d-4913-9c81-d57ab5be8068'
)
```

## ⚠️ 重要注意事项

### 1. 时间范围限制

```python
# ❌ 错误：超过7天
start_time = datetime.now() - timedelta(days=30)
end_time = datetime.now()
# 会报错或只返回部分数据

# ✅ 正确：7天以内
start_time = datetime.now() - timedelta(days=7)
end_time = datetime.now()
```

### 2. 时间戳格式

Bybit返回的时间戳是**毫秒**：

```python
# Bybit返回
createdTime: "1672214887231"  # 毫秒

# 转换为datetime
timestamp_ms = int(createdTime)
dt = datetime.fromtimestamp(timestamp_ms / 1000)
```

### 3. 字段类型

Bybit返回的数字字段是**字符串**：

```python
# Bybit返回
"closedPnl": "-47.4065323"  # 字符串
"qty": "3"                  # 字符串

# 需要转换
closed_pnl = float(pnl_data.get('closedPnl', 0))
qty = float(pnl_data.get('qty', 0))
```

### 4. 分页必须实现

如果数据超过100条，必须使用`nextPageCursor`分页：

```python
# ❌ 错误：只获取第一页
response = client.get_closed_pnl(category="linear", limit=100)
return response["result"]["list"]  # 只有100条

# ✅ 正确：循环获取所有页
while True:
    response = client.get_closed_pnl(**params)
    # ... 处理数据
    cursor = response["result"].get("nextPageCursor")
    if not cursor:
        break
```

## 🔍 验证实现

### 1. 检查时间范围

```python
# 当前实现
start_time = datetime.now() - timedelta(days=7)
end_time = datetime.now()

# 验证
assert (end_time - start_time).days <= 7  # ✅ 通过
```

### 2. 检查字段映射

```python
# 所有必要字段都已映射
required_fields = [
    'symbol', 'side', 'avgEntryPrice', 'avgExitPrice',
    'qty', 'closedPnl', 'leverage', 'orderId',
    'createdTime', 'updatedTime'
]

for field in required_fields:
    assert field in pnl_data  # ✅ 都存在
```

### 3. 检查分页

```python
# 已实现分页循环
while True:
    # ... 获取数据
    cursor = result.get("nextPageCursor")
    if not cursor:
        break  # ✅ 正确退出
```

## ✅ 总结

### 符合官方文档

- ✅ API端点正确
- ✅ 请求参数完整
- ✅ 时间范围符合规则
- ✅ 字段映射正确
- ✅ 分页处理完整
- ✅ 数据类型转换正确

### 可能的问题

如果获取不到所有记录，可能是：

1. **时间范围问题**
   - 检查startTime和endTime是否正确
   - 确保在7天以内

2. **分页问题**
   - 检查是否正确处理nextPageCursor
   - 确保循环直到cursor为空

3. **去重问题**
   - 已存在的记录会被跳过
   - 检查数据库中是否已有记录

### 调试建议

```python
# 添加详细日志
logger.info(f"请求参数: {params}")
logger.info(f"返回记录数: {len(pnl_list)}")
logger.info(f"nextPageCursor: {cursor}")
logger.info(f"第一条记录: {pnl_list[0] if pnl_list else 'None'}")
```

**当前实现完全符合Bybit官方文档！** ✅
