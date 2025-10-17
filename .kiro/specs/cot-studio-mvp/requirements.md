# COT Studio MVP 需求文档

## 介绍

COT Studio 是一个端到端的交互式平台，旨在帮助研究者和工程团队以高质量、可验证和可追溯的方式构建、泛化和合成 Chain-of-Thought (CoT) 数据集。该 MVP 版本将实现核心功能：文件上传 -> OCR -> 切片 -> 生成 CoT 问题与候选答案 -> 人机标注界面 -> 存储 CoT 数据 -> 基本 KG 抽取 -> 导出数据包。

## 需求

### 需求 1: 项目与文件管理

**用户故事:** 作为研究者，我希望能够创建项目并上传多种格式的文档，以便组织和管理我的数据源。

#### 验收标准

1. WHEN 用户创建新项目 THEN 系统 SHALL 生成唯一项目ID并保存项目元数据（名称、所有者、标签、创建时间）
2. WHEN 用户上传文件（PDF、Word、TXT、Markdown、LaTeX、JSON） THEN 系统 SHALL 验证文件格式并存储到对象存储
3. WHEN 文件上传完成 THEN 系统 SHALL 生成文件记录包含文件ID、哈希值、大小、MIME类型和OCR状态
4. WHEN 用户查看项目 THEN 系统 SHALL 显示所有关联文件和其处理状态
5. WHEN 用户删除项目 THEN 系统 SHALL 删除所有关联文件和数据并记录审计日志

### 需求 2: OCR 与文档切片

**用户故事:** 作为研究者，我希望系统能够自动识别文档中的文本和图像，并将其切分为可管理的片段，以便后续处理。

#### 验收标准

1. WHEN 用户触发OCR处理 THEN 系统 SHALL 支持选择OCR引擎（Alibaba AdvancedLiterateMachinery、mineru、PaddleOCR）
2. WHEN OCR处理完成 THEN 系统 SHALL 提取文本内容并保持与原文件的字符偏移映射
3. WHEN 系统执行自动切片 THEN 系统 SHALL 按段落、图片、表格、页码生成片段记录
4. WHEN 切片完成 THEN 系统 SHALL 为每个切片生成唯一ID并支持回溯到原文件位置
5. WHEN 用户查看切片 THEN 系统 SHALL 在界面中高亮显示对应的原文位置

### 需求 3: CoT 数据生成与标注

**用户故事:** 作为研究者，我希望能够选择文本片段并生成高质量的CoT问题和答案，然后通过直观的界面进行标注和评分。

#### 验收标准

1. WHEN 用户选择文本片段 THEN 系统 SHALL 调用配置的LLM API生成学术水平的问题
2. WHEN 问题生成完成 THEN 系统 SHALL 生成3-5个CoT格式的候选答案
3. WHEN 用户进行标注 THEN 系统 SHALL 提供拖拽排序功能调整答案顺序
4. WHEN 用户评分答案 THEN 系统 SHALL 提供0-1分的滑动条（最小刻度0.1）
5. WHEN 用户选择最佳答案 THEN 系统 SHALL 提供Y/N按钮且仅允许一个Y（chosen）
6. WHEN 标注完成 THEN 系统 SHALL 保存完整的CoT数据包含问题、答案、排序、分数、chosen标记

### 需求 4: 知识图谱抽取与可视化

**用户故事:** 作为研究者，我希望系统能够从CoT数据中抽取知识图谱，并提供可视化界面进行查看和查询。

#### 验收标准

1. WHEN CoT数据创建完成 THEN 系统 SHALL 自动抽取实体、属性、关系并存储到Neo4j
2. WHEN KG抽取完成 THEN 系统 SHALL 为每个节点生成向量嵌入并建立索引
3. WHEN 用户查看KG THEN 系统 SHALL 提供可视化界面显示节点和关系
4. WHEN 用户查询KG THEN 系统 SHALL 支持按实体、关系、属性进行过滤
5. WHEN 用户调整显示 THEN 系统 SHALL 支持密度调整和节点交互操作

### 需求 5: 数据导出与交付

**用户故事:** 作为研究者，我希望能够将完整的项目数据导出为标准格式，以便用于模型训练或其他用途。

#### 验收标准

1. WHEN 用户请求导出 THEN 系统 SHALL 支持JSON、Markdown、LaTeX、TXT格式
2. WHEN 导出执行 THEN 系统 SHALL 包含问题、答案、排序、分数、chosen标记、原始证据片段
3. WHEN 生成项目包 THEN 系统 SHALL 创建ZIP文件包含原文件、CoT数据、KG导出、向量索引清单、项目元数据
4. WHEN 导出完成 THEN 系统 SHALL 提供下载链接并记录导出日志
5. WHEN 用户重新导入 THEN 系统 SHALL 能够还原项目状态包含KG引用

### 需求 6: 系统配置与设置

**用户故事:** 作为系统管理员，我希望能够配置各种模型和参数，以便适应不同的使用场景。

#### 验收标准

1. WHEN 管理员访问设置页面 THEN 系统 SHALL 提供LLM API配置界面（OpenAI、DeepSeek、KIMI等）
2. WHEN 配置OCR引擎 THEN 系统 SHALL 允许选择和切换默认OCR模型
3. WHEN 设置生成参数 THEN 系统 SHALL 支持配置候选答案数量（3-5个）
4. WHEN 配置系统提示词 THEN 系统 SHALL 提供默认学术级别的prompt模板并支持自定义
5. WHEN 保存配置 THEN 系统 SHALL 验证配置有效性并应用到后续操作

### 需求 7: 审计与权限管理

**用户故事:** 作为项目管理者，我希望系统能够记录所有操作并提供适当的权限控制，以确保数据安全和可追溯性。

#### 验收标准

1. WHEN 用户执行任何操作 THEN 系统 SHALL 记录操作日志包含用户、时间、操作类型、差异哈希
2. WHEN 项目创建 THEN 系统 SHALL 设置项目级权限（owner/editor/reviewer/viewer）
3. WHEN 数据修改 THEN 系统 SHALL 生成审计记录并支持回溯到操作人
4. WHEN 敏感操作执行 THEN 系统 SHALL 要求适当权限验证
5. WHEN 查看审计日志 THEN 系统 SHALL 提供完整的操作历史和变更记录

### 需求 8: 异步任务处理

**用户故事:** 作为用户，我希望长时间运行的任务（如OCR、KG抽取）能够在后台处理，并及时获得进度反馈。

#### 验收标准

1. WHEN 用户触发长耗时任务 THEN 系统 SHALL 将任务加入异步队列（Celery）
2. WHEN 任务执行中 THEN 系统 SHALL 通过WebSocket或轮询提供进度更新
3. WHEN 任务完成 THEN 系统 SHALL 通知用户并更新相关状态
4. WHEN 任务失败 THEN 系统 SHALL 记录错误信息并提供重试选项
5. WHEN 用户查看任务状态 THEN 系统 SHALL 显示当前进度和预估完成时间