# 📊 数据库迁移指南

## 🎯 需要迁移的内容

添加 `exchange_api_keys` 表，用于存储用户的交易所 API Key。

---

## 🚀 快速执行

### 方法 1：使用 Python 脚本（推荐）

```bash
python migrate_exchange_api_keys.py
```

**输出示例**：
```
============================================================
数据库迁移：添加 exchange_api_keys 表
============================================================
数据库: coingpt
主机: 104.223.121.217:5432
用户: coingpt

正在连接数据库...
✅ 数据库连接成功

检查表是否已存在...
✅ 表不存在，开始创建

1. 创建 exchange_api_keys 表...
   ✅ 表创建成功
2. 创建索引...
   ✅ idx_exchange_api_keys_user_id
   ✅ idx_exchange_api_keys_exchange
   ✅ idx_exchange_api_keys_user_exchange
3. 添加表注释...
   ✅ 注释添加成功

提交事务...
✅ 迁移成功完成！

验证迁移结果...
   表结构（共 10 列）：
   - id: bigint NOT NULL
   - user_id: bigint NOT NULL
   - exchange: character varying NOT NULL
   - api_key: text NOT NULL
   - api_secret: text NOT NULL
   - testnet: integer NOT NULL
   - is_active: integer NOT NULL
   - nickname: character varying NULL
   - created_at: timestamp without time zone NULL
   - updated_at: timestamp without time zone NULL

============================================================
🎉 数据库迁移完成！
============================================================
```

---

### 方法 2：手动执行 SQL

```bash
psql -h 104.223.121.217 -U coingpt -d coingpt -f migrations/add_exchange_api_keys.sql
```

或者直接在 psql 中执行：

```sql
-- 连接数据库
psql -h 104.223.121.217 -U coingpt -d coingpt

-- 执行 SQL
\i migrations/add_exchange_api_keys.sql
```

---

## 📋 迁移内容

### 1. 创建表

```sql
CREATE TABLE exchange_api_keys (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    api_key TEXT NOT NULL,
    api_secret TEXT NOT NULL,
    testnet INTEGER DEFAULT 1 NOT NULL,
    is_active INTEGER DEFAULT 1 NOT NULL,
    nickname VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_exchange_api_keys_user_id 
        FOREIGN KEY (user_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE
);
```

### 2. 创建索引

```sql
CREATE INDEX idx_exchange_api_keys_user_id ON exchange_api_keys(user_id);
CREATE INDEX idx_exchange_api_keys_exchange ON exchange_api_keys(exchange);
CREATE INDEX idx_exchange_api_keys_user_exchange ON exchange_api_keys(user_id, exchange);
```

---

## ✅ 验证迁移

### 检查表是否创建成功

```sql
-- 查看表结构
\d exchange_api_keys

-- 查看索引
\di exchange_api_keys*

-- 查看外键约束
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'exchange_api_keys'
    AND tc.constraint_type = 'FOREIGN KEY';
```

---

## 🔄 回滚迁移

如果需要回滚：

```sql
-- 删除表（会级联删除所有数据）
DROP TABLE IF EXISTS exchange_api_keys CASCADE;
```

---

## ⚠️ 注意事项

### 1. 备份数据库

迁移前建议备份：

```bash
pg_dump -h 104.223.121.217 -U coingpt -d coingpt > backup_before_migration.sql
```

### 2. 检查依赖

确保 `users` 表已存在：

```sql
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'users'
);
```

### 3. 权限

确保数据库用户有创建表的权限。

---

## 🎯 迁移后的配置

### 1. 配置加密密钥

在 `.env` 中添加：

```bash
# 生成密钥
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 添加到 .env
ENCRYPTION_KEY=生成的密钥
```

### 2. 重启服务

```bash
python run.py
```

### 3. 测试 API

```bash
# 测试添加 API Key
curl -X POST http://localhost:5000/api/exchange-api/keys \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exchange": "bybit",
    "api_key": "test_key",
    "api_secret": "test_secret",
    "testnet": true
  }'
```

---

## 📊 表结构说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BIGSERIAL | 主键 |
| `user_id` | BIGINT | 用户ID（外键） |
| `exchange` | VARCHAR(50) | 交易所名称 |
| `api_key` | TEXT | API Key（加密） |
| `api_secret` | TEXT | API Secret（加密） |
| `testnet` | INTEGER | 是否测试网（1=是，0=否） |
| `is_active` | INTEGER | 是否启用（1=是，0=否） |
| `nickname` | VARCHAR(100) | 用户自定义昵称 |
| `created_at` | TIMESTAMP | 创建时间 |
| `updated_at` | TIMESTAMP | 更新时间 |

---

## 🔍 常见问题

### Q1: 迁移失败怎么办？

**A**: 检查错误信息：
- 表是否已存在
- users 表是否存在
- 数据库连接是否正常
- 用户权限是否足够

### Q2: 如何查看当前表结构？

**A**: 
```sql
\d exchange_api_keys
```

### Q3: 如何重新执行迁移？

**A**: 先删除表，再执行迁移：
```sql
DROP TABLE IF EXISTS exchange_api_keys CASCADE;
```
然后重新运行迁移脚本。

---

## ✅ 完成检查清单

- [ ] 备份数据库
- [ ] 执行迁移脚本
- [ ] 验证表结构
- [ ] 配置 ENCRYPTION_KEY
- [ ] 重启服务
- [ ] 测试 API 接口

---

**现在就执行迁移吧！** 🚀

```bash
python migrate_exchange_api_keys.py
```
