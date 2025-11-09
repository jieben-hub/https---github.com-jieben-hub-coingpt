# -*- coding: utf-8 -*-
"""
修复外键约束 - 添加级联删除
"""
from sqlalchemy import create_engine, text
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)

# SQL 语句来修改外键约束
fix_sql = """
-- 1. 删除旧的外键约束
ALTER TABLE message_feedbacks 
DROP CONSTRAINT IF EXISTS message_feedbacks_message_id_fkey;

ALTER TABLE session_feedbacks 
DROP CONSTRAINT IF EXISTS session_feedbacks_session_id_fkey;

-- 2. 添加新的外键约束（带级联删除）
ALTER TABLE message_feedbacks 
ADD CONSTRAINT message_feedbacks_message_id_fkey 
FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE;

ALTER TABLE session_feedbacks 
ADD CONSTRAINT session_feedbacks_session_id_fkey 
FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE;
"""

print("正在修复外键约束...")
print("=" * 80)

try:
    with engine.connect() as conn:
        # 执行每条 SQL 语句
        for sql in fix_sql.strip().split(';'):
            sql = sql.strip()
            if sql and not sql.startswith('--'):
                print(f"执行: {sql[:80]}...")
                conn.execute(text(sql))
                conn.commit()
    
    print("\n✅ 外键约束修复成功！")
    print("\n现在删除消息或会话时，相关的反馈记录会自动删除。")
    
except Exception as e:
    print(f"\n❌ 修复失败: {e}")
    print("\n请检查数据库连接和权限。")
