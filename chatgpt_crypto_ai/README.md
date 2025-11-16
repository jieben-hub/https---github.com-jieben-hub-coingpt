# CoinGPT - 区块链行情聊天机器人

CoinGPT是一个基于Flask和OpenAI API开发的智能加密货币行情分析聊天机器人。它能够理解用户的自然语言提问，自动识别其中提及的加密货币，获取实时市场数据，进行技术分析，并生成专业的回复和建议。

## 🌟 主要功能

- 支持用户发送自然语言提问，自动识别提及的加密货币
- 从Bybit等交易所实时获取K线数据
- 进行技术分析和趋势判断
- 构造合理的Prompt发送给OpenAI的GPT模型
- 支持多轮上下文记忆，实现连贯对话
- 支持Apple Sign-In登录(可选配置)

## 🚀 技术栈

- **后端框架**：Flask
- **数据源**：ccxt库(支持多家交易所)
- **AI引擎**：OpenAI ChatGPT API
- **前端**：HTML5 + CSS3 + JavaScript
- **会话管理**：Flask Session
- **可选功能**：Redis用于会话存储、Apple Sign-In用户认证

## 📋 安装指南

### 前提条件

- Python 3.8+
- pip包管理器
- OpenAI API密钥
- (可选)交易所API密钥

### 安装步骤

1. 克隆项目代码：
   ```
   git clone <项目URL>
   cd chatgpt_crypto_ai
   ```

2. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

3. 配置环境变量：
   ```
   cp .env.example .env
   ```
   然后编辑`.env`文件，填入您的API密钥和配置信息。

4. 运行应用：
   ```
   python app.py
   ```

5. 访问应用：
   在浏览器中打开 http://localhost:5000 即可使用CoinGPT。

## 🔧 配置选项

所有配置选项都可以在`.env`文件中设置：

- `OPENAI_API_KEY`：您的OpenAI API密钥
- `OPENAI_MODEL`：使用的GPT模型，默认为"gpt-3.5-turbo"
- `EXCHANGE`：使用的交易所，默认为"bybit"
- `EXCHANGE_API_KEY`和`EXCHANGE_SECRET`：交易所API密钥(可选)
- `DEBUG`：是否启用调试模式
- `SECRET_KEY`：Flask应用密钥
- `USE_REDIS`：是否使用Redis存储会话

## 💡 使用示例

用户可以通过自然语言向CoinGPT提问，例如：

- "BTC最近一周的走势如何？"
- "分析一下以太坊4小时图的技术指标"
- "SOL和AVAX哪个表现更好？"
- "比特币现在是牛市还是熊市？"

## 📊 项目结构

```
chatgpt_crypto_ai/
│
├── app.py                    # Flask主入口
├── config.py                 # 配置项
├── requirements.txt          # 项目依赖
├── .env.example              # 环境变量示例
│
├── routes/
│   └── chat_routes.py        # 核心聊天接口
│
├── utils/
│   ├── extract.py            # 从prompt中提取币种
│   ├── kline.py              # 拉取行情(ccxt)
│   ├── trend.py              # 趋势分析逻辑
│   └── prompt.py             # 构造GPT输入消息
│
├── static/                   # 静态资源
│   ├── css/
│   │   └── style.css         # 样式表
│   └── js/
│       └── app.js            # 前端交互脚本
│
└── templates/                # HTML模板
    └── index.html            # 主页面
```

## ⚠️ 免责声明

CoinGPT提供的分析和建议仅供参考，不构成投资建议。用户应自行承担使用该工具进行投资决策的全部风险。

## 📝 许可证

[MIT License](LICENSE)

## 📮 API 接口说明

> 除特别说明外，所有接口均返回如下结构的 JSON：
>
> ```json
> {
>   "status": "success" | "error",
>   "data": {...},
>   "message": "可选的提示信息"
> }
> ```
>
> 需要鉴权的接口必须通过 `Authorization: Bearer <token>` 或 Cookie 中的 `token` 携带登录态。

### 认证与用户（`/api/auth`）

| 方法 | 路径 | 说明 | 认证 |
| --- | --- | --- | --- |
| POST | `/register` | 用户名 + 密码注册，可选 `inviter_id` | 否 |
| POST | `/login` | 用户名 + 密码登录 | 否 |
| POST | `/apple/login` | Apple ID 登录，提交 `id_token` | 否 |
| POST | `/logout` | 清除当前会话 | 否（但需 cookie） |
| GET | `/user` | 获取当前用户信息 | 是 |
| GET | `/sessions` | 分页获取用户会话列表（query: `limit`, `offset`） | 是 |
| POST | `/sessions` | 创建新会话（受免费额度限制） | 是 |
| DELETE | `/sessions/<session_id>` | 删除会话（需会员身份） | 是 |
| GET | `/invite` | 获取邀请码及邀请人数 | 是 |
| GET | `/invitees` | 获取邀请的用户列表 | 是 |
| GET | `/usage` `/usage-stats` | 查询当前使用额度 | 是 |

注册示例：

```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "demo",
  "password": "P@ssw0rd",
  "inviter_id": "COINGPT-123"
}
```

成功响应示例：

```json
{
  "status": "success",
  "data": {
    "user": {
      "user_id": 8,
      "username": "demo",
      "membership": "free"
    },
    "token": "<JWT>"
  }
}
```

