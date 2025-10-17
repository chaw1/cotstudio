#!/usr/bin/env python3
"""
更新数据库架构脚本
"""
import sqlite3

def update_schema():
    conn = sqlite3.connect('cot_studio.db')
    cursor = conn.cursor()

    # 添加缺少的列
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT "user"')
        print('Added role column')
    except Exception as e:
        print(f'Role column: {e}')

    try:
        cursor.execute('ALTER TABLE users ADD COLUMN department VARCHAR(100)')
        print('Added department column')
    except Exception as e:
        print(f'Department column: {e}')

    try:
        cursor.execute('ALTER TABLE users ADD COLUMN last_login DATETIME')
        print('Added last_login column')
    except Exception as e:
        print(f'Last_login column: {e}')

    try:
        cursor.execute('ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0')
        print('Added login_count column')
    except Exception as e:
        print(f'Login_count column: {e}')

    conn.commit()
    conn.close()
    print('Database schema updated')

if __name__ == "__main__":
    update_schema()