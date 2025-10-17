"""
CoT标注API测试
"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.cot import COTItem, COTCandidate, COTStatus, COTSource
from app.models.project import Project
from app.models.slice import Slice
from app.models.file import File
from app.models.user import User


client = TestClient(app)


class TestCOTAnnotationAPI:
    """CoT标注API测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.test_user = {
            "username": "test_user",
            "email": "test@example.com",
            "password": "test_password"
        }
        
        # 创建测试用户
        response = client.post("/api/v1/auth/register", json=self.test_user)
        assert response.status_code == 201
        
        # 登录获取token
        login_response = client.post("/api/v1/auth/login", json={
            "username": self.test_user["username"],
            "password": self.test_user["password"]
        })
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def create_test_project(self, db: Session) -> str:
        """创建测试项目"""
        project = Project(
            name="Test Project",
            owner=self.test_user["username"],
            description="Test project for CoT annotation"
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project.id
    
    def create_test_slice(self, db: Session, project_id: str) -> str:
        """创建测试切片"""
        # 先创建文件
        file = File(
            project_id=project_id,
            filename="test.txt",
            file_path="/test/test.txt",
            file_hash="test_hash",
            size=1000,
            mime_type="text/plain"
        )
        db.add(file)
        db.commit()
        db.refresh(file)
        
        # 创建切片
        slice_obj = Slice(
            file_id=file.id,
            content="This is a test content for CoT generation.",
            start_offset=0,
            end_offset=45,
            slice_type="paragraph",
            page_number=1
        )
        db.add(slice_obj)
        db.commit()
        db.refresh(slice_obj)
        return slice_obj.id
    
    def test_create_cot_annotation(self, db_session):
        """测试创建CoT标注"""
        project_id = self.create_test_project(db_session)
        slice_id = self.create_test_slice(db_session, project_id)
        
        cot_data = {
            "project_id": project_id,
            "slice_id": slice_id,
            "question": "What is the main topic of this text?",
            "chain_of_thought": "Let me analyze the content step by step...",
            "source": "manual",
            "candidates": [
                {
                    "text": "The text discusses testing procedures.",
                    "chain_of_thought": "Based on the content, it seems to be about testing.",
                    "score": 0.8,
                    "chosen": True,
                    "rank": 1
                },
                {
                    "text": "The text is about CoT generation.",
                    "chain_of_thought": "The mention of CoT suggests this topic.",
                    "score": 0.6,
                    "chosen": False,
                    "rank": 2
                }
            ]
        }
        
        response = client.post(
            "/api/v1/cot-annotation/",
            json=cot_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["question"] == cot_data["question"]
        assert data["project_id"] == project_id
        assert data["slice_id"] == slice_id
        assert len(data["candidates"]) == 2
        assert data["status"] == "draft"
    
    def test_create_cot_annotation_validation_errors(self, db_session):
        """测试创建CoT标注的验证错误"""
        project_id = self.create_test_project(db_session)
        slice_id = self.create_test_slice(db_session, project_id)
        
        # 测试多个chosen候选答案
        cot_data = {
            "project_id": project_id,
            "slice_id": slice_id,
            "question": "Test question?",
            "candidates": [
                {
                    "text": "Answer 1",
                    "score": 0.8,
                    "chosen": True,
                    "rank": 1
                },
                {
                    "text": "Answer 2",
                    "score": 0.6,
                    "chosen": True,  # 错误：多个chosen
                    "rank": 2
                }
            ]
        }
        
        response = client.post(
            "/api/v1/cot-annotation/",
            json=cot_data,
            headers=self.headers
        )
        
        assert response.status_code == 422
        assert "Only one candidate can be marked as chosen" in response.text
    
    def test_get_cot_annotation(self, db_session):
        """测试获取CoT标注"""
        project_id = self.create_test_project(db_session)
        slice_id = self.create_test_slice(db_session, project_id)
        
        # 先创建一个CoT标注
        cot_item = COTItem(
            project_id=project_id,
            slice_id=slice_id,
            question="Test question?",
            source=COTSource.MANUAL,
            status=COTStatus.DRAFT,
            created_by=self.test_user["username"]
        )
        db_session.add(cot_item)
        db_session.commit()
        db_session.refresh(cot_item)
        
        # 添加候选答案
        candidate = COTCandidate(
            cot_item_id=cot_item.id,
            text="Test answer",
            score=0.8,
            chosen=True,
            rank=1
        )
        db_session.add(candidate)
        db_session.commit()
        
        response = client.get(
            f"/api/v1/cot-annotation/{cot_item.id}",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == cot_item.id
        assert data["question"] == "Test question?"
        assert len(data["candidates"]) == 1
    
    def test_update_cot_annotation(self, db_session):
        """测试更新CoT标注"""
        project_id = self.create_test_project(db_session)
        slice_id = self.create_test_slice(db_session, project_id)
        
        # 创建CoT标注
        cot_item = COTItem(
            project_id=project_id,
            slice_id=slice_id,
            question="Original question?",
            source=COTSource.MANUAL,
            status=COTStatus.DRAFT,
            created_by=self.test_user["username"]
        )
        db_session.add(cot_item)
        db_session.commit()
        db_session.refresh(cot_item)
        
        # 更新数据
        update_data = {
            "question": "Updated question?",
            "candidates": [
                {
                    "text": "Updated answer",
                    "score": 0.9,
                    "chosen": True,
                    "rank": 1
                }
            ]
        }
        
        response = client.put(
            f"/api/v1/cot-annotation/{cot_item.id}",
            json=update_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "Updated question?"
        assert len(data["candidates"]) == 1
        assert data["candidates"][0]["text"] == "Updated answer"
    
    def test_update_candidates_ranking(self, db_session):
        """测试更新候选答案排序"""
        project_id = self.create_test_project(db_session)
        slice_id = self.create_test_slice(db_session, project_id)
        
        # 创建CoT标注和候选答案
        cot_item = COTItem(
            project_id=project_id,
            slice_id=slice_id,
            question="Test question?",
            source=COTSource.MANUAL,
            status=COTStatus.DRAFT,
            created_by=self.test_user["username"]
        )
        db_session.add(cot_item)
        db_session.commit()
        db_session.refresh(cot_item)
        
        candidate1 = COTCandidate(
            cot_item_id=cot_item.id,
            text="Answer 1",
            score=0.6,
            chosen=False,
            rank=1
        )
        candidate2 = COTCandidate(
            cot_item_id=cot_item.id,
            text="Answer 2",
            score=0.8,
            chosen=True,
            rank=2
        )
        db_session.add_all([candidate1, candidate2])
        db_session.commit()
        
        # 更新排序和分数
        update_data = [
            {
                "candidate_id": candidate1.id,
                "score": 0.9,
                "chosen": True,
                "rank": 1
            },
            {
                "candidate_id": candidate2.id,
                "score": 0.7,
                "chosen": False,
                "rank": 2
            }
        ]
        
        response = client.patch(
            f"/api/v1/cot-annotation/{cot_item.id}/candidates",
            json=update_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # 验证更新结果
        candidate1_data = next(c for c in data if c["id"] == candidate1.id)
        assert candidate1_data["score"] == 0.9
        assert candidate1_data["chosen"] is True
    
    def test_update_cot_status(self, db_session):
        """测试更新CoT状态"""
        project_id = self.create_test_project(db_session)
        slice_id = self.create_test_slice(db_session, project_id)
        
        # 创建完整的CoT标注
        cot_item = COTItem(
            project_id=project_id,
            slice_id=slice_id,
            question="Test question?",
            source=COTSource.MANUAL,
            status=COTStatus.DRAFT,
            created_by=self.test_user["username"]
        )
        db_session.add(cot_item)
        db_session.commit()
        db_session.refresh(cot_item)
        
        candidate = COTCandidate(
            cot_item_id=cot_item.id,
            text="Test answer",
            score=0.8,
            chosen=True,
            rank=1
        )
        db_session.add(candidate)
        db_session.commit()
        
        # 更新状态为reviewed
        status_data = {"status": "reviewed"}
        
        response = client.patch(
            f"/api/v1/cot-annotation/{cot_item.id}/status",
            json=status_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reviewed"
        assert data["reviewed_by"] == self.test_user["username"]
    
    def test_validate_cot_annotation(self, db_session):
        """测试验证CoT标注"""
        project_id = self.create_test_project(db_session)
        slice_id = self.create_test_slice(db_session, project_id)
        
        # 创建不完整的CoT标注（没有候选答案）
        cot_item = COTItem(
            project_id=project_id,
            slice_id=slice_id,
            question="Test question?",
            source=COTSource.MANUAL,
            status=COTStatus.DRAFT,
            created_by=self.test_user["username"]
        )
        db_session.add(cot_item)
        db_session.commit()
        db_session.refresh(cot_item)
        
        response = client.get(
            f"/api/v1/cot-annotation/{cot_item.id}/validate",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert "At least one candidate is required" in data["errors"]
    
    def test_get_project_annotation_stats(self, db_session):
        """测试获取项目标注统计"""
        project_id = self.create_test_project(db_session)
        slice_id = self.create_test_slice(db_session, project_id)
        
        # 创建不同状态的CoT标注
        cot_items = [
            COTItem(
                project_id=project_id,
                slice_id=slice_id,
                question=f"Question {i}?",
                source=COTSource.MANUAL,
                status=COTStatus.DRAFT if i < 2 else COTStatus.REVIEWED,
                created_by=self.test_user["username"]
            )
            for i in range(4)
        ]
        db_session.add_all(cot_items)
        db_session.commit()
        
        response = client.get(
            f"/api/v1/cot-annotation/project/{project_id}/stats",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 4
        assert data["draft_count"] == 2
        assert data["reviewed_count"] == 2
        assert data["completion_rate"] == 0.5  # 2/4 = 0.5
    
    def test_get_project_quality_metrics(self, db_session):
        """测试获取项目质量指标"""
        project_id = self.create_test_project(db_session)
        slice_id = self.create_test_slice(db_session, project_id)
        
        # 创建CoT标注和候选答案
        cot_item = COTItem(
            project_id=project_id,
            slice_id=slice_id,
            question="Test question?",
            source=COTSource.MANUAL,
            status=COTStatus.DRAFT,
            created_by=self.test_user["username"]
        )
        db_session.add(cot_item)
        db_session.commit()
        db_session.refresh(cot_item)
        
        candidates = [
            COTCandidate(
                cot_item_id=cot_item.id,
                text=f"Answer {i}",
                score=0.5 + i * 0.1,
                chosen=i == 0,
                rank=i + 1
            )
            for i in range(3)
        ]
        db_session.add_all(candidates)
        db_session.commit()
        
        response = client.get(
            f"/api/v1/cot-annotation/project/{project_id}/quality-metrics",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "average_score" in data
        assert "score_distribution" in data
        assert "chosen_distribution" in data
        assert data["average_score"] > 0
    
    def test_batch_update_cot_annotations(self, db_session):
        """测试批量更新CoT标注"""
        project_id = self.create_test_project(db_session)
        slice_id = self.create_test_slice(db_session, project_id)
        
        # 创建多个CoT标注
        cot_items = []
        for i in range(3):
            cot_item = COTItem(
                project_id=project_id,
                slice_id=slice_id,
                question=f"Question {i}?",
                source=COTSource.MANUAL,
                status=COTStatus.DRAFT,
                created_by=self.test_user["username"]
            )
            db_session.add(cot_item)
            db_session.commit()
            db_session.refresh(cot_item)
            
            # 添加候选答案以满足状态转换要求
            candidate = COTCandidate(
                cot_item_id=cot_item.id,
                text=f"Answer {i}",
                score=0.8,
                chosen=True,
                rank=1
            )
            db_session.add(candidate)
            cot_items.append(cot_item)
        
        db_session.commit()
        
        # 批量更新状态
        batch_data = {
            "cot_ids": [item.id for item in cot_items],
            "status": "reviewed"
        }
        
        response = client.post(
            "/api/v1/cot-annotation/batch-update",
            json=batch_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        for item in data:
            assert item["status"] == "reviewed"
    
    def test_delete_cot_annotation(self, db_session):
        """测试删除CoT标注"""
        project_id = self.create_test_project(db_session)
        slice_id = self.create_test_slice(db_session, project_id)
        
        # 创建CoT标注
        cot_item = COTItem(
            project_id=project_id,
            slice_id=slice_id,
            question="Test question?",
            source=COTSource.MANUAL,
            status=COTStatus.DRAFT,
            created_by=self.test_user["username"]
        )
        db_session.add(cot_item)
        db_session.commit()
        db_session.refresh(cot_item)
        
        response = client.delete(
            f"/api/v1/cot-annotation/{cot_item.id}",
            headers=self.headers
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # 验证已删除
        get_response = client.get(
            f"/api/v1/cot-annotation/{cot_item.id}",
            headers=self.headers
        )
        assert get_response.status_code == 404
    
    def test_unauthorized_access(self, db_session):
        """测试未授权访问"""
        # 不提供token
        response = client.get("/api/v1/cot-annotation/project/test-id")
        assert response.status_code == 401
        
        # 提供无效token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = client.get(
            "/api/v1/cot-annotation/project/test-id",
            headers=invalid_headers
        )
        assert response.status_code == 401
    
    def test_access_other_user_project(self, db_session):
        """测试访问其他用户的项目"""
        # 创建另一个用户的项目
        other_project = Project(
            name="Other Project",
            owner="other_user",
            description="Other user's project"
        )
        db_session.add(other_project)
        db_session.commit()
        
        response = client.get(
            f"/api/v1/cot-annotation/project/{other_project.id}",
            headers=self.headers
        )
        
        assert response.status_code == 403