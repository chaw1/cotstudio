"""
导出任务管理服务
"""
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..models import ExportTask, Project, User
from ..schemas.export import ExportRequest, ExportTaskResponse, ExportStatus
from .base_service import BaseService


class ExportTaskService(BaseService):
    """导出任务管理服务"""
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    async def create_export_task(
        self, 
        task_id: str,
        project_id: str,
        user_id: str,
        export_request: ExportRequest,
        export_type: str = "single"
    ) -> ExportTask:
        """
        创建导出任务记录
        
        Args:
            task_id: Celery任务ID
            project_id: 项目ID
            user_id: 用户ID
            export_request: 导出请求
            export_type: 导出类型 (single/package)
            
        Returns:
            导出任务对象
        """
        export_task = ExportTask(
            task_id=task_id,
            project_id=project_id,
            user_id=user_id,
            export_format=export_request.format.value,
            export_type=export_type,
            export_options=export_request.model_dump(),
            status=ExportStatus.PENDING.value,
            progress=0.0,
            message="任务已创建",
            # 设置文件过期时间（24小时后）
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        self.db.add(export_task)
        self.db.commit()
        self.db.refresh(export_task)
        
        return export_task
    
    async def update_task_status(
        self,
        task_id: str,
        status: str,
        progress: float = None,
        message: str = None,
        error_message: str = None,
        file_path: str = None,
        file_size: int = None,
        download_url: str = None,
        checksum: str = None,
        validation_result: Dict[str, Any] = None,
        total_items: int = None
    ) -> Optional[ExportTask]:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 任务状态
            progress: 进度百分比
            message: 状态消息
            error_message: 错误消息
            file_path: 文件路径
            file_size: 文件大小
            download_url: 下载链接
            checksum: 文件校验和
            validation_result: 验证结果
            total_items: 数据项总数
            
        Returns:
            更新后的任务对象
        """
        export_task = self.db.query(ExportTask).filter(
            ExportTask.task_id == task_id
        ).first()
        
        if not export_task:
            return None
        
        # 更新状态
        export_task.status = status
        
        if progress is not None:
            export_task.progress = progress
        
        if message is not None:
            export_task.message = message
        
        if error_message is not None:
            export_task.error_message = error_message
        
        if file_path is not None:
            export_task.file_path = file_path
        
        if file_size is not None:
            export_task.file_size = file_size
        
        if download_url is not None:
            export_task.download_url = download_url
        
        if checksum is not None:
            export_task.checksum = checksum
        
        if validation_result is not None:
            export_task.validation_result = validation_result
        
        if total_items is not None:
            export_task.total_items = total_items
        
        # 更新时间戳
        if status == ExportStatus.PROCESSING.value and not export_task.started_at:
            export_task.started_at = datetime.utcnow()
        
        if status in [ExportStatus.COMPLETED.value, ExportStatus.FAILED.value]:
            export_task.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(export_task)
        
        return export_task
    
    async def get_task_by_id(self, task_id: str) -> Optional[ExportTask]:
        """
        根据任务ID获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象
        """
        return self.db.query(ExportTask).filter(
            ExportTask.task_id == task_id
        ).first()
    
    async def get_user_tasks(
        self,
        user_id: str,
        project_id: str = None,
        status: str = None,
        limit: int = 10,
        offset: int = 0
    ) -> tuple[List[ExportTask], int]:
        """
        获取用户的导出任务列表
        
        Args:
            user_id: 用户ID
            project_id: 项目ID（可选）
            status: 任务状态（可选）
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            任务列表和总数
        """
        query = self.db.query(ExportTask).filter(
            ExportTask.user_id == user_id
        )
        
        if project_id:
            query = query.filter(ExportTask.project_id == project_id)
        
        if status:
            query = query.filter(ExportTask.status == status)
        
        # 获取总数
        total = query.count()
        
        # 获取分页数据
        tasks = query.order_by(desc(ExportTask.created_at)).offset(offset).limit(limit).all()
        
        return tasks, total
    
    async def get_project_export_history(
        self,
        project_id: str,
        user_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> tuple[List[ExportTask], int]:
        """
        获取项目的导出历史
        
        Args:
            project_id: 项目ID
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            任务列表和总数
        """
        query = self.db.query(ExportTask).filter(
            and_(
                ExportTask.project_id == project_id,
                ExportTask.user_id == user_id
            )
        )
        
        total = query.count()
        tasks = query.order_by(desc(ExportTask.created_at)).offset(offset).limit(limit).all()
        
        return tasks, total
    
    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """
        删除导出任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        export_task = self.db.query(ExportTask).filter(
            and_(
                ExportTask.task_id == task_id,
                ExportTask.user_id == user_id
            )
        ).first()
        
        if not export_task:
            return False
        
        # 删除文件
        if export_task.file_path and os.path.exists(export_task.file_path):
            try:
                os.remove(export_task.file_path)
            except Exception:
                pass  # 忽略文件删除错误
        
        # 删除数据库记录
        self.db.delete(export_task)
        self.db.commit()
        
        return True
    
    async def cleanup_expired_tasks(self) -> int:
        """
        清理过期的导出任务
        
        Returns:
            清理的任务数量
        """
        current_time = datetime.utcnow()
        
        # 查找过期任务
        expired_tasks = self.db.query(ExportTask).filter(
            ExportTask.expires_at < current_time
        ).all()
        
        cleaned_count = 0
        
        for task in expired_tasks:
            # 删除文件
            if task.file_path and os.path.exists(task.file_path):
                try:
                    os.remove(task.file_path)
                except Exception:
                    pass
            
            # 删除数据库记录
            self.db.delete(task)
            cleaned_count += 1
        
        if cleaned_count > 0:
            self.db.commit()
        
        return cleaned_count
    
    def task_to_response(self, task: ExportTask) -> ExportTaskResponse:
        """
        将任务对象转换为响应对象
        
        Args:
            task: 任务对象
            
        Returns:
            任务响应对象
        """
        return ExportTaskResponse(
            task_id=task.task_id,
            status=ExportStatus(task.status),
            progress=task.progress,
            message=task.message,
            download_url=task.download_url,
            created_at=task.created_at,
            completed_at=task.completed_at
        )