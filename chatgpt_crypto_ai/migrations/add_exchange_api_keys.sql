-- 添加 exchange_api_keys 表
-- 用于存储用户的交易所 API Key（加密存储）

CREATE TABLE IF NOT EXISTS exchange_api_keys (
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

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_exchange_api_keys_user_id ON exchange_api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_exchange_api_keys_exchange ON exchange_api_keys(exchange);
CREATE INDEX IF NOT EXISTS idx_exchange_api_keys_user_exchange ON exchange_api_keys(user_id, exchange);

-- 添加注释
COMMENT ON TABLE exchange_api_keys IS '用户交易所API密钥表';
COMMENT ON COLUMN exchange_api_keys.user_id IS '用户ID';
COMMENT ON COLUMN exchange_api_keys.exchange IS '交易所名称(bybit/binance/huobi)';
COMMENT ON COLUMN exchange_api_keys.api_key IS 'API Key(加密存储)';
COMMENT ON COLUMN exchange_api_keys.api_secret IS 'API Secret(加密存储)';
COMMENT ON COLUMN exchange_api_keys.testnet IS '是否测试网(1=是,0=否)';
COMMENT ON COLUMN exchange_api_keys.is_active IS '是否启用(1=是,0=否)';
COMMENT ON COLUMN exchange_api_keys.nickname IS '用户自定义昵称';
