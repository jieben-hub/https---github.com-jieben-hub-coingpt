"""添加订阅记录表

Revision ID: add_subscription_table
Revises: 
Create Date: 2025-11-11 15:26:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_subscription_table'
down_revision = None  # 如果有之前的迁移，填写上一个revision ID
branch_labels = None
depends_on = None


def upgrade():
    # 创建订阅记录表
    op.create_table('subscriptions',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('product_id', sa.String(length=255), nullable=False),
        sa.Column('product_type', sa.String(length=50), nullable=False),
        sa.Column('transaction_id', sa.String(length=255), nullable=False),
        sa.Column('original_transaction_id', sa.String(length=255), nullable=False),
        sa.Column('purchase_date', sa.DateTime(), nullable=False),
        sa.Column('expires_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('is_trial_period', sa.Boolean(), nullable=True),
        sa.Column('is_in_intro_offer_period', sa.Boolean(), nullable=True),
        sa.Column('auto_renew_status', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_id')
    )


def downgrade():
    # 删除订阅记录表
    op.drop_table('subscriptions')
