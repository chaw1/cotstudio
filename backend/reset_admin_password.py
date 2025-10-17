#!/usr/bin/env python3
"""
重置admin用户密码脚本
"""
import sys
import os
sys.path.append('/app')

from app.core.security import get_password_hash
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
        
        print(f"✅ 找到admin用户: {admin_user.username}")
        
        # 设置新密码
        new_password = "971028"
        new_hashed_password = get_password_hash(new_password)
        
        print(f"🔄 正在重置密码为: {new_password}")
        
        # 更新密码
        admin_user.hashed_password = new_hashed_password
        db_session.commit()
        
        print("✅ 密码重置成功!")
        print(f"   新的哈希密码: {new_hashed_password[:20]}...")
        
        # 验证新密码
        from app.core.security import verify_password
        if verify_password(new_password, new_hashed_password):
            print("✅ 密码验证成功!")
        else:
            print("❌ 密码验证失败!")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        db_session.rollback()
    finally:
        db_session.close()

if __name__ == "__main__":
    main()