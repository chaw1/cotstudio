"""
任务监控服务
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func

from app.core.app_logging import logger
from app.core.celery_app import celery_app
from app.models.task import TaskMonitor, TaskStatus, TaskType, TaskPriority
from app.schemas.task import (
    TaskMonitorCreate, TaskMonitorUpdate, TaskMonitorResponse,
    TaskStatistics, TaskQueueInfo, WorkerInfo, TaskFilterParams
)


class TaskMonitorService:
    """任务监控服务"""
    
    def create_task_monitor(
        self, 
        db: Session, 
        task_data: TaskMonitorCreate
    ) -> TaskMonitor:
        """创建任务监控记录"""
        try:
            task_monitor = TaskMonitor(**task_data.dict())
            db.add(task_monitor)
            db.commit()
            db.refresh(task_monitor)
            
            logger.info(
                "Task monitor created",
                task_id=task_monitor.task_id,
                task_type=task_monitor.task_type,
                user_id=task_monitor.user_id
            )
            
            return task_monitor
            
        except Exception as e:
            db.rollback()
            logger.error("Failed to create task monitor", error=str(e))
            raise
    
    def get_task_monitor(
        self, 
        db: Session, 
        task_id: str
    ) -> Optional[TaskMonitor]:
        """根据任务ID获取任务监控记录"""
        return db.query(TaskMonitor).filter(TaskMonitor.task_id == task_id).first()
    
    def get_task_monitor_by_id(
        self, 
        db: Session, 
        monitor_id: UUID
    ) -> Optional[TaskMonitor]:
        """根据监控ID获取任务监控记录"""
        return db.query(TaskMonitor).filter(TaskMonitor.id == monitor_id).first()
    
    def update_task_monitor(
        self, 
        db: Session, 
        task_id: str, 
        update_data: TaskMonitorUpdate
    ) -> Optional[TaskMonitor]:
        """更新任务监控记录"""
        try:
            task_monitor = self.get_task_monitor(db, task_id)
            if not task_monitor:
                return None
            
            update_dict = update_data.dict(exclude_unset=True)
            
            # 自动设置时间戳
            if update_data.status == TaskStatus.PROGRESS and not task_monitor.started_at:
                update_dict["started_at"] = datetime.utcnow()
            elif update_data.status in [TaskStatus.SUCCESS, TaskStatus.FAILURE, TaskStatus.REVOKED]:
                update_dict["completed_at"] = datetime.utcnow()
                # 计算实际执行时间
                if task_monitor.started_at:
                    duration = int((datetime.utcnow() - task_monitor.started_at).total_seconds())
                    update_dict["actual_duration"] = duration
            
            for field, value in update_dict.items():
                setattr(task_monitor, field, value)
            
            db.commit()
            db.refresh(task_monitor)
            
            logger.info(
                "Task monitor updated",
                task_id=task_id,
                status=task_monitor.status,
                progress=task_monitor.progress
            )
            
            return task_monitor
            
        except Exception as e:
            db.rollback()
            logger.error("Failed to update task monitor", task_id=task_id, error=str(e))
            raise
    
    def list_task_monitors(
        self, 
        db: Session, 
        filters: TaskFilterParams
    ) -> Tuple[List[TaskMonitor], int]:
        """列出任务监控记录"""
        try:
            query = db.query(TaskMonitor)
            
            # 应用过滤条件
            if filters.status:
                query = query.filter(TaskMonitor.status.in_(filters.status))
            
            if filters.task_type:
                query = query.filter(TaskMonitor.task_type.in_(filters.task_type))
            
            if filters.priority:
                query = query.filter(TaskMonitor.priority.in_(filters.priority))
            
            if filters.user_id:
                query = query.filter(TaskMonitor.user_id == filters.user_id)
            
            if filters.queue_name:
                query = query.filter(TaskMonitor.queue_name == filters.queue_name)
            
            if filters.is_critical is not None:
                query = query.filter(TaskMonitor.is_critical == filters.is_critical)
            
            if filters.created_after:
                query = query.filter(TaskMonitor.created_at >= filters.created_after)
            
            if filters.created_before:
                query = query.filter(TaskMonitor.created_at <= filters.created_before)
            
            # 获取总数
            total = query.count()
            
            # 应用排序
            order_column = getattr(TaskMonitor, filters.order_by, TaskMonitor.created_at)
            if filters.order_desc:
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
            
            # 应用分页
            tasks = query.offset(filters.offset).limit(filters.limit).all()
            
            return tasks, total
            
        except Exception as e:
            logger.error("Failed to list task monitors", error=str(e))
            raise
    
    def get_task_statistics(
        self, 
        db: Session, 
        user_id: Optional[str] = None,
        days: int = 7
    ) -> TaskStatistics:
        """获取任务统计信息"""
        try:
            # 时间范围
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = db.query(TaskMonitor).filter(TaskMonitor.created_at >= start_date)
            if user_id:
                query = query.filter(TaskMonitor.user_id == user_id)
            
            tasks = query.all()
            
            total_tasks = len(tasks)
            active_tasks = len([t for t in tasks if t.is_active])
            completed_tasks = len([t for t in tasks if t.is_completed])
            failed_tasks = len([t for t in tasks if t.status == TaskStatus.FAILURE])
            
            success_rate = 0.0
            if completed_tasks > 0:
                success_tasks = len([t for t in tasks if t.status == TaskStatus.SUCCESS])
                success_rate = success_tasks / completed_tasks
            
            # 计算平均执行时间
            durations = [t.actual_duration for t in tasks if t.actual_duration]
            average_duration = sum(durations) / len(durations) if durations else None
            
            # 按类型统计
            by_type = {}
            for task_type in TaskType:
                count = len([t for t in tasks if t.task_type == task_type])
                if count > 0:
                    by_type[task_type.value] = count
            
            # 按状态统计
            by_status = {}
            for status in TaskStatus:
                count = len([t for t in tasks if t.status == status])
                if count > 0:
                    by_status[status.value] = count
            
            # 按优先级统计
            by_priority = {}
            for priority in TaskPriority:
                count = len([t for t in tasks if t.priority == priority])
                if count > 0:
                    by_priority[priority.value] = count
            
            return TaskStatistics(
                total_tasks=total_tasks,
                active_tasks=active_tasks,
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                success_rate=success_rate,
                average_duration=average_duration,
                by_type=by_type,
                by_status=by_status,
                by_priority=by_priority
            )
            
        except Exception as e:
            logger.error("Failed to get task statistics", error=str(e))
            raise
    
    def get_queue_info(self) -> List[TaskQueueInfo]:
        """获取队列信息"""
        try:
            inspect = celery_app.control.inspect()
            
            # 获取活跃任务
            active_tasks = inspect.active() or {}
            # 获取预定任务
            scheduled_tasks = inspect.scheduled() or {}
            # 获取保留任务
            reserved_tasks = inspect.reserved() or {}
            
            queue_info = {}
            
            # 统计各队列的任务数量
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    queue = task.get('delivery_info', {}).get('routing_key', 'default')
                    if queue not in queue_info:
                        queue_info[queue] = {'active': 0, 'scheduled': 0, 'reserved': 0}
                    queue_info[queue]['active'] += 1
            
            for worker, tasks in scheduled_tasks.items():
                for task in tasks:
                    queue = task.get('delivery_info', {}).get('routing_key', 'default')
                    if queue not in queue_info:
                        queue_info[queue] = {'active': 0, 'scheduled': 0, 'reserved': 0}
                    queue_info[queue]['scheduled'] += 1
            
            for worker, tasks in reserved_tasks.items():
                for task in tasks:
                    queue = task.get('delivery_info', {}).get('routing_key', 'default')
                    if queue not in queue_info:
                        queue_info[queue] = {'active': 0, 'scheduled': 0, 'reserved': 0}
                    queue_info[queue]['reserved'] += 1
            
            result = []
            for queue_name, counts in queue_info.items():
                total = counts['active'] + counts['scheduled'] + counts['reserved']
                result.append(TaskQueueInfo(
                    queue_name=queue_name,
                    active_tasks=counts['active'],
                    scheduled_tasks=counts['scheduled'],
                    reserved_tasks=counts['reserved'],
                    total_tasks=total
                ))
            
            return result
            
        except Exception as e:
            logger.error("Failed to get queue info", error=str(e))
            return []
    
    def get_worker_info(self) -> List[WorkerInfo]:
        """获取工作节点信息"""
        try:
            inspect = celery_app.control.inspect()
            
            # 获取工作节点统计
            stats = inspect.stats() or {}
            # 获取活跃任务
            active_tasks = inspect.active() or {}
            
            result = []
            for worker_name, worker_stats in stats.items():
                active_count = len(active_tasks.get(worker_name, []))
                
                result.append(WorkerInfo(
                    worker_name=worker_name,
                    status="online",
                    active_tasks=active_count,
                    processed_tasks=worker_stats.get('total', {}).get('tasks.processed', 0),
                    load_average=worker_stats.get('rusage', {}).get('load_avg', [0.0, 0.0, 0.0]),
                    last_heartbeat=datetime.utcnow()  # Celery doesn't provide this directly
                ))
            
            return result
            
        except Exception as e:
            logger.error("Failed to get worker info", error=str(e))
            return []
    
    def retry_task(
        self, 
        db: Session, 
        task_id: str, 
        reason: Optional[str] = None
    ) -> bool:
        """重试任务"""
        try:
            task_monitor = self.get_task_monitor(db, task_id)
            if not task_monitor or not task_monitor.can_retry():
                return False
            
            # 更新重试计数
            task_monitor.retry_count += 1
            task_monitor.status = TaskStatus.RETRY
            task_monitor.message = f"Retrying task. Reason: {reason or 'Manual retry'}"
            task_monitor.updated_at = datetime.utcnow()
            
            db.commit()
            
            # 重新提交任务到Celery
            # 这里需要根据任务类型重新提交相应的任务
            # 暂时使用通用的重试机制
            celery_app.send_task(
                task_monitor.task_name,
                args=task_monitor.parameters.get('args', []) if task_monitor.parameters else [],
                kwargs=task_monitor.parameters.get('kwargs', {}) if task_monitor.parameters else {},
                task_id=task_monitor.task_id,
                countdown=task_monitor.retry_delay
            )
            
            logger.info(
                "Task retry initiated",
                task_id=task_id,
                retry_count=task_monitor.retry_count,
                reason=reason
            )
            
            return True
            
        except Exception as e:
            db.rollback()
            logger.error("Failed to retry task", task_id=task_id, error=str(e))
            return False
    
    def cancel_task(
        self, 
        db: Session, 
        task_id: str, 
        reason: Optional[str] = None
    ) -> bool:
        """取消任务"""
        try:
            # 取消Celery任务
            celery_app.control.revoke(task_id, terminate=True)
            
            # 更新任务状态
            task_monitor = self.get_task_monitor(db, task_id)
            if task_monitor:
                task_monitor.status = TaskStatus.REVOKED
                task_monitor.completed_at = datetime.utcnow()
                task_monitor.message = f"Task cancelled. Reason: {reason or 'Manual cancellation'}"
                task_monitor.updated_at = datetime.utcnow()
                
                if task_monitor.started_at:
                    duration = int((datetime.utcnow() - task_monitor.started_at).total_seconds())
                    task_monitor.actual_duration = duration
                
                db.commit()
            
            logger.info("Task cancelled", task_id=task_id, reason=reason)
            return True
            
        except Exception as e:
            db.rollback()
            logger.error("Failed to cancel task", task_id=task_id, error=str(e))
            return False
    
    def cleanup_old_tasks(
        self, 
        db: Session, 
        days: int = 30
    ) -> int:
        """清理旧任务记录"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # 只删除已完成的任务
            deleted_count = db.query(TaskMonitor).filter(
                and_(
                    TaskMonitor.completed_at < cutoff_date,
                    TaskMonitor.status.in_([TaskStatus.SUCCESS, TaskStatus.FAILURE, TaskStatus.REVOKED])
                )
            ).delete()
            
            db.commit()
            
            logger.info("Old tasks cleaned up", deleted_count=deleted_count, days=days)
            return deleted_count
            
        except Exception as e:
            db.rollback()
            logger.error("Failed to cleanup old tasks", error=str(e))
            return 0


# 创建服务实例
task_monitor_service = TaskMonitorService()