### 聊天与会话（`/api/chat`）

- `POST /api/chat/`
  - Body：
    ```json
    {
      "message": "分析下 BTC 四小时走势",
      "session_id": 123,           // 可选，不传则自动创建
      "stream": false               // 可选，true 时以 SSE 流式返回
    }
    ```
  - 返回：`message`（普通模式）或 SSE 数据流（流式模式）。
- `POST /api/chat/show_prompt`：仅返回意图提取用的 prompt、解析结果等调试信息。
- `POST /api/chat/sessions`：创建新会话，返回 `session_id`。
- `GET /api/chat/session/<session_id>`：获取指定会话的全部历史消息。

### Prompt 调试接口（`/api/show_prompt`）

与 `POST /api/chat/show_prompt` 功能一致，提供独立路由：

```http
POST /api/show_prompt/
Authorization: Bearer <token>
{
  "message": "BTC 会涨吗？",
  "session_id": 321
}
```

返回意图提取 prompt、结构化意图与传统解析结果。

### 交易接口（`/api/trading`）

- `GET /balance`：查询余额，支持 `coin`、`exchange` 查询参数。
- `POST /order`：创建订单，支持按币量或 USDT 金额下单，并可一次性设置止盈/止损。

  请求示例：
  ```json
  {
    "symbol": "BTCUSDT",
    "side": "buy",                 // buy/sell
    "quantity_type": "usdt",       // usdt 或 coin，默认 coin
    "amount": 100,                  // quantity_type 为 usdt 时必填
    "order_type": "limit",         // market/limit
    "price": 104500,
    "position_side": "long",       // long/short（合约）
    "leverage": 5,
    "take_profit": 109500,
    "stop_loss": 101400,
    "exchange": "bybit"
  }
  ```

  响应示例：
  ```json
  {
    "status": "success",
    "data": {
      "order_id": "6dc2...",
      "symbol": "BTCUSDT",
      "side": "Buy",
      "quantity": 0.00096,
      "order_type": "Limit",
      "status": "Created",
      "position_side": "Long"
    }
  }
  ```

- `DELETE /order/<order_id>`：取消订单，需提供 `symbol`（query）。
- `GET /orders`：获取当前挂单，可选 `symbol`、`exchange`。
- `GET /positions`：查询持仓。
- `POST /position/close`：平仓，Body 包含 `symbol`、`position_side`。
- `POST /leverage`：设置杠杆，Body 包含 `symbol`、`leverage`。
- `GET /pnl`：实时盈亏统计，可选 `symbol`、`exchange`。

> 更深入的交易模块说明与示例可参考 `TRADING_MODULE_GUIDE.md`。

### 交易历史接口（`/api/trading/history`）

- `GET /pnl`：分页查询历史盈亏记录，支持 `limit`、`offset`、`symbol`、`exchange`、`start_date`、`end_date`。
- `GET /pnl/summary`：盈亏汇总，支持 `period`（today/week/month/quarter/year/all）或自定义日期区间。
- `GET /orders`：历史订单列表，支持 `status`、`symbol`、`exchange`。
- `POST /pnl`：手动补录一条盈亏记录（通常由系统内部调用）。

### 订阅接口（`/api/subscription`）

- `POST /verify`：提交 `receipt_data` 验证并激活订阅。
- `POST /restore`：恢复购买，同样需要 `receipt_data`。
- `GET /status`：获取当前订阅状态。
- `GET /products`：列出可购买的订阅产品。

验证成功响应示例：

```json
{
  "status": "success",
  "message": "订阅激活成功",
  "data": {
    "product_id": "dev.zonekit.coingpt.Premium.year",
    "transaction_id": "1000001234567890",
    "expires_date": "2026-11-11T14:30:00",
    "is_trial_period": false
  }
}
```

### 反馈接口（`/api/feedback`）

- `POST /rate`：对整段会话评分，Body 包含 `session_id`、`rating` (1-5)、可选 `feedback`、`context`。
- `POST /rate_message`：对单条 AI 回复评分，Body 需提供 `assistant_id` 或 `message_id`、`rating`。
- `GET /analytics`：获取反馈统计，支持 `session_id` 过滤。
- `GET /suggestions`：获取改进建议列表，可选 `count`。
- `POST /text`：提交文字反馈，仅需 `content` 字段。

### 收藏币种接口（`/api/favorites`）

- `GET /api/favorites?limit=5`
- `POST /api/favorites` Body：`{"symbol": "BTCUSDT"}`
- `DELETE /api/favorites/<symbol>`

响应结构参见前文示例。

### 图片上传接口（`/api/upload`）

- `POST /api/upload/image`
  - 请求方式：`multipart/form-data`
  - 字段：`file`（必填，图片文件）
  - 成功返回上传后的 URL、对象键、MIME 类型。

### Prompt/调试接口补充

- `POST /api/show_prompt/`：详见上文。
- `POST /api/chat/show_prompt`：同上，位于聊天命名空间内。

---

如需快速联调可结合 `TRADING_MODULE_GUIDE.md`、`TRADING_MODULE_SUMMARY.md` 中的示例脚本或直接使用 Postman/Thunder Client 参考以上请求体与响应格式。
