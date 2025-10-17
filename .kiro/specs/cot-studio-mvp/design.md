# COT Studio MVP 设计文档

## 概述

COT Studio MVP 是一个基于微服务架构的全栈应用，采用 FastAPI + React + TypeScript 技术栈。系统设计遵循模块化、可扩展和可维护的原则，支持异步任务处理、多模型集成和知识图谱管理。

## 架构

### 整体架构

```mermaid
graph TB
    subgraph "前端层"
        UI[React + TypeScript + Ant Design]
        VIS[知识图谱可视化 Cytoscape.js]
        DND[拖拽组件 React DnD]
    end
    
    subgraph "API网关层"
        GW[Nginx/Traefik]
        AUTH[JWT认证]
    end
    
    subgraph "应用服务层"
        API[FastAPI主服务]
        WORKER[Celery异步任务]
        WS[WebSocket服务]
    end
    
    subgraph "AI服务层"
        OCR[OCR服务集群]
        LLM[LLM编排服务]
        KG[知识图谱抽取]
        EMB[向量嵌入服务]
    end
    
    subgraph "存储层"
        OBJ[MinIO对象存储]
        DB[PostgreSQL]
        NEO[Neo4j图数据库]
        VDB[向量数据库]
        REDIS[Redis缓存]
    end
    
    UI --> GW
    GW --> API
    API --> WORKER
    API --> OCR
    API --> LLM
    WORKER --> KG
    WORKER --> EMB
    API --> DB
    KG --> NEO
    EMB --> VDB
    API --> OBJ
    API --> REDIS
```

### 技术栈选择

**前端技术栈:**
- **React 18** + **TypeScript** - 类型安全的组件化开发
- **Vite** - 快速构建工具，支持热重载
- **Ant Design 5** - 企业级UI组件库
- **Zustand** - 轻量级状态管理
- **Cytoscape.js** - 知识图谱可视化
- **React DnD** - 拖拽功能实现
- **Axios** - HTTP客户端

**后端技术栈:**
- **FastAPI** - 高性能异步Web框架
- **SQLAlchemy** - ORM框架
- **Celery** + **RabbitMQ** - 异步任务队列
- **Pydantic** - 数据验证
- **LangChain** - LLM编排框架

**存储技术栈:**
- **PostgreSQL** - 主数据库
- **Neo4j** - 知识图谱存储
- **MinIO** - 对象存储
- **Redis** - 缓存和会话存储
- **Milvus/Qdrant** - 向量数据库

## 组件和接口

### 前端组件架构

```typescript
// 主要组件结构
src/
├── components/
│   ├── common/           // 通用组件
│   ├── project/          // 项目管理组件
│   ├── upload/           // 文件上传组件
│   ├── annotation/       // 标注界面组件
│   ├── knowledge-graph/  // KG可视化组件
│   └── export/           // 导出组件
├── pages/
│   ├── Dashboard.tsx
│   ├── ProjectDetail.tsx
│   ├── AnnotationWorkspace.tsx
│   └── Settings.tsx
├── hooks/                // 自定义Hooks
├── services/             // API服务
├── stores/               // Zustand状态管理
└── types/                // TypeScript类型定义
```

### 后端服务架构

```python
# 主要服务模块
app/
├── api/
│   ├── v1/
│   │   ├── projects.py      # 项目管理API
│   │   ├── files.py         # 文件管理API
│   │   ├── ocr.py           # OCR处理API
│   │   ├── annotation.py    # 标注API
│   │   ├── knowledge_graph.py # KG API
│   │   └── export.py        # 导出API
├── core/
│   ├── config.py           # 配置管理
│   ├── security.py         # 安全认证
│   └── database.py         # 数据库连接
├── models/                 # SQLAlchemy模型
├── schemas/                # Pydantic模式
├── services/               # 业务逻辑服务
├── workers/                # Celery任务
└── utils/                  # 工具函数
```

### 核心接口设计

