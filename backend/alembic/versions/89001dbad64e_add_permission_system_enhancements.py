"""add_permission_system_enhancements

Revision ID: 89001dbad64e
Revises: cee76a73467f
Create Date: 2025-09-16 11:22:29.306291

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89001dbad64e'
down_revision: Union[str, Sequence[str], None] = 'cee76a73467f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for permission system enhancements."""
    from datetime import datetime
    
    # Create UserRole enum
    user_role_enum = sa.Enum('SUPER_ADMIN', 'ADMIN', 'USER', 'VIEWER', name='userrole')
    user_role_enum.create(op.get_bind())
    
    # Create user_project_permissions table
    op.create_table(
        'user_project_permissions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('permissions', sa.JSON(), nullable=False, default=list),
        sa.Column('granted_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('granted_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow)
    )
    
    # Add new columns to users table
    op.add_column('users', sa.Column('role', user_role_enum, nullable=True))
    op.add_column('users', sa.Column('department', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('login_count', sa.Integer(), nullable=True, default=0))
    
    # Data migration: Set default roles for existing users
    connection = op.get_bind()
    
    # Set existing superusers to SUPER_ADMIN role
    connection.execute(
        sa.text("UPDATE users SET role = 'SUPER_ADMIN' WHERE is_superuser = 1")
    )
    
    # Set other existing users to ADMIN role (since they were likely admin users in the old system)
    connection.execute(
        sa.text("UPDATE users SET role = 'ADMIN' WHERE is_superuser = 0 OR is_superuser IS NULL")
    )
    
    # Set default login_count to 0 for existing users
    connection.execute(
        sa.text("UPDATE users SET login_count = 0 WHERE login_count IS NULL")
    )


def downgrade() -> None:
    """Downgrade schema for permission system enhancements."""
    
    # Drop new columns from users table
    op.drop_column('users', 'login_count')
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'department')
    op.drop_column('users', 'role')
    
    # Drop user_project_permissions table
    op.drop_table('user_project_permissions')
    
    # Note: SQLite doesn't support DROP TYPE, so we skip dropping the enum
