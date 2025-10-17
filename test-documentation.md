# COT Studio MVP 系统集成测试文档

## 概述

本文档描述了 COT Studio MVP 的完整测试策略，包括端到端测试、集成测试、性能测试和负载测试的实施方案。

## 测试架构

### 测试分层

```
┌─────────────────────────────────────┐
│           E2E Tests                 │  ← 用户完整流程测试
├─────────────────────────────────────┤
│        Integration Tests            │  ← 服务间集成测试
├─────────────────────────────────────┤
│          Unit Tests                 │  ← 单元功能测试
├─────────────────────────────────────┤
│       Performance Tests             │  ← 性能基准测试
└─────────────────────────────────────┘
```

### 测试覆盖范围

#### 1. 端到端测试 (E2E Tests)
- **完整业务流程测试**
  - 项目创建 → 文件上传 → OCR处理 → 切片生成 → CoT标注 → 导出
  - 知识图谱抽取 → 可视化 → 查询过滤
  - 数据导入导出完整流程

- **用户界面交互测试**
  - 拖拽文件上传
  - CoT候选答案排序
  - 知识图谱节点交互
  - 实时进度更新

#### 2. 集成测试 (Integration Tests)
- **API集成测试**
  - 项目管理API完整流程
  - 文件处理服务集成
  - OCR服务集成
  - LLM服务集成
  - 知识图谱服务集成

- **数据库集成测试**
  - PostgreSQL数据一致性
  - Neo4j图数据库操作
  - 跨数据库事务处理

- **外部服务集成测试**
  - MinIO对象存储
  - Redis缓存服务
  - Celery异步任务

#### 3. 性能测试 (Performance Tests)
- **负载测试**
  - 并发文件上传 (10+ 文件)
  - 并发CoT生成 (5+ 请求)
  - 大量数据查询 (1000+ 记录)

- **压力测试**
  - 内存使用监控
  - CPU使用率测试
  - 数据库连接池测试

- **基准测试**
  - API响应时间分布
  - 数据库查询性能
  - 文件处理速度

## 测试实施

### 后端测试

#### 目录结构
```
backend/tests/
├── __init__.py
├── conftest.py                    # pytest配置
├── test_*.py                      # 单元测试
├── integration/                   # 集成测试
│   ├── __init__.py
│   ├── test_complete_workflow.py  # 完整流程测试
│   └── test_knowledge_graph_integration.py
├── performance/                   # 性能测试
│   ├── __init__.py
│   └── test_load_performance.py
├── test_runner.py                 # 测试运行器
└── benchmark.py                   # 性能基准测试
```

#### 运行测试

```bash
# 运行所有测试
python tests/test_runner.py

# 运行特定类型测试
python tests/test_runner.py unit
python tests/test_runner.py integration
python tests/test_runner.py performance

# 运行性能基准测试
python tests/benchmark.py

# 使用pytest直接运行
pytest tests/ -v
pytest tests/integration/ -v --tb=short
pytest tests/performance/ -v -s
```

### 前端测试

#### 目录结构
```
frontend/src/test/
├── setup.ts                      # 测试环境设置
├── e2e/                          # 端到端测试
│   ├── __init__.ts
│   └── complete-workflow.test.tsx
├── integration/                   # 集成测试
│   └── knowledge-graph.test.tsx
└── utils/                        # 测试工具
    └── test-helpers.ts
```

#### 运行测试

```bash
# 进入前端目录
cd frontend

# 运行所有测试
npm run test

# 运行特定测试文件
npm run test -- complete-workflow.test.tsx

# 运行测试并生成覆盖率报告
npm run test:coverage

# 监听模式运行测试
npm run test:watch
```

## 测试用例详解

### 1. 完整业务流程测试

#### 测试场景：文件上传到CoT生成
```typescript
it('should complete full project creation to CoT annotation workflow', async () => {
  // 1. 创建项目
  // 2. 上传文件
  // 3. 触发OCR处理
  // 4. 获取切片
  // 5. 生成CoT问题和答案
  // 6. 保存标注数据
  // 7. 验证项目统计
});
```

#### 测试数据
- 测试文件：包含中文AI相关内容的文本文件
- 预期切片：按段落自动分割
- CoT生成：3-5个候选答案
- 标注数据：评分、排序、chosen标记

### 2. 知识图谱集成测试

#### 测试场景：KG抽取和可视化
```python
def test_entity_extraction_and_storage(self, client, db_session, neo4j_session):
    # 1. 创建包含丰富实体的CoT数据
    # 2. 触发知识图谱抽取
    # 3. 验证实体抽取结果
    # 4. 验证Neo4j中的数据
```

