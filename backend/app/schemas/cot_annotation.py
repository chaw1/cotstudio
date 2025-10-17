"""
CoT标注相关Pydantic模式
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID

from ..models.cot import COTSource, COTStatus
from .cot import COTCandidateCreate, COTCreate


class COTCandidateAnnotation(BaseModel):
    """CoT候选答案标注模式"""
    text: str = Field(..., min_length=1)
    chain_of_thought: Optional[str] = None
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    chosen: bool = False
    rank: int = Field(..., ge=1)
    
    @validator('score')
    def validate_score(cls, v):
        """验证分数精度"""
        # 确保分数精度为0.1
        return round(v, 1)


class COTAnnotationCreate(BaseModel):
    """CoT标注创建模式"""
    project_id: UUID
    slice_id: UUID
    question: str = Field(..., min_length=1)
    chain_of_thought: Optional[str] = None
    source: COTSource = COTSource.MANUAL
    candidates: List[COTCandidateAnnotation] = Field(..., min_items=1, max_items=5)
    
    @validator('candidates')
    def validate_candidates(cls, v):
        """验证候选答案"""
        if not v:
            raise ValueError("At least one candidate is required")
        
        if len(v) > 5:
            raise ValueError("Maximum 5 candidates allowed")
        
        # 检查chosen标记唯一性
        chosen_count = sum(1 for candidate in v if candidate.chosen)
        if chosen_count > 1:
            raise ValueError("Only one candidate can be marked as chosen")
        
        # 检查排序唯一性
        ranks = [candidate.rank for candidate in v]
        if len(ranks) != len(set(ranks)):
            raise ValueError("Candidate ranks must be unique")
        
        # 检查排序连续性
        sorted_ranks = sorted(ranks)
        expected_ranks = list(range(1, len(v) + 1))
        if sorted_ranks != expected_ranks:
            raise ValueError("Candidate ranks must be consecutive starting from 1")
        
        return v
    
    def to_cot_create(self, created_by: str) -> COTCreate:
        """转换为COTCreate模式"""
        candidates = [
            COTCandidateCreate(
                text=candidate.text,
                chain_of_thought=candidate.chain_of_thought,
                score=candidate.score,
                chosen=candidate.chosen,
                rank=candidate.rank
            )
            for candidate in self.candidates
        ]
        
        return COTCreate(
            project_id=self.project_id,
            slice_id=self.slice_id,
            question=self.question,
            chain_of_thought=self.chain_of_thought,
            source=self.source,
            status=COTStatus.DRAFT,
            candidates=candidates
        )


class COTAnnotationUpdate(BaseModel):
    """CoT标注更新模式"""
    question: Optional[str] = None
    chain_of_thought: Optional[str] = None
    status: Optional[COTStatus] = None
    candidates: Optional[List[COTCandidateAnnotation]] = None
    
    @validator('question')
    def validate_question(cls, v):
        """验证问题"""
        if v is not None and not v.strip():
            raise ValueError("Question cannot be empty")
        return v
    
    @validator('candidates')
    def validate_candidates(cls, v):
        """验证候选答案"""
        if v is not None:
            if not v:
                raise ValueError("At least one candidate is required")
            
            if len(v) > 5:
                raise ValueError("Maximum 5 candidates allowed")
            
            # 检查chosen标记唯一性
            chosen_count = sum(1 for candidate in v if candidate.chosen)
            if chosen_count > 1:
                raise ValueError("Only one candidate can be marked as chosen")
            
            # 检查排序唯一性
            ranks = [candidate.rank for candidate in v]
            if len(ranks) != len(set(ranks)):
                raise ValueError("Candidate ranks must be unique")
        
        return v


class COTCandidateUpdate(BaseModel):
    """CoT候选答案更新模式"""
    candidate_id: UUID
    score: Optional[float] = Field(None, ge=0.0, le=1.0)
    chosen: Optional[bool] = None
    rank: Optional[int] = Field(None, ge=1)
    
    @validator('score')
    def validate_score(cls, v):
        """验证分数精度"""
        if v is not None:
            return round(v, 1)
        return v


class COTStatusUpdate(BaseModel):
    """CoT状态更新模式"""
    status: COTStatus
    
    @validator('status')
    def validate_status(cls, v):
        """验证状态"""
        if v not in [COTStatus.DRAFT, COTStatus.REVIEWED, COTStatus.APPROVED, COTStatus.REJECTED]:
            raise ValueError("Invalid status")
        return v


class COTBatchUpdate(BaseModel):
    """CoT批量更新模式"""
    cot_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    status: Optional[COTStatus] = None
    
    @validator('cot_ids')
    def validate_cot_ids(cls, v):
        """验证CoT ID列表"""
        if len(v) > 100:
            raise ValueError("Maximum 100 CoT items can be updated in batch")
        
        # 检查重复ID
        if len(v) != len(set(v)):
            raise ValueError("Duplicate CoT IDs found")
        
        return v


class COTValidationResult(BaseModel):
    """CoT验证结果模式"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    
    
class COTAnnotationStats(BaseModel):
    """CoT标注统计模式"""
    total_count: int
    draft_count: int
    reviewed_count: int
    approved_count: int
    rejected_count: int
    completion_rate: float = Field(..., ge=0.0, le=1.0)
    
    @validator('completion_rate')
    def validate_completion_rate(cls, v):
        """验证完成率精度"""
        return round(v, 3)


class COTQualityMetrics(BaseModel):
    """CoT质量指标模式"""
    average_score: float = Field(..., ge=0.0, le=1.0)
    score_distribution: dict  # {score_range: count}
    chosen_distribution: dict  # {rank: count}
    question_length_stats: dict  # {min, max, avg}
    answer_length_stats: dict  # {min, max, avg}
    
    @validator('average_score')
    def validate_average_score(cls, v):
        """验证平均分精度"""
        return round(v, 3)