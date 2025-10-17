"""
导入相关的API端点
"""
import os
import tempfile
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from ...core.database import get_db
from ...middleware.auth import get_current_user
from ...models import User, Project
from ...schemas.import_schemas import (
    ImportRequest, ImportTaskResponse, ImportStatus, ImportMode,
    ImportAnalysisResult, ImportConfirmation, ImportResult,
    ImportValidationResult, ConflictResolution, ImportProgress
)
from ...schemas.common import MessageResponse
from ...services.import_service import ImportService
from ...workers.import_tasks import (
    validate_import_file_task, analyze_import_differences_task,
    execute_import_task, cleanup_import_files_task
)
from ...core.config import settings


router = APIRouter()


@router.post("/upload", response_model=Dict[str, str])
async def upload_import_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    上传导入文件
    
    Args:
        file: 上传的文件
        current_user: 当前用户
        
    Returns:
        文件信息
    """
    try:
        # 检查文件格式
        allowed_extensions = ['.json', '.zip']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件格式。支持的格式: {', '.join(allowed_extensions)}"
            )
        
        # 检查文件大小
        max_size = 100 * 1024 * 1024  # 100MB
        if file.size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制 ({max_size // (1024*1024)}MB)"
            )
        
        # 创建临时文件
        import_dir = Path(settings.IMPORT_DIR or "imports")
        import_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"import_{current_user.id}_{timestamp}{file_extension}"
        file_path = import_dir / filename
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "file_path": str(file_path),
            "filename": file.filename,
            "size": len(content),
            "message": "文件上传成功"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/validate", response_model=ImportTaskResponse)
async def validate_import_file(
    file_path: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    验证导入文件
    
    Args:
        file_path: 文件路径
        background_tasks: 后台任务
        current_user: 当前用户
        
    Returns:
        验证任务响应
    """
    try:
        # 检查文件路径安全性
        import_dir = Path(settings.IMPORT_DIR or "imports")
        full_path = Path(file_path)
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not str(full_path).startswith(str(import_dir)):
            raise HTTPException(status_code=403, detail="非法文件路径")
        
        # 创建验证任务
        task = validate_import_file_task.delay(str(full_path))
        
        return ImportTaskResponse(
            task_id=task.id,
            status=ImportStatus.PENDING,
            progress=0.0,
            message="文件验证任务已创建",
            created_at=datetime.now()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建验证任务失败: {str(e)}")


@router.post("/analyze", response_model=ImportTaskResponse)
async def analyze_import_differences(
    file_path: str,
    target_project_id: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    分析导入差异
    
    Args:
        file_path: 导入文件路径
        target_project_id: 目标项目ID（可选）
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        分析任务响应
    """
    try:
        # 验证目标项目（如果指定）
        if target_project_id:
            project = db.query(Project).filter(Project.id == target_project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="目标项目不存在")
            
            # 检查权限
            if project.owner_id != current_user.id:
                raise HTTPException(status_code=403, detail="无权限访问此项目")
        
        # 检查文件路径安全性
        import_dir = Path(settings.IMPORT_DIR or "imports")
        full_path = Path(file_path)
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not str(full_path).startswith(str(import_dir)):
            raise HTTPException(status_code=403, detail="非法文件路径")
        
        # 创建分析任务
        task = analyze_import_differences_task.delay(str(full_path), target_project_id)
        
        return ImportTaskResponse(
            task_id=task.id,
            status=ImportStatus.ANALYZING,
            progress=0.0,
            message="差异分析任务已创建",
            created_at=datetime.now()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建分析任务失败: {str(e)}")


@router.post("/execute", response_model=ImportTaskResponse)
async def execute_import(
    confirmation: ImportConfirmation,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    执行导入操作
    
    Args:
        confirmation: 导入确认信息
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        导入任务响应
    """
    try:
        # 获取分析任务结果
        analysis_task = AsyncResult(confirmation.task_id)
        if analysis_task.state != 'SUCCESS':
            raise HTTPException(status_code=400, detail="分析任务未完成或失败")
        
        analysis_result = analysis_task.result
        if analysis_result['status'] != 'completed':
            raise HTTPException(status_code=400, detail="分析任务未成功完成")
        
        # 构建导入请求
        # 这里需要从分析结果中提取原始请求信息
        # 为简化，我们假设在任务元数据中存储了这些信息
        import_request_dict = {
            "file_path": "path_from_analysis",  # 应该从分析结果中获取
            "import_mode": ImportMode.MERGE,
            "target_project_id": None,
            "new_project_name": None,
            "conflict_resolution": {}
        }
        
        # 转换冲突解决方案
        conflict_resolutions_dict = {}
        for key, resolution in confirmation.conflict_resolutions.items():
            conflict_resolutions_dict[key] = {
                "difference_id": key,
                "resolution": resolution,
                "custom_value": None,
                "reason": None
            }
        
        # 创建导入任务
        task = execute_import_task.delay(
            import_request_dict,
            confirmation.confirmed_differences,
            conflict_resolutions_dict,
            str(current_user.id)
        )
        
        return ImportTaskResponse(
            task_id=task.id,
            status=ImportStatus.IMPORTING,
            progress=0.0,
            message="导入任务已创建",
            created_at=datetime.now()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建导入任务失败: {str(e)}")


@router.get("/tasks/{task_id}/status", response_model=ImportTaskResponse)
async def get_import_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取导入任务状态
    
    Args:
        task_id: 任务ID
        current_user: 当前用户
        
    Returns:
        任务状态响应
    """
    try:
        # 获取任务结果
        result = AsyncResult(task_id)
        
        if result.state == 'PENDING':
            status = ImportStatus.PENDING
            progress = 0.0
            message = "任务等待中"
            differences_summary = None
        elif result.state == 'PROGRESS':
            status = ImportStatus.ANALYZING
            progress = result.info.get('progress', 0.0)
            message = result.info.get('message', '处理中')
            differences_summary = result.info.get('differences_summary')
        elif result.state == 'SUCCESS':
            task_result = result.result
            if task_result['status'] == 'completed':
                status = ImportStatus.COMPLETED
                progress = 100.0
                message = task_result.get('message', '任务完成')
                differences_summary = task_result.get('differences_summary')
            else:
                status = ImportStatus.FAILED
                progress = 0.0
                message = task_result.get('error', '任务失败')
                differences_summary = None
        elif result.state == 'FAILURE':
            status = ImportStatus.FAILED
            progress = 0.0
            message = str(result.info) if result.info else '任务失败'
            differences_summary = None
        else:
            status = ImportStatus.FAILED
            progress = 0.0
            message = f"未知任务状态: {result.state}"
            differences_summary = None
        
        return ImportTaskResponse(
            task_id=task_id,
            status=status,
            progress=progress,
            message=message,
            created_at=datetime.now(),  # 应该从任务中获取实际创建时间
            differences_summary=differences_summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


@router.get("/tasks/{task_id}/result")
async def get_import_task_result(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取导入任务结果
    
    Args:
        task_id: 任务ID
        current_user: 当前用户
        
    Returns:
        任务结果
    """
    try:
        # 获取任务结果
        result = AsyncResult(task_id)
        
        if result.state != 'SUCCESS':
            raise HTTPException(status_code=400, detail="任务未完成")
        
        return result.result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务结果失败: {str(e)}")


@router.delete("/tasks/{task_id}", response_model=MessageResponse)
async def cancel_import_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    取消导入任务
    
    Args:
        task_id: 任务ID
        current_user: 当前用户
        
    Returns:
        操作结果
    """
    try:
        # 获取任务结果
        result = AsyncResult(task_id)
        
        if result.state in ['PENDING', 'PROGRESS']:
            # 撤销任务
            result.revoke(terminate=True)
            return MessageResponse(message="任务已取消")
        else:
            return MessageResponse(message=f"任务无法取消，当前状态: {result.state}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


@router.post("/cleanup", response_model=MessageResponse)
async def cleanup_import_files(
    file_paths: List[str],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    清理导入文件
    
    Args:
        file_paths: 要清理的文件路径列表
        background_tasks: 后台任务
        current_user: 当前用户
        
    Returns:
        操作结果
    """
    try:
        # 验证文件路径安全性
        import_dir = Path(settings.IMPORT_DIR or "imports")
        validated_paths = []
        
        for file_path in file_paths:
            full_path = Path(file_path)
            if str(full_path).startswith(str(import_dir)):
                validated_paths.append(str(full_path))
        
        if validated_paths:
            # 创建清理任务
            task = cleanup_import_files_task.delay(validated_paths)
            return MessageResponse(message=f"清理任务已创建，任务ID: {task.id}")
        else:
            return MessageResponse(message="没有有效的文件路径需要清理")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建清理任务失败: {str(e)}")


@router.get("/history")
async def get_import_history(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取导入历史
    
    Args:
        limit: 限制数量
        offset: 偏移量
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        导入历史列表
    """
    # 这里应该从数据库或缓存中获取导入历史
    # 暂时返回空列表
    return {
        "items": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/supported-formats", response_model=List[str])
async def get_supported_import_formats():
    """
    获取支持的导入格式
    
    Returns:
        支持的格式列表
    """
    return ["json", "zip"]