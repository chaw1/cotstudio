"""
文件相关Pydantic模式
"""
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID

from .common import BaseSchema
from ..models.file import OCRStatus


class FileBase(BaseModel):
    """文件基础模式"""
    filename: str
    original_filename: str
    size: int = Field(..., gt=0)
    mime_type: str


class FileUploadResponse(BaseSchema, FileBase):
    """文件上传响应模式"""
    project_id: UUID
    file_hash: str
    ocr_status: OCRStatus
    
    class Config:
        from_attributes = True


class FileResponse(BaseSchema, FileBase):
    """文件响应模式"""
    project_id: UUID
    file_path: str
    file_hash: str
    ocr_status: OCRStatus
    ocr_engine: Optional[str] = None
    slice_count: int = 0
    
    class Config:
        from_attributes = True