"""Add seed data

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Boolean, DateTime, JSON
from datetime import datetime
import uuid

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create a table representation for inserting data
    users_table = table('users',
        column('id', String),
        column('created_at', DateTime),
        column('updated_at', DateTime),
        column('username', String),
        column('email', String),
        column('hashed_password', String),
        column('full_name', String),
        column('is_active', Boolean),
        column('is_superuser', Boolean),
        column('roles', JSON)
    )
    
    # Insert seed users
    now = datetime.utcnow()
    
    # Admin user (password: secret)
    # Hash generated with: from passlib.context import CryptContext; CryptContext(schemes=["bcrypt"], deprecated="auto").hash("secret")
    admin_id = str(uuid.uuid4())
    
    # Editor user (password: secret)
    editor_id = str(uuid.uuid4())
    
    op.bulk_insert(users_table, [
        {
            'id': admin_id,
            'created_at': now,
            'updated_at': now,
            'username': 'admin',
            'email': 'admin@cotstudio.com',
            'hashed_password': '$2b$12$rdO5ZWS17HGZf06YJtuH.erhaHwq7YOm6BBiEHWpGPGZI7oiJg83K',  # 971028
            'full_name': 'System Administrator',
            'is_active': True,
            'is_superuser': True,
            'roles': '["admin"]'
        },
        {
            'id': editor_id,
            'created_at': now,
            'updated_at': now,
            'username': 'editor',
            'email': 'editor@cotstudio.com',
            'hashed_password': '$2b$12$FmwB3UIMw.OewIUkW8Ihu.Qi/gJbUheVJwnoeSAtS7Qgr7atPhSkK',  # secret
            'full_name': 'Editor User',
            'is_active': True,
            'is_superuser': False,
            'roles': '["editor"]'
        }
    ])


def downgrade() -> None:
    # Remove seed data
    op.execute("DELETE FROM users WHERE username IN ('admin', 'editor')")