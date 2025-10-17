"""
导出任务数据模型
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import BaseModel


class ExportTask(BaseModel):
    """导出任务模型"""
    __tablename__ = "export_tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), unique=True, nullable=False, index=True)  # Celery任务ID
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # 导出配置
    export_format = Column(String(20), nullable=False)  # json, markdown, latex, txt
    export_type = Column(String(20), default="single", nullable=False)  # single, package
    export_options = Column(JSON, default=dict)  # 导出选项
    
    # 任务状态
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, processing, completed, failed
    progress = Column(Float, default=0.0)  # 进度百分比
    message = Column(Text)  # 状态消息
    error_message = Column(Text)  # 错误消息
    
    # 结果信息
    file_path = Column(String(500))  # 导出文件路径
    file_size = Column(Integer)  # 文件大小（字节）
    download_url = Column(String(500))  # 下载链接
    checksum = Column(String(64))  # 文件校验和
    
    # 验证信息
    validation_result = Column(JSON)  # 验证结果
    total_items = Column(Integer)  # 导出数据项总数
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)  # 开始处理时间
    completed_at = Column(DateTime)  # 完成时间
    expires_at = Column(DateTime)  # 文件过期时间
    
    # 关系
    project = relationship("Project", back_populates="export_tasks")
    user = relationship("User", back_populates="export_tasks")
    
    def __repr__(self):
        return f"<ExportTask(id={self.id}, task_id={self.task_id}, status={self.status})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "export_format": self.export_format,
            "export_type": self.export_type,
            "export_options": self.export_options,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "error_message": self.error_message,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "download_url": self.download_url,
            "checksum": self.checksum,
            "validation_result": self.validation_result,
            "total_items": self.total_items,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }