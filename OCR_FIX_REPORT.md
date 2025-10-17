# OCR处理修复报告

## 问题描述

用户报告OCR处理存在以下问题:
1. OCR处理速度异常快,但没有生成有效的切片数据
2. 文件一直卡在PROCESSING状态
3. 前端界面出现多个Ant Design警告

## 根本原因分析

### 主要问题:Celery Worker队列配置错误

**问题根源**:
- Celery配置文件(`app/core/celery_app.py`)中定义了任务路由规则:
  - `ocr_processing` 任务 → `ocr` 队列
  - `llm_processing` 任务 → `llm` 队列  
  - `kg_extraction` 任务 → `kg` 队列

- 但是docker-compose中的Celery worker启动命令没有指定要监听的队列:
  ```yaml
  command: celery -A app.worker worker --loglevel=info --concurrency=2
  ```
  
- 这导致worker只监听默认的`celery`队列,**完全无法接收发送到`ocr`队列的OCR任务**

**验证过程**:
1. 检查Celery注册的任务 - ✅ `ocr_processing`任务已正确注册
2. 检查worker监听的队列 - ❌ 仅监听`celery`队列
3. 检查任务路由配置 - ✅ OCR任务被路由到`ocr`队列
4. 检查worker统计信息 - ✅ `total: {}` 显示从未执行过任何任务

## 修复方案

### 1. 修复Celery Worker队列配置

**修改文件**:
- `docker-compose.yml`
- `docker-compose.override.yml`
- `docker-compose.prod.yml`

**修改内容**:
在Celery worker命令中添加 `-Q celery,ocr,llm,kg` 参数:

```yaml
# 开发环境
command: celery -A app.worker worker --loglevel=debug --concurrency=2 -Q celery,ocr,llm,kg

# 生产环境
command: celery -A app.worker worker --loglevel=info --concurrency=4 -Q celery,ocr,llm,kg
```

**验证结果**:
重新创建容器后,worker现在正确监听所有4个队列:
```
✅ celery (默认队列)
✅ ocr (OCR处理队列)
✅ llm (LLM处理队列)
✅ kg (知识图谱处理队列)
```

### 2. 修复Ant Design警告

#### 警告1: Static Message API Deprecated
**文件**: `frontend/src/components/ocr/OCREngineSelector.tsx`

**问题**: 使用已废弃的静态message API
```typescript
import { message } from 'antd';
message.success('...');  // ❌ 已废弃
```

**修复**:
```typescript
import { App } from 'antd';

const OCREngineSelector: React.FC<OCREngineSelectorProps> = ({...}) => {
  const { message } = App.useApp();  // ✅ 使用新的hook API
  // ...
  message.success('...');  // ✅ 现在可以正常使用
};
```

#### 警告2: destroyOnClose Deprecated
**文件**: `frontend/src/components/project/OCRProcessingTab.tsx`

**问题**: Modal的`destroyOnClose`属性已废弃
```typescript
<ModalContainer destroyOnClose={true}>  // ❌ 已废弃
```

**修复**: 移除该属性(默认行为已改变)
```typescript
<ModalContainer>  // ✅ 默认行为已包含销毁功能
```

## 测试建议

### 1. 验证OCR处理功能
1. 上传一个小型PDF文件(1-2页)
2. 选择OCR引擎(建议先用paddleocr测试)
3. 观察处理过程:
   - 文件状态应从PENDING → PROCESSING → COMPLETED
   - 处理时间应合理(取决于文件大小和引擎)
   - 完成后应能看到切片数据(文本、图像、表格)

### 2. 检查Celery日志
```bash
# 实时查看worker日志
docker logs -f cotstudio-celery-1

# 应该能看到类似以下的日志:
# [INFO] Received task: app.workers.tasks.ocr_processing[...]
# [INFO] Task app.workers.tasks.ocr_processing[...] succeeded in ...s
```

### 3. 验证切片数据
在数据库中检查:
```sql
SELECT 
    f.filename,
    f.ocr_status,
    f.ocr_engine,
    COUNT(s.id) as slice_count,
    COUNT(CASE WHEN s.slice_type = 'text' THEN 1 END) as text_count,
    COUNT(CASE WHEN s.slice_type = 'image' THEN 1 END) as image_count,
    COUNT(CASE WHEN s.slice_type = 'table' THEN 1 END) as table_count
FROM files f
LEFT JOIN slices s ON f.id = s.file_id
WHERE f.ocr_status = 'COMPLETED'
GROUP BY f.id, f.filename, f.ocr_status, f.ocr_engine
ORDER BY f.updated_at DESC;
```

## 已知问题

### 数据库Enum大小写不一致
**问题**: Python代码中的OCRStatus枚举值是小写,但数据库中存储的是大写
```python
# Python代码
class OCRStatus(PyEnum):
    PENDING = "pending"      # ❌ 小写
    PROCESSING = "processing"
    
# 数据库实际值
PENDING, PROCESSING, COMPLETED, FAILED  # ✅ 大写
```

**影响**: 可能导致某些直接查询失败

**建议**: 统一为大写(数据库标准)或修改Python枚举定义

## 其他待修复的警告

1. **Form.Item with name must have single child** - 需要检查Form.Item结构
2. **rc-collapse children deprecated** - 需要将`children`迁移到`items`属性

## 修改文件清单

- ✅ `docker-compose.yml` - 添加队列参数
- ✅ `docker-compose.override.yml` - 添加队列参数
- ✅ `docker-compose.prod.yml` - 添加队列参数
- ✅ `frontend/src/components/ocr/OCREngineSelector.tsx` - 修复message API
- ✅ `frontend/src/components/project/OCRProcessingTab.tsx` - 移除destroyOnClose

## 总结

本次修复解决了OCR处理的核心问题 - Celery worker队列配置错误导致OCR任务永远无法被执行。通过添加正确的队列监听参数,现在worker可以正确接收并处理OCR任务。同时修复了部分Ant Design的废弃API警告,提升了代码质量。

**关键修复**: 在所有docker-compose文件中的Celery worker命令添加 `-Q celery,ocr,llm,kg` 参数

**修复日期**: 2025-01-16
**修复人**: AI Assistant
