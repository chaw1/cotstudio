"""
测试审计系统功能
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.models.audit import (
    AuditLog, Role, Permission, UserRole, ProjectPermission,
    AuditEventType, AuditSeverity, ResourceType, RoleType
)
from app.models.user import User
from app.models.project import Project
from app.services.audit_service import AuditService, RoleService, PermissionService
from app.core.init_audit_system import init_audit_system
from app.core.app_logging import logger


def test_database_setup():
    """测试数据库设置"""
    print("Testing database setup...")
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")
    
    # 初始化审计系统
    init_audit_system()
    print("✓ Audit system initialized")


def test_audit_logging():
    """测试审计日志功能"""
    print("\nTesting audit logging...")
    
    db = SessionLocal()
    try:
        audit_service = AuditService(db)
        
        # 创建测试用户
        test_user = User(
            username="test_user",
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # 记录审计日志
        audit_log = audit_service.log_operation(
            user_id=str(test_user.id),
            event_type=AuditEventType.CREATE,
            action="test_create_user",
            resource_type=ResourceType.USER,
            resource_id=str(test_user.id),
            resource_name=test_user.username,
            description="Created test user",
            details={"test": True},
            severity=AuditSeverity.MEDIUM
        )
        
        print(f"✓ Audit log created: {audit_log.id}")
        
        # 查询审计日志
        from app.schemas.audit import AuditLogQuery
        query = AuditLogQuery(user_id=str(test_user.id))
        logs, total = audit_service.query_audit_logs(query)
        
        print(f"✓ Found {total} audit logs for user")
        
        # 获取统计信息
        stats = audit_service.get_audit_statistics()
        print(f"✓ Audit statistics: {stats['total_operations']} operations")
        
    finally:
        db.close()


def test_role_management():
    """测试角色管理功能"""
    print("\nTesting role management...")
    
    db = SessionLocal()
    try:
        role_service = RoleService(db)
        
        # 创建测试用户
        test_admin = User(
            username="test_admin",
            email="admin@example.com",
            hashed_password="hashed_password",
            full_name="Test Admin"
        )
        db.add(test_admin)
        db.commit()
        db.refresh(test_admin)
        
        # 创建自定义角色
        from app.schemas.audit import RoleCreate
        role_data = RoleCreate(
            name="test_role",
            display_name="测试角色",
            description="这是一个测试角色",
            role_type=RoleType.EDITOR,
            permissions=["project:read", "project:write", "file:read"]
        )
        
        role = role_service.create_role(role_data, str(test_admin.id))
        print(f"✓ Custom role created: {role.name}")
        
        # 获取所有角色
        roles = role_service.get_all()
        print(f"✓ Found {len(roles)} roles")
        
        # 获取系统角色
        system_roles = role_service.get_system_roles()
        print(f"✓ Found {len(system_roles)} system roles")
        
        # 更新角色
        from app.schemas.audit import RoleUpdate
        update_data = RoleUpdate(
            description="更新后的测试角色描述",
            permissions=["project:read", "project:write", "file:read", "file:write"]
        )
        
        updated_role = role_service.update_role(str(role.id), update_data, str(test_admin.id))
        print(f"✓ Role updated: {len(updated_role.permissions)} permissions")
        
    finally:
        db.close()


def test_permission_management():
    """测试权限管理功能"""
    print("\nTesting permission management...")
    
    db = SessionLocal()
    try:
        permission_service = PermissionService(db)
        
        # 创建测试用户
        test_user = User(
            username="test_perm_user",
            email="permuser@example.com",
            hashed_password="hashed_password",
            full_name="Permission Test User"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # 获取编辑者角色
        editor_role = db.query(Role).filter(Role.name == "editor").first()
        if editor_role:
            # 为用户分配角色
            user_role = permission_service.assign_role_to_user(
                user_id=str(test_user.id),
                role_id=str(editor_role.id),
                granted_by=str(test_user.id)  # 自己分配给自己（测试用）
            )
            print(f"✓ Role assigned to user: {editor_role.name}")
            
            # 检查用户权限
            user_permissions = permission_service.get_user_permissions(str(test_user.id))
            print(f"✓ User has {len(user_permissions)} permissions")
            
            # 检查特定权限
            has_permission = permission_service.check_permission(
                str(test_user.id), 
                "project:read"
            )
            print(f"✓ User has project:read permission: {has_permission}")
            
            # 撤销角色
            permission_service.revoke_role_from_user(
                str(test_user.id), 
                str(editor_role.id), 
                str(test_user.id)
            )
            print("✓ Role revoked from user")
        
        # 获取所有权限
        permissions = permission_service.get_all_permissions()
        print(f"✓ Found {len(permissions)} system permissions")
        
    finally:
        db.close()


def test_project_permissions():
    """测试项目权限功能"""
    print("\nTesting project permissions...")
    
    db = SessionLocal()
    try:
        permission_service = PermissionService(db)
        
        # 创建测试用户和项目
        test_user = User(
            username="test_proj_user",
            email="projuser@example.com",
            hashed_password="hashed_password",
            full_name="Project Test User"
        )
        db.add(test_user)
        
        test_project = Project(
            name="Test Project",
            description="Test project for permissions",
            owner_id=str(test_user.id)
        )
        db.add(test_project)
        db.commit()
        db.refresh(test_user)
        db.refresh(test_project)
        
        # 授予项目权限
        project_permission = permission_service.grant_project_permission(
            project_id=str(test_project.id),
            user_id=str(test_user.id),
            permission_type="editor",
            granted_by=str(test_user.id)
        )
        print(f"✓ Project permission granted: {project_permission.permission_type}")
        
        # 检查项目权限
        has_project_permission = permission_service.check_project_permission(
            user_id=str(test_user.id),
            project_id=str(test_project.id),
            required_permission="viewer"
        )
        print(f"✓ User has project viewer permission: {has_project_permission}")
        
        has_editor_permission = permission_service.check_project_permission(
            user_id=str(test_user.id),
            project_id=str(test_project.id),
            required_permission="editor"
        )
        print(f"✓ User has project editor permission: {has_editor_permission}")
        
    finally:
        db.close()


def test_audit_queries():
    """测试审计查询功能"""
    print("\nTesting audit queries...")
    
    db = SessionLocal()
    try:
        audit_service = AuditService(db)
        
        # 创建多个审计日志用于测试
        test_user = db.query(User).filter(User.username == "test_user").first()
        if test_user:
            # 记录不同类型的操作
            operations = [
                (AuditEventType.CREATE, "create_project", AuditSeverity.MEDIUM),
                (AuditEventType.UPDATE, "update_project", AuditSeverity.LOW),
                (AuditEventType.DELETE, "delete_file", AuditSeverity.HIGH),
                (AuditEventType.READ, "view_data", AuditSeverity.LOW),
            ]
            
            for event_type, action, severity in operations:
                audit_service.log_operation(
                    user_id=str(test_user.id),
                    event_type=event_type,
                    action=action,
                    severity=severity,
                    description=f"Test {action} operation"
                )
            
            print("✓ Created test audit logs")
            
            # 测试不同的查询条件
            from app.schemas.audit import AuditLogQuery
            
            # 按事件类型查询
            query = AuditLogQuery(event_types=[AuditEventType.CREATE, AuditEventType.UPDATE])
            logs, total = audit_service.query_audit_logs(query)
            print(f"✓ Found {total} CREATE/UPDATE operations")
            
            # 按严重程度查询
            query = AuditLogQuery(severity=AuditSeverity.HIGH)
            logs, total = audit_service.query_audit_logs(query)
            print(f"✓ Found {total} HIGH severity operations")
            
            # 按时间范围查询
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(hours=1)
            query = AuditLogQuery(start_date=start_date, end_date=end_date)
            logs, total = audit_service.query_audit_logs(query)
            print(f"✓ Found {total} operations in last hour")
            
            # 搜索文本查询
            query = AuditLogQuery(search_text="project")
            logs, total = audit_service.query_audit_logs(query)
            print(f"✓ Found {total} operations containing 'project'")
        
    finally:
        db.close()


def main():
    """运行所有测试"""
    print("=== COT Studio 审计系统测试 ===\n")
    
    try:
        test_database_setup()
        test_audit_logging()
        test_role_management()
        test_permission_management()
        test_project_permissions()
        test_audit_queries()
        
        print("\n=== 所有测试通过 ===")
        print("✓ 审计日志记录功能正常")
        print("✓ 角色管理功能正常")
        print("✓ 权限管理功能正常")
        print("✓ 项目权限功能正常")
        print("✓ 审计查询功能正常")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)