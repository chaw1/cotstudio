"""
用户管理相关Pydantic模式
"""
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID

from .common import BaseSchema
from ..models.user import UserRole
from ..models.permission import ProjectPermission


class UserCreateRequest(BaseModel):
    """用户创建请求模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=8, description="密码")
    full_name: Optional[str] = Field(None, max_length=255, description="全名")
    role: UserRole = Field(UserRole.USER, description="用户角色")
    department: Optional[str] = Field(None, max_length=100, description="部门")
    is_active: bool = Field(True, description="是否激活")


class UserUpdateRequest(BaseModel):
    """用户更新请求模式"""
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    full_name: Optional[str] = Field(None, max_length=255, description="全名")
    role: Optional[UserRole] = Field(None, description="用户角色")
    department: Optional[str] = Field(None, max_length=100, description="部门")
    is_active: Optional[bool] = Field(None, description="是否激活")


class UserResponse(BaseSchema):
    """用户响应模式"""
    username: str
    email: str
    full_name: Optional[str]
    role: UserRole
    department: Optional[str]
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime]
    login_count: int
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """用户列表响应模式"""
    users: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int


class UserSearchRequest(BaseModel):
    """用户搜索请求模式"""
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")
    search: Optional[str] = Field(None, description="搜索关键词")
    role: Optional[UserRole] = Field(None, description="角色筛选")
    department: Optional[str] = Field(None, description="部门筛选")
    is_active: Optional[bool] = Field(None, description="激活状态筛选")


class PermissionGrantRequest(BaseModel):
    """权限授予请求模式"""
    user_id: str = Field(..., description="用户ID")
    project_id: str = Field(..., description="项目ID")
    permissions: List[ProjectPermission] = Field(..., description="权限列表")


class PermissionRevokeRequest(BaseModel):
    """权限撤销请求模式"""
    user_id: str = Field(..., description="用户ID")
    project_id: str = Field(..., description="项目ID")
    permissions: Optional[List[ProjectPermission]] = Field(None, description="要撤销的权限列表，为空则撤销所有权限")


class PermissionResponse(BaseSchema):
    """权限响应模式"""
    user_id: str
    project_id: str
    permissions: List[str]
    granted_by: Optional[str]
    granted_at: datetime
    
    # 关联信息
    user_username: Optional[str] = None
    project_name: Optional[str] = None
    granter_username: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserPermissionResponse(BaseModel):
    """用户权限响应模式"""
    user: UserResponse
    project_permissions: List[PermissionResponse]


class ProjectPermissionResponse(BaseModel):
    """项目权限响应模式"""
    project_id: str
    project_name: str
    permissions: List[PermissionResponse]


class PermissionListResponse(BaseModel):
    """权限列表响应模式"""
    permissions: List[PermissionResponse]
    total: int
    page: int
    size: int
    pages: int


class PermissionSearchRequest(BaseModel):
    """权限搜索请求模式"""
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")
    user_id: Optional[str] = Field(None, description="用户ID筛选")
    project_id: Optional[str] = Field(None, description="项目ID筛选")
    permission: Optional[ProjectPermission] = Field(None, description="权限类型筛选")


class PasswordChangeRequest(BaseModel):
    """密码修改请求模式"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=8, description="新密码")


class PasswordResetRequest(BaseModel):
    """密码重置请求模式（管理员操作）"""
    user_id: str = Field(..., description="用户ID")
    new_password: str = Field(..., min_length=8, description="新密码")


class UserStatsResponse(BaseModel):
    """用户统计响应模式"""
    total_users: int
    active_users: int
    inactive_users: int
    users_by_role: dict
    users_by_department: dict
    recent_logins: int  # 最近7天登录用户数