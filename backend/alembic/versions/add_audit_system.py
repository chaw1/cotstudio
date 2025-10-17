"""Add audit system tables

Revision ID: add_audit_system
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_audit_system'
down_revision = None  # 这里应该是上一个迁移的ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建审计日志表
    op.create_table('audit_logs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('event_type', sa.Enum('CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'PERMISSION_CHANGE', 'EXPORT', 'IMPORT', 'SYSTEM_CONFIG', name='auditeventtype'), nullable=False),
        sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='auditseverity'), nullable=False),
        sa.Column('resource_type', sa.Enum('PROJECT', 'FILE', 'COT_ITEM', 'USER', 'ROLE', 'PERMISSION', 'SYSTEM_SETTING', 'KNOWLEDGE_GRAPH', name='resourcetype'), nullable=True),
        sa.Column('resource_id', sa.String(36), nullable=True),
        sa.Column('resource_name', sa.String(255), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(36), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('old_values', sa.JSON(), nullable=False),
        sa.Column('new_values', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('idx_audit_user_time', 'audit_logs', ['user_id', 'created_at'])
    op.create_index('idx_audit_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_event_time', 'audit_logs', ['event_type', 'created_at'])
    op.create_index('idx_audit_severity', 'audit_logs', ['severity'])

    # 创建角色表
    op.create_table('roles',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('role_type', sa.Enum('ADMIN', 'EDITOR', 'REVIEWER', 'VIEWER', name='roletype'), nullable=False),
        sa.Column('is_system_role', sa.Boolean(), nullable=False),
        sa.Column('permissions', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)

    # 创建权限表
    op.create_table('permissions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('resource_type', sa.Enum('PROJECT', 'FILE', 'COT_ITEM', 'USER', 'ROLE', 'PERMISSION', 'SYSTEM_SETTING', 'KNOWLEDGE_GRAPH', name='resourcetype'), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('is_system_permission', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_permissions_name'), 'permissions', ['name'], unique=True)

    # 创建用户角色关联表
    op.create_table('user_roles',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('role_id', sa.String(36), nullable=False),
        sa.Column('granted_by', sa.String(36), nullable=True),
        sa.Column('granted_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建用户角色唯一索引
    op.create_index('idx_user_role_unique', 'user_roles', ['user_id', 'role_id'], unique=True)
    op.create_index('idx_user_role_expires', 'user_roles', ['expires_at'])

    # 创建项目权限表
    op.create_table('project_permissions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('project_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('role_id', sa.String(36), nullable=True),
        sa.Column('permission_type', sa.String(50), nullable=False),
        sa.Column('granted_by', sa.String(36), nullable=True),
        sa.Column('granted_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建项目权限索引
    op.create_index('idx_project_user_permission', 'project_permissions', ['project_id', 'user_id'])
    op.create_index('idx_project_role_permission', 'project_permissions', ['project_id', 'role_id'])


def downgrade() -> None:
    # 删除表和索引
    op.drop_index('idx_project_role_permission', table_name='project_permissions')
    op.drop_index('idx_project_user_permission', table_name='project_permissions')
    op.drop_table('project_permissions')
    
    op.drop_index('idx_user_role_expires', table_name='user_roles')
    op.drop_index('idx_user_role_unique', table_name='user_roles')
    op.drop_table('user_roles')
    
    op.drop_index(op.f('ix_permissions_name'), table_name='permissions')
    op.drop_table('permissions')
    
    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_table('roles')
    
    op.drop_index('idx_audit_severity', table_name='audit_logs')
    op.drop_index('idx_audit_event_time', table_name='audit_logs')
    op.drop_index('idx_audit_resource', table_name='audit_logs')
    op.drop_index('idx_audit_user_time', table_name='audit_logs')
    op.drop_table('audit_logs')
    
    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS auditeventtype')
    op.execute('DROP TYPE IF EXISTS auditseverity')
    op.execute('DROP TYPE IF EXISTS resourcetype')
    op.execute('DROP TYPE IF EXISTS roletype')