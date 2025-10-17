#!/usr/bin/env python3
"""
简单的导出功能测试
"""
import sys
import os
import asyncio
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.export_service import ExportService
from app.schemas.export import ExportRequest, ExportFormat
from app.core.database import get_db
from app.models import Project, User

async def test_export_service():
    """测试导出服务基本功能"""
    print("开始测试导出服务...")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 创建导出服务实例
        export_service = ExportService(db)
        print("✓ 导出服务实例创建成功")
        
        # 检查是否有项目数据
        projects = db.query(Project).limit(1).all()
        if not projects:
            print("⚠ 数据库中没有项目数据，跳过导出测试")
            return
        
        project = projects[0]
        print(f"✓ 找到测试项目: {project.name} (ID: {project.id})")
        
        # 创建导出请求
        export_request = ExportRequest(
            project_id=project.id,
            format=ExportFormat.JSON,
            include_metadata=True,
            include_files=False,
            include_kg_data=False
        )
        print("✓ 导出请求创建成功")
        
        # 测试数据收集
        try:
            project_data = await export_service._collect_project_data(export_request)
            print(f"✓ 项目数据收集成功:")
            print(f"  - CoT数据项: {len(project_data.cot_items)}")
            print(f"  - 文件信息: {len(project_data.files_info)}")
            print(f"  - 项目名称: {project_data.metadata.project_name}")
        except Exception as e:
            print(f"✗ 项目数据收集失败: {e}")
            return
        
        # 测试JSON导出
        try:
            json_file = await export_service._export_json(project_data, project.id)
            print(f"✓ JSON导出成功: {json_file}")
            
            # 检查文件是否存在
            if os.path.exists(json_file):
                file_size = os.path.getsize(json_file)
                print(f"  - 文件大小: {file_size} bytes")
            else:
                print("✗ 导出文件不存在")
        except Exception as e:
            print(f"✗ JSON导出失败: {e}")
        
        # 测试Markdown导出
        try:
            md_file = await export_service._export_markdown(project_data, project.id)
            print(f"✓ Markdown导出成功: {md_file}")
        except Exception as e:
            print(f"✗ Markdown导出失败: {e}")
        
        # 测试导出验证
        if 'json_file' in locals() and os.path.exists(json_file):
            try:
                validation_result = await export_service.validate_export_data(json_file)
                print(f"✓ 导出验证完成:")
                print(f"  - 验证通过: {validation_result.is_valid}")
                print(f"  - 数据项数量: {validation_result.total_items}")
                print(f"  - 错误数量: {len(validation_result.validation_errors)}")
                print(f"  - 警告数量: {len(validation_result.warnings)}")
                if validation_result.validation_errors:
                    print(f"  - 错误详情: {validation_result.validation_errors}")
            except Exception as e:
                print(f"✗ 导出验证失败: {e}")
        
        print("\n导出服务测试完成!")
        
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_export_service())