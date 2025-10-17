"""
任务监控API端点
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.app_logging import logger
from app.core.database import get_db
from app.middleware.auth import get_current_active_user
from app.workers.tasks import ocr_processing, llm_processing, kg_extraction, file_processing
from app.services.task_monitor_service import task_monitor_service
from app.schemas.task import (
    TaskMonitorResponse, TaskStatistics, TaskQueueInfo, WorkerInfo,
    TaskFilterParams, TaskRetryRequest, TaskBatchOperation
)
from app.models.task import TaskStatus, TaskType, TaskPriority

router = APIRouter()


class TaskResponse(BaseModel):
    """任务响应模式"""
    task_id: str
    status: str
    progress: int = 0
    message: str = ""
    result: Dict[str, Any] = {}
    error: str = ""


class TaskCreate(BaseModel):
    """任务创建模式"""
    task_type: str
    parameters: Dict[str, Any]


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> TaskResponse:
    """
    获取任务状态
    """
    try:
        # 获取任务结果
        result = celery_app.AsyncResult(task_id)
        
        response = TaskResponse(
            task_id=task_id,
            status=result.status,
        )
        
        if result.status == "PENDING":
            response.message = "Task is waiting to be processed"
        elif result.status == "PROGRESS":
            if result.info:
                response.progress = result.info.get("current", 0)
                response.message = result.info.get("status", "Processing...")
        elif result.status == "SUCCESS":
            response.progress = 100
            response.message = "Task completed successfully"
            response.result = result.result or {}
        elif result.status == "FAILURE":
            response.message = "Task failed"
            response.error = str(result.info) if result.info else "Unknown error"
        
        return response
        
    except Exception as e:
        logger.error("Failed to get task status", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get task status")


@router.post("/tasks/ocr", response_model=Dict[str, str])
async def start_ocr_task(
    file_id: UUID,
    engine: str = "paddleocr",
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, str]:
    """
    启动OCR处理任务
    """
    try:
        task = ocr_processing.delay(
            file_id=str(file_id),
            engine=engine,
            user_id=current_user["user_id"]
        )
        
        logger.info("OCR task started", task_id=task.id, file_id=str(file_id), user_id=current_user["user_id"])
        
        return {
            "task_id": task.id,
            "message": "OCR processing task started",
            "status": "PENDING"
        }
        
    except Exception as e:
        logger.error("Failed to start OCR task", file_id=str(file_id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to start OCR task")


@router.post("/tasks/llm", response_model=Dict[str, str])
async def start_llm_task(
    slice_id: UUID,
    provider: str = "openai",
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, str]:
    """
    启动LLM处理任务
    """
    try:
        task = llm_processing.delay(
            slice_id=str(slice_id),
            provider=provider
        )
        
        logger.info("LLM task started", task_id=task.id, slice_id=str(slice_id), user_id=current_user["user_id"])
        
        return {
            "task_id": task.id,
            "message": "LLM processing task started",
            "status": "PENDING"
        }
        
    except Exception as e:
        logger.error("Failed to start LLM task", slice_id=str(slice_id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to start LLM task")


@router.post("/tasks/kg", response_model=Dict[str, str])
async def start_kg_task(
    cot_item_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, str]:
    """
    启动知识图谱抽取任务
    """
    try:
        task = kg_extraction.delay(cot_item_id=str(cot_item_id))
        
        logger.info("KG task started", task_id=task.id, cot_item_id=str(cot_item_id), user_id=current_user["user_id"])
        
        return {
            "task_id": task.id,
            "message": "Knowledge graph extraction task started",
            "status": "PENDING"
        }
        
    except Exception as e:
        logger.error("Failed to start KG task", cot_item_id=str(cot_item_id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to start KG task")


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, str]:
    """
    取消任务
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        
        logger.info("Task cancelled", task_id=task_id, user_id=current_user["user_id"])
        
        return {
            "task_id": task_id,
            "message": "Task cancelled successfully",
            "status": "REVOKED"
        }
        
    except Exception as e:
        logger.error("Failed to cancel task", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to cancel task")


@router.get("/tasks", response_model=Dict[str, Any])
async def list_tasks(
    status: Optional[List[TaskStatus]] = Query(None),
    task_type: Optional[List[TaskType]] = Query(None),
    priority: Optional[List[TaskPriority]] = Query(None),
    user_id: Optional[str] = Query(None),
    queue_name: Optional[str] = Query(None),
    is_critical: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    order_by: str = Query("created_at"),
    order_desc: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    列出任务监控记录
    """
    try:
        # 如果不是管理员，只能查看自己的任务
        if not current_user.get("is_admin", False):
            user_id = current_user["user_id"]
        
        filters = TaskFilterParams(
            status=status,
            task_type=task_type,
            priority=priority,
            user_id=user_id,
            queue_name=queue_name,
            is_critical=is_critical,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_desc=order_desc
        )
        
        tasks, total = task_monitor_service.list_task_monitors(db, filters)
        
        return {
            "items": [TaskMonitorResponse.from_orm(task) for task in tasks],
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error("Failed to list tasks", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list tasks")


@router.get("/tasks/statistics", response_model=TaskStatistics)
async def get_task_statistics(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> TaskStatistics:
    """
    获取任务统计信息
    """
    try:
        user_id = None if current_user.get("is_admin", False) else current_user["user_id"]
        return task_monitor_service.get_task_statistics(db, user_id, days)
        
    except Exception as e:
        logger.error("Failed to get task statistics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get task statistics")


@router.get("/tasks/queues", response_model=List[TaskQueueInfo])
async def get_queue_info(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> List[TaskQueueInfo]:
    """
    获取任务队列信息
    """
    try:
        return task_monitor_service.get_queue_info()
        
    except Exception as e:
        logger.error("Failed to get queue info", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get queue info")


@router.get("/tasks/workers", response_model=List[WorkerInfo])
async def get_worker_info(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> List[WorkerInfo]:
    """
    获取工作节点信息
    """
    try:
        return task_monitor_service.get_worker_info()
        
    except Exception as e:
        logger.error("Failed to get worker info", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get worker info")


@router.post("/tasks/{task_id}/retry")
async def retry_task(
    task_id: str,
    retry_request: TaskRetryRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, str]:
    """
    重试任务
    """
    try:
        # 检查任务权限
        task_monitor = task_monitor_service.get_task_monitor(db, task_id)
        if not task_monitor:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if not current_user.get("is_admin", False) and task_monitor.user_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        success = task_monitor_service.retry_task(db, task_id, retry_request.reason)
        
        if success:
            return {"message": "Task retry initiated", "task_id": task_id}
        else:
            raise HTTPException(status_code=400, detail="Task cannot be retried")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retry task", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retry task")


@router.post("/tasks/batch")
async def batch_task_operation(
    batch_op: TaskBatchOperation,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    批量任务操作
    """
    try:
        results = {"success": [], "failed": []}
        
        for task_id in batch_op.task_ids:
            try:
                # 检查任务权限
                task_monitor = task_monitor_service.get_task_monitor(db, task_id)
                if not task_monitor:
                    results["failed"].append({"task_id": task_id, "error": "Task not found"})
                    continue
                
                if not current_user.get("is_admin", False) and task_monitor.user_id != current_user["user_id"]:
                    results["failed"].append({"task_id": task_id, "error": "Permission denied"})
                    continue
                
                if batch_op.operation == "cancel":
                    success = task_monitor_service.cancel_task(db, task_id, batch_op.reason)
                elif batch_op.operation == "retry":
                    success = task_monitor_service.retry_task(db, task_id, batch_op.reason)
                else:
                    results["failed"].append({"task_id": task_id, "error": "Unknown operation"})
                    continue
                
                if success:
                    results["success"].append(task_id)
                else:
                    results["failed"].append({"task_id": task_id, "error": "Operation failed"})
                    
            except Exception as e:
                results["failed"].append({"task_id": task_id, "error": str(e)})
        
        return results
        
    except Exception as e:
        logger.error("Failed to perform batch operation", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to perform batch operation")


@router.get("/tasks/active", response_model=List[TaskResponse])
async def list_active_tasks(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> List[TaskResponse]:
    """
    列出活跃任务 (兼容旧API)
    """
    try:
        # 获取活跃任务
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        tasks = []
        if active_tasks:
            for worker, task_list in active_tasks.items():
                for task_info in task_list:
                    task_id = task_info["id"]
                    result = celery_app.AsyncResult(task_id)
                    
                    task_response = TaskResponse(
                        task_id=task_id,
                        status=result.status,
                        message=task_info.get("name", "Unknown task")
                    )
                    
                    if result.status == "PROGRESS" and result.info:
                        task_response.progress = result.info.get("current", 0)
                        task_response.message = result.info.get("status", "Processing...")
                    
                    tasks.append(task_response)
        
        return tasks
        
    except Exception as e:
        logger.error("Failed to list active tasks", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list active tasks")