"""
自定义异常类和异常处理器
"""
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class COTStudioException(Exception):
    """
    COT Studio 基础异常类
    """
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or "GENERAL_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class FileProcessingError(COTStudioException):
    """
    文件处理异常
    """
    def __init__(self, message: str, error_code: str = "FILE_PROCESSING_ERROR", filename: Optional[str] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            details={"filename": filename} if filename else {}
        )


class OCRProcessingError(COTStudioException):
    """
    OCR处理异常
    """
    def __init__(self, message: str, engine: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="OCR_PROCESSING_ERROR",
            details={"engine": engine} if engine else {}
        )


class LLMServiceError(COTStudioException):
    """
    LLM服务异常
    """
    def __init__(self, message: str, provider: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="LLM_SERVICE_ERROR",
            details={"provider": provider} if provider else {}
        )


class DatabaseError(COTStudioException):
    """
    数据库操作异常
    """
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details={"operation": operation} if operation else {}
        )


class AuthenticationError(COTStudioException):
    """
    认证异常
    """
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationError(COTStudioException):
    """
    授权异常
    """
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR"
        )


class ValidationError(COTStudioException):
    """
    数据验证异常
    """
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field": field} if field else {}
        )


# 异常处理器
async def cot_studio_exception_handler(request: Request, exc: COTStudioException):
    """
    COT Studio 异常处理器
    """
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": request.state.timestamp if hasattr(request.state, 'timestamp') else None
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP异常处理器
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "timestamp": request.state.timestamp if hasattr(request.state, 'timestamp') else None
        }
    )


async def validation_exception_handler(request: Request, exc: Exception):
    """
    验证异常处理器
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": str(exc),
            "timestamp": request.state.timestamp if hasattr(request.state, 'timestamp') else None
        }
    )