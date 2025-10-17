#!/usr/bin/env python3
"""
检查管理员用户
"""
import sqlite3

def check_admin():
    conn = sqlite3.connect('cot_studio.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, email, role, is_superuser FROM users WHERE username = "admin"')
    result = cursor.fetchone()
    print('Admin user:', result)
    conn.close()

if __name__ == "__main__":
    check_admin()