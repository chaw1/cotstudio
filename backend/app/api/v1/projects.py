"""
项目管理API端点
"""
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.app_logging import AuditLogger
from app.middleware.auth import get_current_active_user, require_permission
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_service import project_service
from app.models.project import ProjectStatus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: Request,
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("project:write"))
) -> ProjectResponse:
    """
    创建新项目
    
    需要权限: project:write
    """
    # 检查项目名称是否已存在（同一用户下）
    existing_project = project_service.get_by_name(
        db, project_data.name, current_user["user_id"]
    )
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project with name '{project_data.name}' already exists"
        )
    
    # 创建项目数据
    project_dict = project_data.model_dump()
    project_dict["owner_id"] = current_user["user_id"]
    
    # 创建项目
    project = project_service.create(db, project_dict)
    
    # 记录审计日志
    AuditLogger.log_operation(
        user_id=current_user["user_id"],
        operation="project_created",
        resource_type="project",
        resource_id=str(project.id),
        details={
            "project_name": project.name,
            "project_type": project.project_type.value
        },
        request=request
    )
    
    # 构建响应
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        tags=project.tags,
        project_type=project.project_type,
        owner_id=UUID(project.owner_id),
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        file_count=0,  # 新项目没有文件
        cot_count=0    # 新项目没有CoT数据
    )


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("project:read"))
) -> List[ProjectResponse]:
    """
    获取项目列表
    
    需要权限: project:read
    - 管理员可以看到所有项目
    - 普通用户只能看到自己创建的项目
    """
    # 检查用户角色
    from app.models.user import User, UserRole
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    
    if user and user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        # 管理员可以看到所有项目
        projects = project_service.get_all(db)
    else:
        # 普通用户只能看到自己的项目
        projects = project_service.get_by_owner(db, current_user["user_id"])
    
    # 构建响应列表
    project_responses = []
    for project in projects:
        # 计算文件和CoT数量
        file_count = len(project.files) if project.files else 0
        cot_count = len(project.cot_items) if project.cot_items else 0
        
        # 计算知识图谱实体数量
        kg_count = 0
        try:
            from app.models.knowledge_graph import KGEntity
            kg_count = db.query(KGEntity).filter(KGEntity.project_id == project.id).count()
        except Exception as e:
            logger.warning(f"Failed to count KG entities for project {project.id}: {e}")
        
        # 获取所有者用户名
        from app.models.user import User
        owner_user = db.query(User).filter(User.id == project.owner_id).first()
        owner_name = owner_user.username if owner_user else None
        
        project_responses.append(ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            tags=project.tags,
            project_type=project.project_type,
            owner_id=UUID(project.owner_id),
            owner_name=owner_name,
            status=project.status,
            created_at=project.created_at,
            updated_at=project.updated_at,
            file_count=file_count,
            cot_count=cot_count,
            kg_count=kg_count
        ))
    
    return project_responses


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("project:read"))
) -> ProjectResponse:
    """
    获取指定项目详情
    
    需要权限: project:read
    """
    project = project_service.get(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 检查用户权限（只能访问自己的项目，除非是管理员）
    if (project.owner_id != current_user["user_id"] and 
        "admin" not in current_user.get("roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    # 计算文件和CoT数量
    file_count = len(project.files) if project.files else 0
    cot_count = len(project.cot_items) if project.cot_items else 0
    
    # 获取所有者用户名
    from app.models.user import User
    owner_user = db.query(User).filter(User.id == project.owner_id).first()
    owner_name = owner_user.username if owner_user else None
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        tags=project.tags,
        project_type=project.project_type,
        owner_id=UUID(project.owner_id),
        owner_name=owner_name,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        file_count=file_count,
        cot_count=cot_count
    )


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    request: Request,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("project:write"))
) -> ProjectResponse:
    """
    更新项目信息
    
    需要权限: project:write
    """
    project = project_service.get(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 检查用户权限（只能修改自己的项目，除非是管理员）
    if (project.owner_id != current_user["user_id"] and 
        "admin" not in current_user.get("roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to modify this project"
        )
    
    # 如果更新名称，检查是否与其他项目冲突
    if project_data.name and project_data.name != project.name:
        existing_project = project_service.get_by_name(
            db, project_data.name, project.owner_id
        )
        if existing_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project with name '{project_data.name}' already exists"
            )
    
    # 准备更新数据（只更新提供的字段）
    update_data = {}
    for field, value in project_data.model_dump(exclude_unset=True).items():
        if value is not None:
            update_data[field] = value
    
    # 更新项目
    updated_project = project_service.update(db, project_id, update_data)
    
    # 记录审计日志
    AuditLogger.log_operation(
        user_id=current_user["user_id"],
        operation="project_updated",
        resource_type="project",
        resource_id=str(project_id),
        details={
            "updated_fields": list(update_data.keys()),
            "project_name": updated_project.name
        },
        request=request
    )
    
    # 计算文件和CoT数量
    file_count = len(updated_project.files) if updated_project.files else 0
    cot_count = len(updated_project.cot_items) if updated_project.cot_items else 0
    
    return ProjectResponse(
        id=updated_project.id,
        name=updated_project.name,
        description=updated_project.description,
        tags=updated_project.tags,
        project_type=updated_project.project_type,
        owner_id=UUID(updated_project.owner_id),
        status=updated_project.status,
        created_at=updated_project.created_at,
        updated_at=updated_project.updated_at,
        file_count=file_count,
        cot_count=cot_count
    )


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("project:delete"))
):
    """
    删除项目（软删除）
    
    需要权限: project:delete
    """
    project = project_service.get(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 检查用户权限（只能删除自己的项目，除非是管理员）
    if (project.owner_id != current_user["user_id"] and 
        "admin" not in current_user.get("roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to delete this project"
        )
    
    # 软删除项目（更新状态为DELETED）
    project_service.update(db, project_id, {"status": ProjectStatus.DELETED})
    
    # 记录审计日志
    AuditLogger.log_operation(
        user_id=current_user["user_id"],
        operation="project_deleted",
        resource_type="project",
        resource_id=str(project_id),
        details={
            "project_name": project.name,
            "deletion_type": "soft_delete"
        },
        request=request
    )


@router.post("/projects/{project_id}/archive", response_model=ProjectResponse)
async def archive_project(
    project_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("project:write"))
) -> ProjectResponse:
    """
    归档项目
    
    需要权限: project:write
    """
    project = project_service.get(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 检查用户权限
    if (project.owner_id != current_user["user_id"] and 
        "admin" not in current_user.get("roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to archive this project"
        )
    
    # 更新项目状态为归档
    updated_project = project_service.update(
        db, project_id, {"status": ProjectStatus.ARCHIVED}
    )
    
    # 记录审计日志
    AuditLogger.log_operation(
        user_id=current_user["user_id"],
        operation="project_archived",
        resource_type="project",
        resource_id=str(project_id),
        details={"project_name": project.name},
        request=request
    )
    
    # 计算文件和CoT数量
    file_count = len(updated_project.files) if updated_project.files else 0
    cot_count = len(updated_project.cot_items) if updated_project.cot_items else 0
    
    return ProjectResponse(
        id=updated_project.id,
        name=updated_project.name,
        description=updated_project.description,
        tags=updated_project.tags,
        project_type=updated_project.project_type,
        owner_id=UUID(updated_project.owner_id),
        status=updated_project.status,
        created_at=updated_project.created_at,
        updated_at=updated_project.updated_at,
        file_count=file_count,
        cot_count=cot_count
    )


@router.post("/projects/{project_id}/restore", response_model=ProjectResponse)
async def restore_project(
    project_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("project:write"))
) -> ProjectResponse:
    """
    恢复归档的项目
    
    需要权限: project:write
    """
    project = project_service.get(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 检查用户权限
    if (project.owner_id != current_user["user_id"] and 
        "admin" not in current_user.get("roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to restore this project"
        )
    
    # 只能恢复归档的项目
    if project.status != ProjectStatus.ARCHIVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only archived projects can be restored"
        )
    
    # 更新项目状态为活跃
    updated_project = project_service.update(
        db, project_id, {"status": ProjectStatus.ACTIVE}
    )
    
    # 记录审计日志
    AuditLogger.log_operation(
        user_id=current_user["user_id"],
        operation="project_restored",
        resource_type="project",
        resource_id=str(project_id),
        details={"project_name": project.name},
        request=request
    )
    
    # 计算文件和CoT数量
    file_count = len(updated_project.files) if updated_project.files else 0
    cot_count = len(updated_project.cot_items) if updated_project.cot_items else 0
    
    return ProjectResponse(
        id=updated_project.id,
        name=updated_project.name,
        description=updated_project.description,
        tags=updated_project.tags,
        project_type=updated_project.project_type,
        owner_id=UUID(updated_project.owner_id),
        status=updated_project.status,
        created_at=updated_project.created_at,
        updated_at=updated_project.updated_at,
        file_count=file_count,
        cot_count=cot_count
    )


@router.get("/projects/search", response_model=List[ProjectResponse])
async def search_projects(
    query: str = None,
    tags: List[str] = None,
    project_type: str = None,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("project:read"))
) -> List[ProjectResponse]:
    """
    搜索项目
    
    需要权限: project:read
    """
    from app.models.project import ProjectStatus, ProjectType
    
    # 转换状态和类型参数
    status_enum = None
    if status:
        try:
            status_enum = ProjectStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}"
            )
    
    # 搜索项目
    projects = project_service.search_projects(
        db=db,
        owner_id=current_user["user_id"],
        query=query,
        tags=tags,
        project_type=project_type,
        status=status_enum
    )
    
    # 构建响应列表
    project_responses = []
    for project in projects:
        stats = project_service.get_project_statistics(db, str(project.id))
        
        project_responses.append(ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            tags=project.tags,
            project_type=project.project_type,
            owner_id=UUID(project.owner_id),
            status=project.status,
            created_at=project.created_at,
            updated_at=project.updated_at,
            file_count=stats.get("file_count", 0),
            cot_count=stats.get("cot_count", 0)
        ))
    
    return project_responses


