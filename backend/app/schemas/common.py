"""
通用Pydantic模式
"""
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

T = TypeVar('T')


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    success: bool = True


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模式"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


class ResponseModel(BaseModel, Generic[T]):
    """通用响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[T] = None
    
    class Config:
        from_attributes = True


class BaseSchema(BaseModel):
    """基础模式类"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True