# 数据库外键约束修复说明

## 问题描述

删除消息时出现外键约束错误：
```
sqlalchemy.exc.IntegrityError: (psycopg2.errors.ForeignKeyViolation) 
update or delete on table "messages" violates foreign key constraint 
"message_feedbacks_message_id_fkey" on table "message_feedbacks"
```

## 原因分析

- `message_feedbacks` 表通过 `message_id` 外键引用 `messages` 表
- `session_feedbacks` 表通过 `session_id` 外键引用 `sessions` 表
- 原外键约束没有设置级联删除（CASCADE）
- 当删除被引用的消息/会话时，数据库拒绝操作以保护数据完整性

## 解决方案

### 1. 修改数据库模型（已完成）

在 `models.py` 中添加 `ondelete='CASCADE'`：

```python
# MessageFeedback 模型
message_id = Column(BigInteger, ForeignKey('messages.id', ondelete='CASCADE'), nullable=False)

# SessionFeedback 模型
session_id = Column(BigInteger, ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
```

### 2. 更新数据库约束（已完成）

运行 `fix_foreign_keys.py` 脚本：
```bash
python fix_foreign_keys.py
```

该脚本执行以下操作：
1. 删除旧的外键约束
2. 添加新的外键约束（带 CASCADE）

## 修复后的行为

✅ **删除消息时**：自动删除该消息的所有反馈记录
✅ **删除会话时**：自动删除该会话的所有反馈记录和消息
✅ **删除用户时**：级联删除用户的所有会话、消息和反馈

## 数据库关系图

```
users
  ├── sessions (CASCADE)
  │   ├── messages (CASCADE)
  │   │   └── message_feedbacks (CASCADE) ✅ 新增
  │   └── session_feedbacks (CASCADE) ✅ 新增
  └── user_symbols (CASCADE)
```

## 验证

可以通过以下 SQL 查看外键约束：

```sql
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
  AND tc.table_name IN ('message_feedbacks', 'session_feedbacks');
```

应该看到 `delete_rule` 为 `CASCADE`。

## 注意事项

⚠️ **重要**：级联删除是不可逆的操作
- 删除会话会永久删除所有相关消息和反馈
- 删除消息会永久删除所有相关反馈
- 建议在删除前进行数据备份或软删除

## 未来改进建议

可以考虑实现软删除机制：
1. 添加 `is_deleted` 字段
2. 删除时只标记为已删除，不真正删除数据
3. 查询时过滤已删除的记录
