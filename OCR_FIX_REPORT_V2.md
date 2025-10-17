# OCR功能修复与百分比格式统一报告

## 修复日期
2025-10-16 11:25

## 问题1: OCR处理失败 - MinerU输出文件未找到

### 问题分析
Celery Worker正确接收并执行OCR任务,但MinerU服务返回500错误:"未找到OCR输出结果"。

**根本原因**:
- MinerU 2.5 的输出目录结构可能与预期不符
- 代码只检查了一种固定的输出路径格式
- 缺少详细的调试日志来追踪实际的输出文件位置

### 修复方案

#### 1. 增强调试日志
在 `docker/mineru/mineru_service.py` 中添加:
- 记录mineru命令的return code、stdout、stderr
- 列出输出目录的完整文件结构
- 显示所有检查的路径

#### 2. 支持多种输出路径格式
尝试以下路径:
```python
possible_paths = [
    output_dir / Path(file.filename).stem / f"{Path(file.filename).stem}.md",  # 标准: output/<name>/<name>.md
    output_dir / f"{Path(file.filename).stem}.md",                              # 扁平: output/<name>.md
    output_dir / "auto" / f"{Path(file.filename).stem}.md",                    # auto: output/auto/<name>.md
]
```

#### 3. 兜底搜索
如果以上路径都不存在,搜索输出目录中的任何`.md`文件作为结果。

### 测试步骤
1. 重启MinerU服务: `docker-compose restart mineru`
2. 在前端上传一个小PDF文件(1-3页)
3. 触发OCR处理
4. 实时查看MinerU日志:
   ```bash
   docker logs -f cotstudio-mineru-1
   ```
5. 检查日志中的输出:
   - 命令执行返回码
   - 输出目录文件列表
   - 实际找到的markdown文件路径

### 预期结果
日志应显示:
```
2025-10-16 XX:XX:XX - __main__ - INFO - MinerU return code: 0
2025-10-16 XX:XX:XX - __main__ - INFO - 输出目录: /tmp/mineru_xxxxx/output
2025-10-16 XX:XX:XX - __main__ - INFO - 输出目录中共有 X 个文件/目录
2025-10-16 XX:XX:XX - __main__ - INFO -   - <filename>/<filename>.md (file 12345B)
2025-10-16 XX:XX:XX - __main__ - INFO - ✓ 找到输出文件: /tmp/.../<filename>.md
```

---

## 问题2: 百分比有效位数不统一

### 问题描述
平台各处显示的百分比有效位数不一致:
- 有的使用 `toFixed(0)` (整数)
- 有的使用 `toFixed(1)` (1位小数)
- 有的使用 `toFixed(2)` (2位小数)

用户要求统一为2位小数。

### 修复范围

#### 已修复的文件 (全部改为 `.toFixed(2)`)

1. **KGStatsPanel.tsx**
   - 图谱密度进度条: `toFixed(1)` → `toFixed(2)`
   - 平均连接度: `toFixed(1)` → `toFixed(2)`

2. **SystemResourceMonitor.tsx**
   - CPU使用率百分比: `toFixed(1)` → `toFixed(2)`

3. **TaskStatisticsChart.tsx**
   - 成功率: `toFixed(1)` → `toFixed(2)`
   - 平均执行时间: `toFixed(1)` → `toFixed(2)`

4. **QueueInfoPanel.tsx**
   - 活跃任务百分比: `toFixed(0)` → `toFixed(2)`
   - 预定任务百分比: `toFixed(0)` → `toFixed(2)`

5. **TestDashboard.tsx**
   - 测试通过率: `toFixed(1)` → `toFixed(2)`

#### 保持不变的部分

以下内容不是百分比,保持原有精度:
- 文件大小 (GB/MB): 保持 `toFixed(2)`
- 系统负载 (load1/5/15): 保持 `toFixed(2)`
- 响应时间 (ms): 保持 `toFixed(0)` 或 `toFixed(2)`

### 修改统计
- 修改文件数: 5个
- 修改点数: 9处
- 统一格式: `.toFixed(2)`

---

## 已修复的其他问题(上次会话)