**项目管理接口:**
```python
# POST /api/v1/projects
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str]
    tags: List[str] = []

# GET /api/v1/projects/{project_id}
class ProjectResponse(BaseModel):
    id: UUID
    name: str
    owner: str
    status: ProjectStatus
    created_at: datetime
    file_count: int
    cot_count: int
```

**文件上传接口:**
```python
# POST /api/v1/projects/{project_id}/upload
class FileUploadResponse(BaseModel):
    file_id: UUID
    filename: str
    size: int
    mime_type: str
    ocr_status: OCRStatus
```

**标注接口:**
```python
# POST /api/v1/cot/create
class COTCreate(BaseModel):
    project_id: UUID
    slice_id: UUID
    question: str
    candidates: List[COTCandidate]

class COTCandidate(BaseModel):
    text: str
    chain_of_thought: str
    score: float = Field(ge=0.0, le=1.0)
    chosen: bool = False
    rank: int
```

## 数据模型

### 核心数据模型

```python
# 项目模型
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    description = Column(Text)
    tags = Column(ARRAY(String))
    project_type = Column(Enum(ProjectType))
    status = Column(Enum(ProjectStatus))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

# 文件模型
class File(Base):
    __tablename__ = "files"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    project_id = Column(UUID, ForeignKey("projects.id"))
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_hash = Column(String, nullable=False)
    size = Column(BigInteger)
    mime_type = Column(String)
    ocr_status = Column(Enum(OCRStatus))
    created_at = Column(DateTime, default=datetime.utcnow)

# 切片模型
class Slice(Base):
    __tablename__ = "slices"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    file_id = Column(UUID, ForeignKey("files.id"))
    content = Column(Text, nullable=False)
    start_offset = Column(Integer)
    end_offset = Column(Integer)
    slice_type = Column(Enum(SliceType))  # paragraph, image, table
    page_number = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

# CoT数据模型
class COTItem(Base):
    __tablename__ = "cot_items"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    project_id = Column(UUID, ForeignKey("projects.id"))
    slice_id = Column(UUID, ForeignKey("slices.id"))
    question = Column(Text, nullable=False)
    chain_of_thought = Column(Text)
    source = Column(Enum(COTSource))  # manual, human_ai, generalization
    status = Column(Enum(COTStatus))  # draft, reviewed, approved
    llm_metadata = Column(JSON)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# CoT候选答案模型
class COTCandidate(Base):
    __tablename__ = "cot_candidates"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    cot_item_id = Column(UUID, ForeignKey("cot_items.id"))
    text = Column(Text, nullable=False)
    chain_of_thought = Column(Text)
    score = Column(Float, default=0.0)
    chosen = Column(Boolean, default=False)
    rank = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Neo4j 知识图谱模型

```cypher
// 实体节点
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;

// 文档节点
CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;

// 概念节点
CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE;

// 关系类型
// (:Entity)-[:MENTIONED_IN]->(:Document)
// (:Entity)-[:RELATED_TO]->(:Entity)
// (:Concept)-[:DERIVED_FROM]->(:Document)
// (:COTItem)-[:REFERENCES]->(:Entity)
```

## 错误处理

### 异常处理策略

```python
# 自定义异常类
class COTStudioException(Exception):
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class FileProcessingError(COTStudioException):
    pass

class OCRProcessingError(COTStudioException):
    pass

class LLMServiceError(COTStudioException):
    pass

# 全局异常处理器
@app.exception_handler(COTStudioException)
async def cot_studio_exception_handler(request: Request, exc: COTStudioException):
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.error_code or "GENERAL_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### 错误恢复机制

1. **文件上传失败**: 支持断点续传和重试机制
2. **OCR处理失败**: 自动降级到备用OCR引擎
3. **LLM调用失败**: 实现重试和熔断机制
4. **数据库连接失败**: 连接池管理和自动重连
5. **任务队列失败**: 死信队列和任务重试

