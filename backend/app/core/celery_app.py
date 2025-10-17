"""
Celery应用配置
"""
from celery import Celery

from app.core.config import settings

# 创建Celery应用实例
celery_app = Celery(
    "cot_studio",
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"]
)

# Celery配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 时区设置 - 使用北京时间(UTC+8)
    timezone="Asia/Shanghai",
    enable_utc=False,
    
    # 任务路由
    task_routes={
        "app.workers.tasks.ocr_processing": {"queue": "ocr"},
        "app.workers.tasks.llm_processing": {"queue": "llm"},
        "app.workers.tasks.kg_extraction": {"queue": "kg"},
        "app.workers.tasks.file_processing": {"queue": "files"},
    },
    
    # 任务重试配置
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # 结果过期时间
    result_expires=3600,
    
    # 任务超时配置
    task_soft_time_limit=300,  # 5分钟软超时
    task_time_limit=600,       # 10分钟硬超时
    
    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,
)