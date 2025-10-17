# COT Studio MVP

Chain of Thought Studio - 一个基于思维链的 AI 应用开发平台。

## 🚀 快速开始

### 系统要求
- **Docker Desktop**: 20.10+ (必需)
- **Python 3.11+**: 后端开发
- **Node.js 18+**: 前端开发
- **Git**: 代码管理
- **内存**: 至少 8GB RAM (推荐 16GB)

### 一键安装
```bash
# 1. 克隆项目
git clone <repository-url>
cd cotstudio

# 2. 复制并编辑环境配置
cp .env.example .env
# 编辑 .env 文件，配置 LLM API 密钥

# 3. 网络配置 (如遇到镜像下载问题)
# Windows PowerShell 设置代理:
$env:HTTP_PROXY = "http://127.0.0.1:10808"
$env:HTTPS_PROXY = "http://127.0.0.1:10808"

# 4. 启动所有服务
docker-compose up -d

# 5. 等待服务启动完成 (约2-3分钟)
docker-compose ps
```

### 本地开发模式
```bash
# 1. 启动基础设施服务
docker-compose up -d postgres redis neo4j minio rabbitmq

# 2. 本地运行后端
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 .\venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# 3. 本地运行前端
cd frontend
npm install
npm run dev
```

### 访问服务
安装完成后，可以通过以下地址访问各项服务：

| 服务 | 地址 | 默认凭据 |
|------|------|----------|
| 前端应用 | http://localhost:3000 | admin / 971028 |
| 后端 API | http://localhost:8000 | - |
| API 文档 | http://localhost:8000/docs | - |
| Neo4j 浏览器 | http://localhost:7474 | neo4j / neo4jpass |
| MinIO 控制台 | http://localhost:9001 | minioadmin / minioadmin123 |
| RabbitMQ 管理 | http://localhost:15672 | cotuser / cotpass |
| Celery 监控 | http://localhost:5555 | - |

## 📋 功能特性

- **思维链推理**: 支持复杂的多步骤推理过程
- **知识图谱**: 基于 Neo4j 的知识表示和推理
- **多模型支持**: 集成 OpenAI、DeepSeek 等多种 LLM
- **异步处理**: 基于 Celery 的任务队列系统
- **可视化界面**: 直观的 Web 界面和数据可视化

## 🏗️ 架构概览

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │    │   Backend   │    │   Celery    │
│   (React)   │◄──►│  (FastAPI)  │◄──►│  (Worker)   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│PostgreSQL│    │  Neo4j  │    │  Redis  │    │ MinIO   │
│   DB    │    │  Graph  │    │ Cache   │    │Storage  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

## � 环境配置南

### 必需配置
编辑 `.env` 文件，配置以下关键参数：

```env
# LLM API 密钥 (至少配置一个)
OPENAI_API_KEY=your-openai-api-key-here
DEEPSEEK_API_KEY=your-deepseek-api-key-here
KIMI_API_KEY=your-kimi-api-key-here

# 数据库密码 (保持默认即可)
POSTGRES_PASSWORD=cotpass
NEO4J_PASSWORD=neo4jpass
REDIS_PASSWORD=redispass
RABBITMQ_PASSWORD=cotpass

# 应用安全密钥 (生产环境必须修改)
SECRET_KEY=your-secret-key-change-in-production-please-use-a-strong-key
```

### 服务配置统一标准
| 服务 | 用户名 | 密码 | 端口 |
|------|--------|------|------|
| PostgreSQL | cotuser | cotpass | 5432 |
| Neo4j | neo4j | neo4jpass | 7474/7687 |
| Redis | - | redispass | 6379 |
| MinIO | minioadmin | minioadmin123 | 9000/9001 |
| RabbitMQ | cotuser | cotpass | 5672/15672 |

## 🛠️ 开发指南

### 开发模式选择

#### 方法一：完全 Docker (推荐新手)
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### 方法二：混合开发 (推荐开发者)
```bash
# 启动基础设施服务
docker-compose up -d postgres redis neo4j minio rabbitmq

# 本地运行后端 (支持热重载)
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 .\venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# 本地运行前端 (支持热重载)
cd frontend
npm install
npm run dev
```

