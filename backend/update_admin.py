#!/usr/bin/env python3
"""
更新管理员用户
"""
import sqlite3
from app.core.security import get_password_hash

def update_admin():
    conn = sqlite3.connect('cot_studio.db')
    cursor = conn.cursor()
    
    # 更新管理员用户的密码和角色
    hashed_password = get_password_hash("971028")
    cursor.execute('''
        UPDATE users 
        SET role = "SUPER_ADMIN", 
            hashed_password = ?,
            login_count = 0
        WHERE username = "admin"
    ''', (hashed_password,))
    
    print('Updated admin user')
    
    conn.commit()
    conn.close()
    print('Admin user updated successfully')

if __name__ == "__main__":
    update_admin()