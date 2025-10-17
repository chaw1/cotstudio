"""
用户服务
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.services.base_service import BaseService


class UserService(BaseService[User]):
    """
    用户服务类
    """
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        """
        return db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        根据邮箱获取用户
        """
        return db.query(User).filter(User.email == email).first()
    
    def authenticate(self, db: Session, username: str, password: str) -> Optional[User]:
        """
        用户认证
        """
        user = self.get_by_username(db, username)
        if not user:
            return None
        try:
            if not verify_password(password, user.hashed_password):
                return None
        except Exception as e:
            # 记录错误但不抛出异常
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Password verification error: {e}")
            return None
        return user
    
    def create_user(
        self,
        db: Session,
        *,
        username: str,
        email: str,
        password: str,
        full_name: str = None,
        roles: list = None,
        is_superuser: bool = False
    ) -> User:
        """
        创建用户
        """
        hashed_password = get_password_hash(password)
        user_data = {
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "full_name": full_name,
            "roles": roles or [],
            "is_superuser": is_superuser,
            "is_active": True
        }
        return self.create(db, obj_in=user_data)
    
    def is_active(self, user: User) -> bool:
        """
        检查用户是否活跃
        """
        return user.is_active
    
    def is_superuser(self, user: User) -> bool:
        """
        检查用户是否为超级用户
        """
        return user.is_superuser
    
    def create(self, db: Session, obj_in: dict, user_id: str = None) -> User:
        """
        创建用户的便捷方法
        """
        return super().create(db, obj_in=obj_in, user_id=user_id)


# 创建全局用户服务实例
user_service = UserService()