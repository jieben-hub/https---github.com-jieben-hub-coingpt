# -*- coding: utf-8 -*-
from config import DATABASE_URL
from app import create_app
from models import db

# 使用应用工厂创建Flask应用
app = create_app()

# 添加应用上下文
with app.app_context():
    print('DATABASE_URL:', DATABASE_URL)
    # 检查activities表是否存在
    table_exists = 'activities' in db.inspect(db.engine).get_table_names()
    print('activities表是否存在:', table_exists)
    
    # 如果存在，显示表结构
    if table_exists:
        print('\nactivities表结构:')
        from sqlalchemy import MetaData
        metadata = MetaData()
        metadata.reflect(bind=db.engine)
        table = metadata.tables['activities']
        for column in table.columns:
            print(f"  - {column.name}: {column.type}")
    else:
        print('\n数据库中所有表:')
        for table_name in db.inspect(db.engine).get_table_names():
            print(f"  - {table_name}")
