# 交易历史盈亏API使用指南

## 🎯 功能概述

新增的交易历史系统可以：
- ✅ **自动记录平仓盈亏** - 每次平仓都会写入数据库
- ✅ **查看历史盈亏列表** - 支持分页、筛选、排序
- ✅ **盈亏统计分析** - 胜率、平均盈亏、最佳/最差交易
- ✅ **订单历史记录** - 完整的订单生命周期跟踪
- ✅ **交易表现分析** - 按币种、时间段分析交易表现

## 📊 新增API接口

### 1. 历史盈亏记录 `/api/trading/history/pnl`

#### GET - 获取历史盈亏列表
```http
GET /api/trading/history/pnl?limit=20&offset=0&symbol=BTCUSDT&start_date=2025-11-01
Authorization: Bearer <JWT_TOKEN>
```

**查询参数：**
- `limit`: 返回记录数量 (默认50，最大100)
- `offset`: 偏移量 (默认0)
- `symbol`: 币种筛选 (可选)
- `exchange`: 交易所筛选 (可选)
- `start_date`: 开始日期 YYYY-MM-DD (可选)
- `end_date`: 结束日期 YYYY-MM-DD (可选)

**响应示例：**
```json
{
  "status": "success",
  "data": {
    "records": [
      {
        "id": 1,
        "exchange": "bybit",
        "symbol": "BTCUSDT",
        "side": "Buy",
        "open_time": "2025-11-10T10:00:00Z",
        "open_price": 50000.0,
        "open_size": 0.1,
        "close_time": "2025-11-10T11:00:00Z",
        "close_price": 50500.0,
        "close_size": 0.1,
        "realized_pnl": 50.0,
        "pnl_percentage": 10.0,
        "fee": 2.5,
        "net_pnl": 47.5,
        "leverage": 10.0,
        "created_at": "2025-11-10T11:01:00Z"
      }
    ],
    "pagination": {
      "limit": 20,
      "offset": 0,
      "has_more": false
    }
  }
}
```

### 2. 盈亏统计汇总 `/api/trading/history/pnl/summary`

#### GET - 获取盈亏统计
```http
GET /api/trading/history/pnl/summary?period=month&exchange=bybit
Authorization: Bearer <JWT_TOKEN>
```

**查询参数：**
- `period`: 统计周期 (today, week, month, quarter, year, all)
- `exchange`: 交易所筛选 (可选)
- `start_date`: 自定义开始日期 (可选)
- `end_date`: 自定义结束日期 (可选)

**响应示例：**
```json
{
  "status": "success",
  "data": {
    "summary": {
      "total_trades": 25,
      "total_realized_pnl": 1250.50,
      "total_net_pnl": 1200.00,
      "total_fees": 50.50,
      "win_trades": 15,
      "lose_trades": 10,
      "win_rate": 60.0,
      "avg_win": 120.0,
      "avg_loss": -80.0,
      "best_trade": 500.0,
      "worst_trade": -200.0
    },
    "period": "month"
  }
}
```

### 3. 订单历史记录 `/api/trading/history/orders`

#### GET - 获取订单历史
```http
GET /api/trading/history/orders?limit=20&status=Filled
Authorization: Bearer <JWT_TOKEN>
```

**查询参数：**
- `limit`: 返回记录数量
- `offset`: 偏移量
- `symbol`: 币种筛选
- `exchange`: 交易所筛选
- `status`: 订单状态筛选

### 4. 交易统计数据 `/api/trading/history/stats`

#### GET - 获取多时间段统计
```http
GET /api/trading/history/stats?exchange=bybit
Authorization: Bearer <JWT_TOKEN>
```

**响应包含：**
- 今日统计
- 本周统计
- 本月统计
- 本季度统计
- 本年统计
- 历史总计

## 🔄 自动记录机制

### 平仓自动记录
当检测到持仓减少或消失时，系统会自动调用：

```python
from services.trading_history_service import TradingHistoryService

# 记录平仓盈亏
result = TradingHistoryService.record_position_close(
    user_id=user_id,
    exchange='bybit',
    position_data=position_info,
    close_price=close_price,
    close_size=close_size
)
```

### 订单状态自动记录
每次订单状态更新时：

```python
# 记录订单更新
result = TradingHistoryService.record_order_update(
    user_id=user_id,
    exchange='bybit',
    order_data=order_info
)
```

## 📱 客户端集成示例

