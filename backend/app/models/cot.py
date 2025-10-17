"""
CoT数据模型
"""
from sqlalchemy import Column, String, Text, Float, Boolean, Integer, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import BaseModel


class COTSource(PyEnum):
    """CoT数据来源枚举"""
    MANUAL = "manual"
    HUMAN_AI = "human_ai"
    GENERALIZATION = "generalization"


class COTStatus(PyEnum):
    """CoT数据状态枚举"""
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"


class COTItem(BaseModel):
    """
    CoT数据项模型
    """
    __tablename__ = "cot_items"
    
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    slice_id = Column(String(36), ForeignKey("slices.id"), nullable=False)
    question = Column(Text, nullable=False)
    chain_of_thought = Column(Text)
    source = Column(Enum(COTSource), default=COTSource.MANUAL, nullable=False)
    status = Column(Enum(COTStatus), default=COTStatus.DRAFT, nullable=False)
    llm_metadata = Column(JSON)
    created_by = Column(String(255), nullable=False)
    reviewed_by = Column(String(255))
    
    # 关系 - 使用字符串引用避免循环导入
    project = relationship("Project", back_populates="cot_items")
    slice = relationship("Slice", back_populates="cot_items")
    candidates = relationship("COTCandidate", back_populates="cot_item", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<COTItem(project_id='{self.project_id}', status='{self.status}')>"


class COTCandidate(BaseModel):
    """
    CoT候选答案模型
    """
    __tablename__ = "cot_candidates"
    
    cot_item_id = Column(String(36), ForeignKey("cot_items.id"), nullable=False)
    text = Column(Text, nullable=False)
    chain_of_thought = Column(Text)
    score = Column(Float, default=0.0, nullable=False)
    chosen = Column(Boolean, default=False, nullable=False)
    rank = Column(Integer, nullable=False)
    
    # 关系 - 使用字符串引用避免循环导入
    cot_item = relationship("COTItem", back_populates="candidates")
    
    def __repr__(self):
        return f"<COTCandidate(cot_item_id='{self.cot_item_id}', rank={self.rank}, chosen={self.chosen})>"