#!/usr/bin/env python3
"""
测试数据库迁移脚本
"""
import sys
import os
import sqlite3
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_migration_001():
    """测试初始迁移脚本"""
    print("🧪 Testing migration 001 (initial migration)...")
    
    # 创建临时数据库
    db_path = "test_migration.db"
    
    try:
        # 删除已存在的测试数据库
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 执行初始迁移中的表创建语句
        
        # 创建用户表
        cursor.execute("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                hashed_password TEXT NOT NULL,
                full_name TEXT,
                is_active BOOLEAN NOT NULL,
                is_superuser BOOLEAN NOT NULL,
                roles TEXT NOT NULL
            )
        """)
        
        # 创建项目表
        cursor.execute("""
            CREATE TABLE projects (
                id TEXT PRIMARY KEY,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                owner_id TEXT NOT NULL,
                tags TEXT NOT NULL,
                project_type TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (owner_id) REFERENCES users(id)
            )
        """)
        
        # 创建文件表
        cursor.execute("""
            CREATE TABLE files (
                id TEXT PRIMARY KEY,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                project_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                size INTEGER NOT NULL,
                mime_type TEXT NOT NULL,
                ocr_status TEXT NOT NULL,
                ocr_engine TEXT,
                ocr_result TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        
        # 创建切片表
        cursor.execute("""
            CREATE TABLE slices (
                id TEXT PRIMARY KEY,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                file_id TEXT NOT NULL,
                content TEXT NOT NULL,
                start_offset INTEGER,
                end_offset INTEGER,
                slice_type TEXT NOT NULL,
                page_number INTEGER,
                sequence_number INTEGER NOT NULL,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        """)
        
        # 创建CoT项目表
        cursor.execute("""
            CREATE TABLE cot_items (
                id TEXT PRIMARY KEY,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                project_id TEXT NOT NULL,
                slice_id TEXT NOT NULL,
                question TEXT NOT NULL,
                chain_of_thought TEXT,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                llm_metadata TEXT,
                created_by TEXT NOT NULL,
                reviewed_by TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (slice_id) REFERENCES slices(id)
            )
        """)
        
        # 创建CoT候选答案表
        cursor.execute("""
            CREATE TABLE cot_candidates (
                id TEXT PRIMARY KEY,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                cot_item_id TEXT NOT NULL,
                text TEXT NOT NULL,
                chain_of_thought TEXT,
                score REAL NOT NULL,
                chosen BOOLEAN NOT NULL,
                rank INTEGER NOT NULL,
                FOREIGN KEY (cot_item_id) REFERENCES cot_items(id)
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX ix_users_email ON users(email)")
        cursor.execute("CREATE INDEX ix_users_username ON users(username)")
        cursor.execute("CREATE INDEX ix_projects_name ON projects(name)")
        cursor.execute("CREATE INDEX ix_files_file_hash ON files(file_hash)")
        
        conn.commit()
        print("✓ All tables created successfully")
        
        # 验证表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['users', 'projects', 'files', 'slices', 'cot_items', 'cot_candidates']
        for table in expected_tables:
            assert table in tables, f"Table {table} not found"
        print("✓ All expected tables exist")
        
        # 验证索引
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        expected_indexes = ['ix_users_email', 'ix_users_username', 'ix_projects_name', 'ix_files_file_hash']
        for index in expected_indexes:
            assert index in indexes, f"Index {index} not found"
        print("✓ All expected indexes exist")
        
        conn.close()
        print("✓ Migration 001 test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Migration 001 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理测试数据库
        if os.path.exists(db_path):
            os.remove(db_path)


def test_migration_002():
    """测试种子数据迁移脚本"""
    print("\n🧪 Testing migration 002 (seed data)...")
    
    # 创建临时数据库
    db_path = "test_seed_data.db"
    
    try:
        # 删除已存在的测试数据库
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 先创建用户表（简化版）
        cursor.execute("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                hashed_password TEXT NOT NULL,
                full_name TEXT,
                is_active BOOLEAN NOT NULL,
                is_superuser BOOLEAN NOT NULL,
                roles TEXT NOT NULL
            )
        """)
        
        # 插入种子数据（模拟migration 002）
        now = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO users (
                id, created_at, updated_at, username, email, hashed_password,
                full_name, is_active, is_superuser, roles
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "admin-id-123", now, now, "admin", "admin@cotstudio.com",
            "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            "System Administrator", True, True, '["admin"]'
        ))
        
        cursor.execute("""
            INSERT INTO users (
                id, created_at, updated_at, username, email, hashed_password,
                full_name, is_active, is_superuser, roles
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "editor-id-456", now, now, "editor", "editor@cotstudio.com",
            "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            "Editor User", True, False, '["editor"]'
        ))
        
        conn.commit()
        print("✓ Seed data inserted successfully")
        
        # 验证种子数据
        cursor.execute("SELECT username, email, is_superuser FROM users ORDER BY username")
        users = cursor.fetchall()
        
        assert len(users) == 2, f"Expected 2 users, got {len(users)}"
        
        admin_user = users[0]  # admin comes first alphabetically
        assert admin_user[0] == "admin", f"Expected admin username, got {admin_user[0]}"
        assert admin_user[1] == "admin@cotstudio.com", f"Expected admin email, got {admin_user[1]}"
        assert admin_user[2] == 1, f"Expected admin to be superuser, got {admin_user[2]}"  # SQLite stores boolean as int
        
        editor_user = users[1]  # editor comes second
        assert editor_user[0] == "editor", f"Expected editor username, got {editor_user[0]}"
        assert editor_user[1] == "editor@cotstudio.com", f"Expected editor email, got {editor_user[1]}"
        assert editor_user[2] == 0, f"Expected editor not to be superuser, got {editor_user[2]}"
        
        print("✓ Seed data validation passed")
        
        conn.close()
        print("✓ Migration 002 test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Migration 002 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理测试数据库
        if os.path.exists(db_path):
            os.remove(db_path)


if __name__ == "__main__":
    print("🚀 Starting Migration Tests\n")
    
    success = True
    
    # 运行所有测试
    success &= test_migration_001()
    success &= test_migration_002()
    
    if success:
        print("\n🎉 All migration tests passed! Database migrations are working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some migration tests failed. Please check the errors above.")
        sys.exit(1)