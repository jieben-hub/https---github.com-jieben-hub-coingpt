# -*- coding: utf-8 -*-
import psycopg2
from config import DATABASE_URL

# 解析数据库URL
# postgresql://coingpt:rTCBCm2zaiPAyjf4@104.223.121.217:5432/coingpt
url_parts = DATABASE_URL.replace('postgresql://', '').split('@')
user_pass = url_parts[0].split(':')
host_db = url_parts[1].split('/')
host_port = host_db[0].split(':')

username = user_pass[0]
password = user_pass[1]
host = host_port[0]
port = host_port[1]
database = host_db[1]

print(f"尝试连接到 PostgreSQL:")
print(f"  Host: {host}")
print(f"  Port: {port}")
print(f"  Database: {database}")
print(f"  User: {username}")

try:
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=username,
        password=password,
        connect_timeout=5
    )
    print("✅ 数据库连接成功!")
    conn.close()
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
