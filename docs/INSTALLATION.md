# COT Studio MVP 安装指南

## 概述

COT Studio MVP 是一个基于 Docker 的微服务架构应用，包含前端、后端和多个基础设施服务。本文档提供详细的安装和配置指南。

## 系统要求

### 必需软件
- **Docker Desktop**: 版本 20.10 或更高
- **Docker Compose**: 版本 2.0 或更高
- **Git**: 用于代码管理
- **PowerShell**: Windows 环境（推荐 PowerShell 5.1 或更高）

### 硬件要求
- **内存**: 至少 8GB RAM（推荐 16GB）
- **存储**: 至少 10GB 可用空间
- **网络**: 稳定的互联网连接（用于拉取 Docker 镜像）

### 端口要求
确保以下端口未被占用：
- `3000`: 前端应用
- `8000`: 后端 API
- `5432`: PostgreSQL 数据库
- `7474`, `7687`: Neo4j 图数据库
- `6379`: Redis 缓存
- `9000`, `9001`: MinIO 对象存储
- `5672`, `15672`: RabbitMQ 消息队列
- `5555`: Celery 监控

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd cotstudio
```

### 2. 运行安装脚本
```powershell
# 标准安装（推荐）
.\scripts\setup.ps1

# 跳过代理配置
.\scripts\setup.ps1 -NoProxy

# 跳过所有检查
.\scripts\setup.ps1 -SkipChecks -NoProxy
```

### 3. 配置代理（如需要）
如果您在企业网络环境中，可能需要配置 HTTP 代理：

1. 脚本会询问是否配置代理
2. 输入代理地址（默认：`http://127.0.0.1:10808`）
3. 手动配置 Docker Desktop 代理设置：
   - 打开 Docker Desktop
   - 进入 Settings → Resources → Proxies
   - 设置 HTTP/HTTPS 代理

## 安装脚本功能

### 自动修复功能
安装脚本会自动修复以下已知问题：

1. **Docker Compose 配置修复**
   - 移除过时的 `version` 属性
   - 更新 Neo4j 镜像版本为 `latest`
   - 移除不兼容的 Neo4j 内存配置

2. **服务启动策略**
   - 优先启动基础设施服务
   - 分阶段启动，确保依赖关系
   - 网络问题时提供降级方案

3. **环境配置**
   - 自动生成 `.env` 文件
   - 创建随机密码
   - 配置服务连接参数

### 脚本参数
- `-SkipChecks`: 跳过系统要求检查
- `-NoProxy`: 跳过代理配置询问

## 服务架构

### 基础设施服务
| 服务 | 端口 | 用途 | 管理界面 |
|------|------|------|----------|
| PostgreSQL | 5432 | 主数据库 | - |
| Neo4j | 7474, 7687 | 图数据库 | http://localhost:7474 |
| Redis | 6379 | 缓存 | - |
| MinIO | 9000, 9001 | 对象存储 | http://localhost:9001 |
| RabbitMQ | 5672, 15672 | 消息队列 | http://localhost:15672 |

### 应用服务
| 服务 | 端口 | 用途 | 访问地址 |
|------|------|------|----------|
| Frontend | 3000 | Web 界面 | http://localhost:3000 |
| Backend | 8000 | API 服务 | http://localhost:8000 |
| Celery | - | 异步任务 | - |
| Flower | 5555 | 任务监控 | http://localhost:5555 |

## 常见问题解决

### 1. Neo4j 启动失败
**问题**: Neo4j 容器重启循环
**解决方案**: 
- 检查内存配置是否兼容
- 使用 `docker-compose logs neo4j` 查看日志
- 脚本已自动修复此问题

### 2. 网络连接问题
**问题**: 无法拉取 Docker 镜像
**解决方案**:
- 配置 HTTP 代理
- 使用国内 Docker 镜像源
- 检查防火墙设置

### 3. 端口占用
**问题**: 端口被其他服务占用
**解决方案**:
- 停止占用端口的服务
- 修改 `docker-compose.yml` 中的端口映射
- 使用 `netstat -an | findstr :端口号` 查找占用进程

