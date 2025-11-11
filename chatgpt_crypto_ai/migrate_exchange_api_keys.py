# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加 exchange_api_keys 表
"""
import psycopg2
from config import DATABASE_URL
import sys

def run_migration():
    """执行数据库迁移"""
    
    # 解析数据库 URL
    # postgresql://user:password@host:port/database
    try:
        # 简单解析（假设格式正确）
        url = DATABASE_URL.replace('postgresql://', '')
        auth, location = url.split('@')
        username, password = auth.split(':')
        host_port, database = location.split('/')
        host, port = host_port.split(':')
        
        print("=" * 60)
        print("数据库迁移：添加 exchange_api_keys 表")
        print("=" * 60)
        print(f"数据库: {database}")
        print(f"主机: {host}:{port}")
        print(f"用户: {username}")
        print()
        
        # 连接数据库
        print("正在连接数据库...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("✅ 数据库连接成功")
        print()
        
        # 检查表是否已存在
        print("检查表是否已存在...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'exchange_api_keys'
            );
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            print("⚠️  表 exchange_api_keys 已存在，跳过创建")
            conn.close()
            return
        
        print("✅ 表不存在，开始创建")
        print()
        
        # 创建表
        print("1. 创建 exchange_api_keys 表...")
        cursor.execute("""
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
        """)
        print("   ✅ 表创建成功")
        
        # 创建索引
        print("2. 创建索引...")
        cursor.execute("""
            CREATE INDEX idx_exchange_api_keys_user_id 
            ON exchange_api_keys(user_id);
        """)
        print("   ✅ idx_exchange_api_keys_user_id")
        
        cursor.execute("""
            CREATE INDEX idx_exchange_api_keys_exchange 
            ON exchange_api_keys(exchange);
        """)
        print("   ✅ idx_exchange_api_keys_exchange")
        
        cursor.execute("""
            CREATE INDEX idx_exchange_api_keys_user_exchange 
            ON exchange_api_keys(user_id, exchange);
        """)
        print("   ✅ idx_exchange_api_keys_user_exchange")
        
        # 添加注释
        print("3. 添加表注释...")
        cursor.execute("""
            COMMENT ON TABLE exchange_api_keys IS '用户交易所API密钥表';
        """)
        cursor.execute("""
            COMMENT ON COLUMN exchange_api_keys.user_id IS '用户ID';
        """)
        cursor.execute("""
            COMMENT ON COLUMN exchange_api_keys.exchange IS '交易所名称(bybit/binance/huobi)';
        """)
        cursor.execute("""
            COMMENT ON COLUMN exchange_api_keys.api_key IS 'API Key(加密存储)';
        """)
        cursor.execute("""
            COMMENT ON COLUMN exchange_api_keys.api_secret IS 'API Secret(加密存储)';
        """)
        cursor.execute("""
            COMMENT ON COLUMN exchange_api_keys.testnet IS '是否测试网(1=是,0=否)';
        """)
        cursor.execute("""
            COMMENT ON COLUMN exchange_api_keys.is_active IS '是否启用(1=是,0=否)';
        """)
        cursor.execute("""
            COMMENT ON COLUMN exchange_api_keys.nickname IS '用户自定义昵称';
        """)
        print("   ✅ 注释添加成功")
        
        # 提交事务
        print()
        print("提交事务...")
        conn.commit()
        print("✅ 迁移成功完成！")
        
        # 验证
        print()
        print("验证迁移结果...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'exchange_api_keys'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print(f"   表结构（共 {len(columns)} 列）：")
        for col in columns:
            nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
            print(f"   - {col[0]}: {col[1]} {nullable}")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        print()
        print("=" * 60)
        print("🎉 数据库迁移完成！")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 迁移失败！")
        print("=" * 60)
        print(f"错误: {e}")
        print()
        import traceback
        traceback.print_exc()
        
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        
        sys.exit(1)


if __name__ == "__main__":
    run_migration()
