# COT Studio MVP 项目指南

## 项目概述

COT Studio MVP 是一个基于思维链的 AI 应用开发平台，提供端到端的交互式环境，帮助研究者和工程团队构建、泛化和合成高质量的 Chain-of-Thought (CoT) 数据集。

## 🚀 快速开始

### 系统要求
- **Docker Desktop**: 20.10+ (必需)
- **Python 3.11+**: 后端开发
- **Node.js 18+**: 前端开发
- **Git**: 代码管理
- **内存**: 至少 8GB RAM (推荐 16GB)
- **存储**: 至少 50GB 可用空间

### 一键安装
```bash
# 1. 克隆项目
git clone <repository-url>
cd cotstudio

# 2. 复制环境配置
cp .env.example .env

# 3. 编辑配置文件，设置API密钥
nano .env

# 4. 网络配置 (如果在国内或企业网络环境)
# 参考下面的"网络配置"部分

# 5. 启动所有服务
docker-compose up -d

# 6. 等待服务启动完成 (约2-3分钟)
docker-compose ps
```

### 访问服务
| 服务 | 地址 | 默认凭据 |
|------|------|----------|
| 前端应用 | http://localhost:3000 | admin / 971028 |
| 后端 API | http://localhost:8000 | - |
| API 文档 | http://localhost:8000/docs | - |
| Neo4j 浏览器 | http://localhost:7474 | neo4j / neo4jpass |
| MinIO 控制台 | http://localhost:9001 | minioadmin / minioadmin123 |
| RabbitMQ 管理 | http://localhost:15672 | cotuser / cotpass |
| Celery 监控 | http://localhost:5555 | - |

## 🔧 环境配置

### 网络配置 (重要)

如果你在国内或企业网络环境中，可能需要配置代理来下载 Docker 镜像：

#### Windows PowerShell 代理配置
```powershell
# 1. 设置 PowerShell 代理 (假设代理端口为 10808)
$env:HTTP_PROXY = "http://127.0.0.1:10808"
$env:HTTPS_PROXY = "http://127.0.0.1:10808"

# 2. 配置 Docker Desktop 代理
# 打开 Docker Desktop → Settings → Resources → Proxies
# 设置 HTTP Proxy: http://127.0.0.1:10808
# 设置 HTTPS Proxy: http://127.0.0.1:10808

# 3. 预拉取关键镜像 (避免构建时网络问题)
docker pull python:3.11-slim
docker pull node:18-alpine
docker pull postgres:15
docker pull neo4j:latest
docker pull redis:7-alpine
docker pull minio/minio:latest
docker pull rabbitmq:3-management

# 4. 然后启动服务
docker-compose up -d
```

#### 快速网络配置脚本 (推荐)
```powershell
# Windows 用户可以使用自动化脚本
.\scripts\setup-network.ps1

# 或指定代理端口
.\scripts\setup-network.ps1 -ProxyPort 7890

# 跳过代理配置，只拉取镜像
.\scripts\setup-network.ps1 -SkipProxy
```

#### Docker 构建优化
```bash
# 如果遇到 pip install 失败，使用以下优化方案：

# 方法一：使用国内 PyPI 镜像源
export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
export PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# 方法二：分步构建 (推荐)
docker-compose build --no-cache backend  # 单独构建后端
docker-compose build --no-cache frontend # 单独构建前端
docker-compose up -d                      # 启动所有服务

# 方法三：跳过构建，使用预构建镜像
docker-compose up -d postgres redis neo4j minio rabbitmq  # 只启动基础设施
# 然后本地运行前后端 (参考本地开发模式)
```

#### Linux/Mac 代理配置
```bash
# 1. 设置环境变量
export HTTP_PROXY=http://127.0.0.1:10808
export HTTPS_PROXY=http://127.0.0.1:10808

# 2. 配置 Docker 代理
mkdir -p ~/.docker
cat > ~/.docker/config.json << EOF
{
  "proxies": {
    "default": {
      "httpProxy": "http://127.0.0.1:10808",
      "httpsProxy": "http://127.0.0.1:10808"
    }
  }
}
EOF

# 3. 重启 Docker 服务
sudo systemctl restart docker

# 4. 预拉取镜像
docker pull python:3.11-slim
docker pull node:18-alpine
# ... 其他镜像
```

#### 国内镜像源配置 (推荐)
```bash
# 配置 Docker 镜像源 (阿里云)
# 编辑 /etc/docker/daemon.json (Linux) 或 Docker Desktop 设置
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://reg-mirror.qiniu.com"
  ]
}

# 重启 Docker
sudo systemctl restart docker  # Linux
# 或重启 Docker Desktop
```

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

### 用户账户
| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 管理员 | admin | 971028 | 超级管理员 |
| 编辑者 | editor | secret | 编辑者 |

## 🏗️ 系统架构

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

## 📋 核心功能

