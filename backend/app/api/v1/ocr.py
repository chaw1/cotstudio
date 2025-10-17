"""
OCR处理API端点
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.file_service import file_service
from app.services.slice_service import slice_service
from app.services.ocr_service import ocr_service
from app.workers.tasks import ocr_processing
from app.models.file import OCRStatus
from app.schemas.common import ResponseModel
from app.schemas.ocr import (
    OCREngineInfo, OCRRequest, OCRResponse, SliceResponse, 
    FileSlicesResponse, OCRStatusInfo, ReprocessRequest,
    SliceSearchRequest, SliceSearchResponse, SliceContext
)

router = APIRouter()


@router.get("/engines", response_model=ResponseModel[List[OCREngineInfo]])
async def get_ocr_engines():
    """
    获取可用的OCR引擎列表
    """
    try:
        available_engines = ocr_service.get_available_engines()
        
        engines_info = [
            OCREngineInfo(
                name="paddleocr",
                available="paddleocr" in available_engines,
                description="PaddleOCR - 支持中英文OCR识别，适用于PDF和图像文件"
            ),
            OCREngineInfo(
                name="fallback",
                available="fallback" in available_engines,
                description="Fallback Engine - 用于纯文本文件的文本提取"
            )
        ]
        
        return ResponseModel(
            success=True,
            data=engines_info,
            message="OCR engines retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get OCR engines: {str(e)}")


@router.post("/process", response_model=ResponseModel[OCRResponse])
async def start_ocr_processing(
    request: OCRRequest,
    db: Session = Depends(get_db)
):
    """
    启动OCR处理任务
    """
    try:
        # 验证文件存在
        file_record = file_service.get(db, id=request.file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # 检查文件状态
        if file_record.ocr_status == OCRStatus.PROCESSING:
            raise HTTPException(status_code=400, detail="File is already being processed")
        
        # 验证OCR引擎
        available_engines = ocr_service.get_available_engines()
        if request.engine not in available_engines:
            raise HTTPException(
                status_code=400, 
                detail=f"OCR engine '{request.engine}' not available. Available engines: {available_engines}"
            )
        
        # 启动异步OCR任务
        task = ocr_processing.delay(
            file_id=request.file_id,
            engine=request.engine,
            user_id=request.user_id
        )
        
        # 更新文件状态
        file_service.update(db, db_obj=file_record, obj_in={"ocr_status": OCRStatus.PROCESSING})
        
        response = OCRResponse(
            task_id=task.id,
            file_id=request.file_id,
            engine=request.engine,
            status="started",
            message="OCR processing task started successfully"
        )
        
        return ResponseModel(
            success=True,
            data=response,
            message="OCR processing started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start OCR processing: {str(e)}")


@router.get("/status/{file_id}", response_model=ResponseModel[Dict[str, Any]])
async def get_ocr_status(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    获取文件的OCR处理状态
    """
    try:
        file_record = file_service.get(db, id=file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # 获取切片统计
        slice_stats = slice_service.get_file_slice_stats(db, file_id)
        
        status_info = {
            "file_id": file_id,
            "filename": file_record.filename,
            "ocr_status": file_record.ocr_status.value,
            "ocr_engine": file_record.ocr_engine,
            "has_ocr_result": bool(file_record.ocr_result),
            "text_length": len(file_record.ocr_result) if file_record.ocr_result else 0,
            "slice_stats": slice_stats
        }
        
        return ResponseModel(
            success=True,
            data=status_info,
            message="OCR status retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get OCR status: {str(e)}")


@router.get("/slices/{file_id}", response_model=ResponseModel[FileSlicesResponse])
async def get_file_slices(
    file_id: str,
    page: int = 1,
    size: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取文件的切片列表
    """
    try:
        # 验证文件存在
        file_record = file_service.get(db, id=file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # 获取切片列表
        all_slices = slice_service.get_by_file(db, file_id)
        
        # 分页
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        page_slices = all_slices[start_idx:end_idx]
        
        # 转换为响应格式
        slice_responses = [
            SliceResponse(
                id=str(slice_obj.id),
                content=slice_obj.content,
                slice_type=slice_obj.slice_type.value,
                page_number=slice_obj.page_number or 1,
                sequence_number=slice_obj.sequence_number,
                start_offset=slice_obj.start_offset,
                end_offset=slice_obj.end_offset
            )
            for slice_obj in page_slices
        ]
        
        response = FileSlicesResponse(
            file_id=file_id,
            total_slices=len(all_slices),
            slices=slice_responses
        )
        
        return ResponseModel(
            success=True,
            data=response,
            message=f"Retrieved {len(slice_responses)} slices"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file slices: {str(e)}")


@router.get("/slice/{slice_id}", response_model=ResponseModel[Dict[str, Any]])
async def get_slice_detail(
    slice_id: str,
    include_context: bool = False,
    context_size: int = 2,
    db: Session = Depends(get_db)
):
    """
    获取切片详细信息
    """
    try:
        if include_context:
            # 获取带上下文的切片信息
            slice_context = slice_service.get_slice_context(db, slice_id, context_size)
            if not slice_context:
                raise HTTPException(status_code=404, detail="Slice not found")
            
            return ResponseModel(
                success=True,
                data=slice_context,
                message="Slice with context retrieved successfully"
            )
        else:
            # 获取单个切片
            slice_record = slice_service.get(db, id=slice_id)
            if not slice_record:
                raise HTTPException(status_code=404, detail="Slice not found")
            
            slice_data = {
                "id": str(slice_record.id),
                "file_id": str(slice_record.file_id),
                "content": slice_record.content,
                "slice_type": slice_record.slice_type.value,
                "page_number": slice_record.page_number,
                "sequence_number": slice_record.sequence_number,
                "start_offset": slice_record.start_offset,
                "end_offset": slice_record.end_offset,
                "created_at": slice_record.created_at.isoformat() if slice_record.created_at else None
            }
            
            return ResponseModel(
                success=True,
                data=slice_data,
                message="Slice retrieved successfully"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get slice detail: {str(e)}")


@router.post("/reprocess/{file_id}", response_model=ResponseModel[OCRResponse])
async def reprocess_file(
    file_id: str,
    request: ReprocessRequest,
    db: Session = Depends(get_db)
):
    """
    重新处理文件的OCR
    """
    try:
        # 验证文件存在
        file_record = file_service.get(db, id=file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # 删除现有切片
        existing_slices = slice_service.get_by_file(db, file_id)
        for slice_obj in existing_slices:
            slice_service.remove(db, id=slice_obj.id)
        
        # 重置文件OCR状态
        file_service.update(db, db_obj=file_record, obj_in={
            "ocr_status": OCRStatus.PENDING,
            "ocr_result": None,
            "ocr_engine": None
        })
        
        # 启动新的OCR任务
        task = ocr_processing.delay(
            file_id=file_id,
            engine=request.engine.value,
            user_id=request.user_id
        )
        
        response = OCRResponse(
            task_id=task.id,
            file_id=file_id,
            engine=request.engine.value,
            status="restarted",
            message="OCR reprocessing task started successfully"
        )
        
        return ResponseModel(
            success=True,
            data=response,
            message="OCR reprocessing started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reprocess file: {str(e)}")


@router.post("/search", response_model=ResponseModel[SliceSearchResponse])
async def search_slices(
    request: SliceSearchRequest,
    db: Session = Depends(get_db)
):
    """
    在项目中搜索切片
    """
    try:
        # 搜索切片
        matching_slices = slice_service.search_slices(
            db=db,
            project_id=request.project_id,
            query=request.query,
            limit=request.limit
        )
        
        # 转换为响应格式
        slice_responses = [
            SliceResponse(
                id=str(slice_obj.id),
                content=slice_obj.content,
                slice_type=slice_obj.slice_type.value,
                page_number=slice_obj.page_number or 1,
                sequence_number=slice_obj.sequence_number,
                start_offset=slice_obj.start_offset,
                end_offset=slice_obj.end_offset,
                file_id=str(slice_obj.file_id),
                created_at=slice_obj.created_at.isoformat() if slice_obj.created_at else None
            )
            for slice_obj in matching_slices
        ]
        
        response = SliceSearchResponse(
            query=request.query,
            total_results=len(slice_responses),
            slices=slice_responses
        )
        
        return ResponseModel(
            success=True,
            data=response,
            message=f"Found {len(slice_responses)} matching slices"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search slices: {str(e)}")


@router.get("/project/{project_id}/slices", response_model=ResponseModel[List[SliceResponse]])
async def get_project_slices(
    project_id: str,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=100, description="每页大小"),
    slice_type: Optional[str] = Query(None, description="切片类型过滤"),
    db: Session = Depends(get_db)
):
    """
    获取项目的所有切片
    """
    try:
        # 获取项目的所有切片
        all_slices = slice_service.get_by_project(db, project_id)
        
        # 按类型过滤
        if slice_type:
            from app.models.slice import SliceType
            try:
                filter_type = SliceType(slice_type)
                all_slices = [s for s in all_slices if s.slice_type == filter_type]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid slice type: {slice_type}")
        
        # 分页
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        page_slices = all_slices[start_idx:end_idx]
        
        # 转换为响应格式
        slice_responses = [
            SliceResponse(
                id=str(slice_obj.id),
                content=slice_obj.content,
                slice_type=slice_obj.slice_type.value,
                page_number=slice_obj.page_number or 1,
                sequence_number=slice_obj.sequence_number,
                start_offset=slice_obj.start_offset,
                end_offset=slice_obj.end_offset,
                file_id=str(slice_obj.file_id),
                created_at=slice_obj.created_at.isoformat() if slice_obj.created_at else None
            )
            for slice_obj in page_slices
        ]
        
        return ResponseModel(
            success=True,
            data=slice_responses,
            message=f"Retrieved {len(slice_responses)} slices from project"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project slices: {str(e)}")