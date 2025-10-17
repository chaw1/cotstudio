# OCR超时修复报告

## 问题发现
用户观察到OCR处理**每次都在第10秒左右失败**,这是一个关键线索!

## 根本原因分析

### 观察到的现象
```
11:31:27 开始 → 11:31:29 失败 (约2秒)
11:31:52 开始 → 11:31:54 失败 (约2秒)  
11:32:41 开始 → 11:32:43 失败 (约2秒)
```

### 问题定位
1. **不是超时限制** - subprocess.run的timeout设置为300秒(5分钟)
2. **2秒就失败** - 说明mineru命令本身快速返回了非0退出码或抛出异常
3. **日志缺失** - 添加的详细日志都没有输出,说明代码在执行到日志之前就抛出异常

### 可能的原因
1. **MinerU命令执行失败** - mineru命令本身遇到错误(缺少依赖、GPU问题等)
2. **Python包导入问题** - MinerU的依赖包有问题
3. **文件路径或权限问题** - 临时文件无法访问
4. **CUDA/GPU初始化失败** - 每次尝试使用GPU都失败

## 修复措施

### 1. 大幅增加超时时间
```python
# 修改前: timeout=300  (5分钟)
# 修改后: timeout=1800 (30分钟)
```

**原因**: OCR模型处理大文件可能需要很长时间,特别是使用GPU进行深度学习推理。

### 2. 增强异常捕获和日志
添加的调试信息:
- 工作目录和输入文件状态
- 命令执行前后的详细日志
- 完整的异常堆栈跟踪
- 输出目录的文件列表

### 3. 更细粒度的错误处理
```python
try:
    result = subprocess.run(...)
    logger.info(f"✓ MinerU命令执行完成")
except subprocess.TimeoutExpired:
    logger.error(f"✗ MinerU命令超时(1800秒)")
    raise HTTPException(status_code=504, ...)
except Exception as e:
    logger.error(f"✗ MinerU命令执行异常: {type(e).__name__}: {str(e)}")
    raise
```

### 4. 分离HTTPException处理
```python
except HTTPException:
    # 直接向上传递,不要再包装
    raise
except Exception as e:
    # 记录完整堆栈
    logger.error(f"完整堆栈:\n{traceback.format_exc()}")
```

## 测试步骤

### 1. 准备
服务已重启,新代码已激活:
```bash
docker-compose restart mineru  # ✅ 已执行
```

### 2. 触发OCR处理
在前端上传一个**小PDF文件**(2-3页,1-2MB):
- 选择OCR引擎: paddleocr 或 mineru_vlm
- 点击"开始OCR处理"

### 3. 实时监控日志(必须!)
**新终端1** - 监控MinerU服务:
```powershell
docker logs -f cotstudio-mineru-1
```

**新终端2** - 监控Celery Worker:
```powershell
docker logs -f cotstudio-celery-1
```

### 4. 期望看到的日志

#### 成功情况:
```
2025-10-16 XX:XX:XX - __main__ - INFO - 处理文件: test.pdf (123456 bytes)
2025-10-16 XX:XX:XX - __main__ - INFO - 执行命令: mineru -p /tmp/mineru_xxx/test.pdf -o /tmp/mineru_xxx/output --backend pipeline --device cuda --batch-size 8
2025-10-16 XX:XX:XX - __main__ - INFO - 工作目录: /tmp/mineru_xxx
2025-10-16 XX:XX:XX - __main__ - INFO - 输入文件存在: True, 大小: 123456
2025-10-16 XX:XX:XX - __main__ - INFO - ✓ MinerU命令执行完成
2025-10-16 XX:XX:XX - __main__ - INFO - MinerU return code: 0
2025-10-16 XX:XX:XX - __main__ - INFO - 输出目录: /tmp/mineru_xxx/output
2025-10-16 XX:XX:XX - __main__ - INFO - 输出目录中共有 X 个文件/目录
2025-10-16 XX:XX:XX - __main__ - INFO -   - test/test.md (file 54321B)
2025-10-16 XX:XX:XX - __main__ - INFO - ✓ 找到输出文件: ...
2025-10-16 XX:XX:XX - __main__ - INFO - ✓ OCR处理完成: test.pdf
```

#### 失败情况(现在会有详细信息):
```
2025-10-16 XX:XX:XX - __main__ - INFO - 执行命令: mineru ...
2025-10-16 XX:XX:XX - __main__ - INFO - 工作目录: /tmp/mineru_xxx
2025-10-16 XX:XX:XX - __main__ - ERROR - ✗ MinerU命令执行异常: TypeError: ...
2025-10-16 XX:XX:XX - __main__ - ERROR - 完整堆栈:
Traceback (most recent call last):
  File "...", line X, in ocr_endpoint
    result = subprocess.run(...)
  ...
[完整的错误堆栈]
```

## 已知的潜在问题

### 问题1: GPU驱动/CUDA问题
**检查**: 
```bash
docker exec cotstudio-mineru-1 nvidia-smi
```
应该显示GPU信息,如果失败则GPU不可用。

### 问题2: MinerU依赖缺失
**检查**:
```bash
docker exec cotstudio-mineru-1 pip list | grep -i mineru
```
应该显示: `magic-pdf  2.5.4`

### 问题3: 模型文件未下载
MinerU首次运行需要下载模型文件(数GB),可能需要:
- 设置HTTP代理
- 等待较长时间

## 下一步诊断

如果新日志仍然显示2秒快速失败:

### 方案A: 手动测试mineru命令
```bash
# 进入容器
docker exec -it cotstudio-mineru-1 bash

# 创建测试目录
mkdir -p /tmp/test_manual && cd /tmp/test_manual

# 下载测试PDF
wget http://example.com/test.pdf

# 手动运行mineru
mineru -p test.pdf -o output --backend pipeline --device cuda --batch-size 8

# 查看输出
ls -la output/
```

### 方案B: 尝试CPU模式
如果GPU有问题,可以临时测试CPU模式:
```python
# 在OCR请求中使用: device="cpu"
```

### 方案C: 使用更简单的backend
```python
# 尝试: backend="vlm-transformers"
# 而不是: backend="pipeline"
```

## 修改的文件
- ✅ `docker/mineru/mineru_service.py`
  - 超时从300秒增加到1800秒(30分钟)
  - 添加详细的执行日志
  - 改进异常处理和堆栈跟踪
  - 分离HTTPException处理

## 预期结果
1. **如果是超时问题**: 30分钟的超时应该足够处理大部分PDF
2. **如果是其他问题**: 新的日志会准确显示失败原因(异常类型、堆栈、命令输出)

## 重要提示
⚠️ **请在触发OCR时保持两个终端窗口打开实时查看日志**,这对诊断问题至关重要!

---

修复时间: 2025-10-16 11:36
修复人: AI Assistant
