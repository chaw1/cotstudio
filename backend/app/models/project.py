"""
项目模型
"""
from sqlalchemy import Column, String, Text, JSON, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import BaseModel


class ProjectType(PyEnum):
    """项目类型枚举"""
    STANDARD = "standard"
    RESEARCH = "research"
    COMMERCIAL = "commercial"


class ProjectStatus(PyEnum):
    """项目状态枚举"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Project(BaseModel):
    """
    项目模型
    """
    __tablename__ = "projects"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)  # Use String for SQLite compatibility
    tags = Column(JSON, default=list, nullable=False)
    project_type = Column(Enum(ProjectType), default=ProjectType.STANDARD, nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE, nullable=False)
    
    # 关系 - 使用字符串引用避免循环导入
    owner_user = relationship("User", back_populates="projects")
    files = relationship("File", back_populates="project", cascade="all, delete-orphan")
    cot_items = relationship("COTItem", back_populates="project", cascade="all, delete-orphan")
    export_tasks = relationship("ExportTask", back_populates="project")
    
    def __repr__(self):
        return f"<Project(name='{self.name}', owner_id='{self.owner_id}')>"