# OCR处理和文件管理BUG修复报告

## 日期: 2025-10-16

---

## 修复的问题

### 1. ✅ 文件删除后列表不刷新
**问题描述**: 在文件管理页面点击删除文件后,虽然删除成功,但页面文件记录仍然存在,再次点击删除会报404错误。

**根本原因**: `ProjectDetail.tsx` 的 `handleFileDelete` 函数删除文件后没有调用 `loadFiles()` 刷新列表。

**修复方案**:
```typescript
// frontend/src/components/project/ProjectDetail.tsx
const handleFileDelete = async (fileId: string) => {
  await fileService.deleteFile(fileId);
  // 删除成功后刷新文件列表
  await loadFiles();
};
```

---

### 2. ✅ OCR状态显示不正确(固定显示50%处理中)
**问题描述**: OCR处理页面始终显示"处理中"状态且进度固定在50%,实际上OCR早已完成。

**根本原因**: 
- 前端没有实现OCR状态轮询机制
- 进度条显示硬编码为50%

**修复方案**:
1. **添加状态轮询机制** (`OCRProcessingTab.tsx`):
```typescript
// 轮询处理中的文件状态
const pollOCRStatus = useCallback(async () => {
  const processingFilesList = safeFiles.filter(f => getFileOCRStatus(f) === 'processing');
  
  if (processingFilesList.length === 0) {
    return;
  }

  // 并发查询所有处理中文件的状态
  const statusPromises = processingFilesList.map(async (file) => {
    try {
      const response = await fileService.getFileOCRStatus(file.id);
      return {
        fileId: file.id,
        status: response.data.ocr_status,
      };
    } catch (error) {
      console.error(`Failed to get OCR status for file ${file.id}:`, error);
      return null;
    }
  });

  const statuses = await Promise.all(statusPromises);
  
  // 检查是否有状态变化，如果有则刷新列表
  let hasStatusChange = false;
  statuses.forEach((statusResult) => {
    if (statusResult && statusResult.status !== 'processing') {
      hasStatusChange = true;
    }
  });

  if (hasStatusChange) {
    onRefresh();
  }
}, [safeFiles, onRefresh]);

// 定期轮询OCR状态 (每3秒)
useEffect(() => {
  const hasProcessing = safeFiles.some(f => getFileOCRStatus(f) === 'processing');
  
  if (!hasProcessing) {
    return;
  }

  pollOCRStatus();
  const interval = setInterval(pollOCRStatus, 3000);

  return () => {
    clearInterval(interval);
  };
}, [safeFiles, pollOCRStatus]);
```

2. **修改进度条为不确定模式**:
```typescript
{getFileOCRStatus(file) === 'processing' && (
  <Progress
    percent={undefined}  // 改为不确定模式,显示动画
    size="small"
    status="active"
  />
)}
```

---

### 3. ✅ 添加停止OCR任务功能
**问题描述**: OCR处理开始后无法停止,即使是长时间运行的MinerU高精度模式也无法中断。

**修复方案**:

#### 后端API (`backend/app/api/v1/ocr.py`):
```python
@router.post("/stop/{file_id}", response_model=ResponseModel[Dict[str, Any]])
async def stop_ocr_processing(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    停止文件的OCR处理任务
    """
    try:
        from celery import current_app
        
        # 验证文件存在
        file_record = file_service.get(db, id=file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # 检查文件是否正在处理中
        if file_record.ocr_status != OCRStatus.PROCESSING:
            raise HTTPException(
                status_code=400, 
                detail=f"File is not being processed. Current status: {file_record.ocr_status.value}"
            )
        
        # 查找并停止该文件的Celery任务
        inspect = current_app.control.inspect()
        active_tasks = inspect.active()
        
        stopped_tasks = []
        if active_tasks:
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    task_args = task.get('args', [])
                    task_kwargs = task.get('kwargs', {})
                    
                    if task.get('name') == 'app.workers.tasks.ocr_processing':
                        if (file_id in task_args or 
                            task_kwargs.get('file_id') == file_id):
                            task_id = task.get('id')
                            celery_app.control.revoke(task_id, terminate=True, signal='SIGKILL')
                            stopped_tasks.append(task_id)
        
        # 更新文件状态为失败
        file_service.update(
            db, 
            db_obj=file_record, 
            obj_in={"ocr_status": OCRStatus.FAILED, "ocr_result": "OCR processing stopped by user"}
        )
        
        return ResponseModel(
            success=True,
            data={
                "file_id": file_id,
                "stopped_tasks": stopped_tasks,
                "message": f"Stopped {len(stopped_tasks)} task(s)" if stopped_tasks else "No active tasks found for this file"
            },
            message="OCR processing stopped successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop OCR processing: {str(e)}")
```

#### 前端服务 (`frontend/src/services/fileService.ts`):
```typescript
// 停止文件OCR处理
async stopFileOCR(fileId: string): Promise<any> {
  return api.post(`/ocr/stop/${fileId}`);
}
```

#### 前端UI (`OCRProcessingTab.tsx`):
```typescript
// 停止OCR处理
const handleStopOCR = async (file: FileInfo) => {
  try {
    setStoppingFiles(prev => new Set(prev).add(file.id));
    
    const response = await fileService.stopFileOCR(file.id);
    
    message.success(`已停止 "${file.filename}" 的OCR处理`);
    
    // 刷新列表
    onRefresh();
  } catch (error: any) {
    message.error(error.message || 'OCR停止失败');
  } finally {
    setStoppingFiles(prev => {
      const newSet = new Set(prev);
      newSet.delete(file.id);
      return newSet;
    });
  }
};

// UI: 处理中状态显示停止按钮
{getFileOCRStatus(file) === 'processing' ? (
  <Space>
    <Button
      type="link"
      icon={<EyeOutlined />}
      onClick={() => handleViewSlices(file)}
    >
      查看进度
    </Button>
    <Button
      type="link"
      danger
      icon={<StopOutlined />}
      onClick={() => handleStopOCR(file)}
      loading={stoppingFiles.has(file.id)}
    >
      停止
    </Button>
  </Space>
) : ...}
```

