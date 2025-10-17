"""
权限检查系统
"""
from typing import Optional, List
from functools import wraps
from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from .database import get_db
from ..models.user import User, UserRole
from ..models.permission import ProjectPermission, UserProjectPermission
from ..models.project import Project


class PermissionError(HTTPException):
    """权限错误异常"""
    def __init__(self, detail: str = "权限不足"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ResourceNotFoundError(HTTPException):
    """资源不存在错误"""
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"{resource} {resource_id} 不存在"
        )


class PermissionChecker:
    """权限检查器"""
    
    @staticmethod
    async def check_project_permission(
        user: User, 
        project_id: str, 
        required_permission: ProjectPermission,
        db: Session
    ) -> bool:
        """检查用户对项目的权限"""
        
        # 超级管理员拥有所有权限
        if user.role == UserRole.SUPER_ADMIN:
            return True
            
        # 检查项目是否存在
        project_query = select(Project).where(Project.id == project_id)
        project_result = await db.execute(project_query)
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise ResourceNotFoundError("项目", project_id)
            
        # 项目所有者拥有所有权限
        if project.owner_id == user.id:
            return True
            
        # 检查用户项目权限
        permission_query = select(UserProjectPermission).where(
            UserProjectPermission.user_id == user.id,
            UserProjectPermission.project_id == project_id
        )
        permission_result = await db.execute(permission_query)
        permission = permission_result.scalar_one_or_none()
        
        if permission and required_permission.value in permission.permissions:
            return True
            
        return False
    
    @staticmethod
    async def check_admin_permission(user: User) -> bool:
        """检查用户是否有管理员权限"""
        return user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    
    @staticmethod
    async def check_super_admin_permission(user: User) -> bool:
        """检查用户是否有超级管理员权限"""
        return user.role == UserRole.SUPER_ADMIN
    
    @staticmethod
    def check_admin_permission_sync(user: User) -> bool:
        """检查用户是否有管理员权限（同步版本）"""
        return user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    
    @staticmethod
    def check_super_admin_permission_sync(user: User) -> bool:
        """检查用户是否有超级管理员权限（同步版本）"""
        return user.role == UserRole.SUPER_ADMIN
    
    @staticmethod
    async def get_user_project_permissions(
        user: User, 
        project_id: str, 
        db: Session
    ) -> List[str]:
        """获取用户对项目的权限列表"""
        
        # 超级管理员拥有所有权限
        if user.role == UserRole.SUPER_ADMIN:
            return [p.value for p in ProjectPermission]
            
        # 检查项目是否存在
        project_query = select(Project).where(Project.id == project_id)
        project_result = await db.execute(project_query)
        project = project_result.scalar_one_or_none()
        
        if not project:
            return []
            
        # 项目所有者拥有所有权限
        if project.owner_id == user.id:
            return [p.value for p in ProjectPermission]
            
        # 查询用户项目权限
        permission_query = select(UserProjectPermission).where(
            UserProjectPermission.user_id == user.id,
            UserProjectPermission.project_id == project_id
        )
        permission_result = await db.execute(permission_query)
        permission = permission_result.scalar_one_or_none()
        
        return permission.permissions if permission else []


# 权限检查装饰器
def require_permission(required_permission: ProjectPermission):
    """要求特定项目权限的装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取必要的参数
            project_id = kwargs.get('project_id')
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')
            
            if not all([project_id, current_user, db]):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="权限检查参数不完整"
                )
            
            # 检查权限
            has_permission = await PermissionChecker.check_project_permission(
                current_user, project_id, required_permission, db
            )
            
            if not has_permission:
                raise PermissionError(f"需要 {required_permission.value} 权限")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_admin():
    """要求管理员权限的装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="权限检查参数不完整"
                )
            
            # 检查管理员权限
            has_permission = await PermissionChecker.check_admin_permission(current_user)
            
            if not has_permission:
                raise PermissionError("需要管理员权限")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_super_admin():
    """要求超级管理员权限的装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="权限检查参数不完整"
                )
            
            # 检查超级管理员权限
            has_permission = await PermissionChecker.check_super_admin_permission(current_user)
            
            if not has_permission:
                raise PermissionError("需要超级管理员权限")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# 依赖注入函数
async def get_current_admin(
    current_user: User = Depends(lambda: None),  # 这里需要替换为实际的用户获取依赖
    db: Session = Depends(get_db)
) -> User:
    """获取当前管理员用户的依赖注入函数"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证"
        )
    
    has_permission = await PermissionChecker.check_admin_permission(current_user)
    if not has_permission:
        raise PermissionError("需要管理员权限")
    
    return current_user


async def get_current_super_admin(
    current_user: User = Depends(lambda: None),  # 这里需要替换为实际的用户获取依赖
    db: Session = Depends(get_db)
) -> User:
    """获取当前超级管理员用户的依赖注入函数"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证"
        )
    
    has_permission = await PermissionChecker.check_super_admin_permission(current_user)
    if not has_permission:
        raise PermissionError("需要超级管理员权限")
    
    return current_user


async def check_project_access(
    project_id: str,
    required_permission: ProjectPermission,
    current_user: User = Depends(lambda: None),  # 这里需要替换为实际的用户获取依赖
    db: Session = Depends(get_db)
) -> bool:
    """检查项目访问权限的依赖注入函数"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证"
        )
    
    has_permission = await PermissionChecker.check_project_permission(
        current_user, project_id, required_permission, db
    )
    
    if not has_permission:
        raise PermissionError(f"需要 {required_permission.value} 权限")
    
    return True