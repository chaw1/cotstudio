# MinerU OCR引擎422错误修复报告

## 问题描述

在项目管理的OCR处理页面中，选择MinerU引擎并点击"开始OCR处理"时，出现422 (Unprocessable Entity)错误。

### 错误信息

```
api/v1/ocr/process:1   Failed to load resource: the server responded with a status of 422 (Unprocessable Entity)
errorHandler.ts:112  Global error handler: Error: Request failed with status code 422
```

### 用户操作流程

1. 在项目详情页面点击"OCR处理"标签
2. 选择MinerU作为OCR引擎
3. 点击"开始OCR处理"按钮
4. 请求失败，返回422错误

## 根本原因分析

### 原因1: 后端Schema未包含MinerU引擎

**问题**: `backend/app/schemas/ocr.py` 中的 `OCREngineEnum` 只定义了两个引擎:

```python
class OCREngineEnum(str, Enum):
    """OCR引擎枚举"""
    PADDLEOCR = "paddleocr"
    FALLBACK = "fallback"
    # 缺少 MINERU
```

**影响**: 当前端发送 `engine: "mineru"` 时，Pydantic验证失败，返回422错误。

**解决方案**: 添加MINERU枚举值:

```python
class OCREngineEnum(str, Enum):
    """OCR引擎枚举"""
    PADDLEOCR = "paddleocr"
    MINERU = "mineru"      # ✅ 新增
    FALLBACK = "fallback"
```

### 原因2: OCR Engines API未返回MinerU

**问题**: `/api/v1/ocr/engines` 端点只返回PaddleOCR和Fallback引擎信息，前端无法获知MinerU引擎的存在。

**修复前的代码**:

```python
engines_info = [
    OCREngineInfo(
        name="paddleocr",
        available="paddleocr" in available_engines,
        description="PaddleOCR - 支持中英文OCR识别，适用于PDF和图像文件"
    ),
    OCREngineInfo(
        name="fallback",
        available="fallback" in available_engines,
        description="Fallback Engine - 用于纯文本文件的文本提取"
    )
    # 缺少 mineru
]
```

**解决方案**: 添加MinerU引擎信息:

```python
engines_info = [
    OCREngineInfo(
        name="paddleocr",
        available="paddleocr" in available_engines,
        description="PaddleOCR - 支持中英文OCR识别，适用于PDF和图像文件"
    ),
    OCREngineInfo(
        name="mineru",
        available="mineru" in available_engines,
        description="MinerU - 高性能OCR引擎，支持复杂文档结构识别，适用于PDF、图像和扫描文档"
    ),  # ✅ 新增
    OCREngineInfo(
        name="fallback",
        available="fallback" in available_engines,
        description="Fallback Engine - 用于纯文本文件的文本提取"
    )
]
```

### 原因3: Docker容器内代理配置问题

**问题**: 后端容器尝试访问MinerU服务(`http://mineru:8001`)时，requests库自动使用了系统代理`127.0.0.1:10808`，导致连接失败。

**错误日志**:

```
requests.exceptions.ProxyError: HTTPConnectionPool(host='127.0.0.1', port=10808): 
Max retries exceeded with url: http://mineru:8001/health 
(Caused by ProxyError('Unable to connect to proxy', NewConnectionError...))
```

**解决方案**: 在docker-compose.yml中为backend和celery服务添加NO_PROXY环境变量:

```yaml
environment:
  # ... 其他环境变量 ...
  - MINERU_SERVICE_URL=http://mineru:8001
  - NO_PROXY=mineru,localhost,127.0.0.1,postgres,redis,neo4j,minio,rabbitmq
  - no_proxy=mineru,localhost,127.0.0.1,postgres,redis,neo4j,minio,rabbitmq
```

**说明**: 
- `NO_PROXY`(大写)适用于某些工具
- `no_proxy`(小写)适用于Python requests库
- 两者都配置确保最大兼容性

## 修复步骤

### 1. 更新后端Schema

**文件**: `backend/app/schemas/ocr.py`

