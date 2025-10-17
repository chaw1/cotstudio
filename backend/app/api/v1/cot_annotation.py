"""
CoT数据标注API端点
"""
# type: ignore
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.cot import COTItem, COTCandidate, COTStatus
from ...models.project import Project
from ...schemas.cot import COTResponse, COTCandidateResponse
from ...services.cot_service import COTService
from ...middleware.auth import get_current_user
from ...models.user import User
from ...schemas.cot_annotation import (
    COTAnnotationCreate,
    COTAnnotationUpdate,
    COTCandidateUpdate,
    COTStatusUpdate,
    COTBatchUpdate,
    COTAnnotationStats,
    COTQualityMetrics,
    COTValidationResult
)


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=COTResponse)
async def create_cot_annotation(
    cot_data: COTAnnotationCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建CoT数据标注
    """
    try:
        # 验证项目权限
        project = db.query(Project).filter(Project.id == str(cot_data.project_id)).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # 简单权限检查
        if project.owner_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        # 验证候选答案数据完整性
        _validate_candidates(cot_data.candidates)
        
        # 创建CoT数据
        cot_service = COTService(db)
        cot_item = await cot_service.create_cot_item(cot_data.to_cot_create(current_user["username"]))
        
        logger.info(f"Created CoT annotation {cot_item.id} by user {current_user['username']}")
        return cot_item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating CoT annotation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create CoT annotation: {str(e)}"
        )


@router.get("/{cot_id}", response_model=COTResponse)
async def get_cot_annotation(
    cot_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取CoT数据标注详情
    """
    try:
        cot_item = db.query(COTItem).filter(COTItem.id == str(cot_id)).first()
        if not cot_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CoT annotation not found"
            )
        
        # 验证权限
        project = db.query(Project).filter(Project.id == cot_item.project_id).first()
        if not project or project.owner_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this CoT annotation"
            )
        
        # 构建响应
        candidates = db.query(COTCandidate).filter(
            COTCandidate.cot_item_id == str(cot_id)
        ).order_by(COTCandidate.rank).all()
        
        candidate_responses = [
            COTCandidateResponse.model_validate(candidate)
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting CoT annotation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get CoT annotation: {str(e)}"
        )


@router.put("/{cot_id}", response_model=COTResponse)
async def update_cot_annotation(
    cot_id: UUID,
    cot_update: COTAnnotationUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新CoT数据标注
    """
    try:
        cot_item = db.query(COTItem).filter(COTItem.id == str(cot_id)).first()
        if not cot_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CoT annotation not found"
            )
        
        # 验证权限
        project = db.query(Project).filter(Project.id == cot_item.project_id).first()
        if not project or project.owner_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this CoT annotation"
            )
        
        # 更新CoT项目
        if cot_update.question is not None:
            cot_item.question = cot_update.question
        if cot_update.chain_of_thought is not None:
            cot_item.chain_of_thought = cot_update.chain_of_thought
        if cot_update.status is not None:
            cot_item.status = cot_update.status
        
        # 更新候选答案
        if cot_update.candidates is not None:
            _validate_candidates(cot_update.candidates)
            
            # 删除现有候选答案
            db.query(COTCandidate).filter(COTCandidate.cot_item_id == str(cot_id)).delete()
            
            # 创建新的候选答案
            for candidate_data in cot_update.candidates:
                candidate = COTCandidate(
                    cot_item_id=str(cot_id),
                    text=candidate_data.text,
                    chain_of_thought=candidate_data.chain_of_thought,
                    score=candidate_data.score,
                    chosen=candidate_data.chosen,
                    rank=candidate_data.rank
                )
                db.add(candidate)
        
        # 重置状态为草稿（如果有修改）
        if cot_update.question is not None or cot_update.candidates is not None:
            cot_item.status = COTStatus.DRAFT
        
        db.commit()
        db.refresh(cot_item)
        
        # 返回更新后的数据
        return await get_cot_annotation(cot_id, current_user, db)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating CoT annotation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update CoT annotation: {str(e)}"
        )


@router.patch("/{cot_id}/candidates", response_model=List[COTCandidateResponse])
async def update_candidates_ranking(
    cot_id: UUID,
    candidate_updates: List[COTCandidateUpdate],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新候选答案排序、评分和chosen标记
    """
    try:
        cot_item = db.query(COTItem).filter(COTItem.id == str(cot_id)).first()
        if not cot_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CoT annotation not found"
            )
        
        # 验证权限
        project = db.query(Project).filter(Project.id == cot_item.project_id).first()
        if not project or project.owner_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this CoT annotation"
            )
        
        # 验证chosen标记唯一性
        chosen_count = sum(1 for update in candidate_updates if update.chosen)
        if chosen_count > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only one candidate can be marked as chosen"
            )
        
        # 更新候选答案
        updated_candidates = []
        for update in candidate_updates:
            candidate = db.query(COTCandidate).filter(
                COTCandidate.id == str(update.candidate_id),
                COTCandidate.cot_item_id == str(cot_id)
            ).first()
            
            if not candidate:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Candidate {update.candidate_id} not found"
                )
            
            if update.score is not None:
                candidate.score = update.score
            if update.chosen is not None:
                candidate.chosen = update.chosen
            if update.rank is not None:
                candidate.rank = update.rank
            
            updated_candidates.append(candidate)
        
        # 如果有chosen标记的变化，确保其他候选答案的chosen为False
        chosen_candidates = [c for c in updated_candidates if c.chosen]
        if chosen_candidates:
            # 将其他候选答案的chosen设为False
            db.query(COTCandidate).filter(
                COTCandidate.cot_item_id == str(cot_id),
                COTCandidate.id.notin_([c.id for c in chosen_candidates])
            ).update({"chosen": False})
        
        db.commit()
        
        # 返回更新后的候选答案
        candidates = db.query(COTCandidate).filter(
            COTCandidate.cot_item_id == str(cot_id)
        ).order_by(COTCandidate.rank).all()
        
        return [
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
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating candidates ranking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update candidates ranking: {str(e)}"
        )


