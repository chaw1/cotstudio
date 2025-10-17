#!/usr/bin/env python3
"""
测试数据库模型的简单脚本
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.user import User
from app.models.project import Project, ProjectType, ProjectStatus
from app.models.file import File, OCRStatus
from app.models.slice import Slice, SliceType
from app.models.cot import COTItem, COTCandidate, COTSource, COTStatus


def test_database_models():
    """测试数据库模型"""
    print("🧪 Testing database models...")
    
    # 创建内存数据库
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    # 创建所有表
    Base.metadata.create_all(engine)
    print("✓ Database tables created")
    
    # 创建会话
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # 测试创建用户
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123",
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            roles=["user"]
        )
        session.add(user)
        session.flush()
        print("✓ User created successfully")
        
        # 测试创建项目
        project = Project(
            name="Test Project",
            owner_id=user.id,
            description="A test project",
            tags=["test", "demo"],
            project_type=ProjectType.RESEARCH,
            status=ProjectStatus.ACTIVE
        )
        session.add(project)
        session.flush()
        print("✓ Project created successfully")
        
        # 测试创建文件
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
        session.add(file)
        session.flush()
        print("✓ File created successfully")
        
        # 测试创建切片
        slice_obj = Slice(
            file_id=file.id,
            content="This is a test paragraph from the document.",
            start_offset=100,
            end_offset=150,
            slice_type=SliceType.PARAGRAPH,
            page_number=1,
            sequence_number=1
        )
        session.add(slice_obj)
        session.flush()
        print("✓ Slice created successfully")
        
        # 测试创建CoT项目
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
        session.add(cot_item)
        session.flush()
        print("✓ CoT item created successfully")
        
        # 测试创建CoT候选答案
        candidate = COTCandidate(
            cot_item_id=cot_item.id,
            text="This is a candidate answer.",
            chain_of_thought="Step 1: Analyze... Step 2: Conclude...",
            score=0.85,
            chosen=True,
            rank=1
        )
        session.add(candidate)
        session.commit()
        print("✓ CoT candidate created successfully")
        
        # 测试关系
        assert user.projects[0].name == "Test Project"
        assert project.files[0].filename == "test_document.pdf"
        assert file.slices[0].content == "This is a test paragraph from the document."
        assert slice_obj.cot_items[0].question == "What is the main topic of this text?"
        assert cot_item.candidates[0].text == "This is a candidate answer."
        print("✓ All relationships work correctly")
        
        # 测试查询
        projects = session.query(Project).filter(Project.owner_id == user.id).all()
        assert len(projects) == 1
        assert projects[0].name == "Test Project"
        print("✓ Queries work correctly")
        
        print("\n🎉 All database model tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()


def test_model_enums():
    """测试模型枚举"""
    print("\n🧪 Testing model enums...")
    
    # 测试项目类型枚举
    assert ProjectType.STANDARD.value == "standard"
    assert ProjectType.RESEARCH.value == "research"
    assert ProjectType.COMMERCIAL.value == "commercial"
    print("✓ ProjectType enum works")
    
    # 测试项目状态枚举
    assert ProjectStatus.ACTIVE.value == "active"
    assert ProjectStatus.ARCHIVED.value == "archived"
    assert ProjectStatus.DELETED.value == "deleted"
    print("✓ ProjectStatus enum works")
    
    # 测试OCR状态枚举
    assert OCRStatus.PENDING.value == "pending"
    assert OCRStatus.PROCESSING.value == "processing"
    assert OCRStatus.COMPLETED.value == "completed"
    assert OCRStatus.FAILED.value == "failed"
    print("✓ OCRStatus enum works")
    
    # 测试切片类型枚举
    assert SliceType.PARAGRAPH.value == "paragraph"
    assert SliceType.IMAGE.value == "image"
    assert SliceType.TABLE.value == "table"
    assert SliceType.HEADER.value == "header"
    assert SliceType.FOOTER.value == "footer"
    print("✓ SliceType enum works")
    
    # 测试CoT来源枚举
    assert COTSource.MANUAL.value == "manual"
    assert COTSource.HUMAN_AI.value == "human_ai"
    assert COTSource.GENERALIZATION.value == "generalization"
    print("✓ COTSource enum works")
    
    # 测试CoT状态枚举
    assert COTStatus.DRAFT.value == "draft"
    assert COTStatus.REVIEWED.value == "reviewed"
    assert COTStatus.APPROVED.value == "approved"
    assert COTStatus.REJECTED.value == "rejected"
    print("✓ COTStatus enum works")
    
    print("✓ All enum tests passed!")
    return True


if __name__ == "__main__":
    print("🚀 Starting Database Models Test\n")
    
    success = True
    
    # 运行所有测试
    success &= test_model_enums()
    success &= test_database_models()
    
    if success:
        print("\n🎉 All database model tests passed! Models are working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please check the errors above.")
        sys.exit(1)