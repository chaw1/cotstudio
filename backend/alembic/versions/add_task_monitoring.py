"""Add task monitoring tables

Revision ID: add_task_monitoring
Revises: add_audit_system
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_task_monitoring'
down_revision = 'add_audit_system'
branch_labels = None
depends_on = None


def upgrade():
    # Create task status enum
    task_status_enum = postgresql.ENUM(
        'PENDING', 'PROGRESS', 'SUCCESS', 'FAILURE', 'RETRY', 'REVOKED',
        name='taskstatus'
    )
    task_status_enum.create(op.get_bind())
    
    # Create task type enum
    task_type_enum = postgresql.ENUM(
        'ocr_processing', 'llm_processing', 'kg_extraction', 
        'file_processing', 'export_processing', 'import_processing', 'health_check',
        name='tasktype'
    )
    task_type_enum.create(op.get_bind())
    
    # Create task priority enum
    task_priority_enum = postgresql.ENUM(
        'low', 'normal', 'high', 'critical',
        name='taskpriority'
    )
    task_priority_enum.create(op.get_bind())
    
    # Create task_monitors table
    op.create_table(
        'task_monitors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', sa.String(), nullable=False),
        sa.Column('task_name', sa.String(), nullable=False),
        sa.Column('task_type', task_type_enum, nullable=False),
        sa.Column('status', task_status_enum, nullable=False),
        sa.Column('priority', task_priority_enum, nullable=False),
        
        # 进度信息
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('current_step', sa.String(), nullable=True),
        sa.Column('total_steps', sa.Integer(), nullable=True),
        
        # 执行信息
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('worker_name', sa.String(), nullable=True),
        sa.Column('queue_name', sa.String(), nullable=True),
        
        # 时间信息
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        # 执行时间统计
        sa.Column('estimated_duration', sa.Integer(), nullable=True),
        sa.Column('actual_duration', sa.Integer(), nullable=True),
        
        # 任务参数和结果
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_info', sa.JSON(), nullable=True),
        
        # 重试信息
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=True),
        sa.Column('retry_delay', sa.Integer(), nullable=True),
        
        # 状态消息
        sa.Column('message', sa.Text(), nullable=True),
        
        # 标记和标签
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('is_critical', sa.Boolean(), nullable=True),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_task_monitors_task_id', 'task_monitors', ['task_id'], unique=True)
    op.create_index('ix_task_monitors_user_id', 'task_monitors', ['user_id'])
    op.create_index('ix_task_monitors_status', 'task_monitors', ['status'])
    op.create_index('ix_task_monitors_task_type', 'task_monitors', ['task_type'])
    op.create_index('ix_task_monitors_priority', 'task_monitors', ['priority'])
    op.create_index('ix_task_monitors_created_at', 'task_monitors', ['created_at'])
    op.create_index('ix_task_monitors_queue_name', 'task_monitors', ['queue_name'])
    op.create_index('ix_task_monitors_is_critical', 'task_monitors', ['is_critical'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_task_monitors_is_critical', table_name='task_monitors')
    op.drop_index('ix_task_monitors_queue_name', table_name='task_monitors')
    op.drop_index('ix_task_monitors_created_at', table_name='task_monitors')
    op.drop_index('ix_task_monitors_priority', table_name='task_monitors')
    op.drop_index('ix_task_monitors_task_type', table_name='task_monitors')
    op.drop_index('ix_task_monitors_status', table_name='task_monitors')
    op.drop_index('ix_task_monitors_user_id', table_name='task_monitors')
    op.drop_index('ix_task_monitors_task_id', table_name='task_monitors')
    
    # Drop table
    op.drop_table('task_monitors')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS taskpriority')
    op.execute('DROP TYPE IF EXISTS tasktype')
    op.execute('DROP TYPE IF EXISTS taskstatus')