@router.post("/projects/{project_id}/tags", response_model=ProjectResponse)
async def add_project_tags(
    project_id: UUID,
    request: Request,
    tags: List[str],
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("project:write"))
) -> ProjectResponse:
    """
    为项目添加标签
    
    需要权限: project:write
    """
    # 检查项目是否存在和权限
    project = project_service.get(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if (project.owner_id != current_user["user_id"] and 
        "admin" not in current_user.get("roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to modify this project"
        )
    
    # 添加标签
    updated_project = project_service.add_tags(db, str(project_id), tags)
    
    # 记录审计日志
    AuditLogger.log_operation(
        user_id=current_user["user_id"],
        operation="project_tags_added",
        resource_type="project",
        resource_id=str(project_id),
        details={
            "project_name": project.name,
            "added_tags": tags
        },
        request=request
    )
    
    # 获取统计信息
    stats = project_service.get_project_statistics(db, str(project_id))
    
    return ProjectResponse(
        id=updated_project.id,
        name=updated_project.name,
        description=updated_project.description,
        tags=updated_project.tags,
        project_type=updated_project.project_type,
        owner_id=UUID(updated_project.owner_id),
        status=updated_project.status,
        created_at=updated_project.created_at,
        updated_at=updated_project.updated_at,
        file_count=stats.get("file_count", 0),
        cot_count=stats.get("cot_count", 0)
    )


@router.delete("/projects/{project_id}/tags")
async def remove_project_tags(
    project_id: UUID,
    request: Request,
    tags: List[str],
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("project:write"))
):
    """
    从项目中移除标签
    
    需要权限: project:write
    """
    # 检查项目是否存在和权限
    project = project_service.get(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if (project.owner_id != current_user["user_id"] and 
        "admin" not in current_user.get("roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to modify this project"
        )
    
    # 移除标签
    project_service.remove_tags(db, str(project_id), tags)
    
    # 记录审计日志
    AuditLogger.log_operation(
        user_id=current_user["user_id"],
        operation="project_tags_removed",
        resource_type="project",
        resource_id=str(project_id),
        details={
            "project_name": project.name,
            "removed_tags": tags
        },
        request=request
    )
    
    return {"message": "Tags removed successfully"}


@router.get("/projects/{project_id}/statistics")
async def get_project_statistics(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("project:read"))
):
    """
    获取项目统计信息
    
    需要权限: project:read
    """
    project = project_service.get(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 检查用户权限
    if (project.owner_id != current_user["user_id"] and 
        "admin" not in current_user.get("roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    # 获取详细统计信息
    stats = project_service.get_project_statistics(db, str(project_id))
    
    return {
        "project_id": str(project_id),
        "project_name": project.name,
        "statistics": stats,
        "last_updated": project.updated_at.isoformat()
    }