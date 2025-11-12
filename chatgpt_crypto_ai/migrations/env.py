# -*- coding: utf-8 -*-
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# 这是Alembic配置，使用时请不要修改。
config = context.config

# 解析日志配置文件（如果存在）
if config.config_file_name:
    try:
        fileConfig(config.config_file_name)
    except KeyError:
        # 如果配置文件缺少formatters部分，跳过日志配置
        pass

# 添加模型元数据对象
from models import db
target_metadata = db.metadata

# 其他值从config中获取，如必要定义一个特殊的字符串
from config import DATABASE_URL

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = DATABASE_URL
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
