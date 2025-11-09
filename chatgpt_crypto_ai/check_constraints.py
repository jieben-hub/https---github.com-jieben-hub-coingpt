# -*- coding: utf-8 -*-
"""
检查当前数据库的外键约束
"""
from sqlalchemy import create_engine, text
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)

check_sql = """
SELECT 
    tc.constraint_name, 
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
  ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
  AND tc.table_name IN ('message_feedbacks', 'session_feedbacks')
ORDER BY tc.table_name;
"""

print("检查外键约束...")
print("=" * 100)

try:
    with engine.connect() as conn:
        result = conn.execute(text(check_sql))
        rows = result.fetchall()
        
        if rows:
            print(f"{'约束名称':<40} {'表名':<25} {'列名':<20} {'引用表':<20} {'删除规则':<15}")
            print("-" * 100)
            for row in rows:
                print(f"{row[0]:<40} {row[1]:<25} {row[2]:<20} {row[3]:<20} {row[5]:<15}")
        else:
            print("未找到相关外键约束")
            
except Exception as e:
    print(f"❌ 查询失败: {e}")
