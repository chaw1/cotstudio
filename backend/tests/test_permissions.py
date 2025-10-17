"""
权限检查系统测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.orm import Session

from app.core.permissions import (
    PermissionChecker, 
    PermissionError, 
    ResourceNotFoundError,
    require_permission,
    require_admin,
    require_super_admin
)
from app.models.user import User, UserRole
from app.models.permission import ProjectPermission, UserProjectPermission
from app.models.project import Project


class TestPermissionChecker:
    """权限检查器测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def super_admin_user(self):
        """超级管理员用户"""
        user = MagicMock(spec=User)
        user.id = "super_admin_id"
        user.role = UserRole.SUPER_ADMIN
        return user
    
    @pytest.fixture
    def admin_user(self):
        """管理员用户"""
        user = MagicMock(spec=User)
        user.id = "admin_id"
        user.role = UserRole.ADMIN
        return user
    
    @pytest.fixture
    def regular_user(self):
        """普通用户"""
        user = MagicMock(spec=User)
        user.id = "user_id"
        user.role = UserRole.USER
        return user
    
    @pytest.fixture
    def project(self):
        """项目"""
        project = MagicMock(spec=Project)
        project.id = "project_id"
        project.owner_id = "owner_id"
        return project
    
    @pytest.fixture
    def user_permission(self):
        """用户项目权限"""
        permission = MagicMock(spec=UserProjectPermission)
        permission.user_id = "user_id"
        permission.project_id = "project_id"
        permission.permissions = [ProjectPermission.VIEW.value, ProjectPermission.EDIT.value]
        return permission
    
    @pytest.mark.asyncio
    async def test_super_admin_has_all_permissions(self, super_admin_user, mock_db):
        """测试超级管理员拥有所有权限"""
        result = await PermissionChecker.check_project_permission(
            super_admin_user, "any_project_id", ProjectPermission.ADMIN, mock_db
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_project_owner_has_all_permissions(self, regular_user, project, mock_db):
        """测试项目所有者拥有所有权限"""
        # 设置用户为项目所有者
        regular_user.id = project.owner_id
        
        # 模拟数据库查询返回项目
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = project
        mock_db.execute.return_value = mock_result
        
        result = await PermissionChecker.check_project_permission(
            regular_user, project.id, ProjectPermission.ADMIN, mock_db
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_user_with_specific_permission(self, regular_user, project, user_permission, mock_db):
        """测试用户拥有特定权限"""
        # 模拟数据库查询
        mock_db.execute.side_effect = [
            # 第一次查询：返回项目
            MagicMock(scalar_one_or_none=MagicMock(return_value=project)),
            # 第二次查询：返回用户权限
            MagicMock(scalar_one_or_none=MagicMock(return_value=user_permission))
        ]
        
        result = await PermissionChecker.check_project_permission(
            regular_user, project.id, ProjectPermission.VIEW, mock_db
        )
        assert result is True
        
        result = await PermissionChecker.check_project_permission(
            regular_user, project.id, ProjectPermission.EDIT, mock_db
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_user_without_permission(self, regular_user, project, user_permission, mock_db):
        """测试用户没有特定权限"""
        # 模拟数据库查询
        mock_db.execute.side_effect = [
            # 第一次查询：返回项目
            MagicMock(scalar_one_or_none=MagicMock(return_value=project)),
            # 第二次查询：返回用户权限
            MagicMock(scalar_one_or_none=MagicMock(return_value=user_permission))
        ]
        
        result = await PermissionChecker.check_project_permission(
            regular_user, project.id, ProjectPermission.DELETE, mock_db
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_user_no_permission_record(self, regular_user, project, mock_db):
        """测试用户没有权限记录"""
        # 模拟数据库查询
        mock_db.execute.side_effect = [
            # 第一次查询：返回项目
            MagicMock(scalar_one_or_none=MagicMock(return_value=project)),
            # 第二次查询：没有权限记录
            MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        ]
        
        result = await PermissionChecker.check_project_permission(
            regular_user, project.id, ProjectPermission.VIEW, mock_db
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_project_not_found(self, regular_user, mock_db):
        """测试项目不存在"""
        # 模拟数据库查询返回None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(ResourceNotFoundError):
            await PermissionChecker.check_project_permission(
                regular_user, "nonexistent_project", ProjectPermission.VIEW, mock_db
            )
    
    @pytest.mark.asyncio
    async def test_check_admin_permission(self, super_admin_user, admin_user, regular_user):
        """测试管理员权限检查"""
        assert await PermissionChecker.check_admin_permission(super_admin_user) is True
        assert await PermissionChecker.check_admin_permission(admin_user) is True
        assert await PermissionChecker.check_admin_permission(regular_user) is False
    
    @pytest.mark.asyncio
    async def test_check_super_admin_permission(self, super_admin_user, admin_user, regular_user):
        """测试超级管理员权限检查"""
        assert await PermissionChecker.check_super_admin_permission(super_admin_user) is True
        assert await PermissionChecker.check_super_admin_permission(admin_user) is False
        assert await PermissionChecker.check_super_admin_permission(regular_user) is False
    
    @pytest.mark.asyncio
    async def test_get_user_project_permissions_super_admin(self, super_admin_user, mock_db):
        """测试获取超级管理员的项目权限"""
        permissions = await PermissionChecker.get_user_project_permissions(
            super_admin_user, "any_project_id", mock_db
        )
        expected_permissions = [p.value for p in ProjectPermission]
        assert permissions == expected_permissions
    
    @pytest.mark.asyncio
    async def test_get_user_project_permissions_owner(self, regular_user, project, mock_db):
        """测试获取项目所有者的权限"""
        # 设置用户为项目所有者
        regular_user.id = project.owner_id
        
        # 模拟数据库查询返回项目
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = project
        mock_db.execute.return_value = mock_result
        
        permissions = await PermissionChecker.get_user_project_permissions(
            regular_user, project.id, mock_db
        )
        expected_permissions = [p.value for p in ProjectPermission]
        assert permissions == expected_permissions
    
    @pytest.mark.asyncio
    async def test_get_user_project_permissions_with_record(self, regular_user, project, user_permission, mock_db):
        """测试获取有权限记录的用户权限"""
        # 模拟数据库查询
        mock_db.execute.side_effect = [
            # 第一次查询：返回项目
            MagicMock(scalar_one_or_none=MagicMock(return_value=project)),
            # 第二次查询：返回用户权限
            MagicMock(scalar_one_or_none=MagicMock(return_value=user_permission))
        ]
        
        permissions = await PermissionChecker.get_user_project_permissions(
            regular_user, project.id, mock_db
        )
        assert permissions == user_permission.permissions
    
    @pytest.mark.asyncio
    async def test_get_user_project_permissions_no_record(self, regular_user, project, mock_db):
        """测试获取没有权限记录的用户权限"""
        # 模拟数据库查询
        mock_db.execute.side_effect = [
            # 第一次查询：返回项目
            MagicMock(scalar_one_or_none=MagicMock(return_value=project)),
            # 第二次查询：没有权限记录
            MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        ]
        
        permissions = await PermissionChecker.get_user_project_permissions(
            regular_user, project.id, mock_db
        )
        assert permissions == []
    
    @pytest.mark.asyncio
    async def test_get_user_project_permissions_project_not_found(self, regular_user, mock_db):
        """测试获取不存在项目的用户权限"""
        # 模拟数据库查询返回None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        permissions = await PermissionChecker.get_user_project_permissions(
            regular_user, "nonexistent_project", mock_db
        )
        assert permissions == []


class TestPermissionDecorators:
    """权限装饰器测试"""
    
    @pytest.mark.asyncio
    async def test_require_permission_decorator_success(self):
        """测试权限装饰器成功情况"""
        @require_permission(ProjectPermission.VIEW)
        async def test_function(project_id, current_user, db):
            return "success"
        
        # 模拟权限检查成功
        with pytest.mock.patch.object(
            PermissionChecker, 
            'check_project_permission', 
            return_value=True
        ):
            result = await test_function(
                project_id="test_project",
                current_user=MagicMock(),
                db=MagicMock()
            )
            assert result == "success"
    
    @pytest.mark.asyncio
    async def test_require_permission_decorator_failure(self):
        """测试权限装饰器失败情况"""
        @require_permission(ProjectPermission.VIEW)
        async def test_function(project_id, current_user, db):
            return "success"
        
        # 模拟权限检查失败
        with pytest.mock.patch.object(
            PermissionChecker, 
            'check_project_permission', 
            return_value=False
        ):
            with pytest.raises(PermissionError):
                await test_function(
                    project_id="test_project",
                    current_user=MagicMock(),
                    db=MagicMock()
                )
    
    @pytest.mark.asyncio
    async def test_require_admin_decorator_success(self):
        """测试管理员装饰器成功情况"""
        @require_admin()
        async def test_function(current_user):
            return "success"
        
        # 模拟管理员权限检查成功
        with pytest.mock.patch.object(
            PermissionChecker, 
            'check_admin_permission', 
            return_value=True
        ):
            result = await test_function(current_user=MagicMock())
            assert result == "success"
    
    @pytest.mark.asyncio
    async def test_require_admin_decorator_failure(self):
        """测试管理员装饰器失败情况"""
        @require_admin()
        async def test_function(current_user):
            return "success"
        
        # 模拟管理员权限检查失败
        with pytest.mock.patch.object(
            PermissionChecker, 
            'check_admin_permission', 
            return_value=False
        ):
            with pytest.raises(PermissionError):
                await test_function(current_user=MagicMock())
    
    @pytest.mark.asyncio
    async def test_require_super_admin_decorator_success(self):
        """测试超级管理员装饰器成功情况"""
        @require_super_admin()
        async def test_function(current_user):
            return "success"
        
        # 模拟超级管理员权限检查成功
        with pytest.mock.patch.object(
            PermissionChecker, 
            'check_super_admin_permission', 
            return_value=True
        ):
            result = await test_function(current_user=MagicMock())
            assert result == "success"
    
    @pytest.mark.asyncio
    async def test_require_super_admin_decorator_failure(self):
        """测试超级管理员装饰器失败情况"""
        @require_super_admin()
        async def test_function(current_user):
            return "success"
        
        # 模拟超级管理员权限检查失败
        with pytest.mock.patch.object(
            PermissionChecker, 
            'check_super_admin_permission', 
            return_value=False
        ):
            with pytest.raises(PermissionError):
                await test_function(current_user=MagicMock())