@router.patch("/{cot_id}/status", response_model=COTResponse)
async def update_cot_status(
    cot_id: UUID,
    status_update: COTStatusUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新CoT数据标注状态
    """
    try:
        cot_item = db.query(COTItem).filter(COTItem.id == str(cot_id)).first()
        if not cot_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CoT annotation not found"
            )
        
        # 验证权限
        project = db.query(Project).filter(Project.id == cot_item.project_id).first()
        if not project or project.owner_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this CoT annotation"
            )
        
        # 状态转换验证
        if not _is_valid_status_transition(cot_item.status, status_update.status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {cot_item.status} to {status_update.status}"
            )
        
        # 如果状态为reviewed或approved，需要验证数据完整性
        if status_update.status in [COTStatus.REVIEWED, COTStatus.APPROVED]:
            _validate_cot_completeness(db, cot_id)
        
        # 更新状态
        cot_item.status = status_update.status
        if status_update.status == COTStatus.REVIEWED:
            cot_item.reviewed_by = current_user["username"]
        
        db.commit()
        db.refresh(cot_item)
        
        logger.info(f"Updated CoT {cot_id} status to {status_update.status} by user {current_user['username']}")
        
        # 返回更新后的数据
        return await get_cot_annotation(cot_id, current_user, db)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating CoT status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update CoT status: {str(e)}"
        )


@router.post("/batch-update", response_model=List[COTResponse])
async def batch_update_cot_annotations(
    batch_update: COTBatchUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量更新CoT数据标注
    """
    try:
        updated_items = []
        
        for cot_id in batch_update.cot_ids:
            cot_item = db.query(COTItem).filter(COTItem.id == str(cot_id)).first()
            if not cot_item:
                continue  # 跳过不存在的项目
            
            # 验证权限
            project = db.query(Project).filter(Project.id == cot_item.project_id).first()
            if not project or project.owner_id != current_user["user_id"]:
                continue  # 跳过无权限的项目
            
            # 应用批量更新
            if batch_update.status is not None:
                if _is_valid_status_transition(cot_item.status, batch_update.status):
                    cot_item.status = batch_update.status
                    if batch_update.status == COTStatus.REVIEWED:
                        cot_item.reviewed_by = current_user["username"]
            
            updated_items.append(cot_item)
        
        db.commit()
        
        # 返回更新后的数据
        result = []
        for cot_item in updated_items:
            cot_response = await get_cot_annotation(UUID(cot_item.id), current_user, db)
            result.append(cot_response)
        
        logger.info(f"Batch updated {len(result)} CoT annotations by user {current_user['username']}")
        return result
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in batch update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch update CoT annotations: {str(e)}"
        )


