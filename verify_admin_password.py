#!/usr/bin/env python3
"""
验证admin用户密码脚本
"""
import sys
import os

# 添加backend目录到路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.append(backend_path)

from app.core.security import verify_password
from app.services.user_service import user_service
from app.core.database import get_db
from sqlalchemy.orm import Session

def main():
    # 获取数据库连接
    db_session = next(get_db())
    
    try:
        # 查找admin用户
        admin_user = user_service.get_by_username(db_session, "admin")
        
        if not admin_user:
            print("❌ Admin用户不存在")
            return
        
        print(f"✅ 找到admin用户:")
        print(f"   ID: {admin_user.id}")
        print(f"   用户名: {admin_user.username}")
        print(f"   邮箱: {admin_user.email}")
        print(f"   角色: {admin_user.role}")
        print(f"   是否活跃: {admin_user.is_active}")
        print(f"   哈希密码: {admin_user.hashed_password[:20]}...")
        
        # 测试默认密码
        test_passwords = ["971028", "admin", "password", "123456"]
        
        for password in test_passwords:
            if verify_password(password, admin_user.hashed_password):
                print(f"✅ 密码验证成功: '{password}'")
                return
            else:
                print(f"❌ 密码验证失败: '{password}'")
        
        print("\n❌ 所有测试密码都失败!")
        print("建议重新设置admin密码")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        db_session.close()

if __name__ == "__main__":
    main()