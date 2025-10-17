"""
项目相关Pydantic模式
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID

from .common import BaseSchema
from ..models.project import ProjectType, ProjectStatus


class ProjectBase(BaseModel):
    """项目基础模式"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    tags: List[str] = []
    project_type: ProjectType = ProjectType.STANDARD


class ProjectCreate(ProjectBase):
    """项目创建模式"""
    pass


class ProjectUpdate(BaseModel):
    """项目更新模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    project_type: Optional[ProjectType] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(BaseSchema, ProjectBase):
    """项目响应模式"""
    owner_id: UUID
    owner_name: Optional[str] = None  # 添加所有者用户名
    status: ProjectStatus
    file_count: int = 0
    cot_count: int = 0
    kg_count: int = 0  # 知识图谱实体数量