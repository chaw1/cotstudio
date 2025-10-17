#!/usr/bin/env python3
"""
初始化测试数据库
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.init_db import init_db

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")