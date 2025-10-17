"""
文件模型
"""
from sqlalchemy import Column, String, Text, BigInteger, Enum, ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import BaseModel


class OCRStatus(PyEnum):
    """OCR处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class File(BaseModel):
    """
    文件模型
    """
    __tablename__ = "files"
    
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    ocr_status = Column(Enum(OCRStatus), default=OCRStatus.PENDING, nullable=False)
    ocr_engine = Column(String(50))
    ocr_result = Column(Text)
    
    # 关系 - 使用字符串引用避免循环导入
    project = relationship("Project", back_populates="files")
    slices = relationship("Slice", back_populates="file", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<File(filename='{self.filename}', project_id='{self.project_id}')>"