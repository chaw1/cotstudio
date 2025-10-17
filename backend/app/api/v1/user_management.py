"""
用户管理API端点
"""
import math
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_

from app.core.database import get_db
from app.core.security import get_password_hash
from app.middleware.auth import get_current_active_user
from app.models.user import User, UserRole
from app.models.permission import UserProjectPermission, ProjectPermission
from app.models.project import Project
from app.schemas.user_management import (
    UserCreateRequest, UserUpdateRequest, UserResponse, UserListResponse,
    UserSearchRequest, PermissionGrantRequest, PermissionRevokeRequest,
    PermissionResponse, UserPermissionResponse, ProjectPermissionResponse,
    PermissionListResponse, PermissionSearchRequest, PasswordChangeRequest,
    PasswordResetRequest, UserStatsResponse
)
from app.schemas.common import MessageResponse
from app.services.user_service import user_service
from app.core.permissions import PermissionChecker, PermissionError, ResourceNotFoundError

router = APIRouter()


async def get_current_user_model(
    current_user_data: Dict[str, Any] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户的数据库模型对象"""
    user = user_service.get(db, current_user_data["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


def get_current_admin_user(
    current_user: User = Depends(get_current_user_model)
) -> User:
    """获取当前管理员用户"""
    if not PermissionChecker.check_admin_permission_sync(current_user):
        raise PermissionError("需要管理员权限")
    return current_user


def get_current_super_admin_user(
    current_user: User = Depends(get_current_user_model)
) -> User:
    """获取当前超级管理员用户"""
    if not PermissionChecker.check_super_admin_permission_sync(current_user):
        raise PermissionError("需要超级管理员权限")
    return current_user


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    创建新用户
    需要管理员权限
    """
    # 检查用户名是否已存在
    existing_user = user_service.get_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    existing_email = user_service.get_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    # 只有超级管理员可以创建管理员和超级管理员
    if user_data.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if not PermissionChecker.check_super_admin_permission_sync(current_user):
            raise PermissionError("只有超级管理员可以创建管理员用户")
    
    # 创建用户
    user_dict = user_data.dict(exclude={"password"})
    user_dict["hashed_password"] = get_password_hash(user_data.password)
    user_dict["is_active"] = user_data.is_active
    user_dict["login_count"] = 0
    
    new_user = user_service.create(db, obj_in=user_dict, user_id=str(current_user.id))
    
    return UserResponse.from_orm(new_user)


@router.get("/users", response_model=UserListResponse)
async def list_users(
    search_params: UserSearchRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    获取用户列表
    支持分页、搜索和筛选
    需要管理员权限
    """
    # 构建查询
    query = select(User)
    count_query = select(func.count(User.id))
    
    # 添加搜索条件
    conditions = []
    
    if search_params.search:
        search_term = f"%{search_params.search}%"
        conditions.append(
            or_(
                User.username.ilike(search_term),
                User.email.ilike(search_term),
                User.full_name.ilike(search_term)
            )
        )
    
    if search_params.role:
        conditions.append(User.role == search_params.role)
    
    if search_params.department:
        conditions.append(User.department.ilike(f"%{search_params.department}%"))
    
    if search_params.is_active is not None:
        conditions.append(User.is_active == search_params.is_active)
    
    # 应用条件
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # 获取总数
    total_result = db.execute(count_query)
    total = total_result.scalar()
    
    # 应用分页
    offset = (search_params.page - 1) * search_params.size
    query = query.offset(offset).limit(search_params.size)
    
    # 执行查询
    result = db.execute(query)
    users = result.scalars().all()
    
    # 计算总页数
    pages = math.ceil(total / search_params.size) if total > 0 else 1
    
    return UserListResponse(
        users=[UserResponse.from_orm(user) for user in users],
        total=total,
        page=search_params.page,
        size=search_params.size,
        pages=pages
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    获取用户详情
    需要管理员权限
    """
    user = user_service.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserResponse.from_orm(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    更新用户信息
    需要管理员权限
    """
    # 获取要更新的用户
    user = user_service.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查邮箱是否已被其他用户使用
    if user_data.email and user_data.email != user.email:
        existing_email = user_service.get_by_email(db, user_data.email)
        if existing_email and existing_email.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被其他用户使用"
            )
    
    # 只有超级管理员可以修改用户角色为管理员或超级管理员
    if user_data.role and user_data.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if not PermissionChecker.check_super_admin_permission_sync(current_user):
            raise PermissionError("只有超级管理员可以设置管理员角色")
    
    # 不能修改自己的激活状态
    if user_id == str(current_user.id) and user_data.is_active is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的激活状态"
        )
    
    # 更新用户
    update_data = user_data.dict(exclude_unset=True)
    updated_user = user_service.update(
        db, db_obj=user, obj_in=update_data, user_id=str(current_user.id)
    )
    
    return UserResponse.from_orm(updated_user)


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin_user)
):
    """
    删除用户
    需要超级管理员权限
    """
    # 不能删除自己
    if user_id == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    # 获取要删除的用户
    user = user_service.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 删除用户
    user_service.delete(db, id=user_id, user_id=str(current_user.id))
    
    return MessageResponse(message="用户删除成功")


@router.get("/users/stats", response_model=UserStatsResponse)
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    获取用户统计信息
    需要管理员权限
    """
    # 总用户数
    total_users_result = db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar()
    
    # 活跃用户数
    active_users_result = db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_users_result.scalar()
    
    # 非活跃用户数
    inactive_users = total_users - active_users
    
    # 按角色统计
    role_stats_result = db.execute(
        select(User.role, func.count(User.id)).group_by(User.role)
    )
    users_by_role = {role.value: count for role, count in role_stats_result.all()}
    
    # 按部门统计
    dept_stats_result = db.execute(
        select(User.department, func.count(User.id))
        .where(User.department.isnot(None))
        .group_by(User.department)
    )
    users_by_department = {dept: count for dept, count in dept_stats_result.all()}
    
    # 最近7天登录用户数（这里简化处理，实际需要根据last_login字段计算）
    recent_logins = active_users  # 简化实现
    
    return UserStatsResponse(
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
        users_by_role=users_by_role,
        users_by_department=users_by_department,
        recent_logins=recent_logins
    )


@router.post("/users/{user_id}/reset-password", response_model=MessageResponse)
async def reset_user_password(
    user_id: str,
    password_data: PasswordResetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin_user)
):
    """
    重置用户密码
    需要超级管理员权限
    """
    # 验证用户ID匹配
    if password_data.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户ID不匹配"
        )
    
    # 获取要重置密码的用户
    user = user_service.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 重置密码
    hashed_password = get_password_hash(password_data.new_password)
    user_service.update(
        db, 
        db_obj=user, 
        obj_in={"hashed_password": hashed_password},
        user_id=str(current_user.id)
    )
    
    return MessageResponse(message="密码重置成功")

# ==================== 权限管理API端点 ====================

@router.post("/permissions/grant", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def grant_project_permission(
    permission_data: PermissionGrantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    授予用户项目权限
    需要管理员权限
    """
    # 验证用户存在
    user = user_service.get(db, permission_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 验证项目存在
    project_query = select(Project).where(Project.id == permission_data.project_id)
    project_result = db.execute(project_query)
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查是否已存在权限记录
    existing_permission_query = select(UserProjectPermission).where(
        and_(
            UserProjectPermission.user_id == permission_data.user_id,
            UserProjectPermission.project_id == permission_data.project_id
        )
    )
    existing_permission_result = db.execute(existing_permission_query)
    existing_permission = existing_permission_result.scalar_one_or_none()
    
    # 转换权限枚举为字符串列表
    permission_strings = [p.value for p in permission_data.permissions]
    
    if existing_permission:
        # 更新现有权限
        # 合并权限，去重
        current_permissions = set(existing_permission.permissions)
        new_permissions = set(permission_strings)
        merged_permissions = list(current_permissions.union(new_permissions))
        
        existing_permission.permissions = merged_permissions
        existing_permission.granted_by = str(current_user.id)
        existing_permission.granted_at = func.now()
        
        db.add(existing_permission)
        db.commit()
        db.refresh(existing_permission)
        
        permission_record = existing_permission
    else:
        # 创建新权限记录
        permission_record = UserProjectPermission(
            user_id=permission_data.user_id,
            project_id=permission_data.project_id,
            permissions=permission_strings,
            granted_by=str(current_user.id)
        )
        
        db.add(permission_record)
        db.commit()
        db.refresh(permission_record)
    
    # 构建响应
    response = PermissionResponse(
        id=str(permission_record.id),
        created_at=permission_record.created_at,
        updated_at=permission_record.updated_at,
        user_id=permission_record.user_id,
        project_id=permission_record.project_id,
        permissions=permission_record.permissions,
        granted_by=permission_record.granted_by,
        granted_at=permission_record.granted_at,
        user_username=user.username,
        project_name=project.name,
        granter_username=current_user.username
    )
    
    return response


@router.delete("/permissions/revoke", response_model=MessageResponse)
async def revoke_project_permission(
    permission_data: PermissionRevokeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    撤销用户项目权限
    需要管理员权限
    """
    # 查找权限记录
    permission_query = select(UserProjectPermission).where(
        and_(
            UserProjectPermission.user_id == permission_data.user_id,
            UserProjectPermission.project_id == permission_data.project_id
        )
    )
    permission_result = db.execute(permission_query)
    permission_record = permission_result.scalar_one_or_none()
    
    if not permission_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限记录不存在"
        )
    
    if permission_data.permissions:
        # 撤销指定权限
        permission_strings = [p.value for p in permission_data.permissions]
        current_permissions = set(permission_record.permissions)
        remaining_permissions = list(current_permissions - set(permission_strings))
        
        if remaining_permissions:
            # 更新权限列表
            permission_record.permissions = remaining_permissions
            permission_record.granted_by = str(current_user.id)
            permission_record.granted_at = func.now()
            
            db.add(permission_record)
            db.commit()
            
            return MessageResponse(message="指定权限撤销成功")
        else:
            # 如果没有剩余权限，删除整个记录
            db.delete(permission_record)
            db.commit()
            
            return MessageResponse(message="所有权限撤销成功，权限记录已删除")
    else:
        # 撤销所有权限，删除记录
        db.delete(permission_record)
        db.commit()
        
        return MessageResponse(message="所有权限撤销成功")


@router.get("/permissions/users/{user_id}", response_model=UserPermissionResponse)
async def get_user_permissions(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    获取用户的所有项目权限
    需要管理员权限
    """
    # 验证用户存在
    user = user_service.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 查询用户的所有项目权限
    permissions_query = select(UserProjectPermission, Project, User).join(
        Project, UserProjectPermission.project_id == Project.id
    ).join(
        User, UserProjectPermission.granted_by == User.id, isouter=True
    ).where(UserProjectPermission.user_id == user_id)
    
    permissions_result = db.execute(permissions_query)
    permissions_data = permissions_result.all()
    
    # 构建权限响应列表
    project_permissions = []
    for permission_record, project, granter in permissions_data:
        permission_response = PermissionResponse(
            id=str(permission_record.id),
            created_at=permission_record.created_at,
            updated_at=permission_record.updated_at,
            user_id=permission_record.user_id,
            project_id=permission_record.project_id,
            permissions=permission_record.permissions,
            granted_by=permission_record.granted_by,
            granted_at=permission_record.granted_at,
            user_username=user.username,
            project_name=project.name,
            granter_username=granter.username if granter else None
        )
        project_permissions.append(permission_response)
    
    return UserPermissionResponse(
        user=UserResponse.from_orm(user),
        project_permissions=project_permissions
    )


@router.get("/permissions/projects/{project_id}", response_model=ProjectPermissionResponse)
async def get_project_permissions(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    获取项目的所有用户权限
    需要管理员权限
    """
    # 验证项目存在
    project_query = select(Project).where(Project.id == project_id)
    project_result = db.execute(project_query)
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 查询项目的所有用户权限
    permissions_query = select(UserProjectPermission, User).join(
        User, UserProjectPermission.user_id == User.id
    ).where(UserProjectPermission.project_id == project_id)
    
    permissions_result = db.execute(permissions_query)
    permissions_data = permissions_result.all()
    
    # 构建权限响应列表
    permissions = []
    for permission_record, user in permissions_data:
        # 获取授权人信息
        granter = None
        if permission_record.granted_by:
            granter = user_service.get(db, permission_record.granted_by)
        
        permission_response = PermissionResponse(
            id=str(permission_record.id),
            created_at=permission_record.created_at,
            updated_at=permission_record.updated_at,
            user_id=permission_record.user_id,
            project_id=permission_record.project_id,
            permissions=permission_record.permissions,
            granted_by=permission_record.granted_by,
            granted_at=permission_record.granted_at,
            user_username=user.username,
            project_name=project.name,
            granter_username=granter.username if granter else None
        )
        permissions.append(permission_response)
    
    return ProjectPermissionResponse(
        project_id=project_id,
        project_name=project.name,
        permissions=permissions
    )


@router.get("/permissions", response_model=PermissionListResponse)
async def list_permissions(
    search_params: PermissionSearchRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    获取权限列表
    支持分页和筛选
    需要管理员权限
    """
    # 构建查询
    query = select(UserProjectPermission, User, Project).join(
        User, UserProjectPermission.user_id == User.id
    ).join(
        Project, UserProjectPermission.project_id == Project.id
    )
    
    count_query = select(func.count(UserProjectPermission.id)).join(
        User, UserProjectPermission.user_id == User.id
    ).join(
        Project, UserProjectPermission.project_id == Project.id
    )
    
    # 添加筛选条件
    conditions = []
    
    if search_params.user_id:
        conditions.append(UserProjectPermission.user_id == search_params.user_id)
    
    if search_params.project_id:
        conditions.append(UserProjectPermission.project_id == search_params.project_id)
    
    if search_params.permission:
        # 检查权限列表中是否包含指定权限
        conditions.append(
            UserProjectPermission.permissions.contains([search_params.permission.value])
        )
    
    # 应用条件
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # 获取总数
    total_result = db.execute(count_query)
    total = total_result.scalar()
    
    # 应用分页
    offset = (search_params.page - 1) * search_params.size
    query = query.offset(offset).limit(search_params.size)
    
    # 执行查询
    result = db.execute(query)
    permissions_data = result.all()
    
    # 构建响应
    permissions = []
    for permission_record, user, project in permissions_data:
        # 获取授权人信息
        granter = None
        if permission_record.granted_by:
            granter = user_service.get(db, permission_record.granted_by)
        
        permission_response = PermissionResponse(
            id=str(permission_record.id),
            created_at=permission_record.created_at,
            updated_at=permission_record.updated_at,
            user_id=permission_record.user_id,
            project_id=permission_record.project_id,
            permissions=permission_record.permissions,
            granted_by=permission_record.granted_by,
            granted_at=permission_record.granted_at,
            user_username=user.username,
            project_name=project.name,
            granter_username=granter.username if granter else None
        )
        permissions.append(permission_response)
    
    # 计算总页数
    pages = math.ceil(total / search_params.size) if total > 0 else 1
    
    return PermissionListResponse(
        permissions=permissions,
        total=total,
        page=search_params.page,
        size=search_params.size,
        pages=pages
    )