### 已实现功能 ✅
- [x] **项目管理**: 创建、编辑、删除项目
- [x] **文件上传**: 支持 PDF、Word、TXT、Markdown、LaTeX、JSON
- [x] **OCR处理**: 多引擎支持，自动文档切片
- [x] **CoT生成**: LLM集成，自动问题和候选答案生成
- [x] **标注工作台**: 拖拽排序、评分系统、Chosen标记
- [x] **知识图谱**: 实体关系抽取、可视化界面
- [x] **数据导出**: 多格式导出 (JSON、Markdown、LaTeX、TXT)
- [x] **用户管理**: 认证、权限控制、审计日志
- [x] **系统监控**: 性能监控、任务监控、健康检查

### 技术特性
- **多模型支持**: OpenAI、DeepSeek、KIMI 等 LLM
- **异步处理**: 基于 Celery 的任务队列
- **图数据库**: Neo4j 知识图谱存储
- **对象存储**: MinIO 文件存储
- **实时监控**: 完整的监控和日志系统

## 🛠️ 开发指南

### 本地开发环境

#### 方法一：Docker 开发 (推荐)
```bash
# 启动基础设施服务
docker-compose up -d postgres redis neo4j minio rabbitmq

# 本地运行后端
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 .\venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# 本地运行前端
cd frontend
npm install
npm run dev
```

#### 方法二：完全 Docker
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 常用命令
```bash
# 服务管理
docker-compose ps                    # 查看服务状态
docker-compose logs [service]        # 查看日志
docker-compose restart [service]     # 重启服务
docker-compose down                  # 停止所有服务

# 数据库操作
docker-compose exec postgres psql -U cotuser cotdb  # 连接数据库
docker-compose exec backend alembic upgrade head    # 执行迁移

# 测试
cd backend && pytest                 # 后端测试
cd frontend && npm test              # 前端测试
```

## 🔍 故障排除

### 常见问题

#### 1. Docker 镜像下载失败 ⚠️ **最常见问题**
```bash
# 问题：无法下载 python:3.11-slim 等镜像
# 错误信息：ERROR [backend internal] load metadata for docker.io/library/python:3.11-slim

# 解决方案：

# 方法一：配置代理 (推荐)
# Windows PowerShell:
$env:HTTP_PROXY = "http://127.0.0.1:10808"
$env:HTTPS_PROXY = "http://127.0.0.1:10808"

# Linux/Mac:
export HTTP_PROXY=http://127.0.0.1:10808
export HTTPS_PROXY=http://127.0.0.1:10808

# 方法二：使用国内镜像源 (推荐国内用户)
# 在 Docker Desktop 设置中添加镜像源：
# https://mirror.ccs.tencentyun.com
# https://docker.mirrors.ustc.edu.cn

# 方法三：预拉取镜像
docker pull python:3.11-slim
docker pull node:18-alpine
docker pull postgres:15
docker pull neo4j:latest
docker pull redis:7-alpine
docker pull minio/minio:latest
docker pull rabbitmq:3-management

# 然后重新启动
docker-compose up -d
```

#### 2. Docker 构建失败 (pip install 错误) ⚠️ **常见问题**
```bash
# 问题：ERROR [celery 5/7] RUN pip install --no-cache-dir -r requirements.txt
# 原因：Python 包安装网络问题或依赖冲突

# 解决方案：

# 方法一：使用国内 PyPI 镜像源 (推荐)
# Windows PowerShell:
$env:PIP_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"
$env:PIP_TRUSTED_HOST = "pypi.tuna.tsinghua.edu.cn"

# Linux/Mac:
export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
export PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# 方法二：分步构建
docker-compose build --no-cache backend
docker-compose build --no-cache frontend
docker-compose up -d

# 方法三：清理后重新构建
docker system prune -f
docker-compose build --no-cache
docker-compose up -d

# 方法四：跳过构建，使用混合开发模式
docker-compose up -d postgres redis neo4j minio rabbitmq
# 然后本地运行前后端 (参考下面的本地开发模式)

# 方法五：使用构建修复脚本 (推荐)
.\scripts\build-fix.ps1                    # 标准修复
.\scripts\build-fix.ps1 -UseMinimal        # 使用最小化依赖
.\scripts\build-fix.ps1 -StepByStep        # 分步构建
.\scripts\build-fix.ps1 -InfraOnly         # 只启动基础设施

# 方法六：包分析和测试 (深度诊断)
.\scripts\test-packages.ps1               # 测试核心包
.\scripts\test-packages.ps1 -TestAll      # 测试所有包
.\scripts\test-packages.ps1 -TestProblematic # 测试已知问题包
.\scripts\test-packages.ps1 -GenerateFixed   # 生成修复后的requirements
```

#### 包问题分析

根据分析，以下包可能导致安装失败：

**🚨 冲突包 (必须移除)**:
- `jwt==1.4.0` - 与 PyJWT 冲突
- `jose==1.0.0` - 与 python-jose 冲突

**⚠️ 大型包 (网络问题)**:
- `paddlepaddle==3.2.0` - 体积~500MB，下载容易超时
- `paddleocr==2.7.3` - 依赖 paddlepaddle

