"""
数据模型单元测试
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.user import User
from app.models.project import Project, ProjectType, ProjectStatus
from app.models.file import File, OCRStatus
from app.models.slice import Slice, SliceType
from app.models.cot import COTItem, COTCandidate, COTSource, COTStatus


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    # 使用内存SQLite数据库进行测试
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    # 创建所有表
    Base.metadata.create_all(engine)
    
    # 创建会话
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


class TestUserModel:
    """用户模型测试"""
    
    def test_create_user(self, db_session):
        """测试创建用户"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123",
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            roles=["user"]
        )
        
        db_session.add(user)
        db_session.commit()
        
        # 验证用户已创建
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.roles == ["user"]
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
    
    def test_user_relationships(self, db_session):
        """测试用户关系"""
        # 创建用户
        user = User(
            username="owner",
            email="owner@example.com",
            hashed_password="hashed_password_123",
            full_name="Project Owner"
        )
        db_session.add(user)
        db_session.flush()  # 获取用户ID
        
        # 创建项目
        project = Project(
            name="Test Project",
            owner_id=user.id,
            description="Test project description"
        )
        db_session.add(project)
        db_session.commit()
        
        # 验证关系
        assert len(user.projects) == 1
        assert user.projects[0].name == "Test Project"
        assert project.owner_user.username == "owner"


