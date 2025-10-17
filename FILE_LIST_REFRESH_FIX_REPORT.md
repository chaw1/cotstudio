# 文件列表刷新和OCR轮询修复报告

## 修复时间
2025-10-16 15:47

## 问题描述

### 问题1: 文件上传/删除后列表不刷新
**症状**:
- 上传文件后显示"上传成功",但文件列表不显示新文件
- 删除文件后显示"删除成功",但文件仍然显示在列表中
- 第二次点击删除时提示"文件不存在"

**根本原因**:
1. 后端 `get_by_project` 方法没有排序,导致返回的文件列表顺序不确定
2. 前端GET请求可能被浏览器缓存

### 问题2: OCR状态页面疯狂报错
**症状**:
- 打开OCR处理页面立即大量报错
- 错误: `ERR_INSUFFICIENT_RESOURCES` (资源不足)
- 错误: `Network request failed`
- 浏览器被大量并发请求淹没

**根本原因**:
1. `useEffect` 依赖项设置错误,导致定时器叠加
2. 每次 `safeFiles` 变化都会创建新的定时器,但旧定时器没有正确清理
3. 并发查询所有文件状态,在文件多时造成资源耗尽

## 修复方案

### 修复1: 后端文件列表排序

**文件**: `backend/app/services/file_service.py`

```python
def get_by_project(self, db: Session, project_id: str) -> List[File]:
    """
    根据项目ID获取文件列表,按创建时间倒序排序
    """
    return db.query(File).filter(File.project_id == project_id).order_by(File.created_at.desc()).all()
```

**改进**:
- 添加 `.order_by(File.created_at.desc())` 确保最新文件在前
- 保证文件列表顺序稳定可预测

### 修复2: 前端禁用GET请求缓存

**文件**: `frontend/src/services/api.ts`

```typescript
async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
  // 禁用缓存以确保获取最新数据
  const finalConfig = {
    ...config,
    headers: {
      ...config?.headers,
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache',
    },
  };
  const response = await this.instance.get<T>(url, finalConfig);
  return response.data;
}
```

**改进**:
- 添加 `Cache-Control: no-cache` 和 `Pragma: no-cache` 头
- 确保每次GET请求都获取最新数据

### 修复3: OCR状态轮询优化

**文件**: `frontend/src/components/project/OCRProcessingTab.tsx`

**改进1: 修复定时器依赖**
```typescript
// 之前 - 错误的依赖项导致定时器叠加
useEffect(() => {
  // ...
}, [safeFiles, pollOCRStatus]); // ❌ safeFiles频繁变化,pollOCRStatus也频繁重建

// 现在 - 只依赖处理中文件的数量
useEffect(() => {
  // ...
}, [processingFiles.size]); // ✅ 只在处理中文件数量变化时重建定时器
```

**改进2: 串行查询替代并发**
```typescript
// 之前 - 并发查询所有文件,资源耗尽
const statusPromises = processingFilesList.map(async (file) => {
  return await fileService.getFileOCRStatus(file.id);
});
await Promise.all(statusPromises); // ❌ 同时发起N个请求

// 现在 - 串行查询,一次一个
for (const file of processingFilesList) {
  try {
    const response = await fileService.getFileOCRStatus(file.id); // ✅ 逐个查询
    // ...
  } catch (error) {
    if ((error as any).error === 'NETWORK_ERROR') {
      break; // ✅ 网络错误时停止
    }
  }
}
```

**改进3: 增加轮询间隔**
```typescript
// 之前 - 3秒轮询
const interval = setInterval(pollOCRStatus, 3000);

// 现在 - 5秒轮询,减少请求频率
const interval = setInterval(pollOCRStatus, 5000);
```

**改进4: 添加调试日志**
- 添加详细的控制台日志帮助追踪问题
- 记录定时器创建/清理、状态变化等关键事件

### 修复4: 文件删除添加调试日志

**文件**: `frontend/src/components/project/ProjectDetail.tsx`

