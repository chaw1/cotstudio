# 前端仪表板错误修复需求文档

## 介绍

本文档定义了修复COT Studio前端主页仪表板错误的需求。当前前端主页显示"系统监控不可用"和"用户贡献数据不可用"的错误，控制台显示多个API请求返回401未授权错误。需要修复这些认证和API调用问题，确保仪表板功能正常运行。

## 需求

### 需求 1：修复API认证问题

**用户故事：** 作为用户，我希望前端能够正确发送认证token到后端API，以便系统监控和用户贡献数据能够正常加载。

#### 验收标准

1. WHEN 用户访问仪表板页面 THEN 前端 SHALL 正确获取并发送有效的认证token
2. WHEN 前端调用系统监控API THEN 请求 SHALL 包含正确的Authorization头
3. WHEN 前端调用用户贡献API THEN 请求 SHALL 包含正确的Authorization头
4. WHEN token过期或无效 THEN 系统 SHALL 自动刷新token或重定向到登录页面
5. WHEN API请求成功 THEN 前端 SHALL 正确处理响应数据并显示内容

### 需求 2：修复系统监控组件

**用户故事：** 作为管理员，我希望能够在仪表板上看到实时的系统资源使用情况，包括CPU、内存、磁盘使用率等信息。

#### 验收标准

1. WHEN 系统监控组件加载 THEN 组件 SHALL 成功调用 `/api/v1/system/resources` API
2. WHEN API返回数据 THEN 组件 SHALL 正确显示CPU使用率进度条
3. WHEN API返回数据 THEN 组件 SHALL 正确显示内存使用情况和格式化的大小
4. WHEN API返回数据 THEN 组件 SHALL 正确显示磁盘使用情况
5. WHEN API调用失败 THEN 组件 SHALL 显示友好的错误信息和重试按钮
6. WHEN 用户点击重试按钮 THEN 组件 SHALL 重新尝试获取数据

### 需求 3：修复用户贡献可视化组件

**用户故事：** 作为管理员，我希望能够在仪表板上看到用户贡献的可视化图表，了解用户和项目之间的关系。

#### 验收标准

1. WHEN 用户贡献组件加载 THEN 组件 SHALL 成功调用 `/api/v1/analytics/user-contributions` API
2. WHEN API返回数据 THEN 组件 SHALL 正确转换数据为图形可视化格式
3. WHEN 显示用户节点 THEN 节点大小 SHALL 与用户的CoT数据量相关
4. WHEN 显示项目节点 THEN 节点大小 SHALL 与项目的CoT数据量相关
5. WHEN API调用失败 THEN 组件 SHALL 显示友好的错误信息和重试按钮
6. WHEN 用户点击节点 THEN 组件 SHALL 显示节点详细信息

### 需求 4：改进错误处理和用户体验

**用户故事：** 作为用户，我希望当系统出现错误时能够看到清晰的错误信息，并且有明确的解决方案或重试选项。

#### 验收标准

1. WHEN API请求失败 THEN 前端 SHALL 显示具体的错误原因而不是通用错误
2. WHEN 认证失败 THEN 系统 SHALL 提示用户重新登录
3. WHEN 网络错误 THEN 系统 SHALL 显示网络连接问题提示
4. WHEN 服务器错误 THEN 系统 SHALL 显示服务器暂时不可用提示
5. WHEN 显示错误信息 THEN 界面 SHALL 提供重试或刷新选项
6. WHEN 组件加载中 THEN 界面 SHALL 显示适当的加载指示器

### 需求 5：优化仪表板数据刷新机制

**用户故事：** 作为用户，我希望仪表板数据能够自动刷新，保持信息的实时性，同时不会因为频繁请求影响性能。

#### 验收标准

1. WHEN 仪表板组件挂载 THEN 系统 SHALL 立即加载初始数据
2. WHEN 数据加载成功 THEN 系统 SHALL 设置合理的自动刷新间隔（30秒）
3. WHEN 组件卸载 THEN 系统 SHALL 清理定时器避免内存泄漏
4. WHEN 用户切换到其他页面 THEN 系统 SHALL 暂停数据刷新
5. WHEN 用户返回仪表板 THEN 系统 SHALL 恢复数据刷新
6. WHEN 连续请求失败 THEN 系统 SHALL 增加重试间隔避免过度请求

### 需求 6：验证后端API可用性

**用户故事：** 作为开发者，我希望确认后端API端点正确实现并且可以正常响应请求。

#### 验收标准

1. WHEN 调用 `/api/v1/system/resources` THEN API SHALL 返回正确格式的系统资源数据
2. WHEN 调用 `/api/v1/system/health` THEN API SHALL 返回系统健康状态信息
3. WHEN 调用 `/api/v1/analytics/user-contributions` THEN API SHALL 返回用户贡献统计数据
4. WHEN 使用有效token调用API THEN 所有端点 SHALL 返回200状态码
5. WHEN 使用无效token调用API THEN 所有端点 SHALL 返回401状态码
6. WHEN API发生内部错误 THEN 端点 SHALL 返回500状态码和错误详情