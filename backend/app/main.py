from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.v1 import auth, websocket, tasks, projects, files, ocr, cot_generation, cot_annotation, knowledge_graph, settings as settings_router, export, audit_simple, monitoring, user_management, system_monitor, analytics, errors
from app.core.config import settings
from app.core.database import engine
from app.models.base import Base
from app.core.exceptions import (
    COTStudioException,
    cot_studio_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.app_logging import logger
from app.middleware.auth import request_logging_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    logger.info("Starting COT Studio API")
    
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # 初始化审计系统
    try:
        from app.core.init_audit_system import init_audit_system
        init_audit_system()
        logger.info("Audit system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize audit system: {e}")
    
    # 初始化性能优化
    try:
        from app.core.database_optimization import init_database_optimization
        init_database_optimization()
        logger.info("Performance optimization initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize performance optimization: {e}")
    
    # 初始化Neo4j连接
    try:
        from app.core.neo4j_connection import init_neo4j
        if init_neo4j():
            logger.info("Neo4j connection initialized successfully")
        else:
            logger.warning("Neo4j connection failed - KG features may not work")
    except Exception as e:
        logger.error(f"Neo4j initialization error: {e}")
    
    yield
    
    # 关闭时执行
    logger.info("Shutting down COT Studio API")
    
    # 关闭监控系统
    try:
        from app.core.monitoring import cleanup_monitoring
        cleanup_monitoring()
        logger.info("Monitoring system cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning up monitoring: {e}")
    
    # 关闭Neo4j连接
    try:
        from app.core.neo4j_connection import close_neo4j
        close_neo4j()
        logger.info("Neo4j connection closed")
    except Exception as e:
        logger.error(f"Error closing Neo4j connection: {e}")


app = FastAPI(
    title="COT Studio API",
    description="Chain-of-Thought 数据集构建平台 API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 添加安全中间件
from app.middleware.security import SecurityMiddleware, RequestSizeMiddleware
from app.middleware.performance import performance_monitoring_middleware, response_caching_middleware

app.add_middleware(SecurityMiddleware, enable_rate_limiting=True, enable_security_headers=True)
app.add_middleware(RequestSizeMiddleware, max_size=settings.MAX_FILE_SIZE)

# 添加性能监控中间件
app.middleware("http")(performance_monitoring_middleware)
app.middleware("http")(response_caching_middleware)

# 添加请求日志中间件
app.middleware("http")(request_logging_middleware)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 异常处理器
@app.exception_handler(COTStudioException)
async def handle_cot_studio_exception(request: Request, exc: COTStudioException):
    return await cot_studio_exception_handler(request, exc)

@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException):
    return await http_exception_handler(request, exc)

@app.exception_handler(ValidationError)
async def handle_validation_exception(request: Request, exc: ValidationError):
    return await validation_exception_handler(request, exc)

# 注册API路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(user_management.router, prefix="/api/v1/user-management", tags=["user-management"])
app.include_router(projects.router, prefix="/api/v1", tags=["projects"])
app.include_router(files.router, prefix="/api/v1", tags=["files"])
app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["ocr"])
app.include_router(cot_generation.router, prefix="/api/v1/cot", tags=["cot-generation"])
app.include_router(cot_annotation.router, prefix="/api/v1/cot-annotation", tags=["cot-annotation"])
app.include_router(knowledge_graph.router, prefix="/api/v1/kg", tags=["knowledge-graph"])
app.include_router(settings_router.router, prefix="/api/v1", tags=["settings"])
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
app.include_router(export.router, prefix="/api/v1/export", tags=["export"])
app.include_router(audit_simple.router, prefix="/api/v1/audit", tags=["audit"])
app.include_router(websocket.router, prefix="/api/v1", tags=["websocket"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])
app.include_router(system_monitor.router, prefix="/api/v1/system", tags=["system-monitor"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(errors.router, prefix="/api/v1/errors", tags=["errors"])


@app.get("/")
async def root():
    """
    API根端点
    """
    return JSONResponse(
        content={
            "message": "COT Studio API",
            "version": "0.1.0",
            "status": "running",
            "docs_url": "/docs",
            "redoc_url": "/redoc"
        }
    )


@app.get("/health")
async def health_check():
    """
    健康检查端点
    """
    try:
        # 检查数据库连接
        from app.core.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "healthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        db_status = "unhealthy"
    
    # 检查Celery连接
    try:
        from app.core.celery_app import celery_app
        celery_inspect = celery_app.control.inspect()
        active_workers = celery_inspect.active()
        celery_status = "healthy" if active_workers else "no_workers"
    except Exception as e:
        logger.error("Celery health check failed", error=str(e))
        celery_status = "unhealthy"
    
    return JSONResponse(
        content={
            "status": "healthy" if db_status == "healthy" else "degraded",
            "service": "cot-studio-api",
            "components": {
                "database": db_status,
                "celery": celery_status
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )