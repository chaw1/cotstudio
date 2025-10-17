"""
MinerU 导入命令行工具
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.services.mineru_import_service import mineru_import_service
from app.services.project_service import project_service

def import_document(document_name, mode='vlm'):
    """导入单个文档"""
    db = SessionLocal()
    try:
        # 获取项目
        projects = project_service.get_multi(db, limit=1)
        if not projects:
            print("错误: 未找到项目")
            return False
        
        project_id = str(projects[0].id)
        print(f"使用项目: {projects[0].name}")
        
        # 导入文档
        result = mineru_import_service.import_document(
            db=db,
            document_name=document_name,
            mode=mode,
            project_id=project_id
        )
        
        stats = result['statistics']
        print(f"\n成功!")
        print(f"  文件ID: {result['file_id']}")
        print(f"  导入切片: {stats['imported_slices']}")
        print(f"  跳过块: {stats['skipped_blocks']}")
        print(f"  切片类型: {stats['slice_types']}")
        
        return True
        
    except Exception as e:
        print(f"错误: {e}")
        return False
    finally:
        db.close()

def list_documents():
    """列出可用文档"""
    docs = mineru_import_service.get_available_documents()
    print(f"找到 {len(docs)} 个文档:\n")
    for i, doc in enumerate(docs, 1):
        print(f"{i}. {doc['name']}/{doc['mode']} ({doc['total_blocks']} 块)")
    return docs

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python mineru_cli.py list                    # 列出文档")
        print("  python mineru_cli.py import <doc> [mode]     # 导入文档")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        list_documents()
    elif command == "import":
        if len(sys.argv) < 3:
            print("错误: 需要指定文档名")
            sys.exit(1)
        doc_name = sys.argv[2]
        mode = sys.argv[3] if len(sys.argv) > 3 else 'vlm'
        import_document(doc_name, mode)
    else:
        print(f"未知命令: {command}")
        sys.exit(1)
