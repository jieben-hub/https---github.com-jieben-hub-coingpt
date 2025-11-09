# -*- coding: utf-8 -*-
"""
添加反馈表迁移脚本
创建SessionFeedback和MessageFeedback表，用于存储会话和消息评分
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# 修订ID和标签
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库，添加反馈表"""
    # 创建会话反馈表
    op.create_table(
        'session_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    
    # 创建消息反馈表
    op.create_table(
        'message_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    
    # 添加索引以提高查询性能
    op.create_index('ix_session_feedback_session_id', 'session_feedback', ['session_id'], unique=False)
    op.create_index('ix_session_feedback_user_id', 'session_feedback', ['user_id'], unique=False)
    op.create_index('ix_message_feedback_message_id', 'message_feedback', ['message_id'], unique=False)
    op.create_index('ix_message_feedback_user_id', 'message_feedback', ['user_id'], unique=False)


def downgrade():
    """降级数据库，删除反馈表"""
    # 删除索引
    op.drop_index('ix_message_feedback_user_id', table_name='message_feedback')
    op.drop_index('ix_message_feedback_message_id', table_name='message_feedback')
    op.drop_index('ix_session_feedback_user_id', table_name='session_feedback')
    op.drop_index('ix_session_feedback_session_id', table_name='session_feedback')
    
    # 删除表
    op.drop_table('message_feedback')
    op.drop_table('session_feedback')
