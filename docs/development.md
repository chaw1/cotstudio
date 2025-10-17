# COT Studio MVP 开发指南

## 开发环境搭建

### 前置要求

- **Docker Desktop**: 20.10+ (必需)
- **Python 3.11+**: 后端开发
- **Node.js 18+**: 前端开发
- **Git**: 代码管理
- **内存**: 至少 8GB RAM (推荐 16GB)

### 快速开始

1. **克隆项目**
```bash
git clone <repository-url>
cd cotstudio
```

2. **配置环境**
```bash
# 复制环境配置
cp .env.example .env

# 编辑配置文件，设置 API 密钥
nano .env
```

3. **选择开发模式**

#### 方法一：完全 Docker (推荐新手)
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

#### 方法二：混合开发 (推荐开发者)
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

## 开发流程

### 前端开发

```bash
cd frontend

# 开发命令
npm run dev          # 启动开发服务器 (http://localhost:3000)
npm run build        # 构建生产版本
npm run preview      # 预览生产版本

# 测试命令
npm run test         # 运行测试
npm run test:ui      # 运行测试 UI
npm run test:coverage # 生成覆盖率报告

# 代码质量
npm run lint         # ESLint 检查
npm run lint:fix     # 自动修复 ESLint 问题
npm run type-check   # TypeScript 类型检查
```

### 后端开发

```bash
cd backend

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或 .\venv\Scripts\activate  # Windows

# 开发命令
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000  # 启动开发服务器
python -m app.main                                         # 直接运行

# 测试命令
pytest                           # 运行所有测试
pytest tests/unit/              # 运行单元测试
pytest tests/integration/       # 运行集成测试
pytest --cov=app tests/         # 生成覆盖率报告

# 代码质量
black .                         # 代码格式化
flake8 .                       # 代码检查
mypy app/                      # 类型检查
```

### 数据库操作

```bash
cd backend

# 数据库迁移
alembic revision --autogenerate -m "描述"  # 生成迁移文件
alembic upgrade head                       # 执行迁移
alembic downgrade -1                       # 回滚一个版本
alembic current                            # 查看当前版本
alembic history                            # 查看迁移历史

# 数据库连接
docker-compose exec postgres psql -U cotuser cotdb  # 连接 PostgreSQL
docker-compose exec neo4j cypher-shell -u neo4j -p neo4jpass  # 连接 Neo4j
```

## 代码规范

### 前端规范

- **TypeScript**: 使用严格模式，所有组件必须有类型定义
- **组件**: 使用函数式组件 + React Hooks
- **状态管理**: 使用 Zustand 进行全局状态管理
- **样式**: Ant Design + CSS Modules，遵循 BEM 命名规范
- **代码格式**: 使用 ESLint + Prettier 自动格式化
- **文件命名**: 
  - 组件: PascalCase (如 `UserProfile.tsx`)
  - 工具函数: camelCase (如 `apiClient.ts`)
  - 常量: UPPER_SNAKE_CASE (如 `API_ENDPOINTS.ts`)

### 后端规范

- **代码格式**: 使用 Black 进行自动格式化
- **代码风格**: 严格遵循 PEP 8 规范
- **类型注解**: 所有函数必须有 type hints
- **API 设计**: 遵循 RESTful 设计原则
- **异步编程**: 使用 async/await，避免阻塞操作
- **错误处理**: 使用自定义异常类，提供详细错误信息
- **文档**: 所有公共函数必须有 docstring

### 通用规范

- **提交信息**: 使用语义化提交 (feat, fix, docs, style, refactor, test, chore)
- **分支命名**: feature/功能名, bugfix/问题描述, hotfix/紧急修复
- **代码审查**: 所有 PR 必须经过代码审查
- **测试覆盖**: 新功能必须包含单元测试，覆盖率不低于 80%

## 测试策略

### 前端测试

```bash
cd frontend

# 单元测试 (Vitest)
npm run test                    # 运行所有测试
npm run test:watch             # 监视模式
npm run test:ui                # 测试 UI 界面

# 组件测试 (React Testing Library)
npm run test -- --grep "Component"

# 覆盖率报告
npm run test:coverage
```

