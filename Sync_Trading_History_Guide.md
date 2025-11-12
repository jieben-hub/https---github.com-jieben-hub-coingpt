# Bybit交易历史同步指南

## 🎯 功能说明

同步Bybit历史交易记录到数据库，包括：
- ✅ 已平仓位盈亏记录
- ✅ 订单历史记录

这样可以：
- 📊 查看完整的交易历史
- 💰 统计历史盈亏
- 📈 分析交易表现
- 🔍 追溯历史订单

## 📦 新增功能

### 1. Bybit交易所方法

在 `exchanges/bybit_exchange.py` 中添加：

```python
def get_closed_pnl(symbol=None, start_time=None, end_time=None, limit=100):
    """获取已平仓盈亏记录"""
    
def get_order_history(symbol=None, start_time=None, end_time=None, limit=100):
    """获取订单历史"""
```

### 2. 同步服务

`services/sync_trading_history.py`:

```python
class TradingHistorySync:
    @staticmethod
    def sync_closed_positions(user_id, exchange_name, days, symbol):
        """同步平仓记录"""
    
    @staticmethod
    def sync_order_history(user_id, exchange_name, days, symbol):
        """同步订单历史"""
    
    @staticmethod
    def sync_all_history(user_id, exchange_name, days, symbol):
        """同步所有历史"""
```

### 3. API路由

`routes/sync_routes.py`:

```
POST /api/sync/trading/pnl      # 同步平仓记录
POST /api/sync/trading/orders   # 同步订单记录
POST /api/sync/trading/all      # 同步所有记录
```

## 📊 API使用

### 1. 同步平仓历史

```http
POST /api/sync/trading/pnl
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
    "exchange": "bybit",
    "days": 30,
    "symbol": "BTCUSDT"  // 可选，不填则同步所有
}
```

**响应**：
```json
{
    "status": "success",
    "message": "同步完成",
    "synced_count": 10,      // 新增记录数
    "skipped_count": 5,      // 已存在跳过数
    "total_records": 15      // 总记录数
}
```

### 2. 同步订单历史

```http
POST /api/sync/trading/orders
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
    "exchange": "bybit",
    "days": 30,
    "symbol": "BTCUSDT"  // 可选
}
```

**响应**：
```json
{
    "status": "success",
    "message": "同步完成",
    "synced_count": 20,
    "skipped_count": 10,
    "total_records": 30
}
```

### 3. 同步所有历史

```http
POST /api/sync/trading/all
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
    "exchange": "bybit",
    "days": 30
}
```

**响应**：
```json
{
    "status": "success",
    "message": "所有历史记录同步完成",
    "pnl_sync": {
        "status": "success",
        "synced_count": 10,
        "skipped_count": 5,
        "total_records": 15
    },
    "order_sync": {
        "status": "success",
        "synced_count": 20,
        "skipped_count": 10,
        "total_records": 30
    }
}
```

## 📱 客户端集成

### Swift代码示例

```swift
class TradingHistorySync {
    let baseURL = "http://192.168.100.173:5000"
    var jwtToken: String = ""
    
    // 同步所有历史
    func syncAllHistory(days: Int = 30) async throws -> SyncResult {
        let url = URL(string: "\(baseURL)/api/sync/trading/all")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "exchange": "bybit",
            "days": days
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode(SyncResponse.self, from: data)
        
        return response.data
    }
    
    // 同步平仓记录
    func syncClosedPositions(days: Int = 30, symbol: String? = nil) async throws -> SyncDetail {
        let url = URL(string: "\(baseURL)/api/sync/trading/pnl")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        var body: [String: Any] = [
            "exchange": "bybit",
            "days": days
        ]
        if let symbol = symbol {
            body["symbol"] = symbol
        }
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode(SyncDetailResponse.self, from: data)
        
        return response.data
    }
}

// 数据模型
struct SyncResponse: Codable {
    let status: String
    let message: String
    let data: SyncResult
}

struct SyncResult: Codable {
    let pnlSync: SyncDetail
    let orderSync: SyncDetail
    
    enum CodingKeys: String, CodingKey {
        case pnlSync = "pnl_sync"
        case orderSync = "order_sync"
    }
}

struct SyncDetailResponse: Codable {
    let status: String
    let message: String
    let data: SyncDetail
}

struct SyncDetail: Codable {
    let status: String
    let message: String
    let syncedCount: Int
    let skippedCount: Int
    let totalRecords: Int
    
    enum CodingKeys: String, CodingKey {
        case status, message
        case syncedCount = "synced_count"
        case skippedCount = "skipped_count"
        case totalRecords = "total_records"
    }
}
```

### UI示例

```swift
struct SyncHistoryView: View {
    @State private var isSyncing = false
    @State private var syncResult: SyncResult?
    @State private var showAlert = false
    @State private var alertMessage = ""
    
    var body: some View {
        VStack(spacing: 20) {
            Text("同步交易历史")
                .font(.title)
                .fontWeight(.bold)
            
            if let result = syncResult {
                VStack(alignment: .leading, spacing: 10) {
                    Text("同步完成")
                        .font(.headline)
                    
                    HStack {
                        Text("平仓记录:")
                        Spacer()
                        Text("\(result.pnlSync.syncedCount) 新增 / \(result.pnlSync.skippedCount) 跳过")
                    }
                    
                    HStack {
                        Text("订单记录:")
                        Spacer()
                        Text("\(result.orderSync.syncedCount) 新增 / \(result.orderSync.skippedCount) 跳过")
                    }
                }
                .padding()
                .background(Color.green.opacity(0.1))
                .cornerRadius(10)
            }
            
            Button(action: {
                Task {
                    await syncHistory()
                }
            }) {
                if isSyncing {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                } else {
                    Text("同步最近30天记录")
                        .fontWeight(.semibold)
                }
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color.blue)
            .foregroundColor(.white)
            .cornerRadius(10)
            .disabled(isSyncing)
            
            Text("同步后可以查看完整的交易历史和盈亏统计")
                .font(.caption)
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)
        }
        .padding()
        .alert(isPresented: $showAlert) {
            Alert(title: Text("提示"), message: Text(alertMessage), dismissButton: .default(Text("确定")))
        }
    }
    
    func syncHistory() async {
        isSyncing = true
        
        do {
            let result = try await TradingHistorySync().syncAllHistory(days: 30)
            syncResult = result
            alertMessage = "同步成功！"
            showAlert = true
        } catch {
            alertMessage = "同步失败: \(error.localizedDescription)"
            showAlert = true
        }
        
        isSyncing = false
    }
}
```

