# 更新日志

## [1.1.0] - 2025-09-15

### 🎉 新增功能

#### 开发脚本增强
- **新增**: `scripts/dev-start.ps1` - 开发环境快速启动脚本
- **新增**: `scripts/fix-dependencies.ps1` - 依赖问题修复脚本
- **新增**: `scripts/install-backend.ps1` - 专门的后端安装脚本
- **新增**: `scripts/test-frontend.ps1` - 前端依赖测试脚本
- **新增**: `scripts/verify-environment.ps1` - 完整环境验证脚本
- **新增**: `scripts/fix-python313.ps1` - Python 3.13 兼容性修复脚本
- **新增**: `scripts/fix-backend-issues.ps1` - 后端问题综合修复脚本
- **新增**: `scripts/quick-auth-test.ps1` - 认证系统快速测试脚本
- **新增**: `scripts/test-neo4j-connection.ps1` - Neo4j 连接测试和修复脚本
- **新增**: `scripts/restart-backend.ps1` - 后端服务重启脚本
- **新增**: `scripts/fix-local-dev-config.ps1` - 本地开发环境配置修复脚本
- **增强**: `scripts/setup.ps1` - 添加 `-DevMode` 参数支持开发模式

#### 前端认证系统
- **新增**: 完整的用户认证流程
  - 登录页面组件 (`Login.tsx`)
  - 认证服务 (`authService.ts`)
  - 路由保护组件 (`ProtectedRoute.tsx`)
  - 用户登出功能
- **新增**: 前端环境变量配置 (`frontend/.env`)
- **修复**: Vite 代理配置，正确转发 API 请求到后端
- **修复**: Neo4j 连接失败问题
  - 统一 `.env`、`docker-compose.yml` 和 `backend/config.py` 中的密码配置
  - 修复后端配置文件中的硬编码凭据和主机名问题
  - 本地开发环境使用 `localhost` 而不是 Docker 内部主机名
  - 添加 Neo4j 连接测试和诊断工具
  - 修复 MinIO 和 RabbitMQ 配置以匹配 Docker Compose 设置

#### 文档完善
- **新增**: `docs/LOCAL_DEVELOPMENT.md` - 详细的本地开发指南
- **新增**: `docs/TROUBLESHOOTING.md` - 故障排除指南
- **新增**: `docs/INSTALLATION.md` - 完整安装指南
- **更新**: `README.md` - 改进快速开始指南和认证说明

### 🔧 问题修复

#### PowerShell 兼容性
- **修复**: `Join-String` cmdlet 兼容性问题，改用 `-join` 操作符
- **修复**: 健康检查逻辑，使用正则表达式替代 JSON 解析
- **修复**: 中文字符编码问题，统一使用英文

#### Docker Compose 配置
- **修复**: 自动移除过时的 `version` 属性
- **修复**: Neo4j 镜像版本更新为 `latest`
- **修复**: Neo4j 内存配置兼容性问题

#### 依赖管理
- **更新**: Pillow 版本升级到 11.3.0，支持 Python 3.13
- **恢复**: 启用所有后端依赖，移除不必要的简化
- **修复**: 前端添加缺失的 `recharts` 依赖
- **修复**: 前端添加缺失的 Cytoscape 布局算法依赖
  - `cytoscape-cola@^2.5.1`
  - `cytoscape-cose-bilkent@^4.1.0`
  - `cytoscape-dagre@^2.5.0`
- **新增**: 分层安装策略解决 pyproject.toml 构建问题
  - `requirements-core.txt`: 核心依赖，安装稳定
  - `requirements-problematic.txt`: 问题包，单独处理
- **修复**: psycopg2-binary, asyncpg, yara-python, tiktoken 安装问题
- **修复**: Python 3.13 兼容性问题，替换 python-jose 为 PyJWT
- **修复**: 缺失的 ResponseModel 类，添加到 common schemas
- **修复**: 导入路径错误，统一使用 middleware.auth 中的 get_current_user
- **修复**: Celery 任务中的异步语法错误，移除不当的 await 使用
- **修复**: Pydantic v2 兼容性，将 regex 参数替换为 pattern
- **修复**: 命名冲突，解决 settings 导入冲突问题

### 🚀 改进优化

#### 安装流程
- **优化**: 分阶段启动策略，优先启动基础设施服务
- **增强**: 代理配置支持，适配企业网络环境
- **改进**: 错误处理和用户反馈

#### 开发体验
- **新增**: 开发模式支持，仅启动基础设施服务
- **优化**: 虚拟环境自动创建和管理
- **改进**: 环境变量自动配置

#### 服务监控
- **增强**: 健康检查机制，更准确的状态检测
- **改进**: 服务状态展示，清晰的运行状态信息
- **优化**: 日志输出，更友好的用户提示

### 📋 使用指南

#### 新用户
```powershell
# 完整安装
.\scripts\setup.ps1

# 开发环境
.\scripts\setup.ps1 -DevMode
.\scripts\dev-start.ps1 -All
```

#### 现有用户
```powershell
# 修复依赖问题
.\scripts\fix-dependencies.ps1 -All

# 快速启动开发环境
.\scripts\dev-start.ps1 -Infrastructure
```

### 🔄 迁移说明

#### 从 v1.0.0 升级
1. **更新脚本**: 所有脚本已自动修复兼容性问题
2. **依赖更新**: 后端依赖已更新，建议重新安装
3. **配置修复**: Docker Compose 配置会自动修复

#### 环境要求变更
- **Python**: 现在完全支持 Python 3.13
- **Pillow**: 升级到 11.3.0 版本
- **Node.js**: 推荐使用 18.x 或 20.x

### 🐛 已知问题

#### 网络相关
- **问题**: 企业网络环境可能需要代理配置
- **解决**: 使用 `-NoProxy` 参数或手动配置代理

#### 平台兼容性
- **问题**: 某些 OCR 相关包在特定环境下可能安装失败
- **解决**: 脚本会自动跳过问题包，不影响核心功能

### 📚 相关文档

- [安装指南](INSTALLATION.md)
- [本地开发](LOCAL_DEVELOPMENT.md)
- [故障排除](TROUBLESHOOTING.md)
- [项目概览](../README.md)

---

## [1.0.0] - 2025-09-15

### 🎉 初始版本

#### 核心功能
- COT Studio MVP 基础架构
- Docker Compose 多服务部署
- 前后端分离架构
- 基础设施服务集成

#### 服务组件
- **前端**: React + TypeScript + Vite
- **后端**: FastAPI + Python
- **数据库**: PostgreSQL + Neo4j + Redis
- **存储**: MinIO 对象存储
- **队列**: RabbitMQ + Celery
- **监控**: Flower

#### 安装脚本
- Windows PowerShell 安装脚本
- 自动环境配置
- 服务健康检查
- 基础错误处理

---

**版本说明**:
- **主版本号**: 重大架构变更或不兼容更新
- **次版本号**: 新功能添加或重要改进
- **修订版本号**: 问题修复和小幅优化