#### 验证点
- 实体抽取准确性
- 关系识别正确性
- Neo4j数据一致性
- 可视化数据格式

### 3. 性能负载测试

#### 并发文件上传测试
```python
def test_concurrent_file_uploads(self, client, db_session):
    # 并发上传10个文件
    # 验证：
    # - 所有文件上传成功
    # - 平均上传时间 < 5秒
    # - 最大上传时间 < 10秒
```

#### 性能指标
- **响应时间**：P95 < 2秒，P99 < 5秒
- **吞吐量**：文件上传 > 2 files/s
- **内存使用**：增长 < 500MB (100次操作)
- **并发处理**：支持10个并发请求

## 错误处理测试

### 1. 文件上传错误
- 文件格式不支持
- 文件大小超限
- 存储服务不可用

### 2. OCR处理错误
- OCR服务超时
- 文件格式不兼容
- 处理结果为空

### 3. LLM服务错误
- API调用超时
- 配额不足
- 服务不可用

### 4. 数据库错误
- 连接超时
- 约束违反
- 事务回滚

## 测试数据管理

### 测试数据生成
```python
# 项目测试数据
def create_test_project():
    return Project(
        name="Test Project",
        owner="test_user",
        description="Test project for unit tests",
        tags=["test"],
        project_type=ProjectType.STANDARD
    )

# 文件测试数据
def create_test_file():
    content = "人工智能是计算机科学的一个分支..."
    return tempfile.NamedTemporaryFile(
        mode='w', suffix='.txt', 
        delete=False, encoding='utf-8'
    )
```

### 测试数据清理
- 每个测试前清理数据库
- 删除临时文件
- 重置Redis缓存
- 清理Neo4j测试数据

## 持续集成

### GitHub Actions 配置
```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      neo4j:
        image: neo4j:5.0
        env:
          NEO4J_AUTH: neo4j/password
    
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: python tests/test_runner.py
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage
```

## 测试报告

### 覆盖率要求
- **单元测试覆盖率**：≥ 80%
- **API测试覆盖率**：≥ 90%
- **关键业务流程**：100%

### 报告格式
- HTML覆盖率报告
- JUnit XML测试结果
- JSON性能基准报告
- Markdown测试摘要

### 报告示例
```
📊 测试执行摘要
==========================================
⏱️  总执行时间: 45.23秒
✅ 所有测试通过: 是

📋 测试套件结果:
  unit_tests: ✅ 通过
  integration_tests: ✅ 通过
  performance_tests: ✅ 通过
  frontend_tests: ✅ 通过

📈 代码覆盖率: 85.2%

⚡ 性能指标:
  内存使用变化: 125.3MB
  平均响应时间: 0.245s
  性能等级: A
```

## 故障排除

### 常见问题

#### 1. 测试数据库连接失败
```bash
# 检查数据库服务
docker-compose ps postgres

# 重启数据库服务
docker-compose restart postgres
```

#### 2. Neo4j连接超时
```bash
# 检查Neo4j状态
docker-compose logs neo4j

# 增加连接超时时间
export NEO4J_TIMEOUT=30
```

#### 3. 前端测试失败
```bash
# 清理node_modules
rm -rf frontend/node_modules
cd frontend && npm install

# 更新测试快照
npm run test -- --update-snapshots
```

#### 4. 性能测试不稳定
- 确保测试环境资源充足
- 关闭其他占用资源的程序
- 增加测试重试次数
- 调整性能阈值

## 最佳实践

### 1. 测试编写原则
- **独立性**：每个测试独立运行
- **可重复性**：多次运行结果一致
- **快速性**：单元测试 < 1秒
- **清晰性**：测试意图明确

### 2. 测试数据原则
- 使用工厂模式生成测试数据
- 避免硬编码测试数据
- 每个测试使用独立数据
- 测试后及时清理数据

### 3. 性能测试原则
- 预热系统后再测量
- 多次测量取平均值
- 监控系统资源使用
- 设置合理的性能阈值

### 4. 错误处理原则
- 测试所有错误路径
- 验证错误消息准确性
- 确保系统优雅降级
- 提供重试机制

## 总结

本测试套件提供了 COT Studio MVP 的全面测试覆盖，包括：

1. **完整业务流程验证**：确保端到端功能正常
2. **系统集成验证**：确保各服务协同工作
3. **性能基准测试**：确保系统性能达标
4. **错误处理验证**：确保系统健壮性

通过执行这些测试，可以确保系统的质量、性能和可靠性，为生产环境部署提供信心保障。