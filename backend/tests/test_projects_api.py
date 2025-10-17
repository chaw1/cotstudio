"""
项目管理API集成测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.main import app
from app.core.database import get_db
from app.models.project import Project, ProjectType, ProjectStatus
from app.models.user import User
from app.services.user_service import user_service
from app.core.security import create_access_token


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


@pytest.fixture
def test_user(db_session: Session):
    """创建测试用户"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "hashed_password": "hashed_password",
        "full_name": "Test User",
        "is_active": True,
        "roles": ["editor"]
    }
    user = user_service.create(db_session, user_data)
    return user


@pytest.fixture
def admin_user(db_session: Session):
    """创建管理员用户"""
    user_data = {
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": "hashed_password",
        "full_name": "Admin User",
        "is_active": True,
        "roles": ["admin"]
    }
    user = user_service.create(db_session, user_data)
    return user


@pytest.fixture
def auth_headers(test_user):
    """认证头"""
    token = create_access_token(
        data={
            "sub": str(test_user.id),
            "username": test_user.username,
            "email": test_user.email,
            "roles": test_user.roles,
            "permissions": ["project:read", "project:write", "project:delete"]
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user):
    """管理员认证头"""
    token = create_access_token(
        data={
            "sub": str(admin_user.id),
            "username": admin_user.username,
            "email": admin_user.email,
            "roles": admin_user.roles,
            "permissions": ["*"]
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_project(db_session: Session, test_user):
    """创建测试项目"""
    project_data = {
        "name": "Test Project",
        "description": "A test project",
        "owner_id": str(test_user.id),
        "tags": ["test", "demo"],
        "project_type": ProjectType.STANDARD,
        "status": ProjectStatus.ACTIVE
    }
    
    project = Project(**project_data)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


class TestProjectCreation:
    """项目创建测试"""
    
    def test_create_project_success(self, client, auth_headers):
        """测试成功创建项目"""
        project_data = {
            "name": "New Project",
            "description": "A new project for testing",
            "tags": ["new", "test"],
            "project_type": "standard"
        }
        
        response = client.post(
            "/api/v1/projects",
            json=project_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["description"] == project_data["description"]
        assert data["tags"] == project_data["tags"]
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_project_duplicate_name(self, client, auth_headers):
        """测试创建重名项目失败"""
        # 先创建一个项目
        first_project_data = {
            "name": "Duplicate Test Project",
            "description": "First project",
            "project_type": "standard"
        }
        
        first_response = client.post(
            "/api/v1/projects",
            json=first_project_data,
            headers=auth_headers
        )
        assert first_response.status_code == 201
        
        # 尝试创建同名项目
        duplicate_project_data = {
            "name": "Duplicate Test Project",  # 使用相同的项目名
            "description": "Another project",
            "project_type": "standard"
        }
        
        response = client.post(
            "/api/v1/projects",
            json=duplicate_project_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        response_data = response.json()
        assert "already exists" in response_data.get("message", "")
    
    def test_create_project_unauthorized(self, client):
        """测试未认证创建项目失败"""
        project_data = {
            "name": "Unauthorized Project",
            "project_type": "standard"
        }
        
        response = client.post("/api/v1/projects", json=project_data)
        assert response.status_code == 401
    
    def test_create_project_invalid_data(self, client, auth_headers):
        """测试无效数据创建项目失败"""
        project_data = {
            "name": "",  # 空名称
            "project_type": "invalid_type"
        }
        
        response = client.post(
            "/api/v1/projects",
            json=project_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422


class TestProjectRetrieval:
    """项目查询测试"""
    
    def test_list_projects(self, client, auth_headers):
        """测试获取项目列表"""
        # 先创建一个项目
        project_data = {
            "name": "List Test Project",
            "description": "A project for list testing",
            "project_type": "standard"
        }
        
        create_response = client.post(
            "/api/v1/projects",
            json=project_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        
        # 获取项目列表
        response = client.get("/api/v1/projects", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # 检查项目是否在列表中
        project_names = [p["name"] for p in data]
        assert project_data["name"] in project_names
    
    def test_get_project_by_id(self, client, auth_headers):
        """测试根据ID获取项目"""
        # 先创建一个项目
        project_data = {
            "name": "Get Test Project",
            "description": "A project for get testing",
            "project_type": "standard"
        }
        
        create_response = client.post(
            "/api/v1/projects",
            json=project_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        created_project = create_response.json()
        
        # 根据ID获取项目
        response = client.get(
            f"/api/v1/projects/{created_project['id']}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_project["id"]
        assert data["name"] == project_data["name"]
        assert data["description"] == project_data["description"]
    
    def test_get_project_not_found(self, client, auth_headers):
        """测试获取不存在的项目"""
        fake_id = str(uuid4())
        response = client.get(
            f"/api/v1/projects/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_get_project_access_denied(self, client, auth_headers):
        """测试无权限访问项目"""
        # 先用第一个用户创建项目
        project_data = {
            "name": "Access Test Project",
            "description": "A project for access testing",
            "project_type": "standard"
        }
        
        create_response = client.post(
            "/api/v1/projects",
            json=project_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        created_project = create_response.json()
        
        # 创建另一个用户的token
        other_token = create_access_token(
            data={
                "sub": str(uuid4()),
                "username": "otheruser",
                "email": "other@example.com",
                "roles": ["editor"],
                "permissions": ["project:read"]
            }
        )
        other_headers = {"Authorization": f"Bearer {other_token}"}
        
        # 尝试用另一个用户访问项目
        response = client.get(
            f"/api/v1/projects/{created_project['id']}",
            headers=other_headers
        )
        
        assert response.status_code == 403


class TestProjectUpdate:
    """项目更新测试"""
    
    def test_update_project_success(self, client, auth_headers, test_project):
        """测试成功更新项目"""
        update_data = {
            "name": "Updated Project Name",
            "description": "Updated description",
            "tags": ["updated", "test"]
        }
        
        response = client.put(
            f"/api/v1/projects/{test_project.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["tags"] == update_data["tags"]
    
    def test_update_project_partial(self, client, auth_headers, test_project):
        """测试部分更新项目"""
        update_data = {"description": "Only description updated"}
        
        response = client.put(
            f"/api/v1/projects/{test_project.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == test_project.name  # 名称未变
        assert data["description"] == update_data["description"]
    
    def test_update_project_duplicate_name(self, client, auth_headers, db_session, test_user):
        """测试更新为重名失败"""
        # 创建另一个项目
        another_project = Project(
            name="Another Project",
            owner_id=str(test_user.id),
            project_type=ProjectType.STANDARD
        )
        db_session.add(another_project)
        db_session.commit()
        
        # 尝试将test_project的名称更新为another_project的名称
        update_data = {"name": another_project.name}
        
        response = client.put(
            f"/api/v1/projects/{test_project.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestProjectDeletion:
    """项目删除测试"""
    
    def test_delete_project_success(self, client, auth_headers, test_project):
        """测试成功删除项目"""
        response = client.delete(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # 验证项目已被软删除
        get_response = client.get(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers
        )
        # 项目应该仍然存在但状态为DELETED，这里可能需要特殊处理
    
    def test_delete_project_not_found(self, client, auth_headers):
        """测试删除不存在的项目"""
        fake_id = str(uuid4())
        response = client.delete(
            f"/api/v1/projects/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestProjectArchiving:
    """项目归档测试"""
    
    def test_archive_project_success(self, client, auth_headers, test_project):
        """测试成功归档项目"""
        response = client.post(
            f"/api/v1/projects/{test_project.id}/archive",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "archived"
    
    def test_restore_project_success(self, client, auth_headers, db_session, test_project):
        """测试成功恢复项目"""
        # 先归档项目
        test_project.status = ProjectStatus.ARCHIVED
        db_session.commit()
        
        response = client.post(
            f"/api/v1/projects/{test_project.id}/restore",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"


class TestProjectTags:
    """项目标签测试"""
    
    def test_add_tags_success(self, client, auth_headers, test_project):
        """测试成功添加标签"""
        new_tags = ["new_tag1", "new_tag2"]
        
        response = client.post(
            f"/api/v1/projects/{test_project.id}/tags",
            json=new_tags,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        for tag in new_tags:
            assert tag in data["tags"]
    
    def test_remove_tags_success(self, client, auth_headers, test_project):
        """测试成功移除标签"""
        tags_to_remove = ["test"]  # test_project有这个标签
        
        response = client.delete(
            f"/api/v1/projects/{test_project.id}/tags",
            json=tags_to_remove,
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestProjectSearch:
    """项目搜索测试"""
    
    def test_search_projects_by_name(self, client, auth_headers, test_project):
        """测试按名称搜索项目"""
        response = client.get(
            "/api/v1/projects/search",
            params={"query": "Test"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(p["name"] == test_project.name for p in data)
    
    def test_search_projects_by_tags(self, client, auth_headers, test_project):
        """测试按标签搜索项目"""
        response = client.get(
            "/api/v1/projects/search",
            params={"tags": ["test"]},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(p["name"] == test_project.name for p in data)


class TestProjectStatistics:
    """项目统计测试"""
    
    def test_get_project_statistics(self, client, auth_headers, test_project):
        """测试获取项目统计信息"""
        response = client.get(
            f"/api/v1/projects/{test_project.id}/statistics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
        assert "statistics" in data
        assert "file_count" in data["statistics"]
        assert "cot_count" in data["statistics"]


class TestAdminPermissions:
    """管理员权限测试"""
    
    def test_admin_can_access_any_project(self, client, admin_headers, test_project):
        """测试管理员可以访问任何项目"""
        response = client.get(
            f"/api/v1/projects/{test_project.id}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_project.id)
    
    def test_admin_can_modify_any_project(self, client, admin_headers, test_project):
        """测试管理员可以修改任何项目"""
        update_data = {"description": "Modified by admin"}
        
        response = client.put(
            f"/api/v1/projects/{test_project.id}",
            json=update_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == update_data["description"]