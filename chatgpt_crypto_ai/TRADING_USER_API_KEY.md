# 🔑 用户级别 API Key 管理

## ✅ 正确的设计

每个用户配置**自己的** API Key，而不是系统级别的配置。

---

## 📊 架构说明

### 数据库表：`exchange_api_keys`

```sql
CREATE TABLE exchange_api_keys (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    exchange VARCHAR(50) NOT NULL,  -- bybit, binance, huobi
    api_key TEXT NOT NULL,  -- 加密存储
    api_secret TEXT NOT NULL,  -- 加密存储
    testnet INTEGER DEFAULT 1,  -- 1=测试网, 0=主网
    is_active INTEGER DEFAULT 1,  -- 1=启用, 0=禁用
    nickname VARCHAR(100),  -- 用户自定义昵称
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 加密存储

- 使用 `cryptography.fernet` 对称加密
- 加密密钥存储在环境变量 `ENCRYPTION_KEY` 中
- API Key 和 Secret 加密后存储在数据库

---

## 🚀 使用流程

### 1. 用户添加 API Key

```bash
POST /api/exchange-api/keys
Authorization: Bearer USER_TOKEN
Content-Type: application/json

{
  "exchange": "bybit",
  "api_key": "用户的API_KEY",
  "api_secret": "用户的API_SECRET",
  "testnet": true,
  "nickname": "我的主账户"
}
```

**响应**：
```json
{
  "status": "success",
  "message": "API Key 添加成功",
  "data": {
    "id": 1,
    "exchange": "bybit",
    "testnet": true,
    "nickname": "我的主账户"
  }
}
```

---

### 2. 查看已配置的 API Key

```bash
GET /api/exchange-api/keys
Authorization: Bearer USER_TOKEN
```

**响应**：
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "exchange": "bybit",
      "testnet": true,
      "is_active": true,
      "nickname": "我的主账户",
      "api_key_preview": "xxxxxxxxxxx...",
      "created_at": "2025-11-10T06:00:00"
    }
  ]
}
```

---

### 3. 使用 API Key 进行交易

用户配置 API Key 后，所有交易接口会自动使用该用户的 API Key：

```bash
POST /api/trading/order
Authorization: Bearer USER_TOKEN
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "side": "buy",
  "quantity": 0.001,
  "order_type": "market",
  "position_side": "long"
}
```

**系统自动**：
1. 从 token 中获取 `user_id`
2. 从数据库查询该用户的 API Key
3. 解密 API Key
4. 使用用户的 API Key 连接交易所
5. 执行交易

---

### 4. 更新 API Key

```bash
PUT /api/exchange-api/keys/1
Authorization: Bearer USER_TOKEN
Content-Type: application/json

{
  "testnet": false,  // 切换到主网
  "nickname": "主网账户"
}
```

---

### 5. 删除 API Key

```bash
DELETE /api/exchange-api/keys/1
Authorization: Bearer USER_TOKEN
```

---

## 🔒 安全性

### 1. 加密存储

```python
from cryptography.fernet import Fernet

# 生成加密密钥
key = Fernet.generate_key()
f = Fernet(key)

# 加密
encrypted = f.encrypt(b"api_key").decode()

# 解密
decrypted = f.decrypt(encrypted.encode()).decode()
```

### 2. 环境变量配置

在 `.env` 中配置加密密钥：

```bash
# 生成密钥
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 输出示例：
# gAAAAABhXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX=

# 添加到 .env
ENCRYPTION_KEY=gAAAAABhXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX=
```

### 3. 权限控制

- ✅ 用户只能访问自己的 API Key
- ✅ 所有接口都需要 token 认证
- ✅ API Key 加密存储
- ✅ 不返回完整的 API Secret

---

## 📱 前端集成示例

### React/Vue 示例

