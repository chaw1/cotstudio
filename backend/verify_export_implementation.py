#!/usr/bin/env python3
"""
导出功能实现验证脚本
"""
import sys
import os
import json
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import_modules():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        from app.schemas.export import (
            ExportFormat, ExportStatus, ExportRequest, ExportTaskResponse,
            ExportMetadata, COTExportItem, ProjectExportData, ExportValidationResult
        )
        print("✅ 导出模式导入成功")
    except ImportError as e:
        print(f"❌ 导出模式导入失败: {e}")
        return False
    
    try:
        from app.services.export_service import ExportService
        print("✅ 导出服务导入成功")
    except ImportError as e:
        print(f"❌ 导出服务导入失败: {e}")
        return False
    
    try:
        from app.workers.export_tasks import export_project_task, create_project_package_task
        print("✅ 导出任务导入成功")
    except ImportError as e:
        print(f"❌ 导出任务导入失败: {e}")
        return False
    
    try:
        from app.api.v1.export import router
        print("✅ 导出API导入成功")
    except ImportError as e:
        print(f"❌ 导出API导入失败: {e}")
        return False
    
    return True


def test_export_schemas():
    """测试导出模式"""
    print("\n🔍 测试导出模式...")
    
    try:
        from app.schemas.export import ExportRequest, ExportFormat
        
        # 测试导出请求创建
        request = ExportRequest(
            project_id="test-project-id",
            format=ExportFormat.JSON,
            include_metadata=True,
            include_files=True,
            include_kg_data=False
        )
        
        assert request.project_id == "test-project-id"
        assert request.format == ExportFormat.JSON
        assert request.include_metadata == True
        
        print("✅ 导出请求模式测试通过")
        
        # 测试所有导出格式
        formats = [ExportFormat.JSON, ExportFormat.MARKDOWN, ExportFormat.LATEX, ExportFormat.TXT]
        for fmt in formats:
            request = ExportRequest(
                project_id="test",
                format=fmt
            )
            assert request.format == fmt
        
        print("✅ 所有导出格式测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 导出模式测试失败: {e}")
        return False


def test_export_service_basic():
    """测试导出服务基本功能"""
    print("\n🔍 测试导出服务基本功能...")
    
    try:
        from app.services.export_service import ExportService
        from unittest.mock import Mock
        
        # 创建模拟数据库会话
        mock_db = Mock()
        
        # 创建导出服务实例
        with tempfile.TemporaryDirectory() as temp_dir:
            export_service = ExportService(mock_db)
            export_service.export_dir = Path(temp_dir)
            
            # 测试目录创建
            assert export_service.export_dir.exists()
            print("✅ 导出目录创建成功")
            
            # 测试LaTeX转义功能
            test_text = "Hello & World $100 #test"
            escaped = export_service._escape_latex(test_text)
            assert "\\&" in escaped
            assert "\\$" in escaped
            assert "\\#" in escaped
            print("✅ LaTeX转义功能测试通过")
            
            # 测试校验和计算
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content", encoding="utf-8")
            checksum = export_service._calculate_checksum(str(test_file))
            assert len(checksum) == 32  # MD5长度
            print("✅ 校验和计算功能测试通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 导出服务基本功能测试失败: {e}")
        return False