### ✅ Celery Worker队列配置
- **问题**: Worker只监听默认队列,无法接收OCR任务
- **修复**: 在所有docker-compose文件中添加 `-Q celery,ocr,llm,kg`
- **状态**: 已验证,Worker现在正确监听4个队列

### ✅ Ant Design 警告
- **OCREngineSelector.tsx**: 静态message API → `App.useApp()` hook
- **OCRProcessingTab.tsx**: 移除废弃的 `destroyOnClose` 属性

---

## 待处理问题

### ⚠️ 数据库Enum大小写不一致
- Python代码: 小写 (`"pending"`, `"processing"`)
- 数据库实际: 大写 (`PENDING`, `PROCESSING`)
- 建议: 统一为大写(符合PostgreSQL标准)

### ⚠️ 其他Ant Design警告
1. Form.Item with name must have single child
2. rc-collapse `children` deprecated → 使用 `items` prop

---

## 测试检查清单

### OCR功能测试
- [ ] 上传PDF文件
- [ ] 选择OCR引擎(paddleocr/mineru_vlm)
- [ ] 触发OCR处理
- [ ] 查看MinerU日志输出
- [ ] 确认文件状态变为COMPLETED
- [ ] 验证切片数据已生成
- [ ] 检查切片管理中的文本/图像/表格数据

### 百分比显示测试
- [ ] 知识图谱统计页面 - 图谱密度显示2位小数
- [ ] 系统资源监控 - CPU使用率显示2位小数
- [ ] 任务统计图表 - 成功率显示2位小数
- [ ] 队列信息面板 - 活跃/预定百分比显示2位小数
- [ ] 测试控制台 - 通过率显示2位小数

### 前端警告检查
- [ ] 打开浏览器Console
- [ ] 确认无Ant Design deprecation警告
- [ ] 确认无React strict mode警告

---

## 修改文件清单

### Backend
- ✅ `docker-compose.yml` - Celery队列配置
- ✅ `docker-compose.override.yml` - Celery队列配置
- ✅ `docker-compose.prod.yml` - Celery队列配置
- ✅ `docker/mineru/mineru_service.py` - 增强调试日志,支持多种输出路径

### Frontend
- ✅ `frontend/src/components/ocr/OCREngineSelector.tsx` - message API修复
- ✅ `frontend/src/components/project/OCRProcessingTab.tsx` - destroyOnClose移除
- ✅ `frontend/src/components/knowledge-graph/KGStatsPanel.tsx` - 百分比格式统一
- ✅ `frontend/src/components/dashboard/SystemResourceMonitor.tsx` - 百分比格式统一
- ✅ `frontend/src/components/task/TaskStatisticsChart.tsx` - 百分比格式统一
- ✅ `frontend/src/components/task/QueueInfoPanel.tsx` - 百分比格式统一
- ✅ `frontend/src/pages/TestDashboard.tsx` - 百分比格式统一

---

## 下一步行动

### 立即执行
1. **测试OCR功能**: 上传PDF并查看MinerU日志,确认输出文件路径
2. **验证百分比**: 浏览各个页面,确认所有百分比都是2位小数

### 后续优化
1. 根据MinerU日志确定正确的输出路径格式
2. 修复数据库Enum大小写不一致问题
3. 处理剩余的Ant Design警告
4. 添加OCR进度实时更新(WebSocket)

---

## 关键命令

```bash
# 查看Celery worker日志
docker logs -f cotstudio-celery-1

# 查看MinerU服务日志
docker logs -f cotstudio-mineru-1

# 重启MinerU服务
docker-compose restart mineru

# 检查Worker监听的队列
docker exec cotstudio-celery-1 celery -A app.core.celery_app inspect active_queues

# 查看OCR处理状态
docker exec cotstudio-postgres-1 psql -U cotuser -d cotdb -c "SELECT filename, ocr_status, ocr_engine, updated_at FROM files ORDER BY updated_at DESC LIMIT 5;"
```

---

## 修复人员
AI Assistant

## 备注
- MinerU服务已重启,新的调试日志已激活
- 需要实际触发一次OCR处理来获取详细的调试输出
- 百分比格式已全局统一为2位小数
