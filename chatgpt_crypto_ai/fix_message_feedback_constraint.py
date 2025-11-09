# -*- coding: utf-8 -*-
"""
修复 message_feedbacks 表的外键约束
"""
from sqlalchemy import create_engine, text
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)

print("修复 message_feedbacks 外键约束...")
print("=" * 80)

try:
    with engine.connect() as conn:
        # 开始事务
        trans = conn.begin()
        
        try:
            # 1. 删除旧的外键约束
            print("1. 删除旧的外键约束...")
            conn.execute(text("""
                ALTER TABLE message_feedbacks 
                DROP CONSTRAINT IF EXISTS message_feedbacks_message_id_fkey;
            """))
            print("   ✓ 旧约束已删除")
            
            # 2. 添加新的外键约束（带级联删除）
            print("2. 添加新的外键约束（CASCADE）...")
            conn.execute(text("""
                ALTER TABLE message_feedbacks 
                ADD CONSTRAINT message_feedbacks_message_id_fkey 
                FOREIGN KEY (message_id) 
                REFERENCES messages(id) 
                ON DELETE CASCADE;
            """))
            print("   ✓ 新约束已添加")
            
            # 提交事务
            trans.commit()
            print("\n✅ 修复成功！")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ 修复失败: {e}")
            raise
            
    # 验证修复结果
    print("\n验证修复结果...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                tc.constraint_name,
                rc.delete_rule
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.referential_constraints AS rc
              ON rc.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' 
              AND tc.table_name = 'message_feedbacks'
              AND tc.constraint_name = 'message_feedbacks_message_id_fkey';
        """))
        
        row = result.fetchone()
        if row and row[1] == 'CASCADE':
            print(f"✓ 约束 '{row[0]}' 的删除规则为: {row[1]}")
            print("\n现在删除消息时会自动删除相关的反馈记录！")
        else:
            print("⚠ 警告: 约束可能未正确设置")
            
except Exception as e:
    print(f"\n❌ 操作失败: {e}")
    import traceback
    traceback.print_exc()