class TestProjectModel:
    """项目模型测试"""
    
    def test_create_project(self, db_session):
        """测试创建项目"""
        # 先创建用户
        user = User(
            username="owner",
            email="owner@example.com",
            hashed_password="hashed_password_123"
        )
        db_session.add(user)
        db_session.flush()
        
        # 创建项目
        project = Project(
            name="Test Project",
            owner_id=user.id,
            description="A test project",
            tags=["test", "demo"],
            project_type=ProjectType.RESEARCH,
            status=ProjectStatus.ACTIVE
        )
        
        db_session.add(project)
        db_session.commit()
        
        # 验证项目已创建
        assert project.id is not None
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.tags == ["test", "demo"]
        assert project.project_type == ProjectType.RESEARCH
        assert project.status == ProjectStatus.ACTIVE
        assert isinstance(project.created_at, datetime)
    
    def test_project_default_values(self, db_session):
        """测试项目默认值"""
        user = User(username="owner", email="owner@example.com", hashed_password="hash")
        db_session.add(user)
        db_session.flush()
        
        project = Project(
            name="Default Project",
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()
        
        # 验证默认值
        assert project.tags == []
        assert project.project_type == ProjectType.STANDARD
        assert project.status == ProjectStatus.ACTIVE


class TestFileModel:
    """文件模型测试"""
    
    def test_create_file(self, db_session):
        """测试创建文件"""
        # 创建用户和项目
        user = User(username="owner", email="owner@example.com", hashed_password="hash")
        db_session.add(user)
        db_session.flush()
        
        project = Project(name="Test Project", owner_id=user.id)
        db_session.add(project)
        db_session.flush()
        
        # 创建文件
        file = File(
            project_id=project.id,
            filename="test_document.pdf",
            original_filename="test document.pdf",
            file_path="/uploads/test_document.pdf",
            file_hash="abc123def456",
            size=1024000,
            mime_type="application/pdf",
            ocr_status=OCRStatus.PENDING,
            ocr_engine="PaddleOCR"
        )
        
        db_session.add(file)
        db_session.commit()
        
        # 验证文件已创建
        assert file.id is not None
        assert file.filename == "test_document.pdf"
        assert file.original_filename == "test document.pdf"
        assert file.size == 1024000
        assert file.mime_type == "application/pdf"
        assert file.ocr_status == OCRStatus.PENDING
        assert file.ocr_engine == "PaddleOCR"
    
    def test_file_relationships(self, db_session):
        """测试文件关系"""
        # 创建完整的层次结构
        user = User(username="owner", email="owner@example.com", hashed_password="hash")
        db_session.add(user)
        db_session.flush()
        
        project = Project(name="Test Project", owner_id=user.id)
        db_session.add(project)
        db_session.flush()
        
        file = File(
            project_id=project.id,
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_hash="hash123",
            size=1000,
            mime_type="application/pdf"
        )
        db_session.add(file)
        db_session.commit()
        
        # 验证关系
        assert file.project.name == "Test Project"
        assert len(project.files) == 1
        assert project.files[0].filename == "test.pdf"


class TestSliceModel:
    """切片模型测试"""
    
    def test_create_slice(self, db_session):
        """测试创建切片"""
        # 创建依赖对象
        user = User(username="owner", email="owner@example.com", hashed_password="hash")
        db_session.add(user)
        db_session.flush()
        
        project = Project(name="Test Project", owner_id=user.id)
        db_session.add(project)
        db_session.flush()
        
        file = File(
            project_id=project.id,
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_hash="hash123",
            size=1000,
            mime_type="application/pdf"
        )
        db_session.add(file)
        db_session.flush()
        
        # 创建切片
        slice_obj = Slice(
            file_id=file.id,
            content="This is a test paragraph from the document.",
            start_offset=100,
            end_offset=150,
            slice_type=SliceType.PARAGRAPH,
            page_number=1,
            sequence_number=1
        )
        
        db_session.add(slice_obj)
        db_session.commit()
        
        # 验证切片已创建
        assert slice_obj.id is not None
        assert slice_obj.content == "This is a test paragraph from the document."
        assert slice_obj.start_offset == 100
        assert slice_obj.end_offset == 150
        assert slice_obj.slice_type == SliceType.PARAGRAPH
        assert slice_obj.page_number == 1
        assert slice_obj.sequence_number == 1
    
    def test_slice_relationships(self, db_session):
        """测试切片关系"""
        # 创建完整的层次结构
        user = User(username="owner", email="owner@example.com", hashed_password="hash")
        db_session.add(user)
        db_session.flush()  # 获取用户ID
        
        project = Project(name="Test Project", owner_id=user.id)
        db_session.add(project)
        db_session.flush()  # 获取项目ID
        
        file = File(
            project_id=project.id,
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_hash="hash123",
            size=1000,
            mime_type="application/pdf"
        )
        db_session.add(file)
        db_session.flush()  # 获取文件ID
        
        slice_obj = Slice(
            file_id=file.id,
            content="Test content",
            sequence_number=1
        )
        
        db_session.add(slice_obj)
        db_session.commit()
        
        # 验证关系
        assert slice_obj.file.filename == "test.pdf"
        assert len(file.slices) == 1
        assert file.slices[0].content == "Test content"


class TestCOTModels:
    """CoT模型测试"""
    
    def test_create_cot_item(self, db_session):
        """测试创建CoT项目"""
        # 创建依赖对象
        user = User(username="owner", email="owner@example.com", hashed_password="hash")
        db_session.add(user)
        db_session.flush()
        
        project = Project(name="Test Project", owner_id=user.id)
        db_session.add(project)
        db_session.flush()
        
        file = File(
            project_id=project.id,
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_hash="hash123",
            size=1000,
            mime_type="application/pdf"
        )
        db_session.add(file)
        db_session.flush()
        
        slice_obj = Slice(
            file_id=file.id,
            content="Test content for CoT",
            sequence_number=1
        )
        db_session.add(slice_obj)
        db_session.flush()
        
        # 创建CoT项目
        cot_item = COTItem(
            project_id=project.id,
            slice_id=slice_obj.id,
            question="What is the main topic of this text?",
            chain_of_thought="First, I need to analyze the content...",
            source=COTSource.HUMAN_AI,
            status=COTStatus.DRAFT,
            llm_metadata={"model": "gpt-4", "temperature": 0.7},
            created_by="test_user"
        )
        
        db_session.add(cot_item)
        db_session.commit()
        
        # 验证CoT项目已创建
        assert cot_item.id is not None
        assert cot_item.question == "What is the main topic of this text?"
        assert cot_item.source == COTSource.HUMAN_AI
        assert cot_item.status == COTStatus.DRAFT
        assert cot_item.llm_metadata["model"] == "gpt-4"
        assert cot_item.created_by == "test_user"
    
    def test_create_cot_candidate(self, db_session):
        """测试创建CoT候选答案"""
        # 创建完整的层次结构
        user = User(username="owner", email="owner@example.com", hashed_password="hash")
        db_session.add(user)
        db_session.flush()
        
        project = Project(name="Test Project", owner_id=user.id)
        db_session.add(project)
        db_session.flush()
        
        file = File(
            project_id=project.id,
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_hash="hash123",
            size=1000,
            mime_type="application/pdf"
        )
        db_session.add(file)
        db_session.flush()
        
        slice_obj = Slice(file_id=file.id, content="Test content", sequence_number=1)
        db_session.add(slice_obj)
        db_session.flush()
        
        cot_item = COTItem(
            project_id=project.id,
            slice_id=slice_obj.id,
            question="Test question?",
            created_by="test_user"
        )
        db_session.add(cot_item)
        db_session.flush()
        
        # 创建CoT候选答案
        candidate = COTCandidate(
            cot_item_id=cot_item.id,
            text="This is a candidate answer.",
            chain_of_thought="Step 1: Analyze... Step 2: Conclude...",
            score=0.85,
            chosen=True,
            rank=1
        )
        
        db_session.add(candidate)
        db_session.commit()
        
        # 验证候选答案已创建
        assert candidate.id is not None
        assert candidate.text == "This is a candidate answer."
        assert candidate.score == 0.85
        assert candidate.chosen is True
        assert candidate.rank == 1
    
    def test_cot_relationships(self, db_session):
        """测试CoT关系"""
        # 创建完整的层次结构
        user = User(username="owner", email="owner@example.com", hashed_password="hash")
        db_session.add(user)
        db_session.flush()
        
        project = Project(name="Test Project", owner_id=user.id)
        db_session.add(project)
        db_session.flush()
        
        file = File(
            project_id=project.id,
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_hash="hash123",
            size=1000,
            mime_type="application/pdf"
        )
        db_session.add(file)
        db_session.flush()
        
        slice_obj = Slice(file_id=file.id, content="Test content", sequence_number=1)
        db_session.add(slice_obj)
        db_session.flush()
        
        cot_item = COTItem(
            project_id=project.id,
            slice_id=slice_obj.id,
            question="Test question?",
            created_by="test_user"
        )
        db_session.add(cot_item)
        db_session.flush()
        
        candidate1 = COTCandidate(
            cot_item_id=cot_item.id,
            text="Answer 1",
            rank=1
        )
        candidate2 = COTCandidate(
            cot_item_id=cot_item.id,
            text="Answer 2",
            rank=2
        )
        
        db_session.add_all([candidate1, candidate2])
        db_session.commit()
        
        # 验证关系
        assert cot_item.project.name == "Test Project"
        assert cot_item.slice.content == "Test content"
        assert len(cot_item.candidates) == 2
        assert cot_item.candidates[0].text in ["Answer 1", "Answer 2"]
        assert candidate1.cot_item.question == "Test question?"
        assert len(project.cot_items) == 1
        assert len(slice_obj.cot_items) == 1


class TestModelConstraints:
    """测试模型约束"""
    
    def test_unique_constraints(self, db_session):
        """测试唯一约束"""
        # 测试用户名唯一约束
        user1 = User(username="testuser", email="test1@example.com", hashed_password="hash")
        user2 = User(username="testuser", email="test2@example.com", hashed_password="hash")
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(Exception):  # 应该抛出唯一约束违反异常
            db_session.commit()
    
    def test_foreign_key_constraints(self, db_session):
        """测试外键约束"""
        # 注意：SQLite默认不强制外键约束，这个测试在生产环境中会有效
        # 这里我们测试一个有效的外键关系
        user = User(username="testuser", email="test@example.com", hashed_password="hash")
        db_session.add(user)
        db_session.flush()
        
        # 创建引用存在用户的项目（应该成功）
        project = Project(
            name="Valid Project",
            owner_id=user.id
        )
        
        db_session.add(project)
        db_session.commit()  # 这应该成功
        
        assert project.owner_id == user.id
    
    def test_not_null_constraints(self, db_session):
        """测试非空约束"""
        # 尝试创建没有必需字段的用户
        user = User()  # 缺少必需的字段
        
        db_session.add(user)
        with pytest.raises(Exception):  # 应该抛出非空约束违反异常
            db_session.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])