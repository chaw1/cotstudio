"""
审计日志装饰器
"""
import functools
from typing import Any, Callable, Dict, Optional
from datetime import datetime

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit import AuditEventType, AuditSeverity, ResourceType
from app.services.audit_service import AuditService
from app.core.app_logging import logger


def audit_operation(
    event_type: AuditEventType,
    action: str,
    resource_type: Optional[ResourceType] = None,
    severity: AuditSeverity = AuditSeverity.LOW,
    description: Optional[str] = None,
    capture_args: bool = False,
    capture_result: bool = False
):
    """
    审计操作装饰器
    
    Args:
        event_type: 事件类型
        action: 操作名称
        resource_type: 资源类型
        severity: 严重程度
        description: 操作描述
        capture_args: 是否捕获函数参数
        capture_result: 是否捕获函数返回值
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 提取常用参数
            db: Optional[Session] = None
            current_user: Optional[dict] = None
            request: Optional[Request] = None
            
            # 从参数中提取数据库会话、用户信息和请求对象
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                elif isinstance(arg, Request):
                    request = arg
            
            for key, value in kwargs.items():
                if key == "db" and isinstance(value, Session):
                    db = value
                elif key == "current_user" and isinstance(value, dict):
                    current_user = value
                elif key == "request" and isinstance(value, Request):
                    request = value
            
            if not db:
                logger.warning("No database session found in audit decorator")
                return await func(*args, **kwargs)
            
            audit_service = AuditService(db)
            
            # 准备审计数据
            audit_data = {
                "user_id": current_user.get("user_id") if current_user else None,
                "event_type": event_type,
                "action": action,
                "resource_type": resource_type,
                "severity": severity,
                "description": description or f"Executed {func.__name__}",
                "request": request
            }
            
            # 捕获函数参数
            if capture_args:
                audit_data["details"] = {
                    "function": func.__name__,
                    "args": [str(arg) for arg in args if not isinstance(arg, (Session, Request))],
                    "kwargs": {k: str(v) for k, v in kwargs.items() if k not in ["db", "request"]}
                }
            
            try:
                # 执行原函数
                result = await func(*args, **kwargs)
                
                # 捕获返回值
                if capture_result and result is not None:
                    if not audit_data.get("details"):
                        audit_data["details"] = {}
                    audit_data["details"]["result_type"] = type(result).__name__
                    if hasattr(result, "id"):
                        audit_data["resource_id"] = str(result.id)
                        audit_data["resource_name"] = getattr(result, "name", None)
                
                # 记录成功的操作
                audit_service.log_operation(**audit_data)
                
                return result
                
            except Exception as e:
                # 记录失败的操作
                audit_data.update({
                    "success": False,
                    "error_message": str(e),
                    "severity": AuditSeverity.HIGH
                })
                audit_service.log_operation(**audit_data)
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同步版本的包装器
            db: Optional[Session] = None
            current_user: Optional[dict] = None
            request: Optional[Request] = None
            
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                elif isinstance(arg, Request):
                    request = arg
            
            for key, value in kwargs.items():
                if key == "db" and isinstance(value, Session):
                    db = value
                elif key == "current_user" and isinstance(value, dict):
                    current_user = value
                elif key == "request" and isinstance(value, Request):
                    request = value
            
            if not db:
                logger.warning("No database session found in audit decorator")
                return func(*args, **kwargs)
            
            audit_service = AuditService(db)
            
            audit_data = {
                "user_id": current_user.get("user_id") if current_user else None,
                "event_type": event_type,
                "action": action,
                "resource_type": resource_type,
                "severity": severity,
                "description": description or f"Executed {func.__name__}",
                "request": request
            }
            
            if capture_args:
                audit_data["details"] = {
                    "function": func.__name__,
                    "args": [str(arg) for arg in args if not isinstance(arg, (Session, Request))],
                    "kwargs": {k: str(v) for k, v in kwargs.items() if k not in ["db", "request"]}
                }
            
            try:
                result = func(*args, **kwargs)
                
                if capture_result and result is not None:
                    if not audit_data.get("details"):
                        audit_data["details"] = {}
                    audit_data["details"]["result_type"] = type(result).__name__
                    if hasattr(result, "id"):
                        audit_data["resource_id"] = str(result.id)
                        audit_data["resource_name"] = getattr(result, "name", None)
                
                audit_service.log_operation(**audit_data)
                return result
                
            except Exception as e:
                audit_data.update({
                    "success": False,
                    "error_message": str(e),
                    "severity": AuditSeverity.HIGH
                })
                audit_service.log_operation(**audit_data)
                raise
        
        # 根据函数是否为协程选择包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def audit_create(resource_type: ResourceType, description: Optional[str] = None):
    """创建操作审计装饰器"""
    return audit_operation(
        event_type=AuditEventType.CREATE,
        action="create",
        resource_type=resource_type,
        severity=AuditSeverity.MEDIUM,
        description=description,
        capture_result=True
    )


def audit_update(resource_type: ResourceType, description: Optional[str] = None):
    """更新操作审计装饰器"""
    return audit_operation(
        event_type=AuditEventType.UPDATE,
        action="update",
        resource_type=resource_type,
        severity=AuditSeverity.MEDIUM,
        description=description,
        capture_args=True,
        capture_result=True
    )


def audit_delete(resource_type: ResourceType, description: Optional[str] = None):
    """删除操作审计装饰器"""
    return audit_operation(
        event_type=AuditEventType.DELETE,
        action="delete",
        resource_type=resource_type,
        severity=AuditSeverity.HIGH,
        description=description,
        capture_args=True
    )


def audit_sensitive_operation(action: str, description: Optional[str] = None):
    """敏感操作审计装饰器"""
    return audit_operation(
        event_type=AuditEventType.SYSTEM_CONFIG,
        action=action,
        severity=AuditSeverity.CRITICAL,
        description=description,
        capture_args=True,
        capture_result=True
    )


# 导入asyncio用于检查协程函数
import asyncio