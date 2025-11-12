"""Add activities table

Revision ID: 9999_add_activities_table
Revises: merge_heads
Create Date: 2025-11-11 19:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9999_add_activities_table'
down_revision = 'merge_heads'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create activities table
    op.create_table('activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='active'),
        sa.Column('priority', sa.String(length=50), nullable=True, server_default='medium'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index(op.f('ix_activities_start_date'), 'activities', ['start_date'], unique=False)
    op.create_index(op.f('ix_activities_end_date'), 'activities', ['end_date'], unique=False)
    op.create_index(op.f('ix_activities_status'), 'activities', ['status'], unique=False)

def downgrade() -> None:
    # Drop the activities table
    op.drop_index(op.f('ix_activities_status'), table_name='activities')
    op.drop_index(op.f('ix_activities_end_date'), table_name='activities')
    op.drop_index(op.f('ix_activities_start_date'), table_name='activities')
    op.drop_table('activities')