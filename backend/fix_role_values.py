#!/usr/bin/env python3
"""
修复数据库中的role值
"""
import sqlite3

def fix_role_values():
    conn = sqlite3.connect('cot_studio.db')
    cursor = conn.cursor()

    # 更新现有的role值
    cursor.execute('UPDATE users SET role = "USER" WHERE role = "user"')
    print('Updated role values')

    conn.commit()
    conn.close()
    print('Role values updated')

if __name__ == "__main__":
    fix_role_values()