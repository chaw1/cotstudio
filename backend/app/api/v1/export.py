"""
导出相关的API端点
"""
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from ...core.database import get_db
from ...middleware.auth import get_current_user
from ...models import User, Project
from ...schemas.export import (
    ExportRequest, ExportTaskResponse, ExportStatus, ExportFormat,
    ExportValidationResult
)
from ...schemas.common import MessageResponse
from ...services.export_service import ExportService
from ...services.export_task_service import ExportTaskService
from ...workers.export_tasks import export_project_task, create_project_package_task
from ...core.config import settings


router = APIRouter()


@router.post("/projects/{project_id}/export", response_model=ExportTaskResponse)
async def export_project(
    project_id: str,
    export_request: ExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出项目数据
    
    Args:
        project_id: 项目ID
        export_request: 导出请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        导出任务响应
    """
    # 验证项目存在和权限
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查用户权限（这里简化处理，实际应该检查项目权限）
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限访问此项目")
    
    # 设置项目ID
    export_request.project_id = project_id
    
    # 创建异步任务
    task = export_project_task.delay(export_request.model_dump())
    
    # 创建任务记录
    task_service = ExportTaskService(db)
    export_task = await task_service.create_export_task(
        task_id=task.id,
        project_id=project_id,
        user_id=current_user.id,
        export_request=export_request,
        export_type="single"
    )
    
    return task_service.task_to_response(export_task)


@router.post("/projects/{project_id}/package", response_model=ExportTaskResponse)
async def create_project_package(
    project_id: str,
    export_request: ExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建项目包
    
    Args:
        project_id: 项目ID
        export_request: 导出请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        导出任务响应
    """
    # 验证项目存在和权限
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查用户权限
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限访问此项目")
    
    # 设置项目ID
    export_request.project_id = project_id
    
    # 创建异步任务
    task = create_project_package_task.delay(export_request.model_dump())
    
    # 创建任务记录
    task_service = ExportTaskService(db)
    export_task = await task_service.create_export_task(
        task_id=task.id,
        project_id=project_id,
        user_id=current_user.id,
        export_request=export_request,
        export_type="package"
    )
    
    return task_service.task_to_response(export_task)


@router.get("/tasks/{task_id}/status", response_model=ExportTaskResponse)
async def get_export_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取导出任务状态
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        任务状态响应
    """
    try:
        task_service = ExportTaskService(db)
        
        # 首先从数据库获取任务信息
        export_task = await task_service.get_task_by_id(task_id)
        if not export_task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查用户权限
        if export_task.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限访问此任务")
        
        # 如果任务还在进行中，从Celery获取最新状态
        if export_task.status in ['pending', 'processing']:
            try:
                result = AsyncResult(task_id)
                
                if result.state == 'PENDING':
                    status = 'pending'
                    progress = 0.0
                    message = "任务等待中"
                elif result.state == 'PROGRESS':
                    status = 'processing'
                    progress = result.info.get('progress', export_task.progress)
                    message = result.info.get('message', export_task.message)
                elif result.state == 'SUCCESS':
                    status = 'completed'
                    progress = 100.0
                    message = result.result.get('message', '导出完成')
                    # 更新数据库中的任务状态
                    await task_service.update_task_status(
                        task_id=task_id,
                        status=status,
                        progress=progress,
                        message=message,
                        download_url=result.result.get('download_url'),
                        file_path=result.result.get('file_path'),
                        validation_result=result.result.get('validation')
                    )
                elif result.state == 'FAILURE':
                    status = 'failed'
                    progress = 0.0
                    message = result.info.get('error', '任务失败')
                    # 更新数据库中的任务状态
                    await task_service.update_task_status(
                        task_id=task_id,
                        status=status,
                        progress=progress,
                        error_message=message
                    )
                else:
                    status = 'failed'
                    progress = 0.0
                    message = f"未知任务状态: {result.state}"
                
                # 如果状态有变化，更新数据库
                if status != export_task.status or progress != export_task.progress:
                    export_task = await task_service.update_task_status(
                        task_id=task_id,
                        status=status,
                        progress=progress,
                        message=message
                    )
                    
            except Exception:
                # 如果无法从Celery获取状态，使用数据库中的状态
                pass
        
        return task_service.task_to_response(export_task)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


@router.get("/download/{filename}")
async def download_export_file(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """
    下载导出文件
    
    Args:
        filename: 文件名
        current_user: 当前用户
        
    Returns:
        文件响应
    """
    try:
        # 构建文件路径
        export_dir = settings.EXPORT_DIR or "exports"
        file_path = os.path.join(export_dir, filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 检查文件安全性（防止路径遍历攻击）
        if not os.path.abspath(file_path).startswith(os.path.abspath(export_dir)):
            raise HTTPException(status_code=403, detail="非法文件路径")
        
        # 返回文件
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")


@router.post("/validate", response_model=ExportValidationResult)
async def validate_export_file(
    file_path: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    验证导出文件
    
    Args:
        file_path: 文件路径
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        验证结果
    """
    try:
        export_service = ExportService(db)
        
        # 检查文件路径安全性
        export_dir = settings.EXPORT_DIR or "exports"
        full_path = os.path.join(export_dir, file_path)
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not os.path.abspath(full_path).startswith(os.path.abspath(export_dir)):
            raise HTTPException(status_code=403, detail="非法文件路径")
        
        # 执行验证
        validation_result = await export_service.validate_export_data(full_path)
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证文件失败: {str(e)}")


@router.get("/formats", response_model=List[str])
async def get_supported_formats():
    """
    获取支持的导出格式
    
    Returns:
        支持的格式列表
    """
    return [format.value for format in ExportFormat]


@router.delete("/tasks/{task_id}", response_model=MessageResponse)
async def cancel_export_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    取消导出任务
    
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


@router.get("/projects/{project_id}/history")
async def get_export_history(
    project_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目导出历史
    
    Args:
        project_id: 项目ID
        limit: 限制数量
        offset: 偏移量
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        导出历史列表
    """
    # 验证项目存在和权限
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限访问此项目")
    
    # 获取导出历史
    task_service = ExportTaskService(db)
    tasks, total = await task_service.get_project_export_history(
        project_id=project_id,
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    
    # 转换为响应格式
    items = []
    for task in tasks:
        items.append({
            "id": task.id,
            "project_id": task.project_id,
            "format": task.export_format,
            "status": task.status,
            "file_size": task.file_size,
            "download_url": task.download_url,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message
        })
    
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }