# 项目开发偏好设置

## React 配置偏好

### ❌ 不使用 React.StrictMode
**日期**: 2025-10-13  
**原因**: 
- StrictMode会导致组件在开发环境中double-render（渲染两次）
- 这可能导致useEffect等副作用执行两次，影响调试
- 对于Cytoscape等第三方库，double-render可能导致初始化问题

**配置位置**: `frontend/src/main.tsx`

**修改内容**:
```tsx
// 之前（使用StrictMode）
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

// 现在（不使用StrictMode）
ReactDOM.createRoot(document.getElementById('root')!).render(
  <App />,
)
```

## TypeScript 配置偏好

### TypeScript Strict Mode
**状态**: 已禁用  
**配置位置**: `frontend/tsconfig.json`
```json
{
  "compilerOptions": {
    "strict": false
  }
}
```

## 代码生成规范

### 后续代码生成时需要遵守的规则：

1. **不使用React.StrictMode**
   - 在任何新组件或入口文件中都不要添加`<React.StrictMode>`
   - 保持简单的渲染结构

2. **副作用处理**
   - useEffect等hooks的cleanup函数要正确实现
   - 避免依赖StrictMode来检测副作用问题
   - 使用明确的组件生命周期管理

3. **第三方库集成**
   - 对于Cytoscape、ECharts等需要DOM操作的库，确保：
     - 只初始化一次
     - 有完整的cleanup逻辑
     - 使用ref来管理实例

4. **状态管理**
   - 使用isMounted等flag来防止组件卸载后的状态更新
   - 清理所有定时器和异步操作

## 影响说明

### 移除StrictMode的好处：
✅ 组件只渲染一次，性能更好  
✅ useEffect只执行一次，行为更可预测  
✅ 第三方库（如Cytoscape）初始化更稳定  
✅ 调试日志更清晰，不会看到重复输出  

### 需要注意的事项：
⚠️ 失去了一些React未来兼容性检查  
⚠️ 需要更仔细地处理副作用和清理逻辑  
⚠️ 手动确保组件的幂等性和可靠性  

## 最佳实践

为了弥补不使用StrictMode的影响，我们应该：

1. **手动检查副作用**
   ```tsx
   useEffect(() => {
     let mounted = true;
     
     // 异步操作
     fetchData().then(data => {
       if (mounted) {
         setData(data);
       }
     });
     
     // 清理函数
     return () => {
       mounted = false;
     };
   }, []);
   ```

2. **正确清理资源**
   ```tsx
   useEffect(() => {
     const timer = setTimeout(() => {
       // ...
     }, 1000);
     
     return () => {
       clearTimeout(timer);
     };
   }, []);
   ```

3. **管理第三方库实例**
   ```tsx
   const instanceRef = useRef<SomeLibrary | null>(null);
   
   useEffect(() => {
     if (!instanceRef.current) {
       instanceRef.current = new SomeLibrary(containerRef.current);
     }
     
     return () => {
       if (instanceRef.current) {
         instanceRef.current.destroy();
         instanceRef.current = null;
       }
     };
   }, []);
   ```

## 更新日志

### 2025-10-13
- ✅ 移除了 `frontend/src/main.tsx` 中的 `React.StrictMode`
- ✅ 确认 TypeScript strict mode 已禁用
- ✅ 创建本偏好设置文档

## 相关问题修复

移除StrictMode后，以下问题应该得到改善：
- Dashboard页面知识图谱的double-initialization问题
- Cytoscape实例的重复创建和清理问题
- useEffect相关的race condition

## 团队协作说明

如果团队中有其他开发者，请告知：
1. 项目已禁用React StrictMode
2. 代码审查时要特别注意副作用的清理
3. 测试时需要手动验证组件的mount/unmount行为
4. 添加新功能时参考本文档的最佳实践