@router.delete("/{cot_id}")
async def delete_cot_annotation(
    cot_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除CoT数据标注
    """
    try:
        cot_item = db.query(COTItem).filter(COTItem.id == str(cot_id)).first()
        if not cot_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CoT annotation not found"
            )
        
        # 验证权限
        project = db.query(Project).filter(Project.id == cot_item.project_id).first()
        if not project or project.owner_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this CoT annotation"
            )
        
        # 删除候选答案（级联删除）
        db.query(COTCandidate).filter(COTCandidate.cot_item_id == str(cot_id)).delete()
        
        # 删除CoT项目
        db.delete(cot_item)
        db.commit()
        
        logger.info(f"Deleted CoT annotation {cot_id} by user {current_user['username']}")
        
        return {"message": "CoT annotation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting CoT annotation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete CoT annotation: {str(e)}"
        )


@router.get("/project/{project_id}", response_model=List[COTResponse])
async def get_project_cot_annotations(
    project_id: UUID,
    status_filter: Optional[COTStatus] = None,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取项目的CoT数据标注列表
    """
    try:
        # 验证项目权限
        project = db.query(Project).filter(Project.id == str(project_id)).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        if project.owner_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        # 构建查询
        query = db.query(COTItem).filter(COTItem.project_id == str(project_id))
        
        if status_filter:
            query = query.filter(COTItem.status == status_filter)
        
        # 分页
        cot_items = query.offset(offset).limit(limit).all()
        
        # 构建响应
        result = []
        for cot_item in cot_items:
            candidates = db.query(COTCandidate).filter(
                COTCandidate.cot_item_id == cot_item.id
            ).order_by(COTCandidate.rank).all()
            
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
            
            result.append(COTResponse(
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
            ))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project CoT annotations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project CoT annotations: {str(e)}"
        )


def _validate_candidates(candidates: List) -> None:
    """
    验证候选答案数据完整性
    """
    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one candidate is required"
        )
    
    # 检查chosen标记唯一性
    chosen_count = sum(1 for candidate in candidates if candidate.chosen)
    if chosen_count > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only one candidate can be marked as chosen"
        )
    
    # 检查排序唯一性
    ranks = [candidate.rank for candidate in candidates]
    if len(ranks) != len(set(ranks)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate ranks must be unique"
        )
    
    # 检查分数范围
    for candidate in candidates:
        if not (0.0 <= candidate.score <= 1.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Candidate scores must be between 0.0 and 1.0"
            )


def _is_valid_status_transition(current_status: COTStatus, new_status: COTStatus) -> bool:
    """
    验证状态转换是否有效
    """
    valid_transitions = {
        COTStatus.DRAFT: [COTStatus.REVIEWED, COTStatus.REJECTED],
        COTStatus.REVIEWED: [COTStatus.APPROVED, COTStatus.DRAFT, COTStatus.REJECTED],
        COTStatus.APPROVED: [COTStatus.DRAFT],
        COTStatus.REJECTED: [COTStatus.DRAFT]
    }
    
    return new_status in valid_transitions.get(current_status, [])


def _validate_cot_completeness(db: Session, cot_id: UUID) -> None:
    """
    验证CoT数据完整性
    """
    cot_item = db.query(COTItem).filter(COTItem.id == str(cot_id)).first()
    if not cot_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CoT item not found"
        )
    
    # 检查是否有问题
    if not cot_item.question or not cot_item.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question is required for review/approval"
        )
    
    # 检查是否有候选答案
    candidates = db.query(COTCandidate).filter(COTCandidate.cot_item_id == str(cot_id)).all()
    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one candidate is required for review/approval"
        )
    
    # 检查是否有chosen答案
    chosen_candidates = [c for c in candidates if c.chosen]
    if not chosen_candidates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one candidate must be marked as chosen for review/approval"
        )


@router.get("/{cot_id}/validate", response_model=COTValidationResult)
async def validate_cot_annotation(
    cot_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    验证CoT数据标注完整性
    """
    try:
        cot_item = db.query(COTItem).filter(COTItem.id == str(cot_id)).first()
        if not cot_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CoT annotation not found"
            )
        
        # 验证权限
        project = db.query(Project).filter(Project.id == cot_item.project_id).first()
        if not project or project.owner_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this CoT annotation"
            )
        
        # 执行验证
        cot_service = COTService(db)
        validation_result = cot_service.validate_cot_data(cot_id)
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating CoT annotation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate CoT annotation: {str(e)}"
        )


@router.get("/project/{project_id}/stats", response_model=COTAnnotationStats)
async def get_project_annotation_stats(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取项目标注统计信息
    """
    try:
        # 验证项目权限
        project = db.query(Project).filter(Project.id == str(project_id)).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        if project.owner_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        # 获取统计信息
        cot_service = COTService(db)
        stats = cot_service.get_project_annotation_stats(str(project_id))
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting annotation stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get annotation stats: {str(e)}"
        )


@router.get("/project/{project_id}/quality-metrics", response_model=COTQualityMetrics)
async def get_project_quality_metrics(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取项目质量指标
    """
    try:
        # 验证项目权限
        project = db.query(Project).filter(Project.id == str(project_id)).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        if project.owner_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        # 获取质量指标
        cot_service = COTService(db)
        metrics = cot_service.get_project_quality_metrics(str(project_id))
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quality metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality metrics: {str(e)}"
        )