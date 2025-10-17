#!/usr/bin/env python3
"""
测试后端设置的简单脚本
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试所有重要模块的导入"""
    try:
        print("Testing imports...")
        
        # 测试核心模块
        from app.core.config import settings
        print("✓ Config imported")
        
        from app.core.database import engine, SessionLocal, get_db
        print("✓ Database imported")
        
        from app.core.security import create_access_token, verify_password
        print("✓ Security imported")
        
        from app.core.app_logging import logger
        print("✓ Logging imported")
        
        from app.core.exceptions import COTStudioException
        print("✓ Exceptions imported")
        
        from app.core.celery_app import celery_app
        print("✓ Celery imported")
        
        # 测试模型
        from app.models.base import Base
        print("✓ Base model imported")
        
        from app.models.user import User
        print("✓ User model imported")
        
        from app.models.project import Project
        print("✓ Project model imported")
        
        from app.models.file import File
        print("✓ File model imported")
        
        from app.models.slice import Slice
        print("✓ Slice model imported")
        
        from app.models.cot import COTItem, COTCandidate
        print("✓ CoT models imported")
        
        # 测试服务
        from app.services.user_service import user_service
        print("✓ User service imported")
        
        # 测试API
        from app.api.v1.auth import router as auth_router
        print("✓ Auth API imported")
        
        from app.api.v1.tasks import router as tasks_router
        print("✓ Tasks API imported")
        
        from app.api.v1.websocket import router as ws_router
        print("✓ WebSocket API imported")
        
        # 测试主应用
        from app.main import app
        print("✓ Main app imported")
        
        print("\n✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_models():
    """测试数据库模型创建"""
    try:
        print("\nTesting database models...")
        
        from app.models.base import Base
        from app.core.database import engine
        
        # 创建所有表（在内存中测试）
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Database model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fastapi_app():
    """测试FastAPI应用"""
    try:
        print("\nTesting FastAPI app...")
        
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # 测试根端点
        response = client.get("/")
        assert response.status_code == 200
        print("✓ Root endpoint works")
        
        # 测试健康检查
        response = client.get("/health")
        assert response.status_code == 200
        print("✓ Health check works")
        
        print("✅ FastAPI app test successful!")
        return True
        
    except Exception as e:
        print(f"❌ FastAPI app test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting COT Studio Backend Setup Test\n")
    
    success = True
    
    # 运行所有测试
    success &= test_imports()
    success &= test_database_models()
    success &= test_fastapi_app()
    
    if success:
        print("\n🎉 All tests passed! Backend setup is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please check the errors above.")
        sys.exit(1)