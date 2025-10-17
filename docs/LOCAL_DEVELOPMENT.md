# 本地开发指南

## 环境准备

### Python 版本建议
- **推荐**: Python 3.11
- **支持**: Python 3.10 - 3.12
- **注意**: Python 3.13 可能有兼容性问题

### Node.js 版本建议
- **推荐**: Node.js 18.x 或 20.x
- **最低**: Node.js 16.x

## 快速开始

### 1. 启动基础设施服务
```powershell
# 确保 Docker 服务正常运行
docker-compose up -d postgres redis neo4j minio rabbitmq
```

### 2. 后端开发环境

#### 方法一：使用安装脚本 (推荐)
```powershell
# 使用专门的后端安装脚本
.\scripts\install-backend.ps1

# 启动开发服务器
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 方法二：手动安装
```powershell
cd backend

# 创建虚拟环境
python -m venv venv
.\venv\Scripts\activate

# 升级 pip 和构建工具
python -m pip install --upgrade pip setuptools wheel

# 分层安装策略
pip install -r requirements-core.txt
pip install psycopg2-binary asyncpg yara-python tiktoken --no-build-isolation

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 问题包处理策略
如果遇到 `pyproject.toml` 构建问题：

```powershell
# 策略1: 禁用构建隔离
pip install <package> --no-build-isolation

# 策略2: 仅使用二进制包
pip install <package> --only-binary=all

# 策略3: 逐个安装问题包
pip install psycopg2-binary --only-binary=all
pip install asyncpg --no-build-isolation
pip install yara-python --no-build-isolation
pip install tiktoken --no-build-isolation
```

### 3. 前端开发环境

```powershell
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

如果 `npm install` 失败：
```powershell
# 清理缓存
npm cache clean --force
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

## 环境配置

### 后端环境变量
创建 `backend/.env` 文件：
```env
# 数据库连接（使用 Docker 服务）
DATABASE_URL=postgresql://cotuser:cotpass@localhost:5432/cotdb
REDIS_URL=redis://localhost:6379
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4jpass

# MinIO 配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123

# RabbitMQ 配置
RABBITMQ_URL=amqp://cotuser:cotpass@localhost:5672/

# JWT 配置
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# LLM API 配置
OPENAI_API_KEY=your_openai_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 开发模式
DEBUG=true
LOG_LEVEL=DEBUG
```

### 前端环境变量
创建 `frontend/.env` 文件：
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 开发工作流

### 1. 日常开发
```powershell
# 启动基础设施
docker-compose up -d postgres redis neo4j minio rabbitmq

# 启动后端（终端1）
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload

# 启动前端（终端2）
cd frontend
npm run dev
```

### 2. 数据库操作
```powershell
# 进入后端目录
cd backend
.\venv\Scripts\activate

# 创建迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 3. 测试
```powershell
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm test
```

## 常见问题解决

### 后端问题

#### 1. Pillow 安装失败
```powershell
# 升级 pip 和安装工具
pip install --upgrade pip setuptools wheel

# 重新安装 Pillow
pip install Pillow==11.3.0

# 如果仍有问题，尝试预编译版本
pip install --only-binary=Pillow Pillow==11.3.0
```

#### 2. PaddlePaddle 安装失败
```powershell
# PaddlePaddle 需要特定的安装方式
pip install paddlepaddle==2.5.2 -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 或使用官方源
pip install paddlepaddle==2.5.2 -f https://www.paddlepaddle.org.cn/whl/windows/mkl/avx/stable.html
```

#### 3. 数据库连接失败
```powershell
# 检查 Docker 服务状态
docker-compose ps

# 重启数据库服务
docker-compose restart postgres

# 检查连接
docker-compose exec postgres psql -U cotuser -d cotdb -c "SELECT 1;"
```

### 前端问题

#### 1. recharts 依赖缺失
```powershell
# 安装缺失依赖
npm install recharts

# 或重新安装所有依赖
rm -rf node_modules package-lock.json
npm install
```

#### 2. Vite 构建错误
```powershell
# 清理缓存
npm run build -- --force

# 检查 TypeScript 错误
npx tsc --noEmit
```

#### 3. 端口冲突
```powershell
# 修改前端端口
# 在 vite.config.ts 中添加：
# server: { port: 3001 }
```

## 性能优化

### 开发模式优化
1. **后端热重载**: 使用 `--reload` 参数
2. **前端 HMR**: Vite 自动支持
3. **数据库连接池**: 开发环境使用较小的连接池

### 内存使用优化
```powershell
# 限制 Node.js 内存使用
$env:NODE_OPTIONS="--max-old-space-size=4096"
npm run dev
```

## 调试技巧

### 后端调试
```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用 IDE 调试器
# VS Code: 配置 launch.json
```

### 前端调试
```javascript
// 浏览器开发者工具
console.log('Debug info:', data);

// React DevTools
// 安装浏览器扩展
```

### 数据库调试
```powershell
# 查看 SQL 日志
# 在 SQLAlchemy 配置中启用 echo=True

# 直接连接数据库
docker-compose exec postgres psql -U cotuser -d cotdb
```

## 代码质量

### 后端代码检查
```powershell
cd backend

# 格式化代码
black .
isort .

# 代码检查
flake8 .

# 类型检查（如果使用 mypy）
mypy .
```

### 前端代码检查
```powershell
cd frontend

# ESLint 检查
npm run lint

# 类型检查
npx tsc --noEmit

# 格式化（如果使用 Prettier）
npx prettier --write .
```

## 部署准备

### 构建生产版本
```powershell
# 后端：确保所有依赖都能正常安装
pip install -r requirements.txt

# 前端：构建生产版本
cd frontend
npm run build
```

### 环境变量检查
确保生产环境变量已正确配置：
- 数据库连接字符串
- API 密钥
- 安全密钥
- 服务端点

---

**提示**: 如果遇到依赖问题，优先使用 `requirements-dev.txt` 进行开发，功能完整性可以后续补充。