"""
修改时区配置 - 将所有datetime字段改为带时区的timestamp

Revision ID: add_timezone_support
Revises: 
Create Date: 2025-10-16 16:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_timezone_support'
down_revision = '6c5aa29c1cd2'  # 设置为上一个迁移的revision ID
branch_labels = None
depends_on = None


def upgrade():
    """
    升级数据库 - 将所有datetime字段转换为带时区的timestamptz
    """
    # 获取所有表名和datetime列
    tables_with_datetime = [
        ('users', ['created_at', 'updated_at', 'last_login']),
        ('projects', ['created_at', 'updated_at']),
        ('files', ['created_at', 'updated_at']),
        ('slices', ['created_at', 'updated_at']),
        ('cot_annotations', ['created_at', 'updated_at']),
        ('kg_entities', ['created_at', 'updated_at']),
        ('kg_relations', ['created_at', 'updated_at']),
        ('export_tasks', ['created_at', 'updated_at', 'started_at', 'completed_at']),
    ]
    
    for table_name, columns in tables_with_datetime:
        for column in columns:
            # 检查列是否存在
            try:
                # 将datetime转换为timestamptz,并假设现有数据是UTC时间
                op.execute(f"""
                    ALTER TABLE {table_name} 
                    ALTER COLUMN {column} TYPE timestamp with time zone 
                    USING {column} AT TIME ZONE 'UTC'
                """)
                print(f"✅ 已将 {table_name}.{column} 转换为 timestamptz")
            except Exception as e:
                print(f"⚠️ 跳过 {table_name}.{column}: {e}")


def downgrade():
    """
    降级数据库 - 将timestamptz转回datetime(不带时区)
    """
    tables_with_datetime = [
        ('users', ['created_at', 'updated_at', 'last_login']),
        ('projects', ['created_at', 'updated_at']),
        ('files', ['created_at', 'updated_at']),
        ('slices', ['created_at', 'updated_at']),
        ('cot_annotations', ['created_at', 'updated_at']),
        ('kg_entities', ['created_at', 'updated_at']),
        ('kg_relations', ['created_at', 'updated_at']),
        ('export_tasks', ['created_at', 'updated_at', 'started_at', 'completed_at']),
    ]
    
    for table_name, columns in tables_with_datetime:
        for column in columns:
            try:
                op.execute(f"""
                    ALTER TABLE {table_name} 
                    ALTER COLUMN {column} TYPE timestamp without time zone 
                    USING {column} AT TIME ZONE 'UTC'
                """)
                print(f"✅ 已将 {table_name}.{column} 转换回 timestamp")
            except Exception as e:
                print(f"⚠️ 跳过 {table_name}.{column}: {e}")