### 4. PowerShell 兼容性
**问题**: `Join-String` cmdlet 不存在
**解决方案**: 脚本已修复，使用 `-join` 操作符替代

## 手动安装步骤

如果自动脚本失败，可以手动执行以下步骤：

### 1. 修复 Docker Compose 配置
```powershell
# 移除 version 属性
(Get-Content docker-compose.yml) -replace 'version:.*', '# Removed obsolete version' | Set-Content docker-compose.yml

# 更新 Neo4j 镜像
(Get-Content docker-compose.yml) -replace 'neo4j:5\.0-community', 'neo4j:latest' | Set-Content docker-compose.yml
```

### 2. 创建环境文件
```powershell
Copy-Item .env.example .env
# 编辑 .env 文件，配置 API 密钥
```

### 3. 启动基础设施服务
```powershell
docker-compose up -d postgres redis neo4j minio rabbitmq
```

### 4. 构建应用服务（可选）
```powershell
docker-compose build
docker-compose up -d
```

## 开发环境配置

### 1. 仅基础设施模式
如果只需要基础设施服务进行本地开发：
```powershell
docker-compose up -d postgres redis neo4j minio rabbitmq
```

### 2. 本地开发模式
前端和后端可以在本地运行，连接到 Docker 中的基础设施服务。

### 3. 环境变量配置
编辑 `.env` 文件，配置以下关键参数：
```env
# LLM API 配置 (至少配置一个)
OPENAI_API_KEY=your-openai-api-key-here
DEEPSEEK_API_KEY=your-deepseek-api-key-here
KIMI_API_KEY=your-kimi-api-key-here

# 数据库配置 (统一密码)
POSTGRES_PASSWORD=cotpass
NEO4J_PASSWORD=neo4jpass
REDIS_PASSWORD=redispass
RABBITMQ_PASSWORD=cotpass

# 应用安全密钥 (生产环境必须修改)
SECRET_KEY=your-secret-key-change-in-production-please-use-a-strong-key
```

#### 服务配置统一标准
| 服务 | 用户名 | 密码 | 端口 |
|------|--------|------|------|
| PostgreSQL | cotuser | cotpass | 5432 |
| Neo4j | neo4j | neo4jpass | 7474/7687 |
| Redis | - | redispass | 6379 |
| MinIO | minioadmin | minioadmin123 | 9000/9001 |
| RabbitMQ | cotuser | cotpass | 5672/15672 |

#### 应用用户账户
| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 管理员 | admin | 971028 | 超级管理员 |
| 编辑者 | editor | secret | 编辑者 |

## 维护命令

### 服务管理
```powershell
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs [service_name]

# 重启服务
docker-compose restart [service_name]

# 停止所有服务
docker-compose down

# 完全清理（包括数据卷）
docker-compose down -v
```

### 数据备份
```powershell
# PostgreSQL 备份
docker-compose exec postgres pg_dump -U cotuser cotdb > backup.sql

# Neo4j 备份
docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/tmp/neo4j-backup.dump
```

## 故障排除

### 日志查看
```powershell
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs postgres
docker-compose logs neo4j
docker-compose logs backend
```

### 健康检查
```powershell
# 检查服务健康状态
docker-compose ps

# 测试数据库连接
docker-compose exec postgres psql -U cotuser -d cotdb -c "SELECT 1;"

# 测试 Neo4j 连接
docker-compose exec neo4j cypher-shell -u neo4j -p <password> "RETURN 1;"
```

### 重置环境
```powershell
# 停止并删除所有容器和数据卷
docker-compose down -v

# 重新运行安装脚本
.\scripts\setup.ps1
```

## 生产部署注意事项

1. **安全配置**
   - 更改默认密码
   - 配置防火墙规则
   - 启用 HTTPS

2. **性能优化**
   - 调整数据库连接池
   - 配置缓存策略
   - 监控资源使用

3. **备份策略**
   - 定期备份数据库
   - 配置日志轮转
   - 监控磁盘空间

## 支持和反馈

如果遇到问题，请：
1. 查看本文档的故障排除部分
2. 检查 GitHub Issues
3. 提供详细的错误日志和环境信息

---

**更新日期**: 2025-09-15
**版本**: 1.0.0