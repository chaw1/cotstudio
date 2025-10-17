"""
切片模型
"""
from sqlalchemy import Column, String, Text, Integer, Enum, ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import BaseModel


class SliceType(PyEnum):
    """切片类型枚举"""
    PARAGRAPH = "paragraph"
    IMAGE = "image"
    TABLE = "table"
    HEADER = "header"
    FOOTER = "footer"


class Slice(BaseModel):
    """
    文档切片模型
    """
    __tablename__ = "slices"
    
    file_id = Column(String(36), ForeignKey("files.id"), nullable=False)
    content = Column(Text, nullable=False)
    start_offset = Column(Integer)
    end_offset = Column(Integer)
    slice_type = Column(Enum(SliceType), default=SliceType.PARAGRAPH, nullable=False)
    page_number = Column(Integer)
    sequence_number = Column(Integer, nullable=False)
    
    # 关系 - 使用字符串引用避免循环导入
    file = relationship("File", back_populates="slices")
    cot_items = relationship("COTItem", back_populates="slice", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Slice(file_id='{self.file_id}', type='{self.slice_type}', seq={self.sequence_number})>"