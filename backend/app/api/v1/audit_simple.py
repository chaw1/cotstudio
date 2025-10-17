"""
简化的审计日志和权限管理API端点
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_active_user, require_permission
from app.models.audit import AuditEventType, AuditSeverity, ResourceType, AuditLog, Role, Permission
from app.services.audit_service import AuditService, RoleService, PermissionService

router = APIRouter()


@router.get("/logs")
async def get_audit_logs(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取审计日志列表"""
    
    audit_service = AuditService(db)
    
    # 构建查询
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    if severity:
        query = query.filter(AuditLog.severity == severity)
    
    # 分页
    total = query.count()
    skip = (page - 1) * size
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(size).all()
    
    # 记录查看操作
    audit_service.log_operation(
        user_id=current_user["user_id"],
        event_type=AuditEventType.READ,
        action="view_audit_logs",
        description="Viewed audit logs",
        request=request
    )
    
    return {
        "items": [
            {
                "id": str(log.id),
                "user_id": log.user_id,
                "event_type": log.event_type.value if log.event_type else None,
                "severity": log.severity.value if log.severity else None,
                "action": log.action,
                "description": log.description,
                "success": log.success,
                "created_at": log.created_at.isoformat(),
                "ip_address": log.ip_address,
                "resource_type": log.resource_type.value if log.resource_type else None,
                "resource_name": log.resource_name
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@router.get("/logs/{log_id}")
async def get_audit_log(
    log_id: str,
    request: Request,
    current_user: dict = Depends(get_current_active_user),
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
        resource_id=log_id,
        description=f"Viewed audit log detail: {log_id}",
        request=request
    )
    
    return {
        "id": str(log.id),
        "user_id": log.user_id,
        "event_type": log.event_type.value if log.event_type else None,
        "severity": log.severity.value if log.severity else None,
        "action": log.action,
        "description": log.description,
        "details": log.details,
        "success": log.success,
        "error_message": log.error_message,
        "created_at": log.created_at.isoformat(),
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "resource_type": log.resource_type.value if log.resource_type else None,
        "resource_id": log.resource_id,
        "resource_name": log.resource_name,
        "old_values": log.old_values,
        "new_values": log.new_values
    }


@router.get("/statistics")
async def get_audit_statistics(
    request: Request,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(get_current_active_user),
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
        request=request
    )
    
    return stats


@router.get("/roles")
async def get_roles(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取所有角色"""
    
    roles = db.query(Role).all()
    
    return [
        {
            "id": str(role.id),
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
            "role_type": role.role_type.value if role.role_type else None,
            "permissions": role.permissions,
            "is_system_role": role.is_system_role,
            "created_at": role.created_at.isoformat()
        }
        for role in roles
    ]


@router.post("/roles")
async def create_role(
    role_data: dict,
    request: Request,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新角色"""
    
    role_service = RoleService(db)
    
    try:
        # 创建角色对象
        role = Role(
            name=role_data["name"],
            display_name=role_data["display_name"],
            description=role_data.get("description"),
            role_type=role_data["role_type"],
            permissions=role_data.get("permissions", []),
            is_system_role=False
        )
        
        db.add(role)
        db.commit()
        db.refresh(role)
        
        # 记录审计日志
        audit_service = AuditService(db)
        audit_service.log_operation(
            user_id=current_user["user_id"],
            event_type=AuditEventType.CREATE,
            action="create_role",
            resource_type=ResourceType.ROLE,
            resource_id=str(role.id),
            resource_name=role.name,
            description=f"Created role: {role.name}",
            new_values=role_data,
            severity=AuditSeverity.MEDIUM,
            request=request
        )
        
        return {
            "id": str(role.id),
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
            "role_type": role.role_type.value,
            "permissions": role.permissions,
            "is_system_role": role.is_system_role,
            "created_at": role.created_at.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/permissions")
async def get_permissions(
    resource_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取权限列表"""
    
    query = db.query(Permission)
    
    if resource_type:
        query = query.filter(Permission.resource_type == resource_type)
    
    permissions = query.all()
    
    return [
        {
            "id": str(perm.id),
            "name": perm.name,
            "display_name": perm.display_name,
            "description": perm.description,
            "resource_type": perm.resource_type.value if perm.resource_type else None,
            "action": perm.action,
            "is_system_permission": perm.is_system_permission
        }
        for perm in permissions
    ]


@router.get("/health")
async def audit_health_check(db: Session = Depends(get_db)):
    """审计系统健康检查"""
    
    try:
        # 检查审计日志表
        audit_count = db.query(AuditLog).count()
        
        # 检查角色表
        role_count = db.query(Role).count()
        
        # 检查权限表
        permission_count = db.query(Permission).count()
        
        return {
            "status": "healthy",
            "audit_logs": audit_count,
            "roles": role_count,
            "permissions": permission_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }