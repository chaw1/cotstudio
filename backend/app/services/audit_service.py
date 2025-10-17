"""
审计日志服务
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import Request
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit import (
    AuditLog, Role, Permission, UserRole, ProjectPermission,
    AuditEventType, AuditSeverity, ResourceType, RoleType
)
from app.schemas.audit import (
    AuditLogCreate, AuditLogResponse, AuditLogQuery,
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionResponse, UserRoleCreate, ProjectPermissionCreate
)
from app.services.base_service import BaseService


class AuditService(BaseService[AuditLog]):
    """审计日志服务"""
    
    def __init__(self, db: Session):
        super().__init__(AuditLog)
        self.db = db
    
    def log_operation(
        self,
        user_id: Optional[str],
        event_type: AuditEventType,
        action: str,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.LOW,
        success: bool = True,
        error_message: Optional[str] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """记录操作审计日志"""
        
        audit_data = {
            "user_id": user_id,
            "event_type": event_type,
            "severity": severity,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "resource_name": resource_name,
            "action": action,
            "description": description,
            "details": details or {},
            "old_values": old_values or {},
            "new_values": new_values or {},
            "success": success,
            "error_message": error_message
        }
        
        # 从请求中提取信息
        if request:
            audit_data.update({
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "request_id": getattr(request.state, "request_id", None)
            })
        
        audit_log = AuditLog(**audit_data)
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        return audit_log
    
    def query_audit_logs(
        self,
        query: AuditLogQuery,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[AuditLog], int]:
        """查询审计日志"""
        
        # 构建查询条件
        conditions = []
        
        if query.user_id:
            conditions.append(AuditLog.user_id == query.user_id)
        
        if query.event_types:
            conditions.append(AuditLog.event_type.in_(query.event_types))
        
        if query.resource_type:
            conditions.append(AuditLog.resource_type == query.resource_type)
        
        if query.resource_id:
            conditions.append(AuditLog.resource_id == query.resource_id)
        
        if query.severity:
            conditions.append(AuditLog.severity == query.severity)
        
        if query.success is not None:
            conditions.append(AuditLog.success == query.success)
        
        if query.start_date:
            conditions.append(AuditLog.created_at >= query.start_date)
        
        if query.end_date:
            conditions.append(AuditLog.created_at <= query.end_date)
        
        if query.ip_address:
            conditions.append(AuditLog.ip_address == query.ip_address)
        
        if query.search_text:
            search_conditions = [
                AuditLog.action.ilike(f"%{query.search_text}%"),
                AuditLog.description.ilike(f"%{query.search_text}%"),
                AuditLog.resource_name.ilike(f"%{query.search_text}%")
            ]
            conditions.append(or_(*search_conditions))
        
        # 执行查询
        query_obj = self.db.query(AuditLog)
        
        if conditions:
            query_obj = query_obj.filter(and_(*conditions))
        
        # 获取总数
        total = query_obj.count()
        
        # 分页和排序
        logs = query_obj.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
        
        return logs, total
    
    def get_audit_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取审计统计信息"""
        
        # 默认查询最近30天
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        base_query = self.db.query(AuditLog).filter(
            AuditLog.created_at.between(start_date, end_date)
        )
        
        # 总操作数
        total_operations = base_query.count()
        
        # 按事件类型统计
        event_type_stats = (
            base_query
            .with_entities(AuditLog.event_type, func.count(AuditLog.id))
            .group_by(AuditLog.event_type)
            .all()
        )
        
        # 按严重程度统计
        severity_stats = (
            base_query
            .with_entities(AuditLog.severity, func.count(AuditLog.id))
            .group_by(AuditLog.severity)
            .all()
        )
        
        # 失败操作统计
        failed_operations = base_query.filter(AuditLog.success == False).count()
        
        # 活跃用户统计
        active_users = (
            base_query
            .with_entities(AuditLog.user_id)
            .filter(AuditLog.user_id.isnot(None))
            .distinct()
            .count()
        )
        
        # 按资源类型统计
        resource_type_stats = (
            base_query
            .filter(AuditLog.resource_type.isnot(None))
            .with_entities(AuditLog.resource_type, func.count(AuditLog.id))
            .group_by(AuditLog.resource_type)
            .all()
        )
        
        return {
            "total_operations": total_operations,
            "failed_operations": failed_operations,
            "success_rate": (total_operations - failed_operations) / total_operations * 100 if total_operations > 0 else 0,
            "active_users": active_users,
            "event_type_distribution": {str(event_type): count for event_type, count in event_type_stats},
            "severity_distribution": {str(severity): count for severity, count in severity_stats},
            "resource_type_distribution": {str(resource_type): count for resource_type, count in resource_type_stats},
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }


class RoleService(BaseService[Role]):
    """角色管理服务"""
    
    def __init__(self, db: Session):
        super().__init__(Role)
        self.db = db
    
    def create_role(self, role_data: RoleCreate, created_by: str) -> Role:
        """创建角色"""
        role = Role(**role_data.dict())
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        
        # 记录审计日志
        audit_service = AuditService(self.db)
        audit_service.log_operation(
            user_id=created_by,
            event_type=AuditEventType.CREATE,
            action="create_role",
            resource_type=ResourceType.ROLE,
            resource_id=str(role.id),
            resource_name=role.name,
            description=f"Created role: {role.name}",
            new_values=role_data.dict(),
            severity=AuditSeverity.MEDIUM
        )
        
        return role
    
    def update_role(self, role_id: str, role_data: RoleUpdate, updated_by: str) -> Role:
        """更新角色"""
        role = self.get(role_id)
        if not role:
            raise ValueError("Role not found")
        
        if role.is_system_role:
            raise ValueError("Cannot modify system role")
        
        # 保存旧值
        old_values = {
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
            "permissions": role.permissions
        }
        
        # 更新角色
        update_data = role_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(role, field, value)
        
        self.db.commit()
        self.db.refresh(role)
        
        # 记录审计日志
        audit_service = AuditService(self.db)
        audit_service.log_operation(
            user_id=updated_by,
            event_type=AuditEventType.UPDATE,
            action="update_role",
            resource_type=ResourceType.ROLE,
            resource_id=str(role.id),
            resource_name=role.name,
            description=f"Updated role: {role.name}",
            old_values=old_values,
            new_values=update_data,
            severity=AuditSeverity.MEDIUM
        )
        
        return role
    
    def delete_role(self, role_id: str, deleted_by: str) -> bool:
        """删除角色"""
        role = self.get(role_id)
        if not role:
            raise ValueError("Role not found")
        
        if role.is_system_role:
            raise ValueError("Cannot delete system role")
        
        # 检查是否有用户使用此角色
        user_count = self.db.query(UserRole).filter(UserRole.role_id == role_id).count()
        if user_count > 0:
            raise ValueError(f"Cannot delete role: {user_count} users are assigned to this role")
        
        # 记录审计日志
        audit_service = AuditService(self.db)
        audit_service.log_operation(
            user_id=deleted_by,
            event_type=AuditEventType.DELETE,
            action="delete_role",
            resource_type=ResourceType.ROLE,
            resource_id=str(role.id),
            resource_name=role.name,
            description=f"Deleted role: {role.name}",
            old_values={
                "name": role.name,
                "display_name": role.display_name,
                "permissions": role.permissions
            },
            severity=AuditSeverity.HIGH
        )
        
        self.db.delete(role)
        self.db.commit()
        
        return True
    
    def get_system_roles(self) -> List[Role]:
        """获取系统内置角色"""
        return self.db.query(Role).filter(Role.is_system_role == True).all()
    
    def get_custom_roles(self) -> List[Role]:
        """获取自定义角色"""
        return self.db.query(Role).filter(Role.is_system_role == False).all()