**测试文件结构**:
```
src/
  components/
    Button/
      Button.tsx
      Button.test.tsx
  utils/
    apiClient.ts
    apiClient.test.ts
```

### 后端测试

```bash
cd backend

# 单元测试
pytest tests/unit/             # 单元测试
pytest tests/integration/      # 集成测试
pytest tests/e2e/             # 端到端测试

# 特定测试
pytest tests/unit/test_auth.py -v
pytest -k "test_login"

# 覆盖率报告
pytest --cov=app --cov-report=html tests/
```

**测试文件结构**:
```
tests/
  unit/
    test_auth.py
    test_models.py
  integration/
    test_api.py
    test_database.py
  e2e/
    test_complete_workflow.py
```

### 测试数据管理

- **前端**: 使用 MSW (Mock Service Worker) 模拟 API
- **后端**: 使用 pytest fixtures 和测试数据库
- **集成测试**: 使用 Docker 容器进行隔离测试

## 调试指南

### 前端调试

1. **浏览器开发者工具**
   - Console: 查看日志和错误
   - Network: 监控 API 请求
   - Application: 检查 localStorage 和 sessionStorage

2. **React DevTools**
   - 安装 React DevTools 浏览器扩展
   - 检查组件状态和 props
   - 性能分析

3. **Vite 调试**
   ```bash
   # 启用详细日志
   npm run dev -- --debug
   
   # 清除缓存
   rm -rf node_modules/.vite
   ```

### 后端调试

1. **开发服务器调试**
   ```bash
   # 启用调试模式
   uvicorn app.main:app --reload --log-level debug
   
   # 使用 pdb 断点
   import pdb; pdb.set_trace()
   ```

2. **API 文档和测试**
   - 访问 http://localhost:8000/docs (Swagger UI)
   - 访问 http://localhost:8000/redoc (ReDoc)
   - 使用 curl 或 Postman 测试 API

3. **日志调试**
   ```python
   import logging
   logger = logging.getLogger(__name__)
   logger.debug("调试信息")
   logger.info("普通信息")
   logger.error("错误信息")
   ```

### 数据库调试

```bash
# PostgreSQL 调试
docker-compose exec postgres psql -U cotuser cotdb
\dt  # 查看表
\d users  # 查看表结构

# Neo4j 调试
docker-compose exec neo4j cypher-shell -u neo4j -p neo4jpass
MATCH (n) RETURN count(n);  # 查看节点数量
```

## 性能优化

### 前端性能

1. **代码分割**
   ```typescript
   // 懒加载组件
   const LazyComponent = lazy(() => import('./LazyComponent'));
   ```

2. **缓存优化**
   ```typescript
   // 使用 React.memo
   const MemoizedComponent = memo(Component);
   
   // 使用 useMemo 和 useCallback
   const memoizedValue = useMemo(() => computeExpensiveValue(a, b), [a, b]);
   ```

### 后端性能

1. **数据库优化**
   ```python
   # 使用索引
   # 批量操作
   # 连接池配置
   ```

2. **缓存策略**
   ```python
   # Redis 缓存
   # 内存缓存
   # 查询结果缓存
   ```

## 常见问题

### 端口冲突
```bash
# 查找占用端口的进程
netstat -tulpn | grep :3000
lsof -i :3000

# 杀死进程
kill -9 <PID>
```

### 依赖问题
```bash
# 前端依赖问题
cd frontend
rm -rf node_modules package-lock.json
npm install

# 后端依赖问题
cd backend
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Docker 问题
```bash
# 清理 Docker 资源
docker system prune -f
docker volume prune -f

# 重建容器
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 开发工具推荐

### IDE 和编辑器
- **VS Code**: 推荐插件
  - Python
  - TypeScript and JavaScript
  - ES7+ React/Redux/React-Native snippets
  - Prettier
  - ESLint
  - Docker

### 浏览器扩展
- React Developer Tools
- Redux DevTools
- JSON Viewer

### 命令行工具
- **httpie**: HTTP 客户端
- **jq**: JSON 处理工具
- **docker-compose**: 容器编排

---

更多详细信息请参考 [项目指南](../PROJECT_GUIDE.md) 和 [故障排除指南](TROUBLESHOOTING.md)。