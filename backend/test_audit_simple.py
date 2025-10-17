"""
简单的审计系统测试
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.models.audit import AuditLog, Role, Permission, AuditEventType, AuditSeverity, ResourceType, RoleType
from app.models.user import User
from app.services.audit_service import AuditService
from app.core.init_audit_system import init_audit_system


def test_basic_functionality():
    """测试基本功能"""
    print("Testing basic audit system functionality...")
    
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")
    
    # 初始化审计系统
    try:
        init_audit_system()
        print("✓ Audit system initialized")
    except Exception as e:
        print(f"⚠ Audit system initialization: {e}")
    
    db = SessionLocal()
    try:
        # 测试创建审计日志
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
        print("✓ Test user created")
        
        # 记录审计日志
        audit_log = audit_service.log_operation(
            user_id=str(test_user.id),
            event_type=AuditEventType.CREATE,
            action="test_operation",
            description="Test audit log creation",
            severity=AuditSeverity.LOW
        )
        print(f"✓ Audit log created: {audit_log.id}")
        
        # 查询审计日志
        logs = db.query(AuditLog).filter(AuditLog.user_id == str(test_user.id)).all()
        print(f"✓ Found {len(logs)} audit logs")
        
        # 检查角色
        roles = db.query(Role).all()
        print(f"✓ Found {len(roles)} roles")
        
        # 检查权限
        permissions = db.query(Permission).all()
        print(f"✓ Found {len(permissions)} permissions")
        
        # 获取统计信息
        stats = audit_service.get_audit_statistics()
        print(f"✓ Statistics: {stats['total_operations']} total operations")
        
        print("\n=== 基本功能测试通过 ===")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)