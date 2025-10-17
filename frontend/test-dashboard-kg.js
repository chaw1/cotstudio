// 测试脚本：验证Dashboard中UserContributionGraph的知识图谱显示

console.log('========================================');
console.log('Dashboard 知识图谱显示测试');
console.log('========================================');

// 测试步骤：
// 1. 打开浏览器开发者工具 (F12)
// 2. 访问Dashboard页面 (/)
// 3. 在控制台中查看以下日志：

console.log('\n检查项：');
console.log('1. [UserContributionGraph] 图谱数据更新 - 应该显示nodes和edges数量');
console.log('2. [UserContributionGraph] 节点格式示例 - 验证节点数据结构');
console.log('3. [UserContributionGraph] 边格式示例 - 验证边数据结构');
console.log('4. [KnowledgeGraphViewer] 使用外部数据模式 - 确认数据传递');
console.log('5. [KnowledgeGraphViewer] 接收到外部数据 - 验证数据接收');
console.log('6. [KnowledgeGraphViewer] 转换后的内部数据 - 检查数据转换');
console.log('7. [KnowledgeGraphViewer] Cytoscape元素 - 确认Cytoscape数据');
console.log('8. [KnowledgeGraphViewer] 开始初始化Cytoscape - 查看容器尺寸');
console.log('9. [KnowledgeGraphViewer] Cytoscape实例创建成功 - 验证实例创建');

console.log('\n预期结果：');
console.log('✓ 用户贡献卡片中应该显示知识图谱');
console.log('✓ 图谱应该包含用户节点（蓝色）和项目节点（绿色）');
console.log('✓ 节点之间应该有连线');
console.log('✓ 可以使用鼠标滚轮缩放图谱');
console.log('✓ 可以拖拽图谱进行平移');

console.log('\n如果出现问题：');
console.log('1. 检查是否有错误日志');
console.log('2. 检查容器尺寸是否为0（containerWidth, containerHeight）');
console.log('3. 检查数据格式是否正确（nodes和edges）');
console.log('4. 检查是否有CSS样式冲突');

console.log('\n========================================\n');
