"""
认证中间件
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.app_logging import AuditLogger
from app.core.security import verify_token
from app.core.database import get_db

# HTTP Bearer认证方案
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    获取当前用户信息的依赖注入函数
    """
    if not credentials:
        AuditLogger.log_authentication(
            user_id=None,
            action="token_missing",
            success=False,
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        
        # 记录成功的认证
        AuditLogger.log_authentication(
            user_id=user_id,
            action="token_verified",
            success=True,
            request=request
        )
        
        return {
            "user_id": user_id,
            "username": payload.get("username"),
            "email": payload.get("email"),
            "roles": payload.get("roles", [payload.get("role", "USER")]),  # 支持单数和复数格式
            "permissions": payload.get("permissions", [])
        }
        
    except Exception as e:
        AuditLogger.log_authentication(
            user_id=None,
            action="token_verification_failed",
            success=False,
            details={"error": str(e)},
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    获取当前活跃用户的依赖注入函数
    """
    # 这里可以添加用户状态检查逻辑
    # 例如检查用户是否被禁用、是否需要重新验证等
    return current_user


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    可选的用户认证依赖注入函数 - 用于不强制要求认证的端点
    """
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            return None
        
        # 记录成功的认证
        AuditLogger.log_authentication(
            user_id=user_id,
            action="optional_token_verified",
            success=True,
            request=request
        )
        
        return {
            "user_id": user_id,
            "username": payload.get("username"),
            "email": payload.get("email"),
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", [])
        }
        
    except Exception as e:
        # 对于可选认证，不抛出异常，只记录日志
        AuditLogger.log_authentication(
            user_id=None,
            action="optional_token_verification_failed",
            success=False,
            details={"error": str(e)},
            request=request
        )
        return None


def require_permission(permission: str):
    """
    权限检查装饰器工厂 - 使用数据库权限系统
    """
    def permission_checker(
        current_user: dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        # 导入模型（避免循环导入）
        from app.models.user import User, UserRole
        
        # 获取用户信息
        user = db.query(User).filter(User.id == current_user["user_id"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # 检查管理员权限 - 管理员有所有权限
        if user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            return current_user
        
        # 对于普通用户，检查基于角色的权限
        from app.services.audit_service import PermissionService
        permission_service = PermissionService(db)
        
        # 检查用户权限
        has_permission = permission_service.check_permission(
            current_user["user_id"], 
            permission
        )
        
        if not has_permission:
            # 记录权限拒绝日志
            from app.services.audit_service import AuditService
            from app.models.audit import AuditEventType, AuditSeverity
            
            audit_service = AuditService(db)
            audit_service.log_operation(
                user_id=current_user["user_id"],
                event_type=AuditEventType.READ,
                action="permission_denied",
                description=f"Permission denied: {permission}",
                details={"required_permission": permission},
                severity=AuditSeverity.MEDIUM,
                success=False
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        
        return current_user
    
    return permission_checker


async def request_logging_middleware(request: Request, call_next):
    """
    请求日志中间件
    """
    # 生成请求ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    request.state.timestamp = datetime.utcnow().isoformat()
    
    # 记录请求开始
    start_time = datetime.utcnow()
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    # 记录请求日志
    from app.core.app_logging import logger
    logger.info(
        "Request processed",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time,
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    # 添加响应头
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    return response