class PermissionService:
    """权限管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_permissions(self) -> List[Permission]:
        """获取所有权限"""
        return self.db.query(Permission).all()
    
    def get_permissions_by_resource(self, resource_type: ResourceType) -> List[Permission]:
        """根据资源类型获取权限"""
        return self.db.query(Permission).filter(Permission.resource_type == resource_type).all()
    
    def assign_role_to_user(
        self,
        user_id: str,
        role_id: str,
        granted_by: str,
        expires_at: Optional[datetime] = None
    ) -> UserRole:
        """为用户分配角色"""
        
        # 检查是否已存在
        existing = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        ).first()
        
        if existing:
            raise ValueError("User already has this role")
        
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            granted_by=granted_by,
            expires_at=expires_at
        )
        
        self.db.add(user_role)
        self.db.commit()
        self.db.refresh(user_role)
        
        # 记录审计日志
        role = self.db.query(Role).filter(Role.id == role_id).first()
        audit_service = AuditService(self.db)
        audit_service.log_operation(
            user_id=granted_by,
            event_type=AuditEventType.PERMISSION_CHANGE,
            action="assign_role",
            resource_type=ResourceType.USER,
            resource_id=user_id,
            description=f"Assigned role {role.name if role else role_id} to user",
            new_values={
                "role_id": role_id,
                "role_name": role.name if role else None,
                "expires_at": expires_at.isoformat() if expires_at else None
            },
            severity=AuditSeverity.MEDIUM
        )
        
        return user_role
    
    def revoke_role_from_user(self, user_id: str, role_id: str, revoked_by: str) -> bool:
        """撤销用户角色"""
        
        user_role = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        ).first()
        
        if not user_role:
            raise ValueError("User role assignment not found")
        
        # 记录审计日志
        role = self.db.query(Role).filter(Role.id == role_id).first()
        audit_service = AuditService(self.db)
        audit_service.log_operation(
            user_id=revoked_by,
            event_type=AuditEventType.PERMISSION_CHANGE,
            action="revoke_role",
            resource_type=ResourceType.USER,
            resource_id=user_id,
            description=f"Revoked role {role.name if role else role_id} from user",
            old_values={
                "role_id": role_id,
                "role_name": role.name if role else None,
                "granted_at": user_role.granted_at.isoformat()
            },
            severity=AuditSeverity.MEDIUM
        )
        
        self.db.delete(user_role)
        self.db.commit()
        
        return True
    
    def get_user_roles(self, user_id: str) -> List[UserRole]:
        """获取用户角色"""
        return (
            self.db.query(UserRole)
            .filter(UserRole.user_id == user_id)
            .filter(
                or_(
                    UserRole.expires_at.is_(None),
                    UserRole.expires_at > datetime.utcnow()
                )
            )
            .all()
        )
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """获取用户所有权限"""
        user_roles = self.get_user_roles(user_id)
        permissions = set()
        
        for user_role in user_roles:
            role = self.db.query(Role).filter(Role.id == user_role.role_id).first()
            if role:
                permissions.update(role.permissions)
        
        return list(permissions)
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """检查用户是否有指定权限"""
        user_permissions = self.get_user_permissions(user_id)
        return permission in user_permissions or "*" in user_permissions
    
    def grant_project_permission(
        self,
        project_id: str,
        user_id: Optional[str] = None,
        role_id: Optional[str] = None,
        permission_type: str = "viewer",
        granted_by: str = None
    ) -> ProjectPermission:
        """授予项目权限"""
        
        if not user_id and not role_id:
            raise ValueError("Either user_id or role_id must be provided")
        
        project_permission = ProjectPermission(
            project_id=project_id,
            user_id=user_id,
            role_id=role_id,
            permission_type=permission_type,
            granted_by=granted_by
        )
        
        self.db.add(project_permission)
        self.db.commit()
        self.db.refresh(project_permission)
        
        # 记录审计日志
        audit_service = AuditService(self.db)
        audit_service.log_operation(
            user_id=granted_by,
            event_type=AuditEventType.PERMISSION_CHANGE,
            action="grant_project_permission",
            resource_type=ResourceType.PROJECT,
            resource_id=project_id,
            description=f"Granted {permission_type} permission to {'user' if user_id else 'role'}",
            new_values={
                "user_id": user_id,
                "role_id": role_id,
                "permission_type": permission_type
            },
            severity=AuditSeverity.MEDIUM
        )
        
        return project_permission
    
    def check_project_permission(
        self,
        user_id: str,
        project_id: str,
        required_permission: str
    ) -> bool:
        """检查用户是否有项目权限"""
        
        # 检查直接用户权限
        user_permission = (
            self.db.query(ProjectPermission)
            .filter(
                ProjectPermission.project_id == project_id,
                ProjectPermission.user_id == user_id
            )
            .first()
        )
        
        if user_permission:
            return self._check_permission_level(user_permission.permission_type, required_permission)
        
        # 检查角色权限
        user_roles = self.get_user_roles(user_id)
        for user_role in user_roles:
            role_permission = (
                self.db.query(ProjectPermission)
                .filter(
                    ProjectPermission.project_id == project_id,
                    ProjectPermission.role_id == user_role.role_id
                )
                .first()
            )
            
            if role_permission:
                return self._check_permission_level(role_permission.permission_type, required_permission)
        
        return False
    
    def _check_permission_level(self, granted_permission: str, required_permission: str) -> bool:
        """检查权限级别"""
        permission_hierarchy = {
            "viewer": 1,
            "reviewer": 2,
            "editor": 3,
            "owner": 4
        }
        
        granted_level = permission_hierarchy.get(granted_permission, 0)
        required_level = permission_hierarchy.get(required_permission, 0)
        
        return granted_level >= required_level


from fastapi import Depends

def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    """获取审计服务依赖"""
    return AuditService(db)


def get_role_service(db: Session = Depends(get_db)) -> RoleService:
    """获取角色服务依赖"""
    return RoleService(db)


def get_permission_service(db: Session = Depends(get_db)) -> PermissionService:
    """获取权限服务依赖"""
    return PermissionService(db)