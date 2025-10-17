"""
用户模型
"""
from sqlalchemy import Column, String, Boolean, JSON, Enum, DateTime, Integer
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime

from .base import BaseModel


class UserRole(PyEnum):
    """用户角色枚举"""
    SUPER_ADMIN = "SUPER_ADMIN"      # 超级管理员
    ADMIN = "ADMIN"                  # 管理员
    USER = "USER"                    # 普通用户
    VIEWER = "VIEWER"                # 只读用户


class User(BaseModel):
    """
    用户模型
    """
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    roles = Column(JSON, default=list, nullable=False)
    
    # 新增字段
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    department = Column(String(100))  # 部门
    last_login = Column(DateTime)     # 最后登录时间
    login_count = Column(Integer, default=0)  # 登录次数
    
    # 关系 - 使用字符串引用避免循环导入
    projects = relationship("Project", back_populates="owner_user", cascade="all, delete-orphan")
    project_permissions = relationship("UserProjectPermission", 
                                     foreign_keys="UserProjectPermission.user_id",
                                     back_populates="user")
    export_tasks = relationship("ExportTask", back_populates="user")
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"