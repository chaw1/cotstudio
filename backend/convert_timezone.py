"""
将数据库中的所有datetime字段转换为带时区的timestamptz
这个脚本直接修改PostgreSQL数据库
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

print(f"连接到数据库: {settings.DATABASE_URL}")

# 创建数据库引擎
engine = create_engine(settings.DATABASE_URL)
conn = engine.connect()

# 需要转换的表和列
tables_with_datetime = {
    'users': ['created_at', 'updated_at', 'last_login'],
    'projects': ['created_at', 'updated_at'],
    'files': ['created_at', 'updated_at'],
    'slices': ['created_at', 'updated_at'],
    'cot_annotations': ['created_at', 'updated_at'],
    'kg_entities': ['created_at', 'updated_at'],
    'kg_relations': ['created_at', 'updated_at'],
    'export_tasks': ['created_at', 'updated_at', 'started_at', 'completed_at', 'expires_at'],
}

print("\n开始转换时区...")

for table_name, columns in tables_with_datetime.items():
    for column in columns:
        try:
            # 检查列的当前类型
            result = conn.execute(text(f"""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' AND column_name = '{column}'
            """))
            row = result.fetchone()
            
            if not row:
                print(f"⏭️  跳过 {table_name}.{column} - 列不存在")
                continue
                
            current_type = row[0]
            
            if current_type == 'timestamp with time zone':
                print(f"✓  {table_name}.{column} 已经是 timestamptz")
                continue
            
            # 转换为带时区的timestamp (假设现有数据是UTC)
            conn.execute(text(f"""
                ALTER TABLE {table_name} 
                ALTER COLUMN {column} TYPE timestamp with time zone 
                USING {column} AT TIME ZONE 'UTC'
            """))
            conn.commit()
            print(f"✅ 已将 {table_name}.{column} 转换为 timestamptz")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 转换 {table_name}.{column} 失败: {e}")

conn.close()

print("\n✅ 时区转换完成!")
