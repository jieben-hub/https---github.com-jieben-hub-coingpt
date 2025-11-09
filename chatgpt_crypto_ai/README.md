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

## 📮 API接口说明

### 文字反馈接口

- **接口地址**：`POST /api/feedback/text`
- **认证要求**：需要登录（Bearer Token）
- **请求参数（JSON）**：
  - `content` (string)：反馈内容，必填

- **请求示例**：

```json
POST /api/feedback/text
Authorization: Bearer <token>
Content-Type: application/json
{
  "content": "希望增加更多币种的分析功能！"
}
```

- **返回示例**：
```json
{
  "status": "success",
  "message": "反馈已提交，感谢您的宝贵意见！"
}
```

- **错误返回**：
```json
{
  "status": "error",
  "message": "反馈内容不能为空"
}
```
