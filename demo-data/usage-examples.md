# COT Studio MVP 使用示例

## 概述

本文档提供了 COT Studio MVP 的完整使用示例，展示了从项目创建到数据导出的完整工作流程。

## 快速开始

### 1. 启动系统

```bash
# 克隆项目
git clone <repository-url>
cd cot-studio

# 启动开发环境
docker-compose up -d

# 或使用 Make 命令
make start
```

### 2. 访问系统

- 前端界面: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 完整工作流程示例

### 步骤 1: 创建项目

1. 访问前端界面
2. 点击"创建项目"按钮
3. 填写项目信息：
   - 项目名称: "AI技术研究项目"
   - 描述: "人工智能技术发展研究"
   - 标签: ["AI", "机器学习", "深度学习"]

### 步骤 2: 上传文档

支持的文件格式：
- PDF文档
- Word文档 (.docx)
- 纯文本文件 (.txt)
- Markdown文件 (.md)
- LaTeX文件 (.tex)
- JSON文件 (.json)

**示例文档内容:**
```text
人工智能技术发展概述

人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，
它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

机器学习是人工智能的一个重要分支，它通过算法使计算机能够从数据中学习并做出决策或预测。
深度学习是机器学习的一个子集，它使用多层神经网络来模拟人脑的工作方式。
```

### 步骤 3: OCR处理

1. 选择OCR引擎（推荐PaddleOCR）
2. 点击"开始OCR处理"
3. 等待处理完成，系统会自动生成文档切片

**切片结果示例:**
- 切片1: "人工智能（Artificial Intelligence，AI）是计算机科学的一个分支..."
- 切片2: "机器学习是人工智能的一个重要分支..."
- 切片3: "深度学习是机器学习的一个子集..."

### 步骤 4: CoT数据生成

1. 在切片列表中选择目标切片
2. 点击"生成CoT问题"
3. 系统会调用LLM生成问题和候选答案

**生成示例:**

**问题:** "什么是人工智能？请详细解释其定义和主要特征。"

**候选答案:**
1. **答案1 (Score: 0.95, Chosen: ✓)**
   - 文本: "人工智能是计算机科学的一个分支，旨在创造能够模拟人类智能行为的机器系统。"
   - 思维链: "首先，我需要理解人工智能的基本定义。人工智能（AI）是计算机科学的一个重要分支..."

2. **答案2 (Score: 0.75)**
   - 文本: "AI就是让计算机变得聪明，能够像人一样思考和解决问题。"
   - 思维链: "这是一个比较简化的解释。虽然核心思想是正确的..."

3. **答案3 (Score: 0.80)**
   - 文本: "人工智能包括机器学习、深度学习、自然语言处理等多个技术领域。"
   - 思维链: "这个回答从技术组成的角度来定义AI..."

### 步骤 5: 标注工作台

1. **拖拽排序**: 通过拖拽调整候选答案的排序
2. **评分**: 使用滑动条为每个答案评分（0-1分，精度0.1）
3. **选择最佳**: 点击Y按钮标记最佳答案（chosen）
4. **保存标注**: 点击保存按钮完成标注

### 步骤 6: 知识图谱抽取

1. 点击"抽取知识图谱"按钮
2. 系统自动从CoT数据中抽取实体和关系
3. 在可视化界面中查看图谱

**抽取结果示例:**

**实体:**
- 人工智能 (CONCEPT)
- 机器学习 (CONCEPT)  
- 深度学习 (CONCEPT)
- 神经网络 (TECHNOLOGY)

**关系:**
- 机器学习 → 人工智能 (IS_PART_OF)
- 深度学习 → 机器学习 (IS_SUBSET_OF)
- 深度学习 → 神经网络 (USES)

### 步骤 7: 数据导出

1. 选择导出格式（JSON/Markdown/LaTeX/TXT）
2. 配置导出选项
3. 下载生成的数据包

**导出格式示例:**

**JSON格式:**
```json
{
  "project": {
    "name": "AI技术研究项目",
    "description": "人工智能技术发展研究"
  },
  "cot_data": [
    {
      "question": "什么是人工智能？",
      "candidates": [
        {
          "text": "人工智能是计算机科学的一个分支...",
          "chain_of_thought": "首先，我需要理解...",
          "score": 0.95,
          "chosen": true,
          "rank": 1
        }
      ]
    }
  ]
}
```

**Markdown格式:**
```markdown
# AI技术研究项目

## 问题 1: 什么是人工智能？

### 候选答案

#### 答案 1 (✓ Chosen, Score: 0.95)
人工智能是计算机科学的一个分支，旨在创造能够模拟人类智能行为的机器系统。

**思维链:** 首先，我需要理解人工智能的基本定义...
```

## API使用示例

### 创建项目

```bash
curl -X POST "http://localhost:8000/api/v1/projects/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API测试项目",
    "description": "通过API创建的项目",
    "tags": ["API", "测试"]
  }'
```