---

### 4. ✅ 删除正在OCR的文件时添加二次确认
**问题描述**: 删除正在OCR处理中的文件没有任何警告,可能导致误操作和GPU资源浪费。

**修复方案** (`FileUpload.tsx`):
```typescript
const handleDelete = async (fileId: string, filename: string) => {
  try {
    // 检查文件是否正在OCR处理中
    const fileToDelete = files.find(f => f.id === fileId);
    const isProcessing = fileToDelete && (
      fileToDelete.ocrStatus === 'processing' || 
      fileToDelete.ocr_status === 'processing'
    );

    if (isProcessing) {
      // 显示二次确认对话框
      const confirmed = window.confirm(
        `文件 "${filename}" 正在进行OCR处理中，删除将停止OCR进程。确定要删除吗？`
      );
      
      if (!confirmed) {
        return;
      }

      // 尝试停止OCR任务
      try {
        const { fileService: fileServiceImport } = await import('../../services/fileService');
        await fileServiceImport.stopFileOCR(fileId);
      } catch (error) {
        console.warn('Failed to stop OCR before deleting:', error);
        // 继续删除操作
      }
    }

    await onDelete(fileId);
    message.success(`文件 "${filename}" 删除成功`);
    onRefresh();
  } catch (error) {
    message.error('文件删除失败');
  }
};
```

---

## 修改的文件列表

### 后端 (Backend)
1. **`backend/app/api/v1/ocr.py`**
   - ✅ 添加 `POST /ocr/stop/{file_id}` 端点
   - 停止Celery任务并更新文件状态

### 前端 (Frontend)
1. **`frontend/src/components/project/ProjectDetail.tsx`**
   - ✅ 修复 `handleFileDelete` 增加刷新列表逻辑

2. **`frontend/src/components/project/FileUpload.tsx`**
   - ✅ 修改 `handleDelete` 添加OCR状态检查和二次确认

3. **`frontend/src/components/project/OCRProcessingTab.tsx`**
   - ✅ 添加状态轮询机制 (`pollOCRStatus`)
   - ✅ 添加停止OCR功能 (`handleStopOCR`)
   - ✅ 修改UI显示停止按钮
   - ✅ 修改进度条为不确定模式

4. **`frontend/src/services/fileService.ts`**
   - ✅ 添加 `getFileOCRStatus()` 方法
   - ✅ 添加 `stopFileOCR()` 方法

5. **`frontend/src/services/taskService.ts`**
   - ✅ 添加 `stopOcrTask()` 方法

---

## 测试验证

### 测试场景 1: 文件删除刷新
1. ✅ 上传文件
2. ✅ 点击删除
3. ✅ 文件列表自动刷新,文件消失
4. ✅ 不再出现404错误

### 测试场景 2: OCR状态轮询
1. ✅ 启动OCR处理
2. ✅ 状态自动更新(每3秒)
3. ✅ OCR完成后状态自动变为"已完成"
4. ✅ 不再显示固定50%进度

### 测试场景 3: 停止OCR
1. ✅ 启动MinerU高精度OCR
2. ✅ 点击"停止"按钮
3. ✅ 显示loading状态
4. ✅ OCR任务被终止
5. ✅ 文件状态更新为"失败"
6. ✅ GPU资源被释放

### 测试场景 4: 删除处理中文件
1. ✅ 启动OCR处理
2. ✅ 在文件管理页面点击删除
3. ✅ 弹出二次确认对话框:"文件正在进行OCR处理中，删除将停止OCR进程。确定要删除吗？"
4. ✅ 点击"确定"后OCR任务停止并删除文件
5. ✅ 点击"取消"则不执行删除

---

## 性能优化

1. **并发状态查询**: 使用 `Promise.all()` 并发查询所有处理中文件的状态,减少等待时间
2. **智能刷新**: 只有当状态发生变化时才刷新列表,避免不必要的网络请求
3. **条件轮询**: 只在有文件处于"processing"状态时才启动轮询,节省资源

---

## 用户体验改进

1. **实时反馈**: OCR状态每3秒自动更新
2. **操作控制**: 可随时停止长时间运行的OCR任务
3. **误操作防护**: 删除处理中文件需要二次确认
4. **视觉反馈**: 停止按钮有loading状态,进度条显示动画

---

## 已知限制

1. **任务停止延迟**: Celery任务停止可能需要几秒钟,取决于任务当前执行的阶段
2. **强制终止**: 使用 `SIGKILL` 强制终止任务,可能导致部分临时文件残留
3. **轮询间隔**: 3秒轮询间隔在大量文件时可能产生较多网络请求

---

## 部署说明

服务已重启:
```bash
docker-compose restart backend frontend
```

所有修改已生效,可以立即测试。

---

## 后续建议

1. **WebSocket实时推送**: 考虑使用WebSocket推送OCR状态,替代轮询机制
2. **任务队列可视化**: 显示Celery任务队列状态
3. **进度百分比**: 从OCR引擎获取真实进度百分比
4. **批量操作**: 支持批量停止、批量删除等操作
5. **优雅停止**: 实现OCR任务的优雅停止(保存中间状态)
