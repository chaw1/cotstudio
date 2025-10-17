"""
认证相关API端点
"""
from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.app_logging import AuditLogger
from app.core.security import create_access_token, create_refresh_token
from app.middleware.auth import get_current_active_user
from app.services.user_service import user_service

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    roles: list[str]


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request, 
    login_data: LoginRequest,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    用户登录端点
    """
    # 使用用户服务进行认证
    user = user_service.authenticate(db, login_data.username, login_data.password)
    
    if not user:
        AuditLogger.log_authentication(
            user_id=login_data.username,
            action="login_failed",
            success=False,
            details={"reason": "invalid_credentials"},
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user_service.is_active(user):
        AuditLogger.log_authentication(
            user_id=str(user.id),
            action="login_failed",
            success=False,
            details={"reason": "inactive_user"},
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 获取用户角色
    user_roles = [user.role.value] if user.role is not None else ["USER"]
    
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "roles": user_roles,
            "permissions": []  # 这里可以根据角色设置权限
        },
        expires_delta=access_token_expires
    )
    
    # 创建刷新令牌
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "username": user.username}
    )
    
    # 记录成功登录
    AuditLogger.log_authentication(
        user_id=str(user.id),
        action="login_success",
        success=True,
        request=request
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> UserResponse:
    """
    获取当前用户信息
    """
    return UserResponse(
        user_id=current_user["user_id"],
        username=current_user["username"],
        email=current_user["email"],
        roles=current_user["roles"]
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    用户登出端点
    """
    # 记录登出操作
    AuditLogger.log_authentication(
        user_id=current_user["user_id"],
        action="logout",
        success=True,
        request=request
    )
    
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌
    """
    # 从请求头获取refresh token
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    refresh_token = authorization.split(" ")[1]
    
    try:
        # 验证refresh token
        from app.core.security import verify_token
        payload = verify_token(refresh_token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # 获取用户信息
        user = user_service.get(db, user_id)
        if not user or not user_service.is_active(user):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # 获取用户角色
        user_roles = [user.role.value] if user.role is not None else ["USER"]
        
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "username": user.username,
                "email": user.email,
                "roles": user_roles,
                "permissions": []
            },
            expires_delta=access_token_expires
        )
        
        # 创建新的刷新令牌
        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # 记录token刷新
        AuditLogger.log_authentication(
            user_id=str(user.id),
            action="token_refresh",
            success=True,
            request=request
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )


@router.get("/test-protected")
async def test_protected_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    测试受保护的端点
    """
    return {
        "message": "This is a protected endpoint",
        "user": current_user["username"],
        "user_id": current_user["user_id"]
    }