### 常用命令

#### 服务管理
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs [service_name]
docker-compose logs -f backend  # 实时日志

# 重启服务
docker-compose restart [service_name]

# 停止所有服务
docker-compose down

# 完全清理 (包括数据卷)
docker-compose down -v
```

#### 开发命令
```bash
# 后端开发
cd backend
pytest                    # 运行测试
alembic upgrade head       # 数据库迁移
uvicorn app.main:app --reload  # 启动开发服务器

# 前端开发
cd frontend
npm test                   # 运行测试
npm run build             # 构建生产版本
npm run dev               # 启动开发服务器
```

## 📚 文档

- **[📖 文档索引](DOCUMENTATION_INDEX.md)** - 完整文档导航 ⭐ **推荐查看**
- **[📋 完整项目指南](PROJECT_GUIDE.md)** - 详细的使用和开发指南
- **[🔧 API 文档](http://localhost:8000/docs)** - 自动生成的 OpenAPI 文档
- [安装指南](docs/INSTALLATION.md) - 详细安装说明
- [开发指南](docs/DEVELOPMENT.md) - 开发环境配置
- [部署指南](docs/DEPLOYMENT.md) - 生产环境部署
- [故障排除](docs/TROUBLESHOOTING.md) - 常见问题解决
- [交付文档](DELIVERY_PACKAGE.md) - 完整交付包说明

## 🔧 故障排除

### 常见问题

#### 1. Docker 镜像下载失败 (最常见)
```bash
# 问题：无法下载 python:3.11-slim 等镜像
# 解决：配置代理或使用国内镜像源

# Windows PowerShell 设置代理:
$env:HTTP_PROXY = "http://127.0.0.1:10808"
$env:HTTPS_PROXY = "http://127.0.0.1:10808"

# 预拉取关键镜像:
docker pull python:3.11-slim
docker pull node:18-alpine
docker pull postgres:15

# 然后重新启动:
docker-compose up -d
```

#### 2. Docker 构建失败 (pip install 错误)
```bash
# 问题：pip install 失败
# 解决：使用构建修复脚本

# Windows PowerShell:
.\scripts\build-fix.ps1                    # 自动修复
.\scripts\build-fix.ps1 -UseLatest         # 使用最新版本 (推荐)
.\scripts\build-fix.ps1 -TestPackages      # 测试并修复问题包
.\scripts\build-fix.ps1 -InfraOnly         # 只启动基础设施，本地开发

# 手动设置 PyPI 镜像源:
$env:PIP_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"
docker-compose build --no-cache
```

#### 3. Docker 构建卡住
```bash
# 问题：docker-compose 卡住不动
# 解决：强制停止并重新开始

# Windows PowerShell:
.\scripts\docker-deploy-fix.ps1 -ForceKill    # 强制停止
.\scripts\docker-deploy-fix.ps1 -CleanAll     # 清理资源
.\scripts\docker-deploy-fix.ps1 -InfraOnly    # 基础设施模式
```

#### 4. 服务启动失败
```bash
# 检查端口占用
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# 检查服务状态
docker-compose ps
docker-compose logs [service_name]
```

#### 5. 数据库连接问题
```bash
# 测试 PostgreSQL 连接
docker-compose exec postgres psql -U cotuser -d cotdb -c "SELECT 1;"

# 测试 Neo4j 连接
docker-compose exec neo4j cypher-shell -u neo4j -p neo4jpass "RETURN 1;"
```

#### 6. 前端登录问题
- 确保后端服务正在运行: http://localhost:8000/health
- 使用正确的凭据: `admin / 971028`
- 检查浏览器控制台错误信息

#### 7. LLM API 调用失败
- 检查 `.env` 文件中的 API 密钥配置
- 确认 API 密钥有效且有足够额度
- 查看后端日志了解具体错误信息

#### 8. 内存不足
```bash
# 检查系统资源使用
docker stats

# 清理未使用的容器和镜像
docker system prune -f
```

更多问题解决方案请参考 [完整项目指南](PROJECT_GUIDE.md)。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[MIT License](LICENSE)

---

**注意**: 首次运行可能需要较长时间来下载 Docker 镜像，请耐心等待。