### Swift iOS集成
```swift
class TradingHistoryService {
    private let baseURL = "http://192.168.100.173:5000/api/trading/history"
    
    func getPnlHistory(limit: Int = 20, offset: Int = 0) async throws -> PnlHistoryResponse {
        let url = URL(string: "\(baseURL)/pnl?limit=\(limit)&offset=\(offset)")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(PnlHistoryResponse.self, from: data)
    }
    
    func getPnlSummary(period: String = "month") async throws -> PnlSummaryResponse {
        let url = URL(string: "\(baseURL)/pnl/summary?period=\(period)")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(PnlSummaryResponse.self, from: data)
    }
}

// 数据模型
struct PnlRecord: Codable, Identifiable {
    let id: Int
    let symbol: String
    let side: String
    let openPrice: Double
    let closePrice: Double
    let realizedPnl: Double
    let pnlPercentage: Double
    let netPnl: Double
    let closeTime: String
    
    enum CodingKeys: String, CodingKey {
        case id, symbol, side
        case openPrice = "open_price"
        case closePrice = "close_price"
        case realizedPnl = "realized_pnl"
        case pnlPercentage = "pnl_percentage"
        case netPnl = "net_pnl"
        case closeTime = "close_time"
    }
}
```

### SwiftUI视图示例
```swift
struct TradingHistoryView: View {
    @StateObject private var historyService = TradingHistoryService()
    @State private var pnlRecords: [PnlRecord] = []
    @State private var summary: PnlSummary?
    
    var body: some View {
        NavigationView {
            VStack {
                // 统计卡片
                if let summary = summary {
                    PnlSummaryCard(summary: summary)
                }
                
                // 历史记录列表
                List(pnlRecords) { record in
                    PnlRecordRow(record: record)
                }
            }
            .navigationTitle("交易历史")
            .onAppear {
                loadData()
            }
        }
    }
    
    private func loadData() {
        Task {
            do {
                let historyResponse = try await historyService.getPnlHistory()
                let summaryResponse = try await historyService.getPnlSummary()
                
                DispatchQueue.main.async {
                    self.pnlRecords = historyResponse.data.records
                    self.summary = summaryResponse.data.summary
                }
            } catch {
                print("加载数据失败: \(error)")
            }
        }
    }
}

struct PnlRecordRow: View {
    let record: PnlRecord
    
    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text(record.symbol)
                    .font(.headline)
                Text(record.side)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            VStack(alignment: .trailing) {
                Text("\(record.netPnl, specifier: "%.2f")")
                    .font(.headline)
                    .foregroundColor(record.netPnl >= 0 ? .green : .red)
                Text("\(record.pnlPercentage, specifier: "%.1f")%")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 2)
    }
}
```

## 🛠️ 数据库设置

### 1. 创建数据库表
```bash
python create_trading_history_tables.py
```

### 2. 表结构说明

**trading_pnl_history** - 历史盈亏记录
- 记录每次平仓的详细信息
- 包含开仓/平仓价格、数量、时间
- 自动计算盈亏百分比和净盈亏

**trading_order_history** - 订单历史记录  
- 记录所有订单的生命周期
- 支持订单状态更新
- 包含成交价格、数量、手续费等

## 🔄 WebSocket实时更新

历史盈亏数据也可以通过WebSocket实时推送：

```javascript
// 订阅历史数据更新
socket.on('pnl_history_update', function(data) {
    console.log('新的盈亏记录:', data);
    // 更新历史列表UI
    updatePnlHistoryList(data.record);
});

socket.on('order_history_update', function(data) {
    console.log('订单状态更新:', data);
    // 更新订单历史UI
    updateOrderHistoryList(data.order);
});
```

## 📈 使用场景

1. **交易复盘** - 查看历史交易记录，分析盈亏情况
2. **策略分析** - 统计不同币种、时间段的交易表现
3. **风险管理** - 监控最大回撤、连续亏损等指标
4. **税务申报** - 导出详细的交易记录用于报税
5. **绩效评估** - 计算夏普比率、胜率等交易指标

## 🎯 下一步优化

1. **数据导出** - 支持CSV/Excel格式导出
2. **图表分析** - 盈亏曲线、收益分布图
3. **策略标签** - 为交易添加策略标签便于分析
4. **风险指标** - 计算更多风险管理指标
5. **自动备份** - 定期备份交易历史数据

现在你的CoinGPT应用已经具备完整的历史盈亏功能！每次平仓都会自动记录到数据库，用户可以随时查看详细的交易历史和统计分析。
