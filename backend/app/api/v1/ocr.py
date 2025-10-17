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
from app.services.mineru_import_service import mineru_import_service
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
                name="mineru",
                available="mineru" in available_engines,
                description="MinerU - 高性能OCR引擎，支持复杂文档结构识别，适用于PDF、图像和扫描文档"
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
        
        # 准备引擎配置
        engine_config = {}
        if request.config:
            engine_config = request.config.dict(exclude_none=True)
            
            # MinerU引擎特殊处理：根据use_gpu和recognition_mode自动设置backend和device
            if request.engine == 'mineru':
                use_gpu = engine_config.get('use_gpu', True)
                recognition_mode = engine_config.get('recognition_mode', 'fast')
                
                # 设置device
                engine_config['device'] = 'cuda' if use_gpu else 'cpu'
                
                # 设置backend
                if recognition_mode == 'fast':
                    engine_config['backend'] = 'pipeline'
                elif recognition_mode == 'accurate':
                    engine_config['backend'] = 'vlm-transformers'
        
        # 启动异步OCR任务
        task = ocr_processing.delay(
            file_id=request.file_id,
            engine=request.engine,
            user_id=request.user_id,
            engine_config=engine_config
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


@router.post("/stop/{file_id}", response_model=ResponseModel[Dict[str, Any]])
async def stop_ocr_processing(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    停止文件的OCR处理任务
    """
    try:
        from celery.result import AsyncResult
        from app.core.celery_app import celery_app
        
        # 验证文件存在
        file_record = file_service.get(db, id=file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # 检查文件是否正在处理中
        if file_record.ocr_status != OCRStatus.PROCESSING:
            raise HTTPException(
                status_code=400, 
                detail=f"File is not being processed. Current status: {file_record.ocr_status.value}"
            )
        
        # 查找并停止该文件的Celery任务
        # 使用Celery的inspect API查找正在运行的任务
        from celery import current_app
        inspect = current_app.control.inspect()
        active_tasks = inspect.active()
        
        stopped_tasks = []
        if active_tasks:
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    # 检查任务参数中是否包含该file_id
                    task_args = task.get('args', [])
                    task_kwargs = task.get('kwargs', {})
                    
                    # 检查任务名称和参数
                    if task.get('name') == 'app.workers.tasks.ocr_processing':
                        # 检查file_id是否匹配
                        if (file_id in task_args or 
                            task_kwargs.get('file_id') == file_id):
                            # 停止任务
                            task_id = task.get('id')
                            celery_app.control.revoke(task_id, terminate=True, signal='SIGKILL')
                            stopped_tasks.append(task_id)
        
        # 更新文件状态为失败
        file_service.update(
            db, 
            db_obj=file_record, 
            obj_in={"ocr_status": OCRStatus.FAILED, "ocr_result": "OCR processing stopped by user"}
        )
        
        return ResponseModel(
            success=True,
            data={
                "file_id": file_id,
                "stopped_tasks": stopped_tasks,
                "message": f"Stopped {len(stopped_tasks)} task(s)" if stopped_tasks else "No active tasks found for this file"
            },
            message="OCR processing stopped successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to stop OCR processing: {str(e)}")


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
                end_offset=slice_obj.end_offset,
                file_id=str(slice_obj.file_id),
                created_at=slice_obj.created_at.isoformat() if hasattr(slice_obj.created_at, 'isoformat') else None,
                updated_at=slice_obj.updated_at.isoformat() if hasattr(slice_obj.updated_at, 'isoformat') else None
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


@router.get("/mineru/documents", response_model=ResponseModel[List[Dict[str, Any]]])
async def get_mineru_documents():
    """
    获取可用的MinerU解析文档列表
    """
    try:
        documents = mineru_import_service.get_available_documents()
        return ResponseModel(
            success=True,
            data=documents,
            message=f"Found {len(documents)} MinerU parsed documents"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get MinerU documents: {str(e)}")


@router.post("/mineru/import", response_model=ResponseModel[Dict[str, Any]])
async def import_mineru_document(
    document_name: str,
    mode: str,
    project_id: Optional[str] = None,
    file_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    导入MinerU解析的文档到数据库
    
    Args:
        document_name: 文档名称（output目录下的子目录名）
        mode: 解析模式（vlm或pipeline）
        project_id: 关联的项目ID（可选）
        file_id: 关联的文件ID（可选）
    """
    try:
        result = mineru_import_service.import_document(
            db=db,
            document_name=document_name,
            mode=mode,
            project_id=project_id,
            file_id=file_id
        )
        
        return ResponseModel(
            success=True,
            data=result,
            message=f"Successfully imported {result['statistics']['imported_slices']} slices"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import MinerU document: {str(e)}")


@router.post("/mineru/import-all", response_model=ResponseModel[List[Dict[str, Any]]])
async def import_all_mineru_documents(
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    导入所有可用的MinerU解析文档
    
    Args:
        project_id: 关联的项目ID（可选）
    """
    try:
        results = mineru_import_service.import_all_documents(
            db=db,
            project_id=project_id
        )
        
        success_count = len([r for r in results if 'error' not in r])
        
        return ResponseModel(
            success=True,
            data=results,
            message=f"Successfully imported {success_count}/{len(results)} documents"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import MinerU documents: {str(e)}")