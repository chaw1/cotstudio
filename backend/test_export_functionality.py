"""
导出功能测试
"""
import pytest
import json
import os
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.models import Project, File, Slice, COTItem, COTCandidate, User
from app.models.project import ProjectType, ProjectStatus
from app.models.file import OCRStatus
from app.models.slice import SliceType
from app.models.cot import COTSource, COTStatus
from app.schemas.export import ExportRequest, ExportFormat
from app.services.export_service import ExportService
from app.core.database import get_db


class TestExportService:
    """导出服务测试类"""
    
    @pytest.fixture
    def db_session(self):
        """创建测试数据库会话"""
        # 这里应该使用测试数据库
        db = next(get_db())
        yield db
        db.close()
    
    @pytest.fixture
    def sample_project_data(self, db_session):
        """创建示例项目数据"""
        # 创建用户
        user = User(
            id="test-user-id",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        
        # 创建项目
        project = Project(
            id="test-project-id",
            name="测试项目",
            description="这是一个测试项目",
            owner_id=user.id,
            tags=["test", "export"],
            project_type=ProjectType.STANDARD,
            status=ProjectStatus.ACTIVE
        )
        db_session.add(project)
        
        # 创建文件
        file = File(
            id="test-file-id",
            project_id=project.id,
            filename="test_document.pdf",
            original_filename="测试文档.pdf",
            file_path="/uploads/test_document.pdf",
            file_hash="abc123def456",
            size=1024000,
            mime_type="application/pdf",
            ocr_status=OCRStatus.COMPLETED,
            ocr_engine="PaddleOCR"
        )
        db_session.add(file)
        
        # 创建切片
        slice_obj = Slice(
            id="test-slice-id",
            file_id=file.id,
            content="这是一个测试文档的内容片段，用于演示CoT数据生成。",
            start_offset=0,
            end_offset=50,
            slice_type=SliceType.PARAGRAPH,
            page_number=1,
            sequence_number=1
        )
        db_session.add(slice_obj)
        
        # 创建CoT数据
        cot_item = COTItem(
            id="test-cot-id",
            project_id=project.id,
            slice_id=slice_obj.id,
            question="这个文档片段的主要内容是什么？",
            chain_of_thought="首先分析文档内容，然后总结主要观点。",
            source=COTSource.MANUAL,
            status=COTStatus.APPROVED,
            created_by="testuser"
        )
        db_session.add(cot_item)
        
        # 创建候选答案
        candidates = [
            COTCandidate(
                id="candidate-1",
                cot_item_id=cot_item.id,
                text="这是第一个候选答案",
                chain_of_thought="通过分析可以得出...",
                score=0.9,
                chosen=True,
                rank=1
            ),
            COTCandidate(
                id="candidate-2",
                cot_item_id=cot_item.id,
                text="这是第二个候选答案",
                chain_of_thought="另一种分析方法...",
                score=0.7,
                chosen=False,
                rank=2
            )
        ]
        
        for candidate in candidates:
            db_session.add(candidate)
        
        db_session.commit()
        
        return {
            "user": user,
            "project": project,
            "file": file,
            "slice": slice_obj,
            "cot_item": cot_item,
            "candidates": candidates
        }
    
    def test_export_json_format(self, db_session, sample_project_data):
        """测试JSON格式导出"""
        export_service = ExportService(db_session)
        
        # 创建导出请求
        request = ExportRequest(
            project_id=sample_project_data["project"].id,
            format=ExportFormat.JSON,
            include_metadata=True,
            include_files=True,
            include_kg_data=False
        )
        
        # 执行导出
        with tempfile.TemporaryDirectory() as temp_dir:
            export_service.export_dir = Path(temp_dir)
            
            # 使用异步函数的同步版本进行测试
            import asyncio
            file_path = asyncio.run(export_service.export_project(request))
            
            # 验证文件存在
            assert os.path.exists(file_path)
            
            # 验证JSON内容
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert "metadata" in data
            assert "cot_items" in data
            assert "files_info" in data
            assert len(data["cot_items"]) == 1
            assert data["cot_items"][0]["question"] == "这个文档片段的主要内容是什么？"
            assert len(data["cot_items"][0]["candidates"]) == 2
    
    def test_export_markdown_format(self, db_session, sample_project_data):
        """测试Markdown格式导出"""
        export_service = ExportService(db_session)
        
        request = ExportRequest(
            project_id=sample_project_data["project"].id,
            format=ExportFormat.MARKDOWN,
            include_metadata=True
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_service.export_dir = Path(temp_dir)
            
            import asyncio
            file_path = asyncio.run(export_service.export_project(request))
            
            # 验证文件存在
            assert os.path.exists(file_path)
            
            # 验证Markdown内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "# 测试项目" in content
            assert "## 导出信息" in content
            assert "## CoT数据" in content
            assert "这个文档片段的主要内容是什么？" in content
    
    def test_export_latex_format(self, db_session, sample_project_data):
        """测试LaTeX格式导出"""
        export_service = ExportService(db_session)
        
        request = ExportRequest(
            project_id=sample_project_data["project"].id,
            format=ExportFormat.LATEX,
            include_metadata=True
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_service.export_dir = Path(temp_dir)
            
            import asyncio
            file_path = asyncio.run(export_service.export_project(request))
            
            # 验证文件存在
            assert os.path.exists(file_path)
            
            # 验证LaTeX内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "\\documentclass" in content
            assert "\\title{测试项目}" in content
            assert "\\section{CoT数据}" in content
    
    def test_export_txt_format(self, db_session, sample_project_data):
        """测试TXT格式导出"""
        export_service = ExportService(db_session)
        
        request = ExportRequest(
            project_id=sample_project_data["project"].id,
            format=ExportFormat.TXT,
            include_metadata=True
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_service.export_dir = Path(temp_dir)
            
            import asyncio
            file_path = asyncio.run(export_service.export_project(request))
            
            # 验证文件存在
            assert os.path.exists(file_path)
            
            # 验证TXT内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "项目名称: 测试项目" in content
            assert "CoT数据:" in content
            assert "这个文档片段的主要内容是什么？" in content
    
    def test_create_project_package(self, db_session, sample_project_data):
        """测试项目包创建"""
        export_service = ExportService(db_session)
        
        request = ExportRequest(
            project_id=sample_project_data["project"].id,
            format=ExportFormat.JSON,
            include_metadata=True,
            include_files=True,
            include_kg_data=True
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_service.export_dir = Path(temp_dir)
            
            import asyncio
            package_path = asyncio.run(export_service.create_project_package(request))
            
            # 验证ZIP文件存在
            assert os.path.exists(package_path)
            assert package_path.endswith('.zip')
            
            # 验证ZIP内容
            with zipfile.ZipFile(package_path, 'r') as zipf:
                file_list = zipf.namelist()
                
                assert "metadata.json" in file_list
                assert "data.json" in file_list
                assert "data.md" in file_list
                assert "knowledge_graph.json" in file_list
    
    def test_validate_export_data(self, db_session):
        """测试导出数据验证"""
        export_service = ExportService(db_session)
        
        # 创建测试JSON文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            test_data = {
                "metadata": {
                    "project_name": "测试项目",
                    "total_cot_items": 1
                },
                "cot_items": [
                    {
                        "id": "test-id",
                        "question": "测试问题",
                        "candidates": [
                            {"text": "答案1", "score": 0.9}
                        ]
                    }
                ],
                "files_info": []
            }
            json.dump(test_data, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            import asyncio
            result = asyncio.run(export_service.validate_export_data(temp_file))
            
            assert result.is_valid == True
            assert result.total_items == 1
            assert len(result.validation_errors) == 0
            assert result.checksum != ""
        
        finally:
            os.unlink(temp_file)
    
    def test_validate_invalid_json(self, db_session):
        """测试无效JSON验证"""
        export_service = ExportService(db_session)
        
        # 创建无效JSON文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            import asyncio
            result = asyncio.run(export_service.validate_export_data(temp_file))
            
            assert result.is_valid == False
            assert len(result.validation_errors) > 0
            assert "Invalid JSON format" in result.validation_errors[0]
        
        finally:
            os.unlink(temp_file)
    
    def test_latex_escape_function(self, db_session):
        """测试LaTeX转义函数"""
        export_service = ExportService(db_session)
        
        # 测试特殊字符转义
        test_cases = [
            ("Hello & World", "Hello \\& World"),
            ("Price: $100", "Price: \\$100"),
            ("Math: x^2", "Math: x\\textasciicircum{}2"),
            ("File_name", "File\\_name"),
            ("100%", "100\\%"),
            ("#hashtag", "\\#hashtag")
        ]
        
        for input_text, expected_output in test_cases:
            result = export_service._escape_latex(input_text)
            assert result == expected_output
    
    def test_checksum_calculation(self, db_session):
        """测试校验和计算"""
        export_service = ExportService(db_session)
        
        # 创建测试文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("test content for checksum")
            temp_file = f.name
        
        try:
            checksum1 = export_service._calculate_checksum(temp_file)
            checksum2 = export_service._calculate_checksum(temp_file)
            
            # 相同文件应该有相同的校验和
            assert checksum1 == checksum2
            assert len(checksum1) == 32  # MD5哈希长度
        
        finally:
            os.unlink(temp_file)


def test_export_schemas():
    """测试导出相关的Pydantic模式"""
    from app.schemas.export import ExportRequest, ExportFormat, ExportStatus
    
    # 测试导出请求模式
    request_data = {
        "project_id": "test-project-id",
        "format": "json",
        "include_metadata": True,
        "include_files": False,
        "include_kg_data": True
    }
    
    request = ExportRequest(**request_data)
    assert request.project_id == "test-project-id"
    assert request.format == ExportFormat.JSON
    assert request.include_metadata == True
    assert request.include_files == False
    assert request.include_kg_data == True


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])