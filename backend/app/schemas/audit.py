"""
审计日志和权限相关的Pydantic模式
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.audit import AuditEventType, AuditSeverity, ResourceType, RoleType


class AuditLogBase(BaseModel):
    """审计日志基础模式"""
    user_id: Optional[str] = None
    event_type: AuditEventType
    severity: AuditSeverity = AuditSeverity.LOW
    resource_type: Optional[ResourceType] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    action: str
    description: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    """创建审计日志模式"""
    pass


class AuditLogResponse(AuditLogBase):
    """审计日志响应模式"""
    id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    old_values: Dict[str, Any] = Field(default_factory=dict)
    new_values: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogQuery(BaseModel):
    """审计日志查询模式"""
    user_id: Optional[str] = None
    event_types: Optional[List[AuditEventType]] = None
    resource_type: Optional[ResourceType] = None
    resource_id: Optional[str] = None
    severity: Optional[AuditSeverity] = None
    success: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ip_address: Optional[str] = None
    search_text: Optional[str] = None


class AuditLogListResponse(BaseModel):
    """审计日志列表响应模式"""
    items: List[AuditLogResponse]
    total: int
    page: int
    size: int
    pages: int


class AuditStatisticsResponse(BaseModel):
    """审计统计响应模式"""
    total_operations: int
    failed_operations: int
    success_rate: float
    active_users: int
    event_type_distribution: Dict[str, int]
    severity_distribution: Dict[str, int]
    resource_type_distribution: Dict[str, int]
    period: Dict[str, str]


# 角色相关模式
class RoleBase(BaseModel):
    """角色基础模式"""
    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    role_type: RoleType
    permissions: List[str] = Field(default_factory=list)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Role name must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()


class RoleCreate(RoleBase):
    """创建角色模式"""
    pass


class RoleUpdate(BaseModel):
    """更新角色模式"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class RoleResponse(RoleBase):
    """角色响应模式"""
    id: str
    is_system_role: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# 权限相关模式
class PermissionResponse(BaseModel):
    """权限响应模式"""
    id: str
    name: str
    display_name: str
    description: Optional[str] = None
    resource_type: ResourceType
    action: str
    is_system_permission: bool
    
    class Config:
        from_attributes = True


# 用户角色相关模式
class UserRoleBase(BaseModel):
    """用户角色基础模式"""
    user_id: str
    role_id: str
    expires_at: Optional[datetime] = None


class UserRoleCreate(UserRoleBase):
    """创建用户角色模式"""
    pass


class UserRoleResponse(UserRoleBase):
    """用户角色响应模式"""
    id: str
    granted_by: Optional[str] = None
    granted_at: datetime
    
    class Config:
        from_attributes = True


class UserRoleWithDetails(UserRoleResponse):
    """带详情的用户角色响应模式"""
    role: RoleResponse
    
    class Config:
        from_attributes = True


# 项目权限相关模式
class ProjectPermissionBase(BaseModel):
    """项目权限基础模式"""
    project_id: str
    user_id: Optional[str] = None
    role_id: Optional[str] = None
    permission_type: str = Field(..., pattern="^(owner|editor|reviewer|viewer)$")
    
    @validator('permission_type')
    def validate_permission_type(cls, v):
        allowed_types = ['owner', 'editor', 'reviewer', 'viewer']
        if v not in allowed_types:
            raise ValueError(f'Permission type must be one of: {", ".join(allowed_types)}')
        return v


class ProjectPermissionCreate(ProjectPermissionBase):
    """创建项目权限模式"""
    
    @validator('user_id', 'role_id')
    def validate_user_or_role(cls, v, values):
        if not values.get('user_id') and not values.get('role_id'):
            raise ValueError('Either user_id or role_id must be provided')
        return v


class ProjectPermissionResponse(ProjectPermissionBase):
    """项目权限响应模式"""
    id: str
    granted_by: Optional[str] = None
    granted_at: datetime
    
    class Config:
        from_attributes = True


class ProjectPermissionWithDetails(ProjectPermissionResponse):
    """带详情的项目权限响应模式"""
    user: Optional[Dict[str, Any]] = None
    role: Optional[RoleResponse] = None
    
    class Config:
        from_attributes = True


# 权限检查相关模式
class PermissionCheckRequest(BaseModel):
    """权限检查请求模式"""
    user_id: str
    permission: str
    resource_type: Optional[ResourceType] = None
    resource_id: Optional[str] = None


class PermissionCheckResponse(BaseModel):
    """权限检查响应模式"""
    has_permission: bool
    reason: Optional[str] = None


class UserPermissionsResponse(BaseModel):
    """用户权限响应模式"""
    user_id: str
    roles: List[UserRoleWithDetails]
    permissions: List[str]
    project_permissions: List[ProjectPermissionWithDetails]


# 批量操作模式
class BulkRoleAssignmentRequest(BaseModel):
    """批量角色分配请求模式"""
    user_ids: List[str] = Field(..., min_items=1)
    role_id: str
    expires_at: Optional[datetime] = None


class BulkRoleAssignmentResponse(BaseModel):
    """批量角色分配响应模式"""
    successful_assignments: List[str]
    failed_assignments: List[Dict[str, str]]  # user_id -> error_message


class BulkProjectPermissionRequest(BaseModel):
    """批量项目权限请求模式"""
    project_id: str
    assignments: List[Dict[str, Any]]  # [{"user_id": "...", "permission_type": "..."}, ...]


class BulkProjectPermissionResponse(BaseModel):
    """批量项目权限响应模式"""
    successful_assignments: List[str]
    failed_assignments: List[Dict[str, str]]