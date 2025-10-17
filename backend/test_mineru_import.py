"""
测试MinerU导入服务
"""
import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.services.mineru_import_service import mineru_import_service
from app.services.project_service import project_service

def main():
    print("=== MinerU导入服务测试 ===\n")
    
    # 0. 获取项目ID
    print("0. 获取项目...")
    db = SessionLocal()
    projects = project_service.get_multi(db, limit=1)
    if not projects:
        print("❌ 未找到任何项目，请先创建项目")
        db.close()
        return
    project_id = str(projects[0].id)
    print(f"✓ 使用项目: {projects[0].name} ({project_id})\n")
    db.close()
    
    # 1. 获取可用文档列表
    print("1. 获取可用的MinerU解析文档...")
    documents = mineru_import_service.get_available_documents()
    
    if not documents:
        print("❌ 未找到任何MinerU解析文档")
        print("请确保 ./mineru/output 目录存在且包含解析结果")
        return
    
    print(f"✓ 找到 {len(documents)} 个文档:\n")
    for i, doc in enumerate(documents, 1):
        print(f"  {i}. {doc['name']}/{doc['mode']}")
        print(f"     - 路径: {doc['path']}")
        print(f"     - 总块数: {doc['total_blocks']}")
        print(f"     - 有Markdown: {doc['has_markdown']}")
        print(f"     - 文本长度: {doc['full_text_length']}\n")
    
    # 2. 导入第一个文档作为测试
    print("\n2. 导入第一个文档到数据库...")
    db = SessionLocal()
    try:
        first_doc = documents[0]
        print(f"导入: {first_doc['name']}/{first_doc['mode']}")
        
        result = mineru_import_service.import_document(
            db=db,
            document_name=first_doc['name'],
            mode=first_doc['mode'],
            project_id=project_id
        )
        
        print(f"\n✓ 导入成功!")
        print(f"  - 文件ID: {result['file_id']}")
        print(f"  - 文档名称: {result['document_name']}")
        print(f"  - 模式: {result['mode']}")
        print(f"\n统计信息:")
        stats = result['statistics']
        print(f"  - 总块数: {stats['total_blocks']}")
        print(f"  - 导入切片数: {stats['imported_slices']}")
        print(f"  - 跳过块数: {stats['skipped_blocks']}")
        print(f"\n切片类型分布:")
        for slice_type, count in stats['slice_types'].items():
            print(f"  - {slice_type}: {count}")
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()
