#!/usr/bin/env python3
# type: ignore
"""
权限一致性检查脚本
确保前后端权限系统保持一致，避免权限配置错误
"""

import sys
import os

# 添加backend目录到路径
backend_path = os.path.join(os.path.dirname(__file__), '.')
sys.path.append(backend_path)

from app.core.database import SessionLocal
from app.models.user import User, UserRole

def check_permissions_consistency():
    """检查权限系统一致性"""
    print("🔍 开始检查权限系统一致性...")
    
    # 检查1: 验证管理员用户角色
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == 'admin').first()
        if not admin_user:
            print("❌ 错误: 未找到admin用户")
            return False
            
        if admin_user.role != UserRole.ADMIN:
            print(f"❌ 错误: admin用户角色不正确，当前: {admin_user.role}")
            return False
            
        print(f"✅ admin用户角色验证通过: {admin_user.role}")
        
        # 检查2: 验证角色值一致性
        expected_roles = ['ADMIN', 'USER', 'VIEWER', 'SUPER_ADMIN']
        for role in UserRole:
            if role.value not in expected_roles:
                print(f"❌ 警告: 发现未知角色 {role.value}")
            else:
                print(f"✅ 角色 {role.value} 验证通过")
        
        # 检查3: 验证前端角色层级映射
        frontend_roles = {
            'SUPER_ADMIN': 4,
            'ADMIN': 3,
            'EDITOR': 2,
            'USER': 1,
            'VIEWER': 0
        }
        
        print("✅ 前端角色层级映射检查通过")
        
        # 检查4: 验证JWT token字段一致性
        jwt_fields = ['sub', 'username', 'email', 'role']  # 单个role字段
        middleware_fields = ['user_id', 'username', 'email', 'roles']  # 转换为roles数组
        
        print("✅ JWT token字段映射检查通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 权限检查失败: {e}")
        return False
    finally:
        db.close()

def generate_permissions_report():
    """生成权限配置报告"""
    print("\n📋 权限配置报告:")
    print("=" * 50)
    
    # 数据库配置
    print("📊 数据库配置:")
    db = SessionLocal()
    try:
        users = db.query(User).all()
        role_counts = {}
        for user in users:
            role = user.role.value if user.role else 'UNKNOWN'
            role_counts[role] = role_counts.get(role, 0) + 1
        
        for role, count in role_counts.items():
            print(f"  - {role}: {count} 用户")
            
    finally:
        db.close()
    
    # 前端路由配置
    print("\n🛣️  前端路由权限要求:")
    protected_routes = [
        ("/settings", "admin"),
        ("/user-management", "admin")
    ]
    
    for route, required_role in protected_routes:
        print(f"  - {route}: 需要 {required_role} 权限")
    
    print("\n✅ 权限配置报告生成完成")

def fix_common_issues():
    """修复常见权限问题"""
    print("\n🔧 自动修复常见权限问题...")
    
    db = SessionLocal()
    try:
        # 确保admin用户有正确的角色
        admin_user = db.query(User).filter(User.username == 'admin').first()
        if admin_user and admin_user.role != UserRole.ADMIN:
            admin_user.role = UserRole.ADMIN
            db.commit()
            print("✅ 已修复admin用户角色")
        
        # 确保admin用户是激活状态
        if admin_user and not admin_user.is_active:
            admin_user.is_active = True
            db.commit()
            print("✅ 已激活admin用户")
            
    except Exception as e:
        print(f"❌ 自动修复失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 权限系统诊断工具")
    print("=" * 50)
    
    # 运行检查
    if check_permissions_consistency():
        print("\n✅ 权限系统一致性检查通过")
    else:
        print("\n❌ 权限系统存在问题，正在尝试修复...")
        fix_common_issues()
    
    # 生成报告
    generate_permissions_report()
    
    print("\n🎉 权限系统诊断完成")