# 🎯 开发偏好速查卡

## React 配置

### ❌ 不使用 StrictMode
```tsx
// ✅ 正确 - 不要包裹 StrictMode
ReactDOM.createRoot(root).render(<App />)

// ❌ 错误 - 不要使用 StrictMode
ReactDOM.createRoot(root).render(
  <React.StrictMode><App /></React.StrictMode>
)
```

### 原因
- 避免 double render
- 简化第三方库集成（Cytoscape, ECharts）
- 更好的开发体验

## TypeScript 配置

### 禁用 Strict Mode
```json
{
  "compilerOptions": {
    "strict": false
  }
}
```

## 代码风格要点

### 1. useEffect Cleanup
```tsx
useEffect(() => {
  let mounted = true;
  
  // 异步操作
  fetchData().then(data => {
    if (mounted) setState(data);
  });
  
  // ✅ 必须有 cleanup
  return () => {
    mounted = false;
  };
}, []);
```

### 2. 第三方库实例
```tsx
const instanceRef = useRef(null);

useEffect(() => {
  // ✅ 检查是否已初始化
  if (!instanceRef.current) {
    instanceRef.current = new Library();
  }
  
  // ✅ 清理实例
  return () => {
    instanceRef.current?.destroy();
    instanceRef.current = null;
  };
}, []);
```

### 3. 定时器清理
```tsx
useEffect(() => {
  const timer = setTimeout(...);
  
  // ✅ 必须清理
  return () => clearTimeout(timer);
}, []);
```

## 快速命令

```bash
# 重启前端服务器
docker-compose restart frontend

# 查看前端日志
docker-compose logs -f frontend

# 进入前端容器
docker-compose exec frontend sh
```

## 相关文档

- 📘 [PROJECT_PREFERENCES.md](PROJECT_PREFERENCES.md) - 完整偏好设置
- 📗 [PROJECT_GUIDE.md](PROJECT_GUIDE.md) - 项目指南
- 📕 [REMOVE_STRICT_MODE.md](REMOVE_STRICT_MODE.md) - StrictMode 移除说明

## 记住 ✨

1. **不使用 React StrictMode**
2. **所有副作用必须有 cleanup**
3. **第三方库要防止重复初始化**
4. **定时器和订阅要及时清理**

---

*更新日期: 2025-10-13*