## 🔄 同步流程

### 完整流程

```
1. 用户点击"同步历史"
   ↓
2. 客户端发送同步请求
   POST /api/sync/trading/all
   {
       "exchange": "bybit",
       "days": 30
   }
   ↓
3. 服务器调用Bybit API
   ├─ get_closed_pnl() - 获取平仓记录
   └─ get_order_history() - 获取订单记录
   ↓
4. 解析并保存到数据库
   ├─ 检查是否已存在（通过order_id去重）
   ├─ 计算盈亏百分比
   ├─ 保存到 trading_pnl_history 表
   └─ 保存到 trading_order_history 表
   ↓
5. 返回同步结果
   {
       "synced_count": 10,
       "skipped_count": 5
   }
   ↓
6. 客户端显示结果
   "同步成功！新增10条记录"
```

## 📊 保存的数据

### trading_pnl_history 表

| 字段 | 说明 | 来源 |
|------|------|------|
| symbol | 交易对 | Bybit API |
| side | 方向 | Buy→Long, Sell→Short |
| entry_price | 开仓价格 | avgEntryPrice |
| close_price | 平仓价格 | avgExitPrice |
| size | 数量 | qty |
| realized_pnl | 已实现盈亏 | closedPnl |
| pnl_percentage | 盈亏百分比 | 计算得出 |
| fee | 手续费 | cumExecFee |
| net_pnl | 净盈亏 | closedPnl - fee |
| leverage | 杠杆 | leverage |
| order_id | 订单ID | orderId |
| created_at | 平仓时间 | createdTime |

### trading_order_history 表

| 字段 | 说明 | 来源 |
|------|------|------|
| order_id | 订单ID | orderId |
| symbol | 交易对 | symbol |
| side | 方向 | side |
| order_type | 订单类型 | orderType |
| quantity | 数量 | qty |
| price | 价格 | price |
| filled_quantity | 成交数量 | cumExecQty |
| avg_price | 平均价格 | avgPrice |
| status | 状态 | orderStatus |
| order_time | 下单时间 | createdTime |
| update_time | 更新时间 | updatedTime |
| fee | 手续费 | cumExecFee |
| leverage | 杠杆 | leverage |

## 🧪 测试步骤

### 1. 测试同步平仓记录

```bash
curl -X POST http://192.168.100.173:5000/api/sync/trading/pnl \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "exchange": "bybit",
    "days": 30
  }'
```

### 2. 测试同步订单记录

```bash
curl -X POST http://192.168.100.173:5000/api/sync/trading/orders \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "exchange": "bybit",
    "days": 30
  }'
```

### 3. 测试同步所有记录

```bash
curl -X POST http://192.168.100.173:5000/api/sync/trading/all \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "exchange": "bybit",
    "days": 30
  }'
```

### 4. 验证数据库

```sql
-- 查看平仓记录
SELECT * FROM trading_pnl_history 
WHERE user_id = 4 
ORDER BY created_at DESC 
LIMIT 10;

-- 查看订单记录
SELECT * FROM trading_order_history 
WHERE user_id = 4 
ORDER BY order_time DESC 
LIMIT 10;

-- 统计同步数量
SELECT COUNT(*) as pnl_count FROM trading_pnl_history WHERE user_id = 4;
SELECT COUNT(*) as order_count FROM trading_order_history WHERE user_id = 4;
```

## ⚠️ 注意事项

### 1. 去重机制
- ✅ 通过`order_id`去重
- ✅ 已存在的记录会跳过
- ✅ 订单记录会更新状态

### 2. 时间范围
- 默认同步最近30天
- 可自定义天数（1-90天）
- Bybit API有查询限制

### 3. 数据量
- 每次最多返回100条
- 如果记录很多，可能需要多次同步
- 建议定期同步（如每周一次）

### 4. 性能
- 同步可能需要几秒钟
- 客户端显示加载状态
- 异步处理，不阻塞UI

## 📝 使用建议

### 首次使用
1. 同步最近30天的历史记录
2. 验证数据是否正确
3. 查看盈亏统计

### 日常使用
1. 每周同步一次最近7天
2. 或在查看历史前手动同步
3. 确保数据最新

### 数据分析
同步后可以：
- 查看完整交易历史
- 统计总盈亏
- 计算胜率
- 分析交易模式

## 🎉 总结

现在系统支持：
- ✅ 从Bybit同步历史平仓记录
- ✅ 从Bybit同步历史订单记录
- ✅ 自动去重，避免重复
- ✅ 完整的数据保存
- ✅ 简单的API调用

配合之前的功能：
- ✅ 实时平仓记录保存
- ✅ 查询历史盈亏
- ✅ 统计分析

现在交易历史功能已经完整！🚀