```javascript
// 1. 添加 API Key
async function addApiKey(apiKey, apiSecret, testnet = true) {
    const response = await fetch('/api/exchange-api/keys', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${userToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            exchange: 'bybit',
            api_key: apiKey,
            api_secret: apiSecret,
            testnet: testnet,
            nickname: '我的账户'
        })
    });
    
    return await response.json();
}

// 2. 获取 API Key 列表
async function getApiKeys() {
    const response = await fetch('/api/exchange-api/keys', {
        headers: {
            'Authorization': `Bearer ${userToken}`
        }
    });
    
    return await response.json();
}

// 3. 创建订单（自动使用用户的 API Key）
async function createOrder(symbol, side, quantity) {
    const response = await fetch('/api/trading/order', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${userToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            symbol: symbol,
            side: side,
            quantity: quantity,
            order_type: 'market',
            position_side: 'long'
        })
    });
    
    return await response.json();
}
```

---

## 🎯 与系统级配置的对比

| 特性 | 系统级配置 | 用户级配置 |
|------|-----------|-----------|
| **API Key 来源** | `.env` 文件 | 用户自己添加 |
| **适用场景** | 测试/开发 | 生产环境 |
| **安全性** | ❌ 低（共享） | ✅ 高（隔离） |
| **灵活性** | ❌ 低 | ✅ 高 |
| **多用户支持** | ❌ 不支持 | ✅ 支持 |
| **推荐** | 仅测试 | ⭐⭐⭐⭐⭐ |

---

## 🔧 数据库迁移

### 创建表

```bash
# 生成迁移文件
flask db migrate -m "Add exchange_api_keys table"

# 执行迁移
flask db upgrade
```

或者手动创建：

```sql
CREATE TABLE exchange_api_keys (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exchange VARCHAR(50) NOT NULL,
    api_key TEXT NOT NULL,
    api_secret TEXT NOT NULL,
    testnet INTEGER DEFAULT 1,
    is_active INTEGER DEFAULT 1,
    nickname VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_exchange_api_keys_user_id ON exchange_api_keys(user_id);
CREATE INDEX idx_exchange_api_keys_exchange ON exchange_api_keys(exchange);
```

---

## ⚠️ 重要提示

### 1. 加密密钥管理

- ✅ **必须配置** `ENCRYPTION_KEY` 环境变量
- ✅ 密钥丢失将无法解密已存储的 API Key
- ✅ 生产环境使用强密钥
- ❌ 不要将密钥提交到 Git

### 2. 用户引导

在用户首次使用交易功能时，引导用户添加 API Key：

```javascript
// 检查用户是否已配置 API Key
async function checkApiKeyConfigured() {
    const keys = await getApiKeys();
    if (keys.data.length === 0) {
        // 显示引导页面
        showApiKeySetupGuide();
    }
}
```

### 3. 错误处理

当用户未配置 API Key 时，返回友好的错误提示：

```json
{
  "status": "error",
  "message": "用户未配置 bybit API Key，请先在设置中添加",
  "code": "API_KEY_NOT_CONFIGURED"
}
```

---

## 📚 完整 API 文档

### API Key 管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/exchange-api/keys` | GET | 获取 API Key 列表 |
| `/api/exchange-api/keys` | POST | 添加 API Key |
| `/api/exchange-api/keys/:id` | PUT | 更新 API Key |
| `/api/exchange-api/keys/:id` | DELETE | 删除 API Key |

### 交易接口（自动使用用户 API Key）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/trading/balance` | GET | 获取余额 |
| `/api/trading/order` | POST | 创建订单 |
| `/api/trading/order/:id` | DELETE | 取消订单 |
| `/api/trading/orders` | GET | 获取挂单 |
| `/api/trading/positions` | GET | 获取持仓 |
| `/api/trading/position/close` | POST | 平仓 |
| `/api/trading/leverage` | POST | 设置杠杆 |

---

## ✅ 总结

### 优势

- ✅ **安全** - 每个用户使用自己的 API Key
- ✅ **隔离** - 用户之间完全隔离
- ✅ **灵活** - 用户可以配置多个交易所
- ✅ **加密** - API Key 加密存储
- ✅ **易用** - 配置一次，自动使用

### 使用步骤

1. 用户在 Bybit 创建 API Key
2. 在 App 中添加 API Key
3. 直接使用交易功能，系统自动使用用户的 API Key

**这才是正确的设计！** 🎉