**🔧 编译包 (Windows问题)**:
- `yara-python==4.3.1` - 需要编译，Windows上容易失败

**📋 推荐解决方案**:
```bash
# 使用最新版本的优化依赖
pip install -r backend/requirements-latest.txt

# 或者先测试哪些包有问题
.\scripts\test-packages.ps1 -TestAll -GenerateFixed
pip install -r backend/requirements-fixed.txt
```

#### 3. Docker 构建卡住 ⚠️ **常见问题**
```bash
# 问题：docker-compose up -d 卡住不动，长时间无响应
# 原因：网络超时、资源不足、进程冲突

# 解决方案：

# 方法一：强制停止并重新开始 (推荐)
.\scripts\docker-deploy-fix.ps1 -ForceKill    # 强制停止所有进程
.\scripts\docker-deploy-fix.ps1 -CleanAll     # 清理所有资源
.\scripts\docker-deploy-fix.ps1 -InfraOnly    # 基础设施模式启动

# 方法二：快速启动 (带超时)
.\scripts\docker-deploy-fix.ps1 -QuickStart   # 5分钟超时启动

# 方法三：手动处理
docker-compose down --remove-orphans          # 停止所有服务
docker system prune -af                       # 清理资源
docker-compose up -d postgres redis neo4j minio rabbitmq  # 只启动基础设施
```

#### 4. 服务启动失败
```bash
# 检查端口占用
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# 检查 Docker 状态
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
- 确保后端服务正在运行 (http://localhost:8000/health)
- 使用正确的凭据: `admin / 971028`
- 检查浏览器控制台错误信息

#### 7. LLM API 调用失败
- 检查 `.env` 文件中的 API 密钥配置
- 确认 API 密钥有效且有足够额度
- 查看后端日志了解具体错误信息

### 性能优化

#### 系统资源
- **内存使用**: 正常运行约 4-6GB
- **CPU使用**: 空闲时 < 10%，处理时 < 80%
- **磁盘空间**: 基础安装约 5GB，数据增长视使用情况

#### 数据库优化
```sql
-- PostgreSQL 性能调优
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
SELECT pg_reload_conf();
```

## 📚 API 文档

### 主要端点
- **认证**: `POST /api/v1/auth/login`
- **项目**: `GET/POST/PUT/DELETE /api/v1/projects`
- **文件**: `POST /api/v1/files/upload`
- **CoT**: `GET/POST /api/v1/cot-data`
- **知识图谱**: `GET /api/v1/knowledge-graph`
- **导出**: `POST /api/v1/export`

### 完整文档
访问 http://localhost:8000/docs 查看完整的 OpenAPI 文档。

## 🚀 部署指南

### 生产环境部署
```bash
# 1. 克隆代码
git clone <repository-url>
cd cotstudio

# 2. 配置生产环境
cp .env.example .env
# 编辑 .env，设置强密码和 API 密钥

# 3. 使用生产配置启动
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 4. 配置反向代理 (Nginx)
# 5. 配置 SSL 证书
# 6. 设置防火墙规则
```

### 安全配置
```env
# 生产环境必须修改的配置
SECRET_KEY=<strong-random-key>
DEBUG=false
POSTGRES_PASSWORD=<strong-password>
NEO4J_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
```

## 🧪 测试

### 运行测试
```bash
# 后端测试
cd backend
pytest --cov=app tests/

# 前端测试
cd frontend
npm run test

# 集成测试
python backend/tests/test_runner.py integration

# 性能测试
python backend/tests/benchmark.py
```

### 测试覆盖率
- **后端单元测试**: > 80%
- **前端组件测试**: > 75%
- **API集成测试**: > 90%
- **关键业务流程**: 100%

## 📊 监控和维护

### 监控界面
- **系统监控**: http://localhost:3000/dashboard
- **任务监控**: http://localhost:5555 (Celery Flower)
- **数据库监控**: http://localhost:7474 (Neo4j Browser)
- **存储监控**: http://localhost:9001 (MinIO Console)
- **队列监控**: http://localhost:15672 (RabbitMQ Management)

### 日常维护
```bash
# 数据备份
docker-compose exec postgres pg_dump -U cotuser cotdb > backup.sql
docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/tmp/backup.dump

# 日志清理
docker system prune -f

# 更新应用
git pull origin main
docker-compose build
docker-compose up -d
```

## 🤝 开发贡献

### 代码规范
- **前端**: TypeScript + ESLint + Prettier
- **后端**: Python + Black + Flake8
- **提交**: 使用语义化提交信息
- **测试**: 新功能必须包含测试

### 开发流程
1. Fork 项目
2. 创建功能分支
3. 编写代码和测试
4. 提交 Pull Request
5. 代码审查和合并

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

---

**版本**: 1.0.0 MVP  
**更新日期**: 2025-01-17  
**维护团队**: COT Studio 开发团队

如有问题或建议，请提交 Issue 或联系开发团队。