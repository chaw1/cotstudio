"""
认证功能测试
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_success():
    """
    测试成功登录
    """
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "secret"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials():
    """
    测试无效凭据登录
    """
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong_password"}
    )
    assert response.status_code == 401


def test_protected_endpoint_without_token():
    """
    测试未携带令牌访问受保护端点
    """
    response = client.get("/api/v1/auth/test-protected")
    assert response.status_code == 401


def test_protected_endpoint_with_token():
    """
    测试携带有效令牌访问受保护端点
    """
    # 先登录获取令牌
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "secret"}
    )
    token = login_response.json()["access_token"]
    
    # 使用令牌访问受保护端点
    response = client.get(
        "/api/v1/auth/test-protected",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"] == "admin"


def test_get_current_user():
    """
    测试获取当前用户信息
    """
    # 先登录获取令牌
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "secret"}
    )
    token = login_response.json()["access_token"]
    
    # 获取用户信息
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert "admin" in data["roles"]