# COT Studio MVP 部署指南

## 概述

本文档提供了 COT Studio MVP 的完整部署指南，包括开发环境、测试环境和生产环境的部署方式。

## 系统要求

### 最低硬件要求

- **CPU**: 4核心 (推荐8核心)
- **内存**: 8GB RAM (推荐16GB)
- **存储**: 50GB 可用空间 (推荐100GB SSD)
- **网络**: 稳定的互联网连接

### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+), macOS, Windows 10+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.30+

## 快速部署

### 一键启动 (推荐)

```bash
# 1. 克隆项目
git clone <repository-url>
cd cot-studio-mvp

# 2. 复制环境配置
cp .env.example .env

# 3. 一键启动所有服务
make docker-up

# 4. 等待服务启动完成 (约2-3分钟)
make docker-logs

# 5. 访问应用
# 前端: http://localhost:3000
# 后端API: http://localhost:8000/docs
```

### 验证部署

```bash
# 检查所有服务状态
docker-compose ps

# 检查服务健康状态
docker-compose exec backend curl -f http://localhost:8000/health
docker-compose exec frontend curl -f http://localhost:80/health.html

# 查看服务日志
make docker-logs
```

## 环境配置

### 开发环境

开发环境使用默认的 `docker-compose.yml` 配置，包含以下特性：

- 热重载支持
- 调试模式启用
- 详细日志输出
- 开发工具集成

```bash
# 启动开发环境
make dev

# 或者使用Docker
make docker-up
```

### 生产环境

生产环境使用 `docker-compose.prod.yml` 配置：

```bash
# 使用生产配置启动
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 或者使用环境变量
export COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml
docker-compose up -d
```

### 环境变量配置

创建 `.env` 文件并配置以下变量：

```bash
# 数据库配置 (开发环境默认值)
POSTGRES_DB=cotdb
POSTGRES_USER=cotuser
POSTGRES_PASSWORD=cotpass

# Neo4j配置
NEO4J_PASSWORD=neo4jpass

# Redis配置
REDIS_PASSWORD=redispass

# MinIO配置
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123

# RabbitMQ配置
RABBITMQ_USER=cotuser
RABBITMQ_PASSWORD=cotpass

# JWT配置
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# LLM API配置 (至少配置一个)
OPENAI_API_KEY=your-openai-api-key-here
DEEPSEEK_API_KEY=your-deepseek-api-key-here
KIMI_API_KEY=your-kimi-api-key-here

# 应用配置
DEBUG=false
LOG_LEVEL=INFO
```

## 服务详情

### 核心服务

| 服务名 | 端口 | 描述 | 健康检查 |
|--------|------|------|----------|
| frontend | 3000 | React前端应用 | http://localhost:3000/health.html |
| backend | 8000 | FastAPI后端服务 | http://localhost:8000/health |
| celery | - | 异步任务处理器 | celery inspect ping |
| celery-beat | - | 定时任务调度器 | - |
| flower | 5555 | Celery监控界面 | http://localhost:5555 |

### 数据存储服务

| 服务名 | 端口 | 描述 | 管理界面 |
|--------|------|------|----------|
| postgres | 5432 | PostgreSQL数据库 | - |
| neo4j | 7474/7687 | Neo4j图数据库 | http://localhost:7474 |
| redis | 6379 | Redis缓存 | - |
| minio | 9000/9001 | MinIO对象存储 | http://localhost:9001 |
| rabbitmq | 5672/15672 | RabbitMQ消息队列 | http://localhost:15672 |

### 服务启动顺序

系统会按照以下顺序启动服务，确保依赖关系正确：

1. **基础存储服务**: postgres, redis, neo4j, minio, rabbitmq
2. **后端服务**: backend
3. **异步服务**: celery, celery-beat, flower
4. **前端服务**: frontend

## 数据持久化

### 数据卷配置

所有重要数据都通过Docker卷进行持久化：

```yaml
volumes:
  postgres_data:      # PostgreSQL数据
  neo4j_data:         # Neo4j数据
  neo4j_logs:         # Neo4j日志
  redis_data:         # Redis数据
  minio_data:         # MinIO对象存储
  rabbitmq_data:      # RabbitMQ数据
```

### 数据备份

```bash
# 备份PostgreSQL数据
docker-compose exec postgres pg_dump -U cotuser cotdb > backup_$(date +%Y%m%d).sql

# 备份Neo4j数据
docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/tmp/neo4j_backup_$(date +%Y%m%d).dump

# 备份MinIO数据
docker-compose exec minio mc mirror /data /backup/minio_$(date +%Y%m%d)
```

