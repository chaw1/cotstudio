# COT Studio MVP 交付包文档

## 项目概述

COT Studio MVP 是一个端到端的交互式平台，旨在帮助研究者和工程团队以高质量、可验证和可追溯的方式构建、泛化和合成 Chain-of-Thought (CoT) 数据集。

## 交付内容

### 1. 核心系统组件

#### 后端服务 (FastAPI)
- **位置**: `backend/`
- **功能**: RESTful API服务，处理项目管理、文件上传、OCR处理、CoT生成、知识图谱抽取等核心业务逻辑
- **技术栈**: FastAPI, SQLAlchemy, Celery, PostgreSQL, Neo4j, Redis, MinIO

#### 前端应用 (React + TypeScript)
- **位置**: `frontend/`
- **功能**: 用户界面，提供项目管理、文件上传、标注工作台、知识图谱可视化等功能
- **技术栈**: React 18, TypeScript, Ant Design, Zustand, Cytoscape.js

#### 数据库设计
- **PostgreSQL**: 主数据存储，包含项目、文件、切片、CoT数据等
- **Neo4j**: 知识图谱存储，实体和关系数据
- **Redis**: 缓存和会话管理
- **MinIO**: 对象存储，文件存储

### 2. 部署配置

#### Docker容器化
- **位置**: `docker-compose.yml`, `docker-compose.prod.yml`
- **功能**: 一键部署整个系统，包含所有依赖服务
- **服务**: 前端、后端、数据库、缓存、对象存储、消息队列

#### 环境配置
- **开发环境**: `docker-compose.yml`
- **生产环境**: `docker-compose.prod.yml`
- **环境变量**: `.env.example`

### 3. 测试套件

#### 后端测试
- **位置**: `backend/tests/`
- **覆盖**: 单元测试、集成测试、性能测试
- **工具**: pytest, pytest-cov, pytest-asyncio

#### 前端测试
- **位置**: `frontend/src/test/`
- **覆盖**: 组件测试、集成测试、E2E测试
- **工具**: Vitest, Testing Library, MSW

#### 系统集成测试
- **位置**: `backend/tests/integration/test_system_integration.py`
- **覆盖**: 完整业务流程测试，端到端工作流验证

#### 性能基准测试
- **位置**: `backend/tests/benchmark.py`
- **覆盖**: API响应时间、并发处理、内存使用、数据库性能

### 4. 文档资料

#### 技术文档
- **API文档**: 自动生成的OpenAPI文档 (`/docs`)
- **部署文档**: `docs/deployment.md`
- **开发文档**: `docs/development.md`
- **用户指南**: `docs/user-guide.md`

#### 测试文档
- **测试策略**: `test-documentation.md`
- **测试报告**: 自动生成的测试覆盖率报告

### 5. 演示数据

#### 示例项目
- **位置**: `demo-data/sample-project.json`
- **内容**: 完整的演示项目，包含文件、切片、CoT数据、知识图谱

#### 使用示例
- **位置**: `demo-data/usage-examples.md`
- **内容**: 详细的使用教程和API示例

## 功能特性

### 已实现功能 ✅

#### 1. 项目与文件管理
- [x] 项目创建、编辑、删除
- [x] 多格式文件上传 (PDF, Word, TXT, Markdown, LaTeX, JSON)
- [x] 文件存储和管理
- [x] 项目权限控制

#### 2. OCR与文档处理
- [x] 多OCR引擎支持 (PaddleOCR, 阿里云等)
- [x] 自动文档切片 (按段落、图片、表格、页码)
- [x] 切片与原文位置映射
- [x] 异步OCR处理

#### 3. CoT数据生成与标注
- [x] LLM集成 (OpenAI, DeepSeek等)
- [x] 自动问题生成
- [x] 候选答案生成 (3-5个CoT格式)
- [x] 拖拽排序界面
- [x] 评分系统 (0-1分，精度0.1)
- [x] Chosen标记功能

#### 4. 知识图谱
- [x] 实体关系抽取
- [x] Neo4j图数据库存储
- [x] 可视化界面 (Cytoscape.js)
- [x] 图谱查询和过滤
- [x] 向量嵌入生成

#### 5. 数据导出导入
- [x] 多格式导出 (JSON, Markdown, LaTeX, TXT)
- [x] 项目包生成
- [x] 数据导入功能
- [x] 差异比对

#### 6. 系统管理
- [x] 用户认证和权限
- [x] 审计日志
- [x] 异步任务监控
- [x] 系统配置管理
- [x] 性能监控

### 技术指标

#### 性能指标
- **API响应时间**: P95 < 2秒, P99 < 5秒
- **文件上传**: 支持最大100MB文件
- **并发处理**: 支持10个并发请求
- **内存使用**: 基础运行 < 2GB

