"""
项目服务
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.project import Project, ProjectStatus
from app.services.base_service import BaseService


class ProjectService(BaseService[Project]):
    """
    项目服务类
    """
    
    def __init__(self):
        super().__init__(Project)
    
    def create(self, db: Session, obj_in: Dict[str, Any], user_id: str = None) -> Project:
        """
        创建项目的便捷方法
        """
        return super().create(db, obj_in=obj_in, user_id=user_id)
    
    def update(self, db: Session, id: str, obj_in: Dict[str, Any], user_id: str = None) -> Project:
        """
        更新项目的便捷方法
        """
        from uuid import UUID
        # Convert string to UUID if needed
        if isinstance(id, str):
            id = UUID(id)
        db_obj = self.get(db, id)
        if not db_obj:
            return None
        return super().update(db, db_obj=db_obj, obj_in=obj_in, user_id=user_id)
    
    def get_all(self, db: Session, include_deleted: bool = False) -> List[Project]:
        """
        获取所有项目列表（管理员用）
        
        Args:
            db: 数据库会话
            include_deleted: 是否包含已删除的项目
        """
        query = db.query(Project)
        
        if not include_deleted:
            query = query.filter(Project.status != ProjectStatus.DELETED)
        
        return query.order_by(Project.updated_at.desc()).all()
    
    def get_by_owner(self, db: Session, owner_id: str, include_deleted: bool = False) -> List[Project]:
        """
        根据所有者ID获取项目列表
        
        Args:
            db: 数据库会话
            owner_id: 所有者ID
            include_deleted: 是否包含已删除的项目
        """
        query = db.query(Project).filter(Project.owner_id == owner_id)
        
        if not include_deleted:
            query = query.filter(Project.status != ProjectStatus.DELETED)
        
        return query.order_by(Project.updated_at.desc()).all()
    
    def get_by_name(self, db: Session, name: str, owner_id: str) -> Optional[Project]:
        """
        根据项目名称和所有者获取项目
        """
        return db.query(Project).filter(
            and_(
                Project.name == name,
                Project.owner_id == owner_id,
                Project.status != ProjectStatus.DELETED
            )
        ).first()
    
    def search_projects(
        self, 
        db: Session, 
        owner_id: str, 
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        project_type: Optional[str] = None,
        status: Optional[ProjectStatus] = None
    ) -> List[Project]:
        """
        搜索项目
        
        Args:
            db: 数据库会话
            owner_id: 所有者ID
            query: 搜索关键词（在名称和描述中搜索）
            tags: 标签过滤
            project_type: 项目类型过滤
            status: 状态过滤
        """
        db_query = db.query(Project).filter(Project.owner_id == owner_id)
        
        # 排除已删除的项目
        db_query = db_query.filter(Project.status != ProjectStatus.DELETED)
        
        # 关键词搜索
        if query:
            search_filter = or_(
                Project.name.ilike(f"%{query}%"),
                Project.description.ilike(f"%{query}%")
            )
            db_query = db_query.filter(search_filter)
        
        # 标签过滤
        if tags:
            for tag in tags:
                db_query = db_query.filter(Project.tags.contains([tag]))
        
        # 项目类型过滤
        if project_type:
            db_query = db_query.filter(Project.project_type == project_type)
        
        # 状态过滤
        if status:
            db_query = db_query.filter(Project.status == status)
        
        return db_query.order_by(Project.updated_at.desc()).all()
    
    def get_project_statistics(self, db: Session, project_id: str) -> Dict[str, Any]:
        """
        获取项目统计信息
        
        Args:
            db: 数据库会话
            project_id: 项目ID
            
        Returns:
            包含统计信息的字典
        """
        project = self.get(db, project_id)
        if not project:
            return {}
        
        # 计算文件统计
        file_count = len(project.files) if project.files else 0
        
        # 计算CoT统计
        cot_count = len(project.cot_items) if project.cot_items else 0
        
        # 计算切片统计（通过文件关联）
        slice_count = 0
        if project.files:
            for file in project.files:
                slice_count += len(file.slices) if file.slices else 0
        
        return {
            "file_count": file_count,
            "cot_count": cot_count,
            "slice_count": slice_count,
            "total_size": sum(file.size or 0 for file in project.files) if project.files else 0
        }
    
    def check_user_permission(
        self, 
        db: Session, 
        project_id: str, 
        user_id: str, 
        user_roles: List[str],
        required_permission: str
    ) -> bool:
        """
        检查用户对项目的权限
        
        Args:
            db: 数据库会话
            project_id: 项目ID
            user_id: 用户ID
            user_roles: 用户角色列表
            required_permission: 所需权限
            
        Returns:
            是否有权限
        """
        project = self.get(db, project_id)
        if not project:
            return False
        
        # 管理员拥有所有权限
        if "admin" in user_roles:
            return True
        
        # 项目所有者拥有所有权限
        if project.owner_id == user_id:
            return True
        
        # 这里可以扩展更复杂的权限逻辑
        # 例如项目成员、协作者等
        
        return False
    
    def add_tags(self, db: Session, project_id: str, tags: List[str]) -> Optional[Project]:
        """
        为项目添加标签
        """
        project = self.get(db, project_id)
        if not project:
            return None
        
        current_tags = project.tags or []
        new_tags = list(set(current_tags + tags))  # 去重
        
        return self.update(db, project_id, {"tags": new_tags})
    
    def remove_tags(self, db: Session, project_id: str, tags: List[str]) -> Optional[Project]:
        """
        从项目中移除标签
        """
        project = self.get(db, project_id)
        if not project:
            return None
        
        current_tags = project.tags or []
        new_tags = [tag for tag in current_tags if tag not in tags]
        
        return self.update(db, project_id, {"tags": new_tags})
    
    async def get_user_accessible_projects(self, user_id: str) -> List[Project]:
        """
        获取用户可访问的项目列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户可访问的项目列表
        """
        # For now, return all projects owned by the user
        # This can be extended to include shared projects based on permissions
        from app.core.database import get_db
        
        db = next(get_db())
        try:
            return self.get_by_owner(db, user_id)
        finally:
            db.close()
    
    async def check_user_project_access(self, user_id: str, project_id: str) -> bool:
        """
        检查用户是否可以访问指定项目
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            
        Returns:
            是否有访问权限
        """
        from app.core.database import get_db
        
        db = next(get_db())
        try:
            project = self.get(db, project_id)
            if not project:
                return False
            
            # For now, only project owner has access
            # This can be extended to include permission-based access
            return project.owner_id == user_id
        finally:
            db.close()
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """
        获取项目信息
        
        Args:
            project_id: 项目ID
            
        Returns:
            项目对象或None
        """
        from app.core.database import get_db
        
        db = next(get_db())
        try:
            return self.get(db, project_id)
        finally:
            db.close()


# 创建全局项目服务实例
project_service = ProjectService()