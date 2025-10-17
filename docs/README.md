# COT Studio MVP 文档

## 目录结构

### 用户文档
- [用户使用指南](./user-guide.md) - 完整的用户操作指南
- [API文档](./api.md) - 后端API接口文档和SDK使用

### 部署和运维
- [部署指南](./deployment.md) - 开发和生产环境部署说明
- [故障排除指南](./troubleshooting.md) - 常见问题诊断和解决方案
- [维护指南](./maintenance.md) - 系统维护、监控和备份策略

### 开发文档
- [开发指南](./development.md) - 开发环境搭建和开发流程
- [架构设计](./architecture.md) - 系统架构和技术选型

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Git

### 本地开发

1. 克隆项目
```bash
git clone <repository-url>
cd cot-studio-mvp
```

2. 启动开发环境
```bash
make dev
```

3. 访问应用
- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### 使用Docker

```bash
# 构建并启动所有服务
make docker-up

# 查看服务状态
docker-compose ps

# 查看日志
make docker-logs

# 停止服务
make docker-down
```

## 项目结构

```
cot-studio-mvp/
├── frontend/          # React + TypeScript 前端
├── backend/           # FastAPI 后端
├── docker/            # Docker 配置文件
├── docs/              # 项目文档
├── .github/           # GitHub Actions CI/CD
├── docker-compose.yml # 开发环境配置
├── Makefile          # 构建脚本
└── README.md
```