#### 测试覆盖率
- **后端单元测试**: > 80%
- **前端组件测试**: > 75%
- **API集成测试**: > 90%
- **关键业务流程**: 100%

#### 可靠性指标
- **系统可用性**: > 99%
- **数据一致性**: 强一致性保证
- **错误恢复**: 自动重试和降级机制
- **监控告警**: 完整的监控体系

## 部署说明

### 系统要求

#### 最低配置
- **CPU**: 4核心
- **内存**: 8GB RAM
- **存储**: 50GB可用空间
- **网络**: 稳定的互联网连接

#### 推荐配置
- **CPU**: 8核心
- **内存**: 16GB RAM
- **存储**: 100GB SSD
- **网络**: 高速互联网连接

### 快速部署

#### 1. 环境准备
```bash
# 安装Docker和Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 克隆项目
git clone <repository-url>
cd cot-studio
```

#### 2. 配置环境
```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件
nano .env
```

#### 3. 启动服务
```bash
# 开发环境
docker-compose up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d

# 或使用Make命令
make start
```

#### 4. 验证部署
```bash
# 检查服务状态
docker-compose ps

# 访问应用
# 前端: http://localhost:3000
# 后端: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 生产环境配置

#### 1. 安全配置
- 修改默认密码和密钥
- 配置HTTPS证书
- 设置防火墙规则
- 启用访问日志

#### 2. 性能优化
- 配置数据库连接池
- 启用Redis缓存
- 配置CDN加速
- 设置负载均衡

#### 3. 监控配置
- 配置日志收集
- 设置性能监控
- 配置告警通知
- 定期备份数据

## 测试验证

### 运行测试套件

#### 后端测试
```bash
cd backend

# 运行所有测试
python tests/test_runner.py

# 运行特定类型测试
python tests/test_runner.py unit
python tests/test_runner.py integration
python tests/test_runner.py performance

# 运行性能基准测试
python tests/benchmark.py
```

#### 前端测试
```bash
cd frontend

# 运行所有测试
npm run test

# 运行E2E测试
npm run test:e2e

# 生成覆盖率报告
npm run test:coverage
```

#### 系统验证
```bash
# 运行完整验证
python validate-tests.py

# 检查系统健康状态
curl http://localhost:8000/health
```

### 测试报告

测试执行后会生成以下报告：
- **覆盖率报告**: `htmlcov/index.html`
- **性能报告**: `test-results/benchmark-report.json`
- **测试摘要**: `test-results/test-report.json`

## 使用指南

### 快速开始

1. **创建项目**: 访问前端界面，点击"创建项目"
2. **上传文件**: 拖拽或选择文件上传
3. **OCR处理**: 选择OCR引擎，开始文档处理
4. **CoT标注**: 选择切片，生成和标注CoT数据
5. **知识图谱**: 查看自动抽取的知识图谱
6. **数据导出**: 选择格式，导出完整数据包

### API使用

详细的API使用示例请参考：
- **API文档**: http://localhost:8000/docs
- **使用示例**: `demo-data/usage-examples.md`

## 维护支持

### 日常维护

#### 1. 数据备份
```bash
# 备份数据库
docker-compose exec postgres pg_dump -U postgres cotdb > backup.sql

# 备份Neo4j
docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/backups/

# 备份文件存储
docker-compose exec minio mc mirror /data /backups/minio/
```

#### 2. 日志管理
```bash
# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 清理日志
docker system prune -f
```

#### 3. 性能监控
```bash
# 检查资源使用
docker stats

# 检查数据库性能
docker-compose exec postgres psql -U postgres -c "SELECT * FROM pg_stat_activity;"
```

### 故障排除

常见问题和解决方案请参考：
- **故障排除指南**: `docs/troubleshooting.md`
- **维护手册**: `docs/maintenance.md`

## 扩展开发

### 自定义扩展

系统支持以下扩展：
- **自定义OCR引擎**: 实现OCREngine接口
- **自定义LLM提供商**: 实现LLMProvider接口
- **自定义导出格式**: 实现ExportFormat接口
- **自定义知识抽取**: 实现KGExtractor接口

### 开发环境

详细的开发环境搭建请参考：
- **开发指南**: `docs/development.md`
- **API参考**: `docs/api.md`

## 版本信息

- **版本**: 1.0.0 MVP
- **发布日期**: 2024-01-01
- **兼容性**: Docker 20.10+, Node.js 18+, Python 3.11+

## 联系支持

如有问题或需要支持，请：
1. 查阅文档和FAQ
2. 检查GitHub Issues
3. 联系技术支持团队

---

**注意**: 本交付包包含完整的COT Studio MVP系统，已通过全面测试验证。请按照部署说明进行安装和配置。