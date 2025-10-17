"""
初始化审计系统和权限系统
"""
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.audit import (
    Role, Permission, RoleType, ResourceType,
    AuditEventType, AuditSeverity
)
from app.core.app_logging import logger


def init_system_permissions(db: Session):
    """初始化系统权限"""
    
    # 定义系统权限
    system_permissions = [
        # 项目权限
        {"name": "project:create", "display_name": "创建项目", "resource_type": ResourceType.PROJECT, "action": "create"},
        {"name": "project:read", "display_name": "查看项目", "resource_type": ResourceType.PROJECT, "action": "read"},
        {"name": "project:update", "display_name": "更新项目", "resource_type": ResourceType.PROJECT, "action": "update"},
        {"name": "project:delete", "display_name": "删除项目", "resource_type": ResourceType.PROJECT, "action": "delete"},
        {"name": "project:manage_permissions", "display_name": "管理项目权限", "resource_type": ResourceType.PROJECT, "action": "manage_permissions"},
        {"name": "project:read_permissions", "display_name": "查看项目权限", "resource_type": ResourceType.PROJECT, "action": "read_permissions"},
        
        # 文件权限
        {"name": "file:create", "display_name": "上传文件", "resource_type": ResourceType.FILE, "action": "create"},
        {"name": "file:read", "display_name": "查看文件", "resource_type": ResourceType.FILE, "action": "read"},
        {"name": "file:update", "display_name": "更新文件", "resource_type": ResourceType.FILE, "action": "update"},
        {"name": "file:delete", "display_name": "删除文件", "resource_type": ResourceType.FILE, "action": "delete"},
        
        # CoT数据权限
        {"name": "cot:create", "display_name": "创建CoT数据", "resource_type": ResourceType.COT_ITEM, "action": "create"},
        {"name": "cot:read", "display_name": "查看CoT数据", "resource_type": ResourceType.COT_ITEM, "action": "read"},
        {"name": "cot:update", "display_name": "更新CoT数据", "resource_type": ResourceType.COT_ITEM, "action": "update"},
        {"name": "cot:delete", "display_name": "删除CoT数据", "resource_type": ResourceType.COT_ITEM, "action": "delete"},
        {"name": "cot:review", "display_name": "审核CoT数据", "resource_type": ResourceType.COT_ITEM, "action": "review"},
        
        # 知识图谱权限
        {"name": "kg:read", "display_name": "查看知识图谱", "resource_type": ResourceType.KNOWLEDGE_GRAPH, "action": "read"},
        {"name": "kg:update", "display_name": "更新知识图谱", "resource_type": ResourceType.KNOWLEDGE_GRAPH, "action": "update"},
        
        # 用户管理权限
        {"name": "user:read", "display_name": "查看用户", "resource_type": ResourceType.USER, "action": "read"},
        {"name": "user:update", "display_name": "更新用户", "resource_type": ResourceType.USER, "action": "update"},
        {"name": "user:delete", "display_name": "删除用户", "resource_type": ResourceType.USER, "action": "delete"},
        {"name": "user:manage_roles", "display_name": "管理用户角色", "resource_type": ResourceType.USER, "action": "manage_roles"},
        {"name": "user:read_permissions", "display_name": "查看用户权限", "resource_type": ResourceType.USER, "action": "read_permissions"},
        
        # 角色管理权限
        {"name": "role:create", "display_name": "创建角色", "resource_type": ResourceType.ROLE, "action": "create"},
        {"name": "role:read", "display_name": "查看角色", "resource_type": ResourceType.ROLE, "action": "read"},
        {"name": "role:update", "display_name": "更新角色", "resource_type": ResourceType.ROLE, "action": "update"},
        {"name": "role:delete", "display_name": "删除角色", "resource_type": ResourceType.ROLE, "action": "delete"},
        
        # 权限管理权限
        {"name": "permission:read", "display_name": "查看权限", "resource_type": ResourceType.PERMISSION, "action": "read"},
        {"name": "permission:check", "display_name": "检查权限", "resource_type": ResourceType.PERMISSION, "action": "check"},
        
        # 审计日志权限
        {"name": "audit:read", "display_name": "查看审计日志", "resource_type": ResourceType.SYSTEM_SETTING, "action": "read"},
        
        # 系统设置权限
        {"name": "system:config", "display_name": "系统配置", "resource_type": ResourceType.SYSTEM_SETTING, "action": "config"},
        {"name": "system:admin", "display_name": "系统管理", "resource_type": ResourceType.SYSTEM_SETTING, "action": "admin"},
    ]
    
    # 创建权限
    for perm_data in system_permissions:
        existing_perm = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
        if not existing_perm:
            permission = Permission(
                name=perm_data["name"],
                display_name=perm_data["display_name"],
                resource_type=perm_data["resource_type"],
                action=perm_data["action"],
                is_system_permission=True
            )
            db.add(permission)
            logger.info(f"Created system permission: {perm_data['name']}")
    
    db.commit()


def init_system_roles(db: Session):
    """初始化系统角色"""
    
    # 定义系统角色及其权限
    system_roles = [
        {
            "name": "admin",
            "display_name": "系统管理员",
            "description": "拥有所有系统权限的管理员角色",
            "role_type": RoleType.ADMIN,
            "permissions": ["*"]  # 通配符表示所有权限
        },
        {
            "name": "editor",
            "display_name": "编辑者",
            "description": "可以创建、编辑项目和CoT数据的角色",
            "role_type": RoleType.EDITOR,
            "permissions": [
                "project:create", "project:read", "project:update", "project:delete",
                "file:create", "file:read", "file:update", "file:delete",
                "cot:create", "cot:read", "cot:update", "cot:delete",
                "kg:read", "kg:update"
            ]
        },
        {
            "name": "reviewer",
            "display_name": "审核者",
            "description": "可以查看和审核CoT数据的角色",
            "role_type": RoleType.REVIEWER,
            "permissions": [
                "project:read",
                "file:read",
                "cot:read", "cot:review",
                "kg:read"
            ]
        },
        {
            "name": "viewer",
            "display_name": "查看者",
            "description": "只能查看数据的只读角色",
            "role_type": RoleType.VIEWER,
            "permissions": [
                "project:read",
                "file:read",
                "cot:read",
                "kg:read"
            ]
        }
    ]
    
    # 创建角色
    for role_data in system_roles:
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing_role:
            role = Role(
                name=role_data["name"],
                display_name=role_data["display_name"],
                description=role_data["description"],
                role_type=role_data["role_type"],
                permissions=role_data["permissions"],
                is_system_role=True
            )
            db.add(role)
            logger.info(f"Created system role: {role_data['name']}")
    
    db.commit()


def init_audit_system():
    """初始化审计系统"""
    
    logger.info("Initializing audit system...")
    
    db = SessionLocal()
    try:
        # 初始化权限
        init_system_permissions(db)
        
        # 初始化角色
        init_system_roles(db)
        
        logger.info("Audit system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize audit system: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_audit_system()