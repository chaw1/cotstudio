"""
用户相关Pydantic模式
"""
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

from .common import BaseSchema


class UserBase(BaseModel):
    """用户基础模式"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    roles: List[str] = []


class UserCreate(UserBase):
    """用户创建模式"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """用户更新模式"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None


class UserResponse(BaseSchema, UserBase):
    """用户响应模式"""
    is_superuser: bool
    
    class Config:
        from_attributes = True


class UserInDB(UserBase):
    """数据库中的用户模式"""
    id: UUID
    hashed_password: str