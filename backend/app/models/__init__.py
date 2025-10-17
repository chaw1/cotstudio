"""
数据模型包
"""
# 导入基础模型类
from .base import Base

# 导入所有模型以确保它们被注册到SQLAlchemy
from . import user
from . import project  
from . import file
from . import slice
from . import cot
from . import knowledge_graph
from . import audit
from . import task
from . import permission
from . import export_task

# 导出具体的模型类
from .user import User, UserRole
from .project import Project
from .file import File
from .slice import Slice
from .cot import COTItem, COTCandidate
from .knowledge_graph import KGEntity, KGRelation, KGExtraction, KGEmbedding, EntityType, RelationType
from .audit import (
    AuditLog, Role, Permission, UserRole as AuditUserRole, ProjectPermission as AuditProjectPermission,
    AuditEventType, AuditSeverity, ResourceType, RoleType
)
from .task import TaskMonitor, TaskStatus, TaskType, TaskPriority
from .permission import ProjectPermission, UserProjectPermission
from .export_task import ExportTask

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Project", 
    "File",
    "Slice",
    "COTItem",
    "COTCandidate",
    "KGEntity",
    "KGRelation", 
    "KGExtraction",
    "KGEmbedding",
    "EntityType",
    "RelationType",
    "AuditLog",
    "Role",
    "Permission", 
    "AuditUserRole",
    "AuditProjectPermission",
    "AuditEventType",
    "AuditSeverity",
    "ResourceType",
    "RoleType",
    "TaskMonitor",
    "TaskStatus",
    "TaskType",
    "TaskPriority",
    "ProjectPermission",
    "UserProjectPermission",
    "ExportTask"
]