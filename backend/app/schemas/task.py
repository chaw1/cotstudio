"""
任务监控相关的Pydantic模式
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import UUID

from app.models.task import TaskStatus, TaskType, TaskPriority


class TaskMonitorBase(BaseModel):
    """任务监控基础模式"""
    task_name: str = Field(..., description="任务名称")
    task_type: TaskType = Field(..., description="任务类型")
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="任务优先级")
    parameters: Optional[Dict[str, Any]] = Field(None, description="任务参数")
    estimated_duration: Optional[int] = Field(None, description="预估执行时间(秒)")
    max_retries: int = Field(3, description="最大重试次数")
    retry_delay: int = Field(60, description="重试延迟(秒)")
    tags: Optional[Dict[str, Any]] = Field(None, description="任务标签")
    is_critical: bool = Field(False, description="是否为关键任务")


class TaskMonitorCreate(TaskMonitorBase):
    """创建任务监控"""
    task_id: str = Field(..., description="Celery任务ID")
    user_id: str = Field(..., description="用户ID")
    queue_name: str = Field("default", description="队列名称")


class TaskMonitorUpdate(BaseModel):
    """更新任务监控"""
    status: Optional[TaskStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100, description="进度百分比")
    current_step: Optional[str] = None
    total_steps: Optional[int] = None
    worker_name: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_info: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    retry_count: Optional[int] = None


class TaskMonitorResponse(TaskMonitorBase):
    """任务监控响应"""
    id: UUID
    task_id: str
    status: TaskStatus
    progress: int
    current_step: Optional[str]
    total_steps: Optional[int]
    user_id: str
    worker_name: Optional[str]
    queue_name: str
    
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime
    
    actual_duration: Optional[int]
    result: Optional[Dict[str, Any]]
    error_info: Optional[Dict[str, Any]]
    message: Optional[str]
    
    retry_count: int
    execution_time: Optional[int]
    is_active: bool
    is_completed: bool
    can_retry: bool
    
    class Config:
        from_attributes = True


class TaskStatistics(BaseModel):
    """任务统计信息"""
    total_tasks: int
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    average_duration: Optional[float]
    
    # 按类型统计
    by_type: Dict[str, int]
    # 按状态统计
    by_status: Dict[str, int]
    # 按优先级统计
    by_priority: Dict[str, int]


class TaskQueueInfo(BaseModel):
    """任务队列信息"""
    queue_name: str
    active_tasks: int
    scheduled_tasks: int
    reserved_tasks: int
    total_tasks: int


class WorkerInfo(BaseModel):
    """工作节点信息"""
    worker_name: str
    status: str
    active_tasks: int
    processed_tasks: int
    load_average: List[float]
    last_heartbeat: Optional[datetime]


class TaskRetryRequest(BaseModel):
    """任务重试请求"""
    task_id: str
    reason: Optional[str] = None


class TaskBatchOperation(BaseModel):
    """批量任务操作"""
    task_ids: List[str]
    operation: str  # cancel, retry, delete
    reason: Optional[str] = None


class TaskFilterParams(BaseModel):
    """任务过滤参数"""
    status: Optional[List[TaskStatus]] = None
    task_type: Optional[List[TaskType]] = None
    priority: Optional[List[TaskPriority]] = None
    user_id: Optional[str] = None
    queue_name: Optional[str] = None
    is_critical: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)
    order_by: str = Field("created_at", description="排序字段")
    order_desc: bool = Field(True, description="是否降序")


class TaskWebSocketMessage(BaseModel):
    """WebSocket任务消息"""
    type: str  # task_update, task_created, task_completed, task_failed
    task_id: str
    user_id: str
    status: TaskStatus
    progress: Optional[int] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Optional[Dict[str, Any]] = None