"""
CoT服务
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.cot import COTItem, COTCandidate, COTStatus
from ..schemas.cot import COTCreate, COTResponse, COTCandidateCreate, COTCandidateResponse
from ..schemas.cot_annotation import COTAnnotationStats, COTQualityMetrics, COTValidationResult
from .base_service import BaseService


logger = logging.getLogger(__name__)


class COTService(BaseService[COTItem]):
    """
    CoT服务类
    """
    
    def __init__(self, db: Session):
        super().__init__(COTItem)
        self.db = db
    
    def get_by_project(self, project_id: str) -> List[COTItem]:
        """
        根据项目ID获取CoT数据列表
        """
        return self.db.query(COTItem).filter(COTItem.project_id == project_id).all()
    
    def get_by_slice(self, slice_id: str) -> List[COTItem]:
        """
        根据切片ID获取CoT数据列表
        """
        return self.db.query(COTItem).filter(COTItem.slice_id == slice_id).all()
    
    async def create_cot_item(self, cot_create: COTCreate) -> COTResponse:
        """
        创建CoT数据项
        """
        try:
            # 创建CoT项目
            cot_item = COTItem(
                project_id=str(cot_create.project_id),
                slice_id=str(cot_create.slice_id),
                question=cot_create.question,
                chain_of_thought=cot_create.chain_of_thought,
                source=cot_create.source,
                status=cot_create.status,
                llm_metadata=cot_create.llm_metadata,
                created_by="system"  # 临时设置，应该从认证中获取
            )
            
            self.db.add(cot_item)
            self.db.flush()  # 获取ID但不提交
            
            # 创建候选答案
            candidates = []
            for candidate_create in cot_create.candidates:
                candidate = COTCandidate(
                    cot_item_id=cot_item.id,
                    text=candidate_create.text,
                    chain_of_thought=candidate_create.chain_of_thought,
                    score=candidate_create.score,
                    chosen=candidate_create.chosen,
                    rank=candidate_create.rank
                )
                self.db.add(candidate)
                candidates.append(candidate)
            
            self.db.commit()
            self.db.refresh(cot_item)
            
            # 转换为响应模型
            candidate_responses = [
                COTCandidateResponse(
                    id=UUID(candidate.id),
                    cot_item_id=UUID(candidate.cot_item_id),
                    text=candidate.text,
                    chain_of_thought=candidate.chain_of_thought,
                    score=candidate.score,
                    chosen=candidate.chosen,
                    rank=candidate.rank,
                    created_at=candidate.created_at,
                    updated_at=candidate.updated_at
                )
                for candidate in candidates
            ]
            
            return COTResponse(
                id=UUID(cot_item.id),
                project_id=UUID(cot_item.project_id),
                slice_id=UUID(cot_item.slice_id),
                question=cot_item.question,
                chain_of_thought=cot_item.chain_of_thought,
                source=cot_item.source,
                status=cot_item.status,
                created_by=cot_item.created_by,
                reviewed_by=cot_item.reviewed_by,
                llm_metadata=cot_item.llm_metadata,
                candidates=candidate_responses,
                created_at=cot_item.created_at,
                updated_at=cot_item.updated_at
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating CoT item: {str(e)}")
            raise
    
    def update_cot_question(self, cot_id: UUID, new_question: str) -> COTItem:
        """
        更新CoT问题
        """
        try:
            cot_item = self.db.query(COTItem).filter(COTItem.id == str(cot_id)).first()
            if not cot_item:
                raise ValueError(f"CoT item {cot_id} not found")
            
            cot_item.question = new_question
            cot_item.status = COTStatus.DRAFT  # 重置状态为草稿
            
            self.db.commit()
            self.db.refresh(cot_item)
            
            return cot_item
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating CoT question: {str(e)}")
            raise
    
    def update_candidates(self, cot_id: UUID, new_candidates: List[COTCandidateCreate]) -> List[COTCandidate]:
        """
        更新CoT候选答案
        """
        try:
            # 删除现有候选答案
            self.db.query(COTCandidate).filter(COTCandidate.cot_item_id == str(cot_id)).delete()
            
            # 创建新的候选答案
            candidates = []
            for candidate_create in new_candidates:
                candidate = COTCandidate(
                    cot_item_id=str(cot_id),
                    text=candidate_create.text,
                    chain_of_thought=candidate_create.chain_of_thought,
                    score=candidate_create.score,
                    chosen=candidate_create.chosen,
                    rank=candidate_create.rank
                )
                self.db.add(candidate)
                candidates.append(candidate)
            
            # 更新CoT项目状态
            cot_item = self.db.query(COTItem).filter(COTItem.id == str(cot_id)).first()
            if cot_item:
                cot_item.status = COTStatus.DRAFT
            
            self.db.commit()
            
            return candidates
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating CoT candidates: {str(e)}")
            raise
    
    def update_candidate_scores(self, candidate_updates: List[dict]) -> List[COTCandidate]:
        """
        更新候选答案分数和选择状态
        """
        try:
            updated_candidates = []
            
            for update in candidate_updates:
                candidate_id = update.get("candidate_id")
                score = update.get("score")
                chosen = update.get("chosen")
                rank = update.get("rank")
                
                candidate = self.db.query(COTCandidate).filter(
                    COTCandidate.id == str(candidate_id)
                ).first()
                
                if candidate:
                    if score is not None:
                        candidate.score = score
                    if chosen is not None:
                        candidate.chosen = chosen
                    if rank is not None:
                        candidate.rank = rank
                    
                    updated_candidates.append(candidate)
            
            self.db.commit()
            
            return updated_candidates
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating candidate scores: {str(e)}")
            raise
    
    def validate_cot_data(self, cot_id: UUID) -> COTValidationResult:
        """
        验证CoT数据完整性和质量
        """
        try:
            errors = []
            warnings = []
            
            # 获取CoT项目
            cot_item = self.db.query(COTItem).filter(COTItem.id == str(cot_id)).first()
            if not cot_item:
                errors.append("CoT item not found")
                return COTValidationResult(is_valid=False, errors=errors)
            
            # 验证问题
            if not cot_item.question or not cot_item.question.strip():
                errors.append("Question is required")
            elif len(cot_item.question.strip()) < 10:
                warnings.append("Question is too short (less than 10 characters)")
            
            # 验证候选答案
            candidates = self.db.query(COTCandidate).filter(
                COTCandidate.cot_item_id == str(cot_id)
            ).all()
            
            if not candidates:
                errors.append("At least one candidate is required")
            else:
                # 检查chosen标记
                chosen_candidates = [c for c in candidates if c.chosen]
                if not chosen_candidates:
                    warnings.append("No candidate is marked as chosen")
                elif len(chosen_candidates) > 1:
                    errors.append("Multiple candidates marked as chosen")
                
                # 检查排序
                ranks = [c.rank for c in candidates]
                if len(ranks) != len(set(ranks)):
                    errors.append("Duplicate ranks found")
                
                expected_ranks = list(range(1, len(candidates) + 1))
                if sorted(ranks) != expected_ranks:
                    errors.append("Ranks must be consecutive starting from 1")
                
                # 检查分数
                for candidate in candidates:
                    if not (0.0 <= candidate.score <= 1.0):
                        errors.append(f"Invalid score {candidate.score} for candidate {candidate.id}")
                    
                    if not candidate.text or not candidate.text.strip():
                        errors.append(f"Empty text for candidate {candidate.id}")
                    elif len(candidate.text.strip()) < 5:
                        warnings.append(f"Very short text for candidate {candidate.id}")
            
            is_valid = len(errors) == 0
            return COTValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
            
        except Exception as e:
            logger.error(f"Error validating CoT data: {str(e)}")
            return COTValidationResult(
                is_valid=False, 
                errors=[f"Validation error: {str(e)}"]
            )
    
    def get_project_annotation_stats(self, project_id: str) -> COTAnnotationStats:
        """
        获取项目标注统计信息
        """
        try:
            # 统计各状态的数量
            status_counts = self.db.query(
                COTItem.status,
                func.count(COTItem.id).label('count')
            ).filter(
                COTItem.project_id == project_id
            ).group_by(COTItem.status).all()
            
            # 初始化计数
            total_count = 0
            draft_count = 0
            reviewed_count = 0
            approved_count = 0
            rejected_count = 0
            
            # 填充计数
            for status, count in status_counts:
                total_count += count
                if status == COTStatus.DRAFT:
                    draft_count = count
                elif status == COTStatus.REVIEWED:
                    reviewed_count = count
                elif status == COTStatus.APPROVED:
                    approved_count = count
                elif status == COTStatus.REJECTED:
                    rejected_count = count
            
            # 计算完成率（reviewed + approved）
            completion_rate = 0.0
            if total_count > 0:
                completion_rate = (reviewed_count + approved_count) / total_count
            
            return COTAnnotationStats(
                total_count=total_count,
                draft_count=draft_count,
                reviewed_count=reviewed_count,
                approved_count=approved_count,
                rejected_count=rejected_count,
                completion_rate=completion_rate
            )
            
        except Exception as e:
            logger.error(f"Error getting annotation stats: {str(e)}")
            raise
    
    def get_project_quality_metrics(self, project_id: str) -> COTQualityMetrics:
        """
        获取项目质量指标
        """
        try:
            # 获取所有候选答案
            candidates = self.db.query(COTCandidate).join(COTItem).filter(
                COTItem.project_id == project_id
            ).all()
            
            if not candidates:
                return COTQualityMetrics(
                    average_score=0.0,
                    score_distribution={},
                    chosen_distribution={},
                    question_length_stats={},
                    answer_length_stats={}
                )
            
            # 计算平均分
            scores = [c.score for c in candidates]
            average_score = sum(scores) / len(scores)
            
            # 分数分布（按0.1区间）
            score_distribution = {}
            for score in scores:
                bucket = f"{int(score * 10) / 10:.1f}-{int(score * 10 + 1) / 10:.1f}"
                score_distribution[bucket] = score_distribution.get(bucket, 0) + 1
            
            # chosen分布（按排名）
            chosen_candidates = [c for c in candidates if c.chosen]
            chosen_distribution = {}
            for candidate in chosen_candidates:
                rank = candidate.rank
                chosen_distribution[f"rank_{rank}"] = chosen_distribution.get(f"rank_{rank}", 0) + 1
            
            # 问题长度统计
            cot_items = self.db.query(COTItem).filter(COTItem.project_id == project_id).all()
            question_lengths = [len(item.question) for item in cot_items if item.question]
            question_length_stats = {
                "min": min(question_lengths) if question_lengths else 0,
                "max": max(question_lengths) if question_lengths else 0,
                "avg": sum(question_lengths) / len(question_lengths) if question_lengths else 0
            }
            
            # 答案长度统计
            answer_lengths = [len(c.text) for c in candidates if c.text]
            answer_length_stats = {
                "min": min(answer_lengths) if answer_lengths else 0,
                "max": max(answer_lengths) if answer_lengths else 0,
                "avg": sum(answer_lengths) / len(answer_lengths) if answer_lengths else 0
            }
            
            return COTQualityMetrics(
                average_score=average_score,
                score_distribution=score_distribution,
                chosen_distribution=chosen_distribution,
                question_length_stats=question_length_stats,
                answer_length_stats=answer_length_stats
            )
            
        except Exception as e:
            logger.error(f"Error getting quality metrics: {str(e)}")
            raise
    
    def update_cot_status(self, cot_id: UUID, new_status: COTStatus, reviewed_by: Optional[str] = None) -> COTItem:
        """
        更新CoT状态
        """
        try:
            cot_item = self.db.query(COTItem).filter(COTItem.id == str(cot_id)).first()
            if not cot_item:
                raise ValueError(f"CoT item {cot_id} not found")
            
            # 验证状态转换
            valid_transitions = {
                COTStatus.DRAFT: [COTStatus.REVIEWED, COTStatus.REJECTED],
                COTStatus.REVIEWED: [COTStatus.APPROVED, COTStatus.DRAFT, COTStatus.REJECTED],
                COTStatus.APPROVED: [COTStatus.DRAFT],
                COTStatus.REJECTED: [COTStatus.DRAFT]
            }
            
            if new_status not in valid_transitions.get(cot_item.status, []):
                raise ValueError(f"Invalid status transition from {cot_item.status} to {new_status}")
            
            # 更新状态
            cot_item.status = new_status
            if new_status == COTStatus.REVIEWED and reviewed_by:
                cot_item.reviewed_by = reviewed_by
            
            self.db.commit()
            self.db.refresh(cot_item)
            
            return cot_item
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating CoT status: {str(e)}")
            raise