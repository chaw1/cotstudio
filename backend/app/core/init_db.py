"""
数据库初始化脚本
"""
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.models.user import User
from app.core.security import get_password_hash
from app.core.app_logging import logger


def init_db() -> None:
    """
    初始化数据库
    """
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # 创建默认用户
    db = SessionLocal()
    try:
        # 检查是否已存在管理员用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            from app.models.user import UserRole
            admin_user = User(
                username="admin",
                email="admin@cotstudio.com",
                hashed_password=get_password_hash("971028"),
                full_name="System Administrator",
                is_active=True,
                is_superuser=True,
                role=UserRole.SUPER_ADMIN,
                roles=["admin"],
                login_count=0
            )
            db.add(admin_user)
            logger.info("Created admin user")
        
        # 创建编辑用户
        editor_user = db.query(User).filter(User.username == "editor").first()
        if not editor_user:
            from app.models.user import UserRole
            editor_user = User(
                username="editor",
                email="editor@cotstudio.com", 
                hashed_password=get_password_hash("secret"),
                full_name="Editor User",
                is_active=True,
                is_superuser=False,
                role=UserRole.USER,
                roles=["editor"],
                login_count=0
            )
            db.add(editor_user)
            logger.info("Created editor user")
        
        db.commit()
        logger.info("Default users created successfully")
        
    except Exception as e:
        logger.error("Failed to create default users", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()