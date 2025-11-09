# 📊 ChatGPT 区块链行情聊天机器人（Flask 后端）重点开发方案

---

## 🎯 核心目标

- 支持用户发送自然语言 Prompt
- 自动识别其中提及的加密货币（BTC、ETH、SOL 等）
- 调用 ccxt 拉取实时 K 线数据（Bybit 优先）
- 对行情进行基础技术分析（趋势判断）
- 构造合理 Prompt 传入 GPT，生成操作建议
- 支持多轮上下文记忆（使用 ChatGPT 的 messages[]）

---

## ⚙️ 技术栈

| 功能            | 技术/工具              |
|-----------------|------------------------|
| Web 框架         | Flask                  |
| 币种行情数据     | ccxt（Bybit）          |
| 聊天理解         | OpenAI ChatGPT API     |
| 用户登录         | Apple Sign-In + ID Token 验证 |
| 会话状态         | 内存 / Redis（可选）    |

---

## ✅ 项目目录结构重点

```plaintext
chatgpt_crypto_ai/
│
├── app.py                    # Flask 主入口
├── config.py                 # 配置项（API Key 等）
│
├── routes/
│   └── chat_routes.py        # 核心聊天接口
│
├── utils/
│   ├── extract.py            # 从 prompt 中提取币种
│   ├── kline.py              # 拉取行情（ccxt）
│   ├── trend.py              # 趋势分析逻辑
│   └── prompt.py             # 构造 GPT 输入消息
# 🗄️ ChatGPT 区块链行情聊天机器人 - 数据库结构设计

---

## 设计原则

- 支持多用户登录（Apple 登录唯一 ID）
- 支持多轮对话上下文存储
- 记录用户常用币种，便于上下文币种关联
- 保持对话和会话状态，支持断线重连
- 可扩展（例如后续添加用户偏好、权限等）

---

# 🗄️ ChatGPT 区块链行情聊天机器人 - 完整数据库结构设计（含邀请、会员、对话次数）

---

## 设计原则补充

- 支持用户邀请关系（邀请人ID）
- 会员等级字段（普通、VIP等）
- 统计用户累计对话次数，方便计费或权限控制

---

## 核心数据表设计

### 1. 用户表 `users`

| 字段名        | 类型           | 说明                             |
|---------------|----------------|----------------------------------|
| id            | BIGINT (PK)    | 用户自增主键                     |
| apple_sub     | VARCHAR(255)   | Apple 登录唯一标识符 (sub)       |
| inviter_id    | BIGINT (FK)    | 邀请人用户ID（nullable，可空）   |
| membership    | VARCHAR(50)    | 会员等级（如 free, vip, platinum）默认 free |
| dialog_count  | INTEGER        | 累计对话次数，初始0               |
| created_at    | TIMESTAMP      | 注册时间                         |
| last_login    | TIMESTAMP      | 最近登录时间                     |

---

### 2. 会话表 `sessions`

| 字段名        | 类型           | 说明                             |
|---------------|----------------|----------------------------------|
| id            | BIGINT (PK)    | 会话自增主键                     |
| user_id       | BIGINT (FK)    | 关联用户ID                       |
| created_at    | TIMESTAMP      | 会话开始时间                     |
| updated_at    | TIMESTAMP      | 最近一次对话时间                 |
| last_symbol   | VARCHAR(50)    | 本会话最后使用的币种（如 BTC/USDT） |

---

### 3. 消息表 `messages`

| 字段名        | 类型           | 说明                             |
|---------------|----------------|----------------------------------|
| id            | BIGINT (PK)    | 消息自增主键                     |
| session_id    | BIGINT (FK)    | 关联会话ID                       |
| role          | VARCHAR(20)    | 消息角色（user/assistant/system）|
| content       | TEXT           | 消息内容                         |
| created_at    | TIMESTAMP      | 消息时间                         |

---

### 4. 用户币种偏好表 `user_symbols`（可选）

| 字段名        | 类型           | 说明                             |
|---------------|----------------|----------------------------------|
| id            | BIGINT (PK)    | 主键                           |
| user_id       | BIGINT (FK)    | 关联用户                        |
| symbol        | VARCHAR(50)    | 币种代码（BTC/USDT 等）          |
| added_at      | TIMESTAMP      | 添加时间                        |

---

## 关系说明

- `users.inviter_id` 指向邀请人用户的 `id`，允许链式邀请关系
- 会员等级可影响对话次数上限和功能权限
- `users.dialog_count` 用于统计累计聊天次数，方便计费、限制或升级策略

---

## 数据库建表示例（PostgreSQL）

```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  apple_sub VARCHAR(255) UNIQUE NOT NULL,
  inviter_id INTEGER REFERENCES users(id) NULL,
  membership VARCHAR(50) DEFAULT 'free' NOT NULL,
  dialog_count INTEGER DEFAULT 0 NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  last_login TIMESTAMP
);

CREATE TABLE sessions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  last_symbol VARCHAR(50)
);

CREATE TABLE messages (
  id SERIAL PRIMARY KEY,
  session_id INTEGER REFERENCES sessions(id),
  role VARCHAR(20) NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_symbols (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  symbol VARCHAR(50) NOT NULL,
  added_at TIMESTAMP DEFAULT NOW()
);