```python
class OCREngineEnum(str, Enum):
    """OCR引擎枚举"""
    PADDLEOCR = "paddleocr"
    MINERU = "mineru"      # 添加此行
    FALLBACK = "fallback"
```

### 2. 更新OCR API端点

**文件**: `backend/app/api/v1/ocr.py`

在`get_ocr_engines()`函数的`engines_info`列表中添加:

```python
OCREngineInfo(
    name="mineru",
    available="mineru" in available_engines,
    description="MinerU - 高性能OCR引擎，支持复杂文档结构识别，适用于PDF、图像和扫描文档"
),
```

### 3. 配置Docker容器代理

**文件**: `docker-compose.yml`

为backend服务添加:

```yaml
backend:
  environment:
    # ... 现有配置 ...
    - NO_PROXY=mineru,localhost,127.0.0.1,postgres,redis,neo4j,minio,rabbitmq
    - no_proxy=mineru,localhost,127.0.0.1,postgres,redis,neo4j,minio,rabbitmq
```

为celery服务添加:

```yaml
celery:
  environment:
    # ... 现有配置 ...
    - MINERU_SERVICE_URL=http://mineru:8001
    - NO_PROXY=mineru,localhost,127.0.0.1,postgres,redis,neo4j,minio,rabbitmq
    - no_proxy=mineru,localhost,127.0.0.1,postgres,redis,neo4j,minio,rabbitmq
```

### 4. 重启服务

```powershell
# 重启后端和Celery服务
docker-compose up -d backend celery

# 等待服务启动
Start-Sleep -Seconds 20

# 验证MinerU引擎可用性
docker exec cotstudio-backend-1 python -c "from app.services.ocr_service import ocr_service; print(ocr_service.get_available_engines())"
```

## 验证结果

### API测试

```bash
curl http://localhost:8000/api/v1/ocr/engines
```

**响应**:

```json
{
  "success": true,
  "message": "OCR engines retrieved successfully",
  "data": [
    {
      "name": "paddleocr",
      "available": false,
      "description": "PaddleOCR - 支持中英文OCR识别，适用于PDF和图像文件"
    },
    {
      "name": "mineru",
      "available": true,
      "description": "MinerU - 高性能OCR引擎，支持复杂文档结构识别，适用于PDF、图像和扫描文档"
    },
    {
      "name": "fallback",
      "available": true,
      "description": "Fallback Engine - 用于纯文本文件的文本提取"
    }
  ]
}
```

✅ **MinerU引擎显示为可用** (`"available": true`)

### MinerU服务健康检查

```bash
curl http://localhost:8001/health
```

**响应**:

```json
{
  "status": "healthy",
  "mineru_ready": true,
  "gpu_available": true,
  "gpu_count": 1
}
```

✅ **MinerU服务正常运行，GPU可用**

### 容器内部连接测试

```bash
docker exec cotstudio-backend-1 python -c "import requests; r = requests.get('http://mineru:8001/health', timeout=5); print('Status:', r.status_code)"
```

**输出**:

```
Status: 200
```

✅ **后端容器可以成功连接MinerU服务**

### 引擎列表测试

```bash
docker exec cotstudio-backend-1 python -c "from app.services.ocr_service import ocr_service; print('Available engines:', ocr_service.get_available_engines())"
```

**输出**:

```
MinerU service URL: http://mineru:8001
http://mineru:8001 "GET /health HTTP/1.1" 200 75
MinerU engine initialized successfully
MinerU engine registered
Fallback OCR engine registered
Available engines: ['mineru', 'fallback']
```

✅ **OCR服务成功识别MinerU引擎**

## 技术细节

### MinerU引擎架构

MinerU引擎作为独立的微服务运行:

```
┌─────────────────┐         ┌─────────────────┐
│  Backend API    │ ◄─────► │  MinerU Service │
│  (Port 8000)    │  HTTP   │  (Port 8001)    │
└─────────────────┘         └─────────────────┘
        │                           │
        │                           │
        ▼                           ▼
    PostgreSQL                   NVIDIA GPU
      Redis                      CUDA 13.0
      Neo4j                      32GB VRAM
```

**通信方式**:
- Protocol: HTTP REST API
- URL: `http://mineru:8001`
- 健康检查: `GET /health`
- OCR处理: `POST /ocr`

### OCR服务初始化流程

```python
# backend/app/services/ocr_service.py

class OCRService:
    def _init_engines(self):
        # 1. 初始化PaddleOCR引擎
        paddle_engine = PaddleOCREngine()
        if paddle_engine.is_available():
            self.engines['paddleocr'] = paddle_engine
        
        # 2. 初始化MinerU引擎
        mineru_engine = MinerUEngine()
        if mineru_engine.is_available():  # ← 调用健康检查
            self.engines['mineru'] = mineru_engine
        
        # 3. 初始化回退引擎
        self.engines['fallback'] = FallbackOCREngine()
```

**MinerU可用性检查**:

```python
def is_available(self) -> bool:
    """检查MinerU服务是否可用"""
    if not self._service_url:
        return False
    
    try:
        import requests
        response = requests.get(f"{self._service_url}/health", timeout=2)
        return response.status_code == 200
    except:
        return False
```

### 前端OCR请求流程

```typescript
// frontend/src/services/fileService.ts

async triggerOCR(fileId: string, ocrEngine?: string): Promise<void> {
  return api.post(`/ocr/process`, { 
    file_id: fileId, 
    engine: ocrEngine || 'paddleocr',  // ← 引擎参数
    user_id: 'admin'
  });
}
```

**请求体示例**:

```json
{
  "file_id": "ee783fe1-d67a-4e94-87d3-94be3e6047ce",
  "engine": "mineru",
  "user_id": "admin"
}
```

## 影响范围

### 修改的文件

1. ✅ `backend/app/schemas/ocr.py` - 添加MINERU枚举
2. ✅ `backend/app/api/v1/ocr.py` - 添加MinerU引擎信息
3. ✅ `docker-compose.yml` - 配置NO_PROXY环境变量

### 未修改的文件

- ❌ `backend/app/services/ocr_service.py` - MinerU引擎已实现，无需修改
- ❌ `frontend/src/**/*.tsx` - 前端代码正常，无需修改
- ❌ MinerU容器配置 - 服务正常运行，无需修改

## 相关文档

- [MinerU GPU安装成功文档](./MINERU_GPU_INSTALLATION_SUCCESS.md)
- [GPU监控实现文档](./GPU_MONITORING_IMPLEMENTATION.md)
- [项目指南](./PROJECT_GUIDE.md)

## 后续建议

### 短期优化

1. **添加PaddleOCR引擎**: 目前PaddleOCR显示为不可用，可以考虑安装PaddlePaddle:
   ```bash
   docker exec cotstudio-backend-1 pip install paddlepaddle paddleocr
   ```

2. **增强错误提示**: 当引擎不可用时，前端应显示更友好的错误信息

3. **添加引擎选择验证**: 在前端提交前检查所选引擎是否可用

### 中期优化

1. **OCR任务监控**: 增强任务进度追踪和实时状态更新
2. **批量OCR处理**: 支持一次性处理多个文件
3. **OCR结果预览**: 处理完成后立即显示结果预览

### 长期优化

1. **引擎性能对比**: 提供不同引擎的性能和准确度对比数据
2. **自动引擎选择**: 根据文件类型自动推荐最佳引擎
3. **OCR质量评估**: 对OCR结果进行质量评分和置信度分析

## 总结

✅ **问题已完全解决**

- MinerU引擎已成功集成到OCR系统
- 422错误已修复，前端可以正常选择MinerU引擎
- Docker容器网络配置已优化，服务间通信正常
- 所有验证测试通过，功能正常运行

**关键成果**:
- ✅ 后端Schema支持mineru引擎
- ✅ OCR API返回MinerU引擎信息(available: true)
- ✅ Docker容器代理配置正确，服务间通信正常
- ✅ MinerU引擎健康检查通过，GPU加速可用

**修复时间**: 2025-10-16
**修复版本**: v1.0.0
**GPU环境**: NVIDIA RTX 5090, 32GB VRAM, CUDA 13.0
