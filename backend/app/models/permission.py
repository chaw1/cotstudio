"""
权限相关模型
"""
from sqlalchemy import Column, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime

from .base import BaseModel


class ProjectPermission(PyEnum):
    """项目权限枚举"""
    VIEW = "view"                    # 查看权限
    CREATE = "create"                # 创建权限
    EDIT = "edit"                    # 编辑权限
    DELETE = "delete"                # 删除权限
    ADMIN = "admin"                  # 管理权限


class UserProjectPermission(BaseModel):
    """用户项目权限关联模型"""
    __tablename__ = "user_project_permissions"
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    permissions = Column(JSON, default=list, nullable=False)  # 权限列表
    granted_by = Column(String(36), ForeignKey("users.id"))   # 授权人
    granted_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", foreign_keys=[user_id], back_populates="project_permissions")
    project = relationship("Project")
    granter = relationship("User", foreign_keys=[granted_by])
    
    def __repr__(self):
        return f"<UserProjectPermission(user_id='{self.user_id}', project_id='{self.project_id}', permissions={self.permissions})>"