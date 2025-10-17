# 知识图谱可视化组件

这个模块实现了COT Studio的知识图谱可视化功能，基于Cytoscape.js构建，提供了丰富的交互功能和可视化选项。

## 组件结构

### 核心组件

- **KnowledgeGraphViewer**: 主要的知识图谱可视化组件
- **KGControlPanel**: 图谱控制面板，包含布局、视图控制等功能
- **KGSearchPanel**: 搜索和过滤面板
- **KGEntityPanel**: 实体/关系详情面板
- **KGStatsPanel**: 图谱统计信息面板
- **KGDemo**: 演示组件

### 服务

- **knowledgeGraphService**: 知识图谱API服务

## 功能特性

### 1. 多种布局算法
- **Dagre**: 层次布局，适合有向图和层次结构
- **CoSE-Bilkent**: 力导向布局，适合复杂网络结构
- **Cola**: 约束布局，适合大型图谱
- **Circle**: 圆形布局
- **Grid**: 网格布局
- **Random**: 随机布局
- **Concentric**: 同心圆布局

### 2. 交互功能
- 节点和边的点击选择
- 拖拽移动节点
- 缩放和平移
- 双击节点查看详情
- 右键菜单操作

### 3. 搜索和过滤
- 实体名称搜索
- 实体类型过滤
- 关系类型过滤
- 最小连接数过滤
- 最大节点数限制
- 预设快速过滤器

### 4. 可视化定制
- 节点大小调整
- 边粗细调整
- 标签大小调整
- 颜色主题
- 图谱密度控制

### 5. 数据导出
- PNG格式导出
- JPG格式导出
- 高分辨率输出
- 全图导出

### 6. 统计分析
- 节点和边数量统计
- 实体类型分布
- 关系类型分布
- 图谱密度分析
- 质量指标评估

## 使用方法

### 基本用法

```tsx
import { KnowledgeGraphViewer } from '../components/knowledge-graph';

function MyComponent() {
  return (
    <KnowledgeGraphViewer
      projectId="your-project-id"
      height={600}
      showControls={true}
      showStats={true}
      onNodeSelect={(node) => console.log('Selected:', node)}
      onEdgeSelect={(edge) => console.log('Selected:', edge)}
    />
  );
}
```

### 高级配置

```tsx
<KnowledgeGraphViewer
  projectId="project-123"
  height={800}
  width="100%"
  initialLayout="cose-bilkent"
  showControls={true}
  showStats={true}
  onNodeSelect={handleNodeSelect}
  onEdgeSelect={handleEdgeSelect}
/>
```

### 仅显示图谱（无控制面板）

```tsx
<KnowledgeGraphViewer
  projectId="project-123"
  height={600}
  showControls={false}
  showStats={false}
/>
```

## API接口

### KnowledgeGraphViewer Props

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| projectId | string | - | 项目ID（必需） |
| height | number | 600 | 图谱高度 |
| width | number \| string | - | 图谱宽度 |
| initialLayout | string | 'dagre' | 初始布局算法 |
| showControls | boolean | true | 是否显示控制面板 |
| showStats | boolean | true | 是否显示统计面板 |
| onNodeSelect | (node: KGEntity) => void | - | 节点选择回调 |
| onEdgeSelect | (edge: KGRelation) => void | - | 边选择回调 |

### 数据类型

```typescript
interface KGEntity {
  id: string;
  label: string;
  type: string;
  properties: Record<string, any>;
}

interface KGRelation {
  id: string;
  source: string;
  target: string;
  type: string;
  properties: Record<string, any>;
}
```

## 样式定制

### CSS类名

- `.kg-viewer`: 主容器
- `.kg-control-panel`: 控制面板
- `.kg-search-panel`: 搜索面板
- `.kg-entity-panel`: 实体详情面板
- `.kg-stats-panel`: 统计面板

### 节点样式

节点样式基于实体类型自动分配颜色：

- Person: #FF6B6B (红色)
- Organization: #4ECDC4 (青色)
- Location: #45B7D1 (蓝色)
- Concept: #96CEB4 (绿色)
- Event: #FFEAA7 (黄色)
- Document: #DDA0DD (紫色)
- Technology: #98D8C8 (薄荷绿)

## 性能优化

### 大型图谱处理

1. **节点数量限制**: 默认最多显示100个节点
2. **按需加载**: 支持分页和增量加载
3. **视口裁剪**: 只渲染可见区域的节点
4. **缓存机制**: 缓存布局计算结果

### 渲染优化

1. **WebGL渲染**: 大型图谱自动启用WebGL
2. **LOD**: 根据缩放级别调整细节层次
3. **批量更新**: 合并多个DOM操作
4. **防抖处理**: 搜索和过滤操作防抖

## 测试

### 单元测试

```bash
npm test -- KnowledgeGraphViewer.test.tsx
```

### 集成测试

```bash
npm test -- knowledgeGraph.test.tsx
```

### 演示模式

使用KGDemo组件可以在没有后端数据的情况下演示功能：

```tsx
import { KGDemo } from '../components/knowledge-graph';

function DemoPage() {
  return <KGDemo />;
}
```

## 故障排除

### 常见问题

1. **图谱不显示**
   - 检查projectId是否正确
   - 确认API服务是否正常
   - 查看浏览器控制台错误

2. **布局异常**
   - 尝试切换不同的布局算法
   - 检查数据格式是否正确
   - 重置视图

3. **性能问题**
   - 减少显示的节点数量
   - 使用过滤器简化图谱
   - 检查浏览器内存使用

### 调试模式

启用调试模式查看详细信息：

```tsx
<KnowledgeGraphViewer
  projectId="project-123"
  // 其他props...
  onNodeSelect={(node) => {
    console.log('Node selected:', node);
  }}
  onEdgeSelect={(edge) => {
    console.log('Edge selected:', edge);
  }}
/>
```

## 扩展开发

### 添加新的布局算法

1. 安装Cytoscape扩展包
2. 在KnowledgeGraphViewer中注册
3. 添加到布局选项列表

### 自定义节点样式

修改`getCytoscapeStyle`函数中的样式定义。

### 添加新的过滤器

在KGSearchPanel组件中添加新的过滤选项。

## 依赖项

- cytoscape: ^3.28.1
- cytoscape-dagre: 布局算法
- cytoscape-cose-bilkent: 布局算法
- cytoscape-cola: 布局算法
- antd: UI组件库
- react: ^18.2.0

## 更新日志

### v1.0.0
- 初始版本
- 基础可视化功能
- 多种布局算法支持
- 搜索和过滤功能
- 统计分析面板
- 导出功能