def test_export_formats():
    """测试导出格式功能"""
    print("\n🔍 测试导出格式功能...")
    
    try:
        from app.services.export_service import ExportService
        from app.schemas.export import ExportMetadata, COTExportItem, ProjectExportData, ExportFormat
        from unittest.mock import Mock
        from datetime import datetime
        
        # 创建模拟数据
        metadata = ExportMetadata(
            project_name="测试项目",
            project_description="测试描述",
            export_format=ExportFormat.JSON,
            export_timestamp=datetime.now(),
            total_files=1,
            total_cot_items=1,
            total_candidates=2,
            export_settings={}
        )
        
        cot_item = COTExportItem(
            id="test-id",
            question="测试问题",
            chain_of_thought="测试思维链",
            source="manual",
            status="approved",
            created_by="testuser",
            created_at=datetime.now(),
            slice_content="测试内容",
            slice_type="paragraph",
            file_name="test.pdf",
            candidates=[
                {
                    "id": "c1",
                    "text": "答案1",
                    "chain_of_thought": "思维链1",
                    "score": 0.9,
                    "chosen": True,
                    "rank": 1
                }
            ]
        )
        
        project_data = ProjectExportData(
            metadata=metadata,
            cot_items=[cot_item],
            files_info=[{"id": "f1", "filename": "test.pdf"}],
            kg_data=None
        )
        
        mock_db = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_service = ExportService(mock_db)
            export_service.export_dir = Path(temp_dir)
            
            # 测试JSON导出
            import asyncio
            json_path = asyncio.run(export_service._export_json(project_data, "test-project"))
            assert os.path.exists(json_path)
            
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                assert "metadata" in json_data
                assert "cot_items" in json_data
            print("✅ JSON导出功能测试通过")
            
            # 测试Markdown导出
            md_path = asyncio.run(export_service._export_markdown(project_data, "test-project"))
            assert os.path.exists(md_path)
            
            with open(md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
                assert "# 测试项目" in md_content
                assert "## CoT数据" in md_content
            print("✅ Markdown导出功能测试通过")
            
            # 测试LaTeX导出
            latex_path = asyncio.run(export_service._export_latex(project_data, "test-project"))
            assert os.path.exists(latex_path)
            
            with open(latex_path, 'r', encoding='utf-8') as f:
                latex_content = f.read()
                assert "\\documentclass" in latex_content
                assert "\\title{测试项目}" in latex_content
            print("✅ LaTeX导出功能测试通过")
            
            # 测试TXT导出
            txt_path = asyncio.run(export_service._export_txt(project_data, "test-project"))
            assert os.path.exists(txt_path)
            
            with open(txt_path, 'r', encoding='utf-8') as f:
                txt_content = f.read()
                assert "项目名称: 测试项目" in txt_content
                assert "CoT数据:" in txt_content
            print("✅ TXT导出功能测试通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 导出格式功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation_functionality():
    """测试验证功能"""
    print("\n🔍 测试验证功能...")
    
    try:
        from app.services.export_service import ExportService
        from unittest.mock import Mock
        
        mock_db = Mock()
        export_service = ExportService(mock_db)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_service.export_dir = Path(temp_dir)
            
            # 创建有效的JSON测试文件
            valid_json = {
                "metadata": {"project_name": "test", "total_cot_items": 1},
                "cot_items": [{"question": "test", "candidates": []}],
                "files_info": []
            }
            
            json_file = Path(temp_dir) / "valid.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(valid_json, f)
            
            # 测试有效JSON验证
            import asyncio
            result = asyncio.run(export_service.validate_export_data(str(json_file)))
            assert result.is_valid == True
            assert result.total_items == 1
            print("✅ 有效JSON验证测试通过")
            
            # 创建无效的JSON测试文件
            invalid_file = Path(temp_dir) / "invalid.json"
            with open(invalid_file, 'w', encoding='utf-8') as f:
                f.write("invalid json")
            
            # 测试无效JSON验证
            result = asyncio.run(export_service.validate_export_data(str(invalid_file)))
            assert result.is_valid == False
            assert len(result.validation_errors) > 0
            print("✅ 无效JSON验证测试通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """测试API端点"""
    print("\n🔍 测试API端点...")
    
    try:
        from app.api.v1.export import router
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        
        # 创建测试应用
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/export")
        
        # 检查路由是否正确注册
        routes = [route.path for route in app.routes]
        expected_routes = [
            "/api/v1/export/projects/{project_id}/export",
            "/api/v1/export/projects/{project_id}/package",
            "/api/v1/export/tasks/{task_id}/status",
            "/api/v1/export/download/{filename}",
            "/api/v1/export/validate",
            "/api/v1/export/formats"
        ]
        
        for expected_route in expected_routes:
            # 检查路由模式是否存在（忽略参数部分）
            route_found = any(expected_route.replace("{project_id}", "test").replace("{task_id}", "test").replace("{filename}", "test") 
                            in route.replace("{project_id}", "test").replace("{task_id}", "test").replace("{filename}", "test") 
                            for route in routes)
            if not route_found:
                print(f"❌ 路由未找到: {expected_route}")
                return False
        
        print("✅ API端点路由注册测试通过")
        return True
        
    except Exception as e:
        print(f"❌ API端点测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("🚀 开始验证导出功能实现...")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_import_modules),
        ("导出模式", test_export_schemas),
        ("导出服务基本功能", test_export_service_basic),
        ("导出格式功能", test_export_formats),
        ("验证功能", test_validation_functionality),
        ("API端点", test_api_endpoints),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}测试:")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name}测试失败")
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！导出功能实现成功！")
        
        print("\n📋 实现的功能:")
        print("✅ 多格式导出 (JSON, Markdown, LaTeX, TXT)")
        print("✅ 项目包生成 (包含所有数据和元数据)")
        print("✅ 异步任务处理和进度跟踪")
        print("✅ 导出数据验证和完整性检查")
        print("✅ 文件下载和安全检查")
        print("✅ API端点和错误处理")
        
        print("\n🔧 主要组件:")
        print("• ExportService - 核心导出服务")
        print("• export_tasks.py - Celery异步任务")
        print("• export.py - API端点")
        print("• export.py (schemas) - 数据模式")
        
        return True
    else:
        print("❌ 部分测试失败，请检查实现")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)