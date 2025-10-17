"""
错误报告API端点
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


class ErrorReport(BaseModel):
    """错误报告模型"""
    message: str
    stack: Optional[str] = None
    url: str
    userAgent: str
    timestamp: str
    level: str = "error"
    context: Optional[Dict[str, Any]] = None


class ErrorReportRequest(BaseModel):
    """错误报告请求模型"""
    errors: List[ErrorReport]


@router.post("/report")
async def report_errors(
    request: ErrorReportRequest,
    http_request: Request
):
    """
    接收前端错误报告
    
    Args:
        request: 错误报告请求
        http_request: HTTP请求对象
        
    Returns:
        成功响应
    """
    try:
        # 记录错误到日志
        for error in request.errors:
            logger.error(
                f"Frontend Error: {error.message}",
                extra={
                    "url": error.url,
                    "userAgent": error.userAgent,
                    "timestamp": error.timestamp,
                    "stack": error.stack,
                    "context": error.context,
                    "client_ip": http_request.client.host if http_request.client else "unknown"
                }
            )
        
        return {
            "status": "success",
            "message": f"Received {len(request.errors)} error reports",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to process error reports: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process error reports")


@router.get("/health")
async def error_reporting_health():
    """
    错误报告服务健康检查
    
    Returns:
        健康状态
    """
    return {
        "status": "healthy",
        "service": "error-reporting",
        "timestamp": datetime.utcnow().isoformat()
    }