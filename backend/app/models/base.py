"""
基础模型类
"""
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_time():
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)

Base = declarative_base()


class BaseModel(Base):
    """
    基础模型类，包含通用字段
    使用北京时间(UTC+8)作为默认时区
    """
    __abstract__ = True
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    created_at = Column(DateTime(timezone=True), default=get_beijing_time, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_beijing_time, onupdate=get_beijing_time, nullable=False)