### 上传文件

```bash
curl -X POST "http://localhost:8000/api/v1/projects/{project_id}/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@example.txt"
```

### 生成CoT数据

```bash
curl -X POST "http://localhost:8000/api/v1/projects/{project_id}/cot" \
  -H "Content-Type: application/json" \
  -d '{
    "slice_id": "slice-uuid",
    "question": "什么是机器学习？",
    "candidates": [
      {
        "text": "机器学习是AI的分支",
        "chain_of_thought": "机器学习的定义...",
        "score": 0.9
      }
    ]
  }'
```

### 查询知识图谱

```bash
curl -X GET "http://localhost:8000/api/v1/projects/{project_id}/knowledge-graph" \
  -H "Accept: application/json"
```

## 高级功能示例

### 1. 批量处理

```python
import requests
import json

# 批量上传文件
files = ["doc1.txt", "doc2.pdf", "doc3.md"]
project_id = "your-project-id"

for file_path in files:
    with open(file_path, 'rb') as f:
        response = requests.post(
            f"http://localhost:8000/api/v1/projects/{project_id}/upload",
            files={"file": f}
        )
        print(f"Uploaded {file_path}: {response.status_code}")
```

### 2. 自动化CoT生成

```python
# 获取所有切片并生成CoT
response = requests.get(f"http://localhost:8000/api/v1/projects/{project_id}/slices")
slices = response.json()

for slice_data in slices:
    cot_request = {
        "slice_id": slice_data["id"],
        "auto_generate": True,
        "candidate_count": 5
    }
    
    response = requests.post(
        f"http://localhost:8000/api/v1/projects/{project_id}/cot/generate",
        json=cot_request
    )
    print(f"Generated CoT for slice {slice_data['id']}")
```

### 3. 知识图谱查询

```python
# 查询特定类型的实体
params = {
    "entity_type": "CONCEPT",
    "limit": 20
}

response = requests.get(
    f"http://localhost:8000/api/v1/projects/{project_id}/knowledge-graph/entities",
    params=params
)

entities = response.json()
for entity in entities:
    print(f"Entity: {entity['name']} ({entity['type']})")
```

## 性能优化建议

### 1. 文件处理优化

- 单个文件大小建议不超过50MB
- 批量上传时建议每批不超过10个文件
- PDF文件建议先转换为文本格式以提高处理速度

### 2. OCR处理优化

- 对于纯文本文件，可以跳过OCR直接进行切片
- 图片较多的文档建议使用高精度OCR引擎
- 可以并行处理多个文件的OCR任务

### 3. CoT生成优化

- 合理设置候选答案数量（建议3-5个）
- 使用缓存避免重复生成相同内容的CoT
- 可以预设问题模板提高生成质量

### 4. 知识图谱优化

- 定期清理低置信度的实体和关系
- 使用向量索引加速相似实体查找
- 可以手动标注重要实体提高抽取质量

## 故障排除

### 常见问题

1. **文件上传失败**
   - 检查文件格式是否支持
   - 确认文件大小未超过限制
   - 检查网络连接状态

2. **OCR处理超时**
   - 减小文件大小或分割文件
   - 检查OCR服务状态
   - 尝试使用不同的OCR引擎

3. **CoT生成失败**
   - 检查LLM API配置
   - 确认API密钥有效
   - 检查网络连接和API配额

4. **知识图谱显示异常**
   - 清除浏览器缓存
   - 检查Neo4j数据库连接
   - 重新抽取知识图谱

### 日志查看

```bash
# 查看后端日志
docker-compose logs backend

# 查看前端日志  
docker-compose logs frontend

# 查看数据库日志
docker-compose logs postgres neo4j
```

## 扩展开发

### 自定义OCR引擎

```python
from app.services.ocr_service import OCREngine

class CustomOCREngine(OCREngine):
    def process_file(self, file_path: str) -> dict:
        # 实现自定义OCR逻辑
        return {
            "text": "extracted text",
            "slices": [...]
        }

# 注册自定义引擎
ocr_service.register_engine("custom", CustomOCREngine())
```

### 自定义LLM提供商

```python
from app.services.llm_service import LLMProvider

class CustomLLMProvider(LLMProvider):
    def generate_question(self, context: str) -> str:
        # 实现自定义问题生成逻辑
        return "generated question"
    
    def generate_candidates(self, question: str, context: str) -> list:
        # 实现自定义答案生成逻辑
        return [...]

# 注册自定义提供商
llm_service.register_provider("custom", CustomLLMProvider())
```

## 总结

COT Studio MVP 提供了完整的CoT数据集构建工作流程，从文档处理到知识图谱抽取，支持多种格式和自定义扩展。通过本示例，您可以快速上手并构建高质量的CoT数据集。

更多详细信息请参考：
- [API文档](http://localhost:8000/docs)
- [用户指南](docs/user-guide.md)
- [开发文档](docs/development.md)