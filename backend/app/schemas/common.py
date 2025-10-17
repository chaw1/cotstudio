"""
通用Pydantic模式
"""
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, field_serializer
from datetime import datetime
from uuid import UUID
from app.core.timezone_utils import to_beijing_time

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
    """
    基础模式类
    自动将datetime字段转换为北京时间(UTC+8)
    """
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime) -> datetime:
        """将datetime序列化为北京时间"""
        result = to_beijing_time(dt)
        return result if result is not None else dt
    
    class Config:
        from_attributes = True