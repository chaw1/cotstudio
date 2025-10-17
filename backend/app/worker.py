"""
Celery worker入口点
"""
from app.core.celery_app import celery_app

# 导入任务模块以确保任务被注册
from app.workers import tasks  # noqa

if __name__ == "__main__":
    celery_app.start()