"""
审计日志和权限相关模型
"""
from sqlalchemy import Column, String, Text, JSON, Enum, ForeignKey, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime

from .base import BaseModel


class AuditEventType(PyEnum):
    """审计事件类型枚举"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    PERMISSION_CHANGE = "permission_change"
    EXPORT = "export"
    IMPORT = "import"
    SYSTEM_CONFIG = "system_config"


class AuditSeverity(PyEnum):
    """审计事件严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResourceType(PyEnum):
    """资源类型枚举"""
    PROJECT = "project"
    FILE = "file"
    COT_ITEM = "cot_item"
    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    SYSTEM_SETTING = "system_setting"
    KNOWLEDGE_GRAPH = "knowledge_graph"


class RoleType(PyEnum):
    """角色类型枚举"""
    ADMIN = "admin"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class AuditLog(BaseModel):
    """
    审计日志模型
    """
    __tablename__ = "audit_logs"
    
    # 基本信息
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # 可能是系统操作
    event_type = Column(Enum(AuditEventType), nullable=False)
    severity = Column(Enum(AuditSeverity), default=AuditSeverity.LOW, nullable=False)
    
    # 资源信息
    resource_type = Column(Enum(ResourceType), nullable=True)
    resource_id = Column(String(36), nullable=True)
    resource_name = Column(String(255), nullable=True)
    
    # 操作详情
    action = Column(String(100), nullable=False)
    description = Column(Text)
    details = Column(JSON, default=dict, nullable=False)
    
    # 请求信息
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(Text)
    request_id = Column(String(36))
    
    # 结果信息
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text)
    
    # 变更信息
    old_values = Column(JSON, default=dict, nullable=False)
    new_values = Column(JSON, default=dict, nullable=False)
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    
    # 索引
    __table_args__ = (
        Index('idx_audit_user_time', 'user_id', 'created_at'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_event_time', 'event_type', 'created_at'),
        Index('idx_audit_severity', 'severity'),
    )
    
    def __repr__(self):
        return f"<AuditLog(user_id='{self.user_id}', action='{self.action}', resource='{self.resource_type}:{self.resource_id}')>"


class Role(BaseModel):
    """
    角色模型
    """
    __tablename__ = "roles"
    
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    role_type = Column(Enum(RoleType), nullable=False)
    is_system_role = Column(Boolean, default=False, nullable=False)  # 系统内置角色不可删除
    permissions = Column(JSON, default=list, nullable=False)  # 权限列表
    
    # 关系
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    project_permissions = relationship("ProjectPermission", back_populates="role", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Role(name='{self.name}', type='{self.role_type}')>"


class Permission(BaseModel):
    """
    权限模型
    """
    __tablename__ = "permissions"
    
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    resource_type = Column(Enum(ResourceType), nullable=False)
    action = Column(String(50), nullable=False)  # create, read, update, delete, etc.
    is_system_permission = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f"<Permission(name='{self.name}', resource='{self.resource_type}', action='{self.action}')>"


class UserRole(BaseModel):
    """
    用户角色关联模型
    """
    __tablename__ = "user_roles"
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    granted_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # 角色过期时间，None表示永不过期
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")
    granted_by_user = relationship("User", foreign_keys=[granted_by])
    
    # 复合唯一索引
    __table_args__ = (
        Index('idx_user_role_unique', 'user_id', 'role_id', unique=True),
        Index('idx_user_role_expires', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<UserRole(user_id='{self.user_id}', role_id='{self.role_id}')>"


class ProjectPermission(BaseModel):
    """
    项目级权限模型
    """
    __tablename__ = "project_permissions"
    
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=True)
    permission_type = Column(String(50), nullable=False)  # owner, editor, reviewer, viewer
    granted_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    project = relationship("Project")
    user = relationship("User", foreign_keys=[user_id])
    role = relationship("Role", back_populates="project_permissions")
    granted_by_user = relationship("User", foreign_keys=[granted_by])
    
    # 索引
    __table_args__ = (
        Index('idx_project_user_permission', 'project_id', 'user_id'),
        Index('idx_project_role_permission', 'project_id', 'role_id'),
    )
    
    def __repr__(self):
        return f"<ProjectPermission(project_id='{self.project_id}', permission='{self.permission_type}')>"