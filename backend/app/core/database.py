"""
数据库连接和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings

# 创建数据库引擎
if settings.DATABASE_URL.startswith("postgresql"):
    # PostgreSQL配置
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=1800,  # 30分钟后回收连接
        echo=settings.DEBUG,
    )
else:
    # SQLite配置
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=StaticPool,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 导入所有模型以确保它们被注册
from app.models.base import Base
from app.models import *  # noqa


def get_db():
    """
    获取数据库会话的依赖注入函数
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()