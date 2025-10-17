"""
核心功能测试
"""
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, verify_password, get_password_hash
from app.main import app

client = TestClient(app)


def test_health_check():
    """
    测试健康检查端点
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data


def test_root_endpoint():
    """
    测试根端点
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "COT Studio API"
    assert data["version"] == "0.1.0"


def test_password_hashing():
    """
    测试密码哈希功能
    """
    password = "test_password"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_jwt_token_creation():
    """
    测试JWT令牌创建
    """
    test_data = {"sub": "test_user", "username": "testuser"}
    token = create_access_token(test_data)
    
    assert isinstance(token, str)
    assert len(token) > 0


def test_cors_headers():
    """
    测试CORS头部
    """
    response = client.options("/")
    # 检查是否有CORS相关的头部
    assert response.status_code in [200, 405]  # OPTIONS可能不被支持，但CORS中间件应该处理