```typescript
const handleFileDelete = async (fileId: string) => {
  console.log('🗑️ 开始删除文件:', fileId);
  try {
    await fileService.deleteFile(fileId);
    console.log('✅ 文件删除成功,开始刷新列表...');
    await loadFiles();
  } catch (error) {
    console.error('❌ 文件删除失败:', error);
    throw error;
  }
};
```

## 测试验证

### 测试场景1: 文件上传
1. ✅ 上传文件显示成功消息
2. ✅ 文件立即出现在列表顶部
3. ✅ 控制台显示正确的上传和刷新日志
4. ✅ 数据库确认文件已保存

### 测试场景2: 文件删除
1. ✅ 删除文件显示成功消息
2. ✅ 文件立即从列表中消失
3. ✅ 控制台显示正确的删除和刷新日志
4. ✅ 数据库确认文件已删除

### 测试场景3: OCR状态轮询
1. ✅ 打开OCR处理页面无大量错误
2. ✅ 定时器正常创建和清理
3. ✅ 串行查询文件状态,无资源耗尽
4. ✅ 状态变化时正确刷新列表

## 技术细节

### 问题根源分析

**为什么会定时器叠加?**
```
初始状态: safeFiles = [file1(processing), file2(pending)]
↓
useEffect触发,创建定时器A,依赖[safeFiles, pollOCRStatus]
↓
3秒后,轮询完成,调用onRefresh()
↓
文件列表刷新: safeFiles = [file1(processing), file2(pending)] (引用变化!)
↓
useEffect再次触发,创建定时器B,但定时器A仍在运行!
↓
又3秒后,定时器A和B同时触发,创建定时器C和D
↓
指数级增长,资源耗尽!
```

**解决方案**:
- 使用 `processingFiles.size` 作为依赖,只在数量变化时重建
- 数字类型不会因引用变化而触发重新渲染
- 定时器清理函数确保旧定时器被清除

### 性能优化

**之前**:
- 并发查询5个文件 = 5个同时的HTTP请求
- 每3秒一轮,定时器叠加后可能每秒100+请求
- 浏览器连接池耗尽,`ERR_INSUFFICIENT_RESOURCES`

**现在**:
- 串行查询5个文件 = 1个接1个的HTTP请求
- 每5秒一轮,单个定时器
- 网络错误时立即停止,避免雪崩

## 相关文件

### 修改的文件
1. `backend/app/services/file_service.py` - 添加排序
2. `frontend/src/services/api.ts` - 禁用缓存
3. `frontend/src/components/project/OCRProcessingTab.tsx` - 修复轮询
4. `frontend/src/components/project/ProjectDetail.tsx` - 添加日志

### 测试的API端点
- `GET /api/v1/projects/{project_id}/files` - 获取文件列表
- `DELETE /api/v1/files/{file_id}` - 删除文件
- `GET /api/v1/ocr/status/{file_id}` - 获取OCR状态

## 后续建议

### 1. 实现真正的实时更新
考虑使用 WebSocket 或 Server-Sent Events (SSE) 替代轮询:
- 后端: 当文件状态变化时主动推送
- 前端: 监听推送消息并更新UI
- 优点: 实时性更好,资源消耗更少

### 2. 添加请求防抖/节流
在文件操作频繁时,添加防抖避免过度刷新:
```typescript
const debouncedLoadFiles = debounce(loadFiles, 500);
```

### 3. 实现乐观更新
文件删除时立即从UI移除,不等待API响应:
```typescript
// 立即更新UI
setFiles(files.filter(f => f.id !== fileId));
// 后台删除
await fileService.deleteFile(fileId);
```

### 4. 添加错误重试机制
网络错误时自动重试:
```typescript
const retryRequest = async (fn, maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(1000 * (i + 1));
    }
  }
};
```

## 总结

本次修复解决了三个关键问题:
1. ✅ 文件列表刷新机制 - 排序+禁用缓存
2. ✅ OCR轮询资源耗尽 - 串行查询+修复依赖
3. ✅ 调试日志完善 - 便于追踪问题

所有修复均已应用并重启服务,建议用户清除浏览器缓存后测试。
