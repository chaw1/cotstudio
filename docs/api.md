# COT Studio MVP API 文档

## 概述

COT Studio MVP 提供了完整的 RESTful API，支持项目管理、文件处理、OCR、CoT数据标注、知识图谱等功能。所有API都遵循OpenAPI 3.0规范，并提供自动生成的交互式文档。

## API 基础信息

- **Base URL**: `http://localhost:8000` (开发环境)
- **API Version**: v1
- **API Prefix**: `/api/v1`
- **文档地址**: `http://localhost:8000/docs` (Swagger UI)
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## 认证

### JWT Token 认证

所有需要认证的API都使用JWT Token进行身份验证：

```bash
# 获取访问令牌
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'

# 使用令牌访问API
curl -X GET "http://localhost:8000/api/v1/projects" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 响应格式

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

## API 端点

### 1. 项目管理 API

#### 创建项目

```http
POST /api/v1/projects
```

**请求体:**
```json
{
  "name": "我的CoT项目",
  "description": "项目描述",
  "tags": ["研究", "NLP"],
  "project_type": "standard"
}
```

**响应:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "我的CoT项目",
  "description": "项目描述",
  "tags": ["研究", "NLP"],
  "project_type": "standard",
  "status": "active",
  "owner": "user123",
  "created_at": "2024-03-15T10:30:00Z",
  "updated_at": "2024-03-15T10:30:00Z",
  "file_count": 0,
  "cot_count": 0
}
```

#### 获取项目列表

```http
GET /api/v1/projects?page=1&size=20&search=关键词&tags=研究,NLP
```

**响应:**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "我的CoT项目",
      "status": "active",
      "owner": "user123",
      "created_at": "2024-03-15T10:30:00Z",
      "file_count": 5,
      "cot_count": 23
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

#### 获取项目详情

```http
GET /api/v1/projects/{project_id}
```

#### 更新项目

```http
PUT /api/v1/projects/{project_id}
```

#### 删除项目

```http
DELETE /api/v1/projects/{project_id}
```

### 2. 文件管理 API

#### 上传文件

```http
POST /api/v1/projects/{project_id}/files
```

**请求 (multipart/form-data):**
```bash
curl -X POST "http://localhost:8000/api/v1/projects/{project_id}/files" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@document.pdf" \
  -F "description=研究论文"
```

**响应:**
```json
{
  "id": "456e7890-e89b-12d3-a456-426614174001",
  "filename": "document.pdf",
  "original_filename": "research_paper.pdf",
  "size": 2048576,
  "mime_type": "application/pdf",
  "file_hash": "sha256:abc123...",
  "description": "研究论文",
  "ocr_status": "pending",
  "created_at": "2024-03-15T10:35:00Z",
  "upload_url": "http://localhost:9000/cotbucket/files/456e7890..."
}
```

#### 获取文件列表

```http
GET /api/v1/projects/{project_id}/files?page=1&size=20&status=completed
```

#### 获取文件详情

```http
GET /api/v1/files/{file_id}
```

#### 下载文件

```http
GET /api/v1/files/{file_id}/download
```

#### 删除文件

```http
DELETE /api/v1/files/{file_id}
```

### 3. OCR 处理 API

#### 启动OCR处理

```http
POST /api/v1/files/{file_id}/ocr
```

**请求体:**
```json
{
  "ocr_engine": "paddleocr",
  "language": "ch",
  "options": {
    "auto_slice": true,
    "slice_by": ["paragraph", "image", "table"],
    "min_slice_length": 50
  }
}
```

**响应:**
```json
{
  "task_id": "789e0123-e89b-12d3-a456-426614174002",
  "status": "processing",
  "progress": 0,
  "estimated_time": 300,
  "created_at": "2024-03-15T10:40:00Z"
}
```

#### 获取OCR状态

```http
GET /api/v1/tasks/{task_id}
```

**响应:**
```json
{
  "task_id": "789e0123-e89b-12d3-a456-426614174002",
  "status": "completed",
  "progress": 100,
  "result": {
    "slice_count": 15,
    "text_length": 5420,
    "processing_time": 245
  },
  "created_at": "2024-03-15T10:40:00Z",
  "completed_at": "2024-03-15T10:44:05Z"
}
```

#### 获取文件切片

```http
GET /api/v1/files/{file_id}/slices?page=1&size=20&type=paragraph
```

**响应:**
```json
{
  "items": [
    {
      "id": "abc123-def456-ghi789",
      "content": "这是一个段落的文本内容...",
      "slice_type": "paragraph",
      "start_offset": 0,
      "end_offset": 150,
      "page_number": 1,
      "confidence": 0.95,
      "created_at": "2024-03-15T10:44:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "size": 20
}
```

### 4. CoT 数据标注 API

#### 生成CoT问题

```http
POST /api/v1/cot/generate-question
```

**请求体:**
```json
{
  "slice_id": "abc123-def456-ghi789",
  "context": "额外的上下文信息",
  "question_type": "analytical",
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7
  }
}
```

**响应:**
```json
{
  "question": "基于给定的文本内容，请分析其中的主要论点和支撑证据？",
  "context": "文本上下文...",
  "generated_at": "2024-03-15T10:50:00Z",
  "llm_metadata": {
    "provider": "openai",
    "model": "gpt-4",
    "tokens_used": 150
  }
}
```

#### 生成候选答案

```http
POST /api/v1/cot/generate-candidates
```

**请求体:**
```json
{
  "question": "基于给定的文本内容，请分析其中的主要论点和支撑证据？",
  "slice_id": "abc123-def456-ghi789",
  "candidate_count": 4,
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.8
  }
}
```

**响应:**
```json
{
  "candidates": [
    {
      "id": "cand001",
      "text": "主要论点是...",
      "chain_of_thought": "首先，我需要识别文本中的关键论点。通过分析可以发现...",
      "confidence": 0.92,
      "reasoning_steps": [
        "识别主要论点",
        "分析支撑证据",
        "评估论证逻辑"
      ]
    }
  ],
  "generated_at": "2024-03-15T10:52:00Z"
}
```

#### 创建CoT数据项

```http
POST /api/v1/cot/items
```

**请求体:**
```json
{
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "slice_id": "abc123-def456-ghi789",
  "question": "基于给定的文本内容，请分析其中的主要论点和支撑证据？",
  "candidates": [
    {
      "text": "主要论点是...",
      "chain_of_thought": "首先，我需要识别文本中的关键论点...",
      "score": 0.8,
      "chosen": true,
      "rank": 1
    }
  ],
  "source": "human_ai",
  "metadata": {
    "annotator": "user123",
    "annotation_time": 300
  }
}
```

#### 更新CoT标注

```http
PUT /api/v1/cot/items/{cot_id}
```

#### 获取CoT数据列表

```http
GET /api/v1/projects/{project_id}/cot?page=1&size=20&status=approved
```

### 5. 知识图谱 API

#### 触发KG抽取

```http
POST /api/v1/projects/{project_id}/knowledge-graph/extract
```

**请求体:**
```json
{
  "extraction_config": {
    "entity_types": ["PERSON", "ORGANIZATION", "CONCEPT"],
    "relation_types": ["RELATED_TO", "PART_OF", "CAUSES"],
    "min_confidence": 0.7
  }
}
```

#### 查询知识图谱

```http
GET /api/v1/projects/{project_id}/knowledge-graph/query
```

**查询参数:**
- `entity`: 实体名称
- `relation`: 关系类型
- `limit`: 结果数量限制
- `depth`: 查询深度

**响应:**
```json
{
  "nodes": [
    {
      "id": "entity_001",
      "label": "机器学习",
      "type": "CONCEPT",
      "properties": {
        "confidence": 0.95,
        "frequency": 15
      }
    }
  ],
  "edges": [
    {
      "id": "rel_001",
      "source": "entity_001",
      "target": "entity_002",
      "type": "RELATED_TO",
      "properties": {
        "confidence": 0.88,
        "weight": 0.7
      }
    }
  ]
}
```

#### 获取实体详情

```http
GET /api/v1/knowledge-graph/entities/{entity_id}
```

#### 获取关系详情

```http
GET /api/v1/knowledge-graph/relations/{relation_id}
```

### 6. 数据导出 API

#### 创建导出任务

```http
POST /api/v1/projects/{project_id}/export
```

**请求体:**
```json
{
  "format": "json",
  "include_files": true,
  "include_kg": true,
  "include_vectors": false,
  "filter": {
    "status": ["approved"],
    "date_range": {
      "start": "2024-03-01",
      "end": "2024-03-31"
    }
  }
}
```

**响应:**
```json
{
  "export_id": "exp_123456",
  "status": "processing",
  "format": "json",
  "estimated_size": "50MB",
  "created_at": "2024-03-15T11:00:00Z"
}
```

#### 获取导出状态

```http
GET /api/v1/exports/{export_id}
```

#### 下载导出文件

```http
GET /api/v1/exports/{export_id}/download
```

### 7. 系统配置 API

#### 获取系统配置

```http
GET /api/v1/settings
```

#### 更新LLM配置

```http
PUT /api/v1/settings/llm
```

**请求体:**
```json
{
  "providers": {
    "openai": {
      "api_key": "sk-...",
      "base_url": "https://api.openai.com/v1",
      "models": ["gpt-4", "gpt-3.5-turbo"]
    },
    "deepseek": {
      "api_key": "sk-...",
      "base_url": "https://api.deepseek.com/v1",
      "models": ["deepseek-chat", "deepseek-coder"]
    }
  },
  "default_provider": "openai",
  "default_model": "gpt-4"
}
```

#### 更新OCR配置

```http
PUT /api/v1/settings/ocr
```

### 8. 任务监控 API

#### 获取任务列表

```http
GET /api/v1/tasks?status=running&page=1&size=20
```

#### 取消任务

```http
POST /api/v1/tasks/{task_id}/cancel
```

#### 重试失败任务

```http
POST /api/v1/tasks/{task_id}/retry
```

## WebSocket API

### 实时通知

连接到 WebSocket 端点获取实时更新：

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/notifications');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('通知:', data);
};
```

**消息格式:**
```json
{
  "type": "task_update",
  "task_id": "789e0123-e89b-12d3-a456-426614174002",
  "status": "completed",
  "progress": 100,
  "message": "OCR处理完成",
  "timestamp": "2024-03-15T10:44:05Z"
}
```

## 错误处理

### 标准错误响应

```json
{
  "error": "VALIDATION_ERROR",
  "message": "请求参数验证失败",
  "details": {
    "field": "name",
    "issue": "字段不能为空"
  },
  "timestamp": "2024-03-15T10:30:00Z",
  "request_id": "req_123456"
}
```

### 常见错误码

| 错误码 | HTTP状态 | 描述 |
|--------|----------|------|
| VALIDATION_ERROR | 400 | 请求参数验证失败 |
| UNAUTHORIZED | 401 | 未授权访问 |
| FORBIDDEN | 403 | 权限不足 |
| NOT_FOUND | 404 | 资源不存在 |
| CONFLICT | 409 | 资源冲突 |
| RATE_LIMIT_EXCEEDED | 429 | 请求频率超限 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |

## 速率限制

API 实施了速率限制以确保服务稳定性：

- **认证用户**: 1000 请求/小时
- **匿名用户**: 100 请求/小时
- **文件上传**: 10 次/分钟
- **LLM调用**: 60 次/分钟

## SDK 和客户端库

### Python SDK

```python
from cot_studio_client import COTStudioClient

client = COTStudioClient(
    base_url="http://localhost:8000",
    api_key="your_api_key"
)

# 创建项目
project = client.projects.create(
    name="我的项目",
    description="项目描述"
)

# 上传文件
file = client.files.upload(
    project_id=project.id,
    file_path="document.pdf"
)

# 启动OCR
task = client.ocr.process(file_id=file.id)
```

### JavaScript SDK

```javascript
import { COTStudioClient } from '@cot-studio/client';

const client = new COTStudioClient({
  baseURL: 'http://localhost:8000',
  apiKey: 'your_api_key'
});

// 创建项目
const project = await client.projects.create({
  name: '我的项目',
  description: '项目描述'
});

// 上传文件
const file = await client.files.upload(project.id, fileBlob);
```

## 测试和调试

### 使用 Swagger UI

访问 `http://localhost:8000/docs` 使用交互式API文档进行测试。

### 使用 curl 测试

```bash
# 设置基础URL和认证
export API_BASE="http://localhost:8000/api/v1"
export JWT_TOKEN="your_jwt_token"

# 测试项目创建
curl -X POST "$API_BASE/projects" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "测试项目", "description": "API测试"}'
```

### API 测试集合

项目包含了完整的 Postman 测试集合，位于 `tests/api/postman/` 目录。

## 版本控制

API 使用语义化版本控制：

- **主版本号**: 不兼容的API更改
- **次版本号**: 向后兼容的功能添加
- **修订号**: 向后兼容的问题修复

当前版本: `v1.0.0`

## 更新日志

### v1.0.0 (2024-03-15)
- 初始API版本发布
- 支持项目管理、文件处理、OCR、CoT标注、知识图谱等核心功能
- 提供完整的RESTful API和WebSocket支持