### 数据恢复

```bash
# 恢复PostgreSQL数据
docker-compose exec -T postgres psql -U cotuser cotdb < backup_20240315.sql

# 恢复Neo4j数据
docker-compose exec neo4j neo4j-admin load --from=/tmp/neo4j_backup_20240315.dump --database=neo4j --force

# 恢复MinIO数据
docker-compose exec minio mc mirror /backup/minio_20240315 /data
```

## 网络配置

### 内部网络

所有服务都连接到 `cot-network` 桥接网络，服务间通过服务名进行通信：

- `backend` -> `postgres:5432`
- `backend` -> `neo4j:7687`
- `backend` -> `redis:6379`
- `backend` -> `minio:9000`
- `backend` -> `rabbitmq:5672`

### 外部访问

以下端口对外开放：

- `3000`: 前端应用
- `8000`: 后端API
- `5555`: Celery监控
- `7474`: Neo4j浏览器
- `9001`: MinIO控制台
- `15672`: RabbitMQ管理界面

### 防火墙配置

生产环境建议只开放必要端口：

```bash
# 允许HTTP/HTTPS访问
sudo ufw allow 80
sudo ufw allow 443

# 允许SSH访问
sudo ufw allow 22

# 启用防火墙
sudo ufw enable
```

## 性能优化

### 资源限制

在生产环境中，建议为每个服务设置资源限制：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  postgres:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### 数据库优化

PostgreSQL配置优化：

```sql
-- 在postgres容器中执行
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
SELECT pg_reload_conf();
```

Neo4j配置优化：

```bash
# 在docker-compose.yml中设置
NEO4J_dbms_memory_heap_initial_size=512m
NEO4J_dbms_memory_heap_max_size=2G
NEO4J_dbms_memory_pagecache_size=1G
```

### 缓存配置

Redis缓存优化：

```bash
# 在redis容器中执行
redis-cli CONFIG SET maxmemory 512mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## 监控和日志

### 日志管理

```bash
# 查看所有服务日志
make docker-logs

# 查看特定服务日志
docker-compose logs -f backend

# 查看最近的日志
docker-compose logs --tail=100 backend

# 导出日志到文件
docker-compose logs backend > backend.log
```

### 健康检查

所有服务都配置了健康检查，可以通过以下方式监控：

```bash
# 检查服务健康状态
docker-compose ps

# 查看详细健康检查信息
docker inspect $(docker-compose ps -q backend) | jq '.[0].State.Health'
```

### 性能监控

访问以下监控界面：

- **Celery监控**: http://localhost:5555
- **RabbitMQ监控**: http://localhost:15672
- **Neo4j监控**: http://localhost:7474
- **MinIO监控**: http://localhost:9001

## 扩展部署

### 水平扩展

```bash
# 扩展后端服务实例
docker-compose up -d --scale backend=3

# 扩展Celery工作进程
docker-compose up -d --scale celery=3
```

### 负载均衡

使用Nginx进行负载均衡：

```nginx
upstream backend {
    server backend_1:8000;
    server backend_2:8000;
    server backend_3:8000;
}

server {
    listen 80;
    location /api/ {
        proxy_pass http://backend;
    }
}
```

## 安全配置

### SSL/TLS配置

生产环境建议启用HTTPS：

```bash
# 生成SSL证书 (使用Let's Encrypt)
certbot --nginx -d your-domain.com

# 或者使用自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/nginx/ssl/nginx.key \
  -out docker/nginx/ssl/nginx.crt
```

### 访问控制

```bash
# 设置强密码
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export NEO4J_PASSWORD=$(openssl rand -base64 32)
export REDIS_PASSWORD=$(openssl rand -base64 32)

# 限制网络访问
# 在docker-compose.yml中移除不必要的端口映射
```

### 数据加密

```bash
# 启用PostgreSQL SSL
POSTGRES_SSL_MODE=require

# 启用Redis密码认证
REDIS_PASSWORD=your_secure_password
```

## 故障排除

常见问题和解决方案请参考 [故障排除指南](./troubleshooting.md)。

## 更新和维护

### 应用更新

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build

# 滚动更新服务
docker-compose up -d
```

### 数据库迁移

```bash
# 执行数据库迁移
docker-compose exec backend alembic upgrade head
```

### 清理和维护

```bash
# 清理未使用的镜像和容器
docker system prune -a

# 清理数据卷 (谨慎使用)
docker volume prune
```