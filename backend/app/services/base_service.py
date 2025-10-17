"""
基础服务类
"""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import DatabaseError, ValidationError
from app.core.app_logging import AuditLogger
from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseService(Generic[ModelType]):
    """
    基础服务类，提供通用的CRUD操作
    """
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def create(
        self,
        db: Session,
        *,
        obj_in: Dict[str, Any],
        user_id: str = None
    ) -> ModelType:
        """
        创建对象
        """
        try:
            db_obj = self.model(**obj_in)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            
            # 记录审计日志
            if user_id:
                AuditLogger.log_operation(
                    user_id=user_id,
                    operation="create",
                    resource_type=self.model.__tablename__,
                    resource_id=str(db_obj.id),
                    details={"created_fields": list(obj_in.keys())}
                )
            
            return db_obj
            
        except IntegrityError as e:
            db.rollback()
            raise DatabaseError(f"Failed to create {self.model.__name__}: {str(e)}")
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"Unexpected error creating {self.model.__name__}: {str(e)}")
    
    def get(self, db: Session, id) -> Optional[ModelType]:
        """
        根据ID获取对象
        """
        # ID is stored as string in our models
        if not isinstance(id, str):
            id = str(id)
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Dict[str, Any] = None
    ) -> List[ModelType]:
        """
        获取多个对象
        """
        query = db.query(self.model)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        return query.offset(skip).limit(limit).all()
    
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Dict[str, Any],
        user_id: str = None
    ) -> ModelType:
        """
        更新对象
        """
        try:
            # 记录更新前的值
            old_values = {}
            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    old_values[field] = getattr(db_obj, field)
                    setattr(db_obj, field, value)
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            
            # 记录审计日志
            if user_id:
                AuditLogger.log_operation(
                    user_id=user_id,
                    operation="update",
                    resource_type=self.model.__tablename__,
                    resource_id=str(db_obj.id),
                    details={
                        "updated_fields": list(obj_in.keys()),
                        "old_values": old_values,
                        "new_values": obj_in
                    }
                )
            
            return db_obj
            
        except IntegrityError as e:
            db.rollback()
            raise DatabaseError(f"Failed to update {self.model.__name__}: {str(e)}")
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"Unexpected error updating {self.model.__name__}: {str(e)}")
    
    def delete(
        self,
        db: Session,
        *,
        id: str,
        user_id: str = None
    ) -> ModelType:
        """
        删除对象
        """
        try:
            obj = db.query(self.model).filter(self.model.id == id).first()
            if not obj:
                raise ValidationError(f"{self.model.__name__} not found")
            
            db.delete(obj)
            db.commit()
            
            # 记录审计日志
            if user_id:
                AuditLogger.log_operation(
                    user_id=user_id,
                    operation="delete",
                    resource_type=self.model.__tablename__,
                    resource_id=str(id)
                )
            
            return obj
            
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"Failed to delete {self.model.__name__}: {str(e)}")
    
    def remove(self, db: Session, *, id: str) -> Optional[ModelType]:
        """
        删除对象（简化版本，不记录审计日志）
        """
        try:
            obj = self.get(db, id=id)
            if obj:
                db.delete(obj)
                db.commit()
                return obj
            return None
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"Failed to remove {self.model.__name__}: {str(e)}")
    
    def count(self, db: Session, filters: Dict[str, Any] = None) -> int:
        """
        计算对象数量
        """
        query = db.query(self.model)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        return query.count()