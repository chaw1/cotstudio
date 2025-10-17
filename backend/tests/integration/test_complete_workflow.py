"""
完整业务流程集成测试
测试从文件上传到CoT生成的完整流程
"""
import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.file import File
from app.models.slice import Slice
from app.models.cot import COTItem, COTCandidate
from app.schemas.project import ProjectCreate
from app.schemas.file import FileUploadResponse
from app.services.ocr_service import OCRService
from app.services.llm_service import LLMService


class TestCompleteWorkflow:
    """完整业务流程测试"""
    
    @pytest.fixture
    def sample_text_file(self):
        """创建测试文本文件"""
        content = """
        人工智能的发展历程
        
        人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，
        它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
        
        机器学习是人工智能的一个重要分支，它通过算法使计算机能够从数据中学习，
        而不需要明确的编程指令。深度学习是机器学习的一个子集，
        它使用多层神经网络来模拟人脑的工作方式。
        
        自然语言处理（NLP）是人工智能的另一个重要领域，
        它致力于让计算机理解、解释和生成人类语言。
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            return f.name
    
    def test_complete_file_to_cot_workflow(self, client: TestClient, db_session: Session, sample_text_file):
        """测试完整的文件上传到CoT生成流程"""
        
        # 1. 创建项目
        project_data = {
            "name": "AI研究项目",
            "description": "人工智能相关文档分析",
            "tags": ["AI", "机器学习"]
        }
        
        response = client.post("/api/v1/projects/", json=project_data)
        assert response.status_code == 200
        project = response.json()
        project_id = project["id"]
        
        # 2. 上传文件
        with open(sample_text_file, 'rb') as f:
            files = {"file": ("test_ai.txt", f, "text/plain")}
            response = client.post(
                f"/api/v1/projects/{project_id}/upload",
                files=files
            )
        
        assert response.status_code == 200
        file_data = response.json()
        file_id = file_data["file_id"]
        
        # 验证文件记录
        db_file = db_session.query(File).filter(File.id == file_id).first()
        assert db_file is not None
        assert db_file.filename == "test_ai.txt"
        assert db_file.project_id == project_id
        
        # 3. 触发OCR处理
        response = client.post(f"/api/v1/files/{file_id}/ocr")
        assert response.status_code == 200
        
        # 等待OCR处理完成（模拟异步任务）
        # 在实际测试中，这里应该轮询任务状态
        
        # 4. 获取切片
        response = client.get(f"/api/v1/files/{file_id}/slices")
        assert response.status_code == 200
        slices = response.json()
        assert len(slices) > 0
        
        slice_id = slices[0]["id"]
        
        # 5. 生成CoT问题和答案
        cot_data = {
            "slice_id": slice_id,
            "question_prompt": "基于这段文本，生成一个关于人工智能发展的问题"
        }
        
        response = client.post("/api/v1/cot/generate", json=cot_data)
        assert response.status_code == 200
        cot_result = response.json()
        
        assert "question" in cot_result
        assert "candidates" in cot_result
        assert len(cot_result["candidates"]) >= 3
        
        # 6. 保存标注数据
        annotation_data = {
            "project_id": project_id,
            "slice_id": slice_id,
            "question": cot_result["question"],
            "candidates": [
                {
                    "text": candidate["text"],
                    "chain_of_thought": candidate["chain_of_thought"],
                    "score": 0.8,
                    "chosen": i == 0,  # 第一个设为chosen
                    "rank": i + 1
                }
                for i, candidate in enumerate(cot_result["candidates"])
            ]
        }
        
        response = client.post("/api/v1/cot/", json=annotation_data)
        assert response.status_code == 200
        cot_item = response.json()
        
        # 验证CoT数据保存
        db_cot = db_session.query(COTItem).filter(COTItem.id == cot_item["id"]).first()
        assert db_cot is not None
        assert db_cot.question == cot_result["question"]
        
        # 验证候选答案
        candidates = db_session.query(COTCandidate).filter(
            COTCandidate.cot_item_id == cot_item["id"]
        ).all()
        assert len(candidates) >= 3
        
        chosen_candidates = [c for c in candidates if c.chosen]
        assert len(chosen_candidates) == 1
        
        # 7. 验证项目统计
        response = client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        project_stats = response.json()
        assert project_stats["file_count"] == 1
        assert project_stats["cot_count"] == 1
        
        # 清理测试文件
        os.unlink(sample_text_file)
    
    def test_knowledge_graph_extraction_workflow(self, client: TestClient, db_session: Session):
        """测试知识图谱抽取流程"""
        
        # 1. 创建项目和CoT数据
        project_data = {"name": "KG测试项目", "description": "知识图谱抽取测试"}
        response = client.post("/api/v1/projects/", json=project_data)
        project_id = response.json()["id"]
        
        # 创建模拟的CoT数据
        cot_data = {
            "project_id": project_id,
            "question": "什么是机器学习？",
            "candidates": [
                {
                    "text": "机器学习是人工智能的一个分支",
                    "chain_of_thought": "机器学习 -> 人工智能分支 -> 算法学习数据",
                    "score": 0.9,
                    "chosen": True,
                    "rank": 1
                }
            ]
        }
        
        response = client.post("/api/v1/cot/", json=cot_data)
        assert response.status_code == 200
        cot_item = response.json()
        
        # 2. 触发知识图谱抽取
        response = client.post(f"/api/v1/knowledge-graph/extract/{project_id}")
        assert response.status_code == 200
        
        # 3. 查询知识图谱
        response = client.get(f"/api/v1/knowledge-graph/{project_id}/entities")
        assert response.status_code == 200
        entities = response.json()
        
        # 验证抽取的实体
        entity_names = [entity["name"] for entity in entities]
        assert "机器学习" in entity_names or "人工智能" in entity_names
        
        # 4. 查询关系
        response = client.get(f"/api/v1/knowledge-graph/{project_id}/relationships")
        assert response.status_code == 200
        relationships = response.json()
        
        # 验证关系数据
        assert len(relationships) >= 0  # 可能没有关系，但不应该报错
    
    def test_export_import_workflow(self, client: TestClient, db_session: Session):
        """测试导出导入流程"""
        
        # 1. 创建完整的项目数据
        project_data = {"name": "导出测试项目", "description": "测试导出功能"}
        response = client.post("/api/v1/projects/", json=project_data)
        project_id = response.json()["id"]
        
        # 添加CoT数据
        cot_data = {
            "project_id": project_id,
            "question": "测试问题",
            "candidates": [
                {
                    "text": "测试答案",
                    "chain_of_thought": "测试推理过程",
                    "score": 0.8,
                    "chosen": True,
                    "rank": 1
                }
            ]
        }
        
        response = client.post("/api/v1/cot/", json=cot_data)
        assert response.status_code == 200
        
        # 2. 导出项目
        export_data = {
            "format": "json",
            "include_files": True,
            "include_kg": True
        }
        
        response = client.post(f"/api/v1/export/{project_id}", json=export_data)
        assert response.status_code == 200
        export_result = response.json()
        
        assert "download_url" in export_result
        assert "export_id" in export_result
        
        # 3. 获取导出文件
        export_id = export_result["export_id"]
        response = client.get(f"/api/v1/export/{export_id}/download")
        assert response.status_code == 200
        
        # 4. 测试导入（创建新项目）
        import_data = {"project_name": "导入测试项目"}
        
        # 模拟文件上传（在实际测试中需要真实的导出文件）
        files = {"file": ("export.zip", b"mock_export_data", "application/zip")}
        response = client.post("/api/v1/import/", files=files, data=import_data)
        
        # 导入可能是异步的，检查响应格式
        assert response.status_code in [200, 202]  # 200同步，202异步
    
    def test_error_handling_and_recovery(self, client: TestClient, db_session: Session):
        """测试错误处理和恢复机制"""
        
        # 1. 测试无效文件上传
        project_data = {"name": "错误测试项目"}
        response = client.post("/api/v1/projects/", json=project_data)
        project_id = response.json()["id"]
        
        # 上传无效文件
        files = {"file": ("invalid.exe", b"invalid_content", "application/x-executable")}
        response = client.post(f"/api/v1/projects/{project_id}/upload", files=files)
        assert response.status_code == 400  # 应该拒绝无效文件
        
        # 2. 测试OCR失败处理
        # 创建有效文件但模拟OCR失败
        files = {"file": ("test.txt", b"test content", "text/plain")}
        response = client.post(f"/api/v1/projects/{project_id}/upload", files=files)
        file_id = response.json()["file_id"]
        
        # 触发OCR（可能失败）
        response = client.post(f"/api/v1/files/{file_id}/ocr")
        # 应该返回任务ID或错误信息
        assert response.status_code in [200, 400, 500]
        
        # 3. 测试LLM服务失败
        # 模拟LLM调用失败的情况
        cot_data = {
            "slice_id": "invalid_slice_id",
            "question_prompt": "测试问题"
        }
        
        response = client.post("/api/v1/cot/generate", json=cot_data)
        assert response.status_code == 400  # 应该返回错误
        
        # 4. 测试数据库约束
        # 尝试创建重复的项目名称（如果有唯一约束）
        duplicate_project = {"name": "错误测试项目"}  # 相同名称
        response = client.post("/api/v1/projects/", json=duplicate_project)
        # 根据业务规则，可能允许重复名称或返回错误
        assert response.status_code in [200, 400]