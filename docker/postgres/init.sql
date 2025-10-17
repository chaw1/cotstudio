-- 初始化PostgreSQL数据库
-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建基础表结构（后续会通过Alembic管理）
-- 这里只是确保数据库正确初始化