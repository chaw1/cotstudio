"""
任务监控数据模型
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "PENDING"
    PROGRESS = "PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class TaskType(str, Enum):
    """任务类型枚举"""
    OCR_PROCESSING = "ocr_processing"
    LLM_PROCESSING = "llm_processing"
    KG_EXTRACTION = "kg_extraction"
    FILE_PROCESSING = "file_processing"
    EXPORT_PROCESSING = "export_processing"
    IMPORT_PROCESSING = "import_processing"
    HEALTH_CHECK = "health_check"


class TaskPriority(str, Enum):
    """任务优先级枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskMonitor(Base):
    """任务监控模型"""
    __tablename__ = "task_monitors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(String, unique=True, nullable=False, index=True)
    task_name = Column(String, nullable=False)
    task_type = Column(SQLEnum(TaskType), nullable=False)
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    priority = Column(SQLEnum(TaskPriority), nullable=False, default=TaskPriority.NORMAL)
    
    # 进度信息
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String)
    total_steps = Column(Integer)
    
    # 执行信息
    user_id = Column(String, nullable=False, index=True)
    worker_name = Column(String)
    queue_name = Column(String, default="default")
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 执行时间统计
    estimated_duration = Column(Integer)  # 预估执行时间(秒)
    actual_duration = Column(Integer)     # 实际执行时间(秒)
    
    # 任务参数和结果
    parameters = Column(JSON)  # 任务输入参数
    result = Column(JSON)      # 任务执行结果
    error_info = Column(JSON)  # 错误信息
    
    # 重试信息
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    retry_delay = Column(Integer, default=60)  # 重试延迟(秒)
    
    # 状态消息
    message = Column(Text)
    
    # 标记和标签
    tags = Column(JSON)  # 任务标签
    is_critical = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<TaskMonitor(id={self.id}, task_id={self.task_id}, status={self.status})>"
    
    @property
    def execution_time(self) -> Optional[int]:
        """计算执行时间"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        elif self.started_at:
            return int((datetime.utcnow() - self.started_at).total_seconds())
        return None
    
    @property
    def is_active(self) -> bool:
        """判断任务是否活跃"""
        return self.status in [TaskStatus.PENDING, TaskStatus.PROGRESS, TaskStatus.RETRY]
    
    @property
    def is_completed(self) -> bool:
        """判断任务是否完成"""
        return self.status in [TaskStatus.SUCCESS, TaskStatus.FAILURE, TaskStatus.REVOKED]
    
    def can_retry(self) -> bool:
        """判断是否可以重试"""
        return (
            self.status == TaskStatus.FAILURE and 
            self.retry_count < self.max_retries
        )