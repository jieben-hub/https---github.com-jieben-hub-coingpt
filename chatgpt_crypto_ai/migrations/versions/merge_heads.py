"""Merge multiple heads

Revision ID: merge_heads
Revises: 619c9b3612de, add_activity_table, add_subscription_table
Create Date: 2025-11-11 16:03:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_heads'
down_revision = ['619c9b3612de', 'add_activity_table', 'add_subscription_table']
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 这个迁移文件主要用于合并多个head版本
    # 不执行实际的数据库操作
    pass

def downgrade() -> None:
    # 降级操作也为空
    pass