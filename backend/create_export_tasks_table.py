#!/usr/bin/env python3
"""
手动创建export_tasks表
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.export_task import ExportTask
from app.models.base import Base

def create_export_tasks_table():
    """创建export_tasks表"""
    print("开始创建export_tasks表...")
    
    try:
        # 只创建export_tasks表
        ExportTask.__table__.create(engine, checkfirst=True)
        print("✓ export_tasks表创建成功")
        
        # 验证表是否存在
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'export_tasks' in tables:
            print("✓ 表验证成功")
            
            # 显示表结构
            columns = inspector.get_columns('export_tasks')
            print(f"✓ 表包含 {len(columns)} 个字段:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
        else:
            print("✗ 表验证失败")
            
    except Exception as e:
        print(f"✗ 创建表失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_export_tasks_table()