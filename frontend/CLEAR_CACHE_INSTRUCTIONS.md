# 清除缓存指令

## 问题描述
尽管修改了authService.ts使用fetch而不是axios，但错误堆栈仍显示在使用axios客户端。这表明存在缓存问题。

## 清除缓存的方法

### 1. 浏览器缓存清除
1. 打开浏览器开发者工具 (F12)
2. 右键点击刷新按钮
3. 选择"清空缓存并硬性重新加载"
4. 或者使用快捷键：Ctrl+Shift+R (Windows) 或 Cmd+Shift+R (Mac)

### 2. 开发服务器重启
```bash
# 停止当前的开发服务器 (Ctrl+C)
# 然后重新启动
cd frontend
npm run dev
```

### 3. 清除Node.js模块缓存
```bash
cd frontend
rm -rf node_modules/.cache
rm -rf .vite
npm run dev
```

### 4. 完全重新安装依赖
```bash
cd frontend
rm -rf node_modules
rm package-lock.json
npm install
npm run dev
```

### 5. 浏览器存储清除
在浏览器开发者工具中：
1. 打开Application/Storage标签
2. 清除Local Storage
3. 清除Session Storage
4. 清除所有Cookies

## 验证修复是否生效

### 检查控制台输出
登录时应该看到以下调试信息：
```
🔥 LOGIN COMPONENT: Starting login process
🔥 LOGIN COMPONENT: AuthService instance: [object]
🔥 LOGIN COMPONENT: Calling authService.login
🚀 AuthService instance created, version: FIXED_FETCH_VERSION_2.0
🚀 NEW LOGIN METHOD: Using direct fetch instead of axios
🚀 Login URL: /api/v1/auth/login
🚀 Username: admin
🚀 Response status: [status_code]
```

### 检查网络请求
在浏览器开发者工具的Network标签中：
- 应该看到对 `/api/v1/auth/login` 的请求（不是重复的URL）
- 请求应该是直接的fetch请求，不是通过axios

## 如果仍然有问题

### 1. 检查是否有多个authService实例
```javascript
// 在浏览器控制台中运行
console.log(window.authService || 'No global authService');
```

### 2. 检查模块热重载
确保Vite的热重载正常工作：
- 修改一个简单的文件（如添加console.log）
- 检查浏览器是否自动刷新

### 3. 使用调试页面
访问 `/debug-login` 页面：
- 运行健康检查
- 使用"测试AuthService登录"按钮
- 检查控制台输出

### 4. 检查后端服务
如果前端修复成功但仍有500错误：
```bash
# 检查后端是否运行
curl http://localhost:8000/api/v1/health

# 检查登录端点
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"971028"}'
```

## 预期结果

修复成功后：
1. 不再看到axios相关的错误堆栈
2. 网络请求显示正确的URL（不重复）
3. 如果后端正常，登录应该成功
4. 如果后端有问题，会看到具体的HTTP状态码和错误信息

## 紧急回滚方案

如果修复导致其他问题，可以临时回滚：
```bash
git checkout HEAD -- frontend/src/services/authService.ts
git checkout HEAD -- frontend/src/components/auth/Login.tsx
```

然后重新启动开发服务器。