## 测试策略

### 测试架构

```python
# 测试目录结构
tests/
├── unit/                   # 单元测试
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/            # 集成测试
│   ├── test_api.py
│   ├── test_ocr.py
│   └── test_knowledge_graph.py
├── e2e/                    # 端到端测试
│   ├── test_upload_flow.py
│   ├── test_annotation_flow.py
│   └── test_export_flow.py
├── fixtures/               # 测试数据
└── conftest.py            # pytest配置
```

### 测试覆盖率目标

- **单元测试覆盖率**: ≥ 80%
- **API测试覆盖率**: ≥ 90%
- **关键业务流程**: 100%

### 测试数据管理

```python
# 测试数据工厂
class ProjectFactory:
    @staticmethod
    def create_test_project() -> Project:
        return Project(
            name="Test Project",
            owner="test_user",
            description="Test project for unit tests",
            tags=["test"],
            project_type=ProjectType.STANDARD
        )

# 测试数据库配置
@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///test.db")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
```

### 性能测试

```python
# 性能测试用例
class TestPerformance:
    def test_file_upload_performance(self):
        # 测试大文件上传性能
        pass
    
    def test_ocr_processing_performance(self):
        # 测试OCR处理性能
        pass
    
    def test_knowledge_graph_query_performance(self):
        # 测试KG查询性能
        pass
```

## 安全考虑

### 认证和授权

```python
# JWT认证配置
class SecurityConfig:
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7

# 权限装饰器
def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 权限检查逻辑
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### 数据安全

1. **数据加密**: 敏感数据使用AES-256加密存储
2. **传输安全**: 所有API通信使用HTTPS/TLS
3. **文件安全**: 上传文件进行病毒扫描和格式验证
4. **访问控制**: 基于角色的访问控制(RBAC)
5. **审计日志**: 所有操作记录审计日志

### 输入验证

```python
# 输入验证模式
class FileUploadSchema(BaseModel):
    filename: str = Field(..., regex=r'^[a-zA-Z0-9._-]+$')
    size: int = Field(..., gt=0, le=100*1024*1024)  # 最大100MB
    mime_type: str = Field(..., regex=r'^[a-zA-Z0-9]+/[a-zA-Z0-9.-]+$')
    
    @validator('filename')
    def validate_filename(cls, v):
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Invalid filename')
        return v
```

## 部署架构

### Docker Compose 开发环境

```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
    
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/cotdb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
      - neo4j
    
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: cotdb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  neo4j:
    image: neo4j:5.0
    environment:
      NEO4J_AUTH: neo4j/password
    ports:
      - "7474:7474"
      - "7687:7687"
    
  redis:
    image: redis:7-alpine
    
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    
  celery:
    build: ./backend
    command: celery -A app.worker worker --loglevel=info
    depends_on:
      - redis
      - postgres
```

### 生产环境建议

1. **容器编排**: Kubernetes + Helm Charts
2. **负载均衡**: Nginx Ingress Controller
3. **数据库**: 托管PostgreSQL + Neo4j Aura
4. **对象存储**: AWS S3 或 阿里云OSS
5. **监控**: Prometheus + Grafana + ELK Stack
6. **CI/CD**: GitHub Actions + ArgoCD

## 性能优化

### 前端优化

1. **代码分割**: React.lazy + Suspense
2. **缓存策略**: React Query + Service Worker
3. **虚拟化**: 大列表使用react-window
4. **图片优化**: WebP格式 + 懒加载

### 后端优化

1. **数据库优化**: 索引优化 + 查询优化
2. **缓存策略**: Redis缓存 + CDN
3. **异步处理**: Celery任务队列
4. **连接池**: SQLAlchemy连接池管理

### 扩展性设计

1. **水平扩展**: 无状态服务设计
2. **微服务**: 按功能模块拆分服务
3. **消息队列**: 解耦服务间通信
4. **数据分片**: 大数据量分库分表