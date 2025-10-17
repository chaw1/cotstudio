"""
审计日志和权限管理API端点
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_active_user, require_permission
from app.models.audit import AuditEventType, AuditSeverity, ResourceType, AuditLog, Role, Permission
from app.schemas.audit import (
    AuditLogQuery, AuditLogResponse, AuditLogListResponse, AuditStatisticsResponse,
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionResponse
)
from app.services.audit_service import AuditService, RoleService, PermissionService

router = APIRouter()


# 审计日志相关端点
@router.get("/logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    event_types: Optional[List[AuditEventType]] = Query(None),
    resource_type: Optional[ResourceType] = Query(None),
    resource_id: Optional[str] = Query(None),
    severity: Optional[AuditSeverity] = Query(None),
    success: Optional[bool] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    search_text: Optional[str] = Query(None),
    current_user: dict = Depends(require_permission("audit:read")),
    db: Session = Depends(get_db)
):
    """获取审计日志列表"""
    
    audit_service = AuditService(db)
    
    # 构建查询条件
    query = AuditLogQuery(
        user_id=user_id,
        event_types=event_types,
        resource_type=resource_type,
        resource_id=resource_id,
        severity=severity,
        success=success,
        start_date=start_date,
        end_date=end_date,
        search_text=search_text
    )
    
    # 计算分页参数
    skip = (page - 1) * size
    
    # 查询数据
    logs, total = audit_service.query_audit_logs(query, skip=skip, limit=size)
    
    # 记录查看审计日志的操作
    audit_service.log_operation(
        user_id=current_user["user_id"],
        event_type=AuditEventType.READ,
        action="view_audit_logs",
        description="Viewed audit logs",
        details={
            "query_params": query.dict(exclude_none=True),
            "page": page,
            "size": size
        },
        request=request
    )
    
    return AuditLogListResponse(
        items=[AuditLogResponse.from_orm(log) for log in logs],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    request: Request,
    current_user: dict = Depends(require_permission("audit:read")),
    db: Session = Depends(get_db)
):
    """获取单个审计日志详情"""
    
    audit_service = AuditService(db)
    log = audit_service.get(db, log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )
    
    # 记录查看操作
    audit_service.log_operation(
        user_id=current_user["user_id"],
        event_type=AuditEventType.READ,
        action="view_audit_log_detail",
        resource_type=ResourceType.SYSTEM_SETTING,
        resource_id=log_id,
        description=f"Viewed audit log detail: {log_id}",
        request=request
    )
    
    return AuditLogResponse.from_orm(log)


@router.get("/statistics", response_model=AuditStatisticsResponse)
async def get_audit_statistics(
    request: Request,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(require_permission("audit:read")),
    db: Session = Depends(get_db)
):
    """获取审计统计信息"""
    
    audit_service = AuditService(db)
    stats = audit_service.get_audit_statistics(start_date, end_date)
    
    # 记录查看统计的操作
    audit_service.log_operation(
        user_id=current_user["user_id"],
        event_type=AuditEventType.READ,
        action="view_audit_statistics",
        description="Viewed audit statistics",
        details={
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        },
        request=request
    )
    
    return AuditStatisticsResponse(**stats)


# 角色管理相关端点
@router.get("/roles", response_model=List[RoleResponse])
async def get_roles(
    current_user: dict = Depends(require_permission("role:read")),
    db: Session = Depends(get_db)
):
    """获取所有角色"""
    
    role_service = RoleService(db)
    roles = role_service.get_multi(db)
    return [RoleResponse.from_orm(role) for role in roles]


@router.post("/roles", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreate,
    request: Request,
    current_user: dict = Depends(require_permission("role:create")),
    role_service: RoleService = Depends(RoleService)
):
    """创建新角色"""
    
    try:
        role = role_service.create_role(role_data, current_user["user_id"])
        return RoleResponse.from_orm(role)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    current_user: dict = Depends(require_permission("role:read")),
    role_service: RoleService = Depends(RoleService)
):
    """获取角色详情"""
    
    role = role_service.get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    return RoleResponse.from_orm(role)


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    request: Request,
    current_user: dict = Depends(require_permission("role:update")),
    role_service: RoleService = Depends(RoleService)
):
    """更新角色"""
    
    try:
        role = role_service.update_role(role_id, role_data, current_user["user_id"])
        return RoleResponse.from_orm(role)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: str,
    request: Request,
    current_user: dict = Depends(require_permission("role:delete")),
    role_service: RoleService = Depends(RoleService)
):
    """删除角色"""
    
    try:
        role_service.delete_role(role_id, current_user["user_id"])
        return {"message": "Role deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# 权限管理相关端点
@router.get("/permissions", response_model=List[PermissionResponse])
async def get_permissions(
    resource_type: Optional[ResourceType] = Query(None),
    current_user: dict = Depends(require_permission("permission:read")),
    permission_service: PermissionService = Depends(PermissionService)
):
    """获取权限列表"""
    
    if resource_type:
        permissions = permission_service.get_permissions_by_resource(resource_type)
    else:
        permissions = permission_service.get_all_permissions()
    
    return [PermissionResponse.from_orm(perm) for perm in permissions]


@router.post("/users/{user_id}/roles", response_model=UserRoleResponse)
async def assign_role_to_user(
    user_id: str,
    role_data: UserRoleCreate,
    request: Request,
    current_user: dict = Depends(require_permission("user:manage_roles")),
    permission_service: PermissionService = Depends(PermissionService)
):
    """为用户分配角色"""
    
    try:
        user_role = permission_service.assign_role_to_user(
            user_id=user_id,
            role_id=role_data.role_id,
            granted_by=current_user["user_id"],
            expires_at=role_data.expires_at
        )
        return UserRoleResponse.from_orm(user_role)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/users/{user_id}/roles/{role_id}")
async def revoke_role_from_user(
    user_id: str,
    role_id: str,
    request: Request,
    current_user: dict = Depends(require_permission("user:manage_roles")),
    permission_service: PermissionService = Depends(PermissionService)
):
    """撤销用户角色"""
    
    try:
        permission_service.revoke_role_from_user(user_id, role_id, current_user["user_id"])
        return {"message": "Role revoked successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/users/{user_id}/permissions", response_model=UserPermissionsResponse)
async def get_user_permissions(
    user_id: str,
    current_user: dict = Depends(require_permission("user:read_permissions")),
    permission_service: PermissionService = Depends(PermissionService),
    db: Session = Depends(get_db)
):
    """获取用户权限信息"""
    
    # 获取用户角色
    user_roles = permission_service.get_user_roles(user_id)
    
    # 获取用户权限
    permissions = permission_service.get_user_permissions(user_id)
    
    # 获取项目权限
    project_permissions = (
        db.query(ProjectPermission)
        .filter(ProjectPermission.user_id == user_id)
        .all()
    )
    
    return UserPermissionsResponse(
        user_id=user_id,
        roles=[UserRoleWithDetails.from_orm(ur) for ur in user_roles],
        permissions=permissions,
        project_permissions=[ProjectPermissionWithDetails.from_orm(pp) for pp in project_permissions]
    )


@router.post("/permissions/check", response_model=PermissionCheckResponse)
async def check_permission(
    check_request: PermissionCheckRequest,
    current_user: dict = Depends(require_permission("permission:check")),
    permission_service: PermissionService = Depends(PermissionService)
):
    """检查用户权限"""
    
    has_permission = permission_service.check_permission(
        check_request.user_id,
        check_request.permission
    )
    
    return PermissionCheckResponse(
        has_permission=has_permission,
        reason="Permission granted" if has_permission else "Permission denied"
    )


# 项目权限管理端点
@router.post("/projects/{project_id}/permissions", response_model=ProjectPermissionResponse)
async def grant_project_permission(
    project_id: str,
    permission_data: ProjectPermissionCreate,
    request: Request,
    current_user: dict = Depends(require_permission("project:manage_permissions")),
    permission_service: PermissionService = Depends(PermissionService)
):
    """授予项目权限"""
    
    try:
        project_permission = permission_service.grant_project_permission(
            project_id=project_id,
            user_id=permission_data.user_id,
            role_id=permission_data.role_id,
            permission_type=permission_data.permission_type,
            granted_by=current_user["user_id"]
        )
        return ProjectPermissionResponse.from_orm(project_permission)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/projects/{project_id}/permissions", response_model=List[ProjectPermissionWithDetails])
async def get_project_permissions(
    project_id: str,
    current_user: dict = Depends(require_permission("project:read_permissions")),
    db: Session = Depends(get_db)
):
    """获取项目权限列表"""
    
    permissions = (
        db.query(ProjectPermission)
        .filter(ProjectPermission.project_id == project_id)
        .all()
    )
    
    return [ProjectPermissionWithDetails.from_orm(perm) for perm in permissions]


# 批量操作端点
@router.post("/roles/bulk-assign", response_model=BulkRoleAssignmentResponse)
async def bulk_assign_roles(
    assignment_request: BulkRoleAssignmentRequest,
    request: Request,
    current_user: dict = Depends(require_permission("user:manage_roles")),
    permission_service: PermissionService = Depends(PermissionService)
):
    """批量分配角色"""
    
    successful_assignments = []
    failed_assignments = []
    
    for user_id in assignment_request.user_ids:
        try:
            permission_service.assign_role_to_user(
                user_id=user_id,
                role_id=assignment_request.role_id,
                granted_by=current_user["user_id"],
                expires_at=assignment_request.expires_at
            )
            successful_assignments.append(user_id)
        except Exception as e:
            failed_assignments.append({
                "user_id": user_id,
                "error": str(e)
            })
    
    return BulkRoleAssignmentResponse(
        successful_assignments=successful_assignments,
        failed_assignments=failed_assignments
    )