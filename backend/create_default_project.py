"""
创建默认项目用于MinerU导入
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models.project import Project
from app.services.project_service import project_service

def main():
    db = SessionLocal()
    try:
        # 检查是否已有项目
        projects = project_service.get_multi(db, limit=10)
        
        if projects:
            print(f"✓ 找到 {len(projects)} 个现有项目:")
            for p in projects:
                print(f"  - {p.name} (ID: {p.id})")
            
            # 使用第一个项目
            project_id = str(projects[0].id)
            print(f"\n将使用项目: {projects[0].name} ({project_id})")
        else:
            # 创建新项目
            project_data = {
                'name': 'MinerU导入项目',
                'description': '用于存放MinerU解析的文档'
            }
            project = project_service.create(db, obj_in=project_data)
            project_id = str(project.id)
            print(f"✓ 创建新项目: {project.name} ({project_id})")
        
        return project_id
        
    finally:
        db.close()

if __name__ == "__main__":
    project_id = main()
    print(f"\n项目ID: {project_id}")
