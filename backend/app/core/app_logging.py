"""
日志配置和记录功能
"""
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import structlog
from fastapi import Request

from app.core.config import settings


def configure_logging():
    """
    配置结构化日志
    """
    # 配置structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if not settings.DEBUG 
            else structlog.dev.ConsoleRenderer(colors=True)
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 配置标准库日志
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
    )


# 获取结构化日志记录器
logger = structlog.get_logger()


class AuditLogger:
    """
    审计日志记录器
    """
    
    @staticmethod
    def log_operation(
        user_id: str,
        operation: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """
        记录操作审计日志
        """
        audit_data = {
            "event_type": "audit",
            "user_id": user_id,
            "operation": operation,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if request:
            audit_data.update({
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "request_id": getattr(request.state, "request_id", None)
            })
        
        logger.info("Operation performed", **audit_data)
    
    @staticmethod
    def log_authentication(
        user_id: Optional[str],
        action: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """
        记录认证相关日志
        """
        auth_data = {
            "event_type": "authentication",
            "user_id": user_id,
            "action": action,
            "success": success,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if request:
            auth_data.update({
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            })
        
        if success:
            logger.info("Authentication event", **auth_data)
        else:
            logger.warning("Authentication failed", **auth_data)
    
    @staticmethod
    def log_error(
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """
        记录错误日志
        """
        error_data = {
            "event_type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if request:
            error_data.update({
                "method": request.method,
                "url": str(request.url),
                "ip_address": request.client.host if request.client else None,
                "request_id": getattr(request.state, "request_id", None)
            })
        
        logger.error("Application error", **error_data, exc_info=True)


# 初始化日志配置
configure_logging()