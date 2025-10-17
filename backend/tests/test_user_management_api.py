"""
用户管理API集成测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.permission import UserProjectPermission, ProjectPermission
from app.models.project import Project
from app.core.security import get_password_hash, create_access_token
from tests.conftest import TestingSessionLocal


client = TestClient(app)


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def super_admin_user(db_session: Session):
    """创建超级管理员用户"""
    user = User(
        username="superadmin",
        email="superadmin@test.com",
        hashed_password=get_password_hash("password123"),
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        is_superuser=True,
        login_count=0
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session: Session):
    """创建管理员用户"""
    user = User(
        username="admin",
        email="admin@test.com",
        hashed_password=get_password_hash("password123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        is_superuser=False,
        login_count=0
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session: Session):
    """创建普通用户"""
    user = User(
        username="user",
        email="user@test.com",
        hashed_password=get_password_hash("password123"),
        full_name="Regular User",
        role=UserRole.USER,
        is_active=True,
        is_superuser=False,
        login_count=0
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_project(db_session: Session, regular_user: User):
    """创建测试项目"""
    project = Project(
        name="Test Project",
        description="A test project",
        owner_id=str(regular_user.id),
        tags=["test"],
        project_type="annotation",
        status="active"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def get_auth_headers(user: User) -> dict:
    """获取认证头"""
    token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "roles": [user.role.value],
            "permissions": []
        }
    )
    return {"Authorization": f"Bearer {token}"}


class TestUserManagementAPI:
    """用户管理API测试"""
    
    def test_create_user_success(self, db_session: Session, admin_user: User):
        """测试成功创建用户"""
        headers = get_auth_headers(admin_user)
        user_data = {
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "password123",
            "full_name": "New User",
            "role": "user",
            "department": "IT",
            "is_active": True
        }
        
        response = client.post("/api/v1/user-management/users", json=user_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "user"
        assert data["department"] == "IT"
        assert data["is_active"] is True
    
    def test_create_user_duplicate_username(self, db_session: Session, admin_user: User, regular_user: User):
        """测试创建重复用户名的用户"""
        headers = get_auth_headers(admin_user)
        user_data = {
            "username": regular_user.username,  # 使用已存在的用户名
            "email": "different@test.com",
            "password": "password123",
            "role": "user"
        }
        
        response = client.post("/api/v1/user-management/users", json=user_data, headers=headers)
        
        assert response.status_code == 400
        assert "用户名已存在" in response.json()["detail"]
    
    def test_create_admin_user_requires_super_admin(self, db_session: Session, admin_user: User):
        """测试创建管理员用户需要超级管理员权限"""
        headers = get_auth_headers(admin_user)
        user_data = {
            "username": "newadmin",
            "email": "newadmin@test.com",
            "password": "password123",
            "role": "admin"
        }
        
        response = client.post("/api/v1/user-management/users", json=user_data, headers=headers)
        
        assert response.status_code == 403
        assert "只有超级管理员可以创建管理员用户" in response.json()["detail"]
    
    def test_list_users(self, db_session: Session, admin_user: User, regular_user: User):
        """测试获取用户列表"""
        headers = get_auth_headers(admin_user)
        
        response = client.get("/api/v1/user-management/users", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert data["total"] >= 2  # 至少有admin_user和regular_user
    
    def test_list_users_with_search(self, db_session: Session, admin_user: User, regular_user: User):
        """测试搜索用户"""
        headers = get_auth_headers(admin_user)
        
        response = client.get(
            "/api/v1/user-management/users",
            params={"search": regular_user.username},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) >= 1
        assert any(user["username"] == regular_user.username for user in data["users"])
    
    def test_get_user(self, db_session: Session, admin_user: User, regular_user: User):
        """测试获取用户详情"""
        headers = get_auth_headers(admin_user)
        
        response = client.get(f"/api/v1/user-management/users/{regular_user.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == regular_user.username
        assert data["email"] == regular_user.email
    
    def test_update_user(self, db_session: Session, admin_user: User, regular_user: User):
        """测试更新用户"""
        headers = get_auth_headers(admin_user)
        update_data = {
            "full_name": "Updated Name",
            "department": "HR"
        }
        
        response = client.put(
            f"/api/v1/user-management/users/{regular_user.id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["department"] == "HR"
    
    def test_delete_user(self, db_session: Session, super_admin_user: User, regular_user: User):
        """测试删除用户"""
        headers = get_auth_headers(super_admin_user)
        
        response = client.delete(f"/api/v1/user-management/users/{regular_user.id}", headers=headers)
        
        assert response.status_code == 200
        assert "用户删除成功" in response.json()["message"]
    
    def test_delete_self_forbidden(self, db_session: Session, super_admin_user: User):
        """测试不能删除自己"""
        headers = get_auth_headers(super_admin_user)
        
        response = client.delete(f"/api/v1/user-management/users/{super_admin_user.id}", headers=headers)
        
        assert response.status_code == 400
        assert "不能删除自己" in response.json()["detail"]
    
    def test_get_user_stats(self, db_session: Session, admin_user: User):
        """测试获取用户统计"""
        headers = get_auth_headers(admin_user)
        
        response = client.get("/api/v1/user-management/users/stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "inactive_users" in data
        assert "users_by_role" in data
        assert "users_by_department" in data
        assert "recent_logins" in data


class TestPermissionManagementAPI:
    """权限管理API测试"""
    
    def test_grant_permission(self, db_session: Session, admin_user: User, regular_user: User, test_project: Project):
        """测试授予权限"""
        headers = get_auth_headers(admin_user)
        permission_data = {
            "user_id": str(regular_user.id),
            "project_id": str(test_project.id),
            "permissions": ["view", "edit"]
        }
        
        response = client.post("/api/v1/user-management/permissions/grant", json=permission_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == str(regular_user.id)
        assert data["project_id"] == str(test_project.id)
        assert "view" in data["permissions"]
        assert "edit" in data["permissions"]
    
    def test_revoke_permission(self, db_session: Session, admin_user: User, regular_user: User, test_project: Project):
        """测试撤销权限"""
        # 先授予权限
        permission = UserProjectPermission(
            user_id=str(regular_user.id),
            project_id=str(test_project.id),
            permissions=["view", "edit"],
            granted_by=str(admin_user.id)
        )
        db_session.add(permission)
        db_session.commit()
        
        headers = get_auth_headers(admin_user)
        revoke_data = {
            "user_id": str(regular_user.id),
            "project_id": str(test_project.id),
            "permissions": ["edit"]
        }
        
        response = client.delete("/api/v1/user-management/permissions/revoke", json=revoke_data, headers=headers)
        
        assert response.status_code == 200
        assert "权限撤销成功" in response.json()["message"]
    
    def test_get_user_permissions(self, db_session: Session, admin_user: User, regular_user: User, test_project: Project):
        """测试获取用户权限"""
        # 先授予权限
        permission = UserProjectPermission(
            user_id=str(regular_user.id),
            project_id=str(test_project.id),
            permissions=["view"],
            granted_by=str(admin_user.id)
        )
        db_session.add(permission)
        db_session.commit()
        
        headers = get_auth_headers(admin_user)
        
        response = client.get(f"/api/v1/user-management/permissions/users/{regular_user.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == regular_user.username
        assert len(data["project_permissions"]) >= 1
    
    def test_get_project_permissions(self, db_session: Session, admin_user: User, regular_user: User, test_project: Project):
        """测试获取项目权限"""
        # 先授予权限
        permission = UserProjectPermission(
            user_id=str(regular_user.id),
            project_id=str(test_project.id),
            permissions=["view"],
            granted_by=str(admin_user.id)
        )
        db_session.add(permission)
        db_session.commit()
        
        headers = get_auth_headers(admin_user)
        
        response = client.get(f"/api/v1/user-management/permissions/projects/{test_project.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == str(test_project.id)
        assert data["project_name"] == test_project.name
        assert len(data["permissions"]) >= 1
    
    def test_list_permissions(self, db_session: Session, admin_user: User, regular_user: User, test_project: Project):
        """测试获取权限列表"""
        # 先授予权限
        permission = UserProjectPermission(
            user_id=str(regular_user.id),
            project_id=str(test_project.id),
            permissions=["view"],
            granted_by=str(admin_user.id)
        )
        db_session.add(permission)
        db_session.commit()
        
        headers = get_auth_headers(admin_user)
        
        response = client.get("/api/v1/user-management/permissions", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "permissions" in data
        assert "total" in data
        assert len(data["permissions"]) >= 1


class TestAuthorizationRequirements:
    """权限要求测试"""
    
    def test_regular_user_cannot_access_user_management(self, db_session: Session, regular_user: User):
        """测试普通用户不能访问用户管理功能"""
        headers = get_auth_headers(regular_user)
        
        response = client.get("/api/v1/user-management/users", headers=headers)
        
        assert response.status_code == 403
        assert "需要管理员权限" in response.json()["detail"]
    
    def test_unauthenticated_access_forbidden(self, db_session: Session):
        """测试未认证访问被禁止"""
        response = client.get("/api/v1/user-management/users")
        
        assert response.status_code == 401
    
    def test_admin_cannot_delete_users(self, db_session: Session, admin_user: User, regular_user: User):
        """测试管理员不能删除用户（需要超级管理员权限）"""
        headers = get_auth_headers(admin_user)
        
        response = client.delete(f"/api/v1/user-management/users/{regular_user.id}", headers=headers)
        
        assert response.status_code == 403
        assert "需要超级管理员权限" in response.json()["detail"]