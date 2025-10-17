"""
CoT相关Pydantic模式
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID

from .common import BaseSchema
from ..models.cot import COTSource, COTStatus


class COTCandidateBase(BaseModel):
    """CoT候选答案基础模式"""
    text: str = Field(..., min_length=1)
    chain_of_thought: Optional[str] = None
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    chosen: bool = False
    rank: int = Field(..., ge=1)


class COTCandidateCreate(COTCandidateBase):
    """CoT候选答案创建模式"""
    pass


class COTCandidateResponse(BaseSchema, COTCandidateBase):
    """CoT候选答案响应模式"""
    cot_item_id: UUID
    
    class Config:
        from_attributes = True


class COTBase(BaseModel):
    """CoT数据基础模式"""
    question: str = Field(..., min_length=1)
    chain_of_thought: Optional[str] = None
    source: COTSource = COTSource.MANUAL
    status: COTStatus = COTStatus.DRAFT


class COTCreate(COTBase):
    """CoT数据创建模式"""
    project_id: UUID
    slice_id: UUID
    candidates: List[COTCandidateCreate] = []
    llm_metadata: Optional[Dict[str, Any]] = None


class COTResponse(BaseSchema, COTBase):
    """CoT数据响应模式"""
    project_id: UUID
    slice_id: UUID
    created_by: str
    reviewed_by: Optional[str] = None
    llm_metadata: Optional[Dict[str, Any]] = None
    candidates: List[COTCandidateResponse] = []
    
    class Config:
        from_attributes = True