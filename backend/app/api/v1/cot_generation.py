"""
CoT生成相关API端点
"""
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.slice import Slice
from ...models.project import Project
from ...models.cot import COTItem
from ...schemas.cot import COTCreate, COTResponse, COTCandidateCreate
from ...services.cot_generation_service import create_cot_generation_service
from ...services.cot_service import COTService
from ...middleware.auth import get_current_user
from ...models.user import User


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate-question", response_model=dict)
async def generate_question(
    slice_id: UUID,
    context: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    基于文本片段生成CoT问题
    """
    try:
        # 获取文本片段
        slice_obj = db.query(Slice).filter(Slice.id == str(slice_id)).first()
        if not slice_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slice not found"
            )
        
        # 检查用户权限（通过项目权限）
        project = db.query(Project).filter(Project.id == slice_obj.file.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # 简单权限检查（可以根据需要扩展）
        if project.owner != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        # 生成问题
        cot_service = create_cot_generation_service()
        question = await cot_service.generate_question(
            slice_content=slice_obj.content,
            context=context
        )
        
        return {
            "question": question,
            "slice_id": slice_id,
            "slice_content_length": len(slice_obj.content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate question: {str(e)}"
        )


@router.post("/generate-candidates", response_model=dict)
async def generate_candidates(
    slice_id: UUID,
    question: str,
    candidate_count: Optional[int] = None,
    context: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成CoT候选答案
    """
    try:
        # 获取文本片段
        slice_obj = db.query(Slice).filter(Slice.id == str(slice_id)).first()
        if not slice_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slice not found"
            )
        
        # 检查用户权限
        project = db.query(Project).filter(Project.id == slice_obj.file.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        if project.owner != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        # 生成候选答案
        cot_service = create_cot_generation_service()
        candidates = await cot_service.generate_candidates(
            question=question,
            slice_content=slice_obj.content,
            candidate_count=candidate_count,
            context=context
        )
        
        return {
            "candidates": [candidate.dict() for candidate in candidates],
            "question": question,
            "slice_id": slice_id,
            "candidate_count": len(candidates)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating candidates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate candidates: {str(e)}"
        )


@router.post("/generate-cot", response_model=COTResponse)
async def generate_complete_cot(
    slice_id: UUID,
    candidate_count: Optional[int] = None,
    context: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成完整的CoT数据项（问题+候选答案）
    """
    try:
        # 获取文本片段
        slice_obj = db.query(Slice).filter(Slice.id == str(slice_id)).first()
        if not slice_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slice not found"
            )
        
        # 检查用户权限
        project = db.query(Project).filter(Project.id == slice_obj.file.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        if project.owner != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        # 生成完整CoT数据
        cot_generation_service = create_cot_generation_service()
        cot_create = await cot_generation_service.generate_cot_item(
            project_id=UUID(project.id),
            slice_id=slice_id,
            slice_content=slice_obj.content,
            created_by=current_user.username,
            candidate_count=candidate_count,
            context=context
        )
        
        # 保存到数据库
        cot_service = COTService(db)
        cot_item = await cot_service.create_cot_item(cot_create)
        
        return cot_item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating complete CoT: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate CoT: {str(e)}"
        )


@router.post("/regenerate-question/{cot_id}", response_model=dict)
async def regenerate_question(
    cot_id: UUID,
    context: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    重新生成CoT问题
    """
    try:
        # 获取CoT项目
        cot_item = db.query(COTItem).filter(COTItem.id == str(cot_id)).first()
        if not cot_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CoT item not found"
            )
        
        # 检查用户权限
        project = db.query(Project).filter(Project.id == cot_item.project_id).first()
        if not project or project.owner != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this CoT item"
            )
        
        # 获取关联的文本片段
        slice_obj = db.query(Slice).filter(Slice.id == cot_item.slice_id).first()
        if not slice_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated slice not found"
            )
        
        # 重新生成问题
        cot_service = create_cot_generation_service()
        new_question = await cot_service.regenerate_question(
            cot_item_id=cot_id,
            slice_content=slice_obj.content,
            context=context
        )
        
        return {
            "new_question": new_question,
            "old_question": cot_item.question,
            "cot_id": cot_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate question: {str(e)}"
        )


@router.post("/regenerate-candidates/{cot_id}", response_model=dict)
async def regenerate_candidates(
    cot_id: UUID,
    candidate_count: Optional[int] = None,
    context: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    重新生成CoT候选答案
    """
    try:
        # 获取CoT项目
        cot_item = db.query(COTItem).filter(COTItem.id == str(cot_id)).first()
        if not cot_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CoT item not found"
            )
        
        # 检查用户权限
        project = db.query(Project).filter(Project.id == cot_item.project_id).first()
        if not project or project.owner != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this CoT item"
            )
        
        # 获取关联的文本片段
        slice_obj = db.query(Slice).filter(Slice.id == cot_item.slice_id).first()
        if not slice_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated slice not found"
            )
        
        # 重新生成候选答案
        cot_service = create_cot_generation_service()
        new_candidates = await cot_service.regenerate_candidates(
            question=cot_item.question,
            slice_content=slice_obj.content,
            candidate_count=candidate_count,
            context=context
        )
        
        return {
            "new_candidates": [candidate.dict() for candidate in new_candidates],
            "question": cot_item.question,
            "cot_id": cot_id,
            "candidate_count": len(new_candidates)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating candidates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate candidates: {str(e)}"
        )


@router.get("/providers", response_model=dict)
async def get_available_providers(
    current_user: User = Depends(get_current_user)
):
    """
    获取可用的LLM提供商列表
    """
    try:
        cot_service = create_cot_generation_service()
        providers = cot_service.llm_service.get_available_providers()
        
        return {
            "providers": providers,
            "default_provider": cot_service.llm_service.default_provider
        }
        
    except Exception as e:
        logger.error(f"Error getting providers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get providers: {str(e)}"
        )