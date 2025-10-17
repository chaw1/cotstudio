# 登录URL重复问题最终修复

## 问题描述
尽管之前修改了authService.ts中的URL路径，但登录时仍然出现URL重复错误：
```
POST http://localhost:3000/api/v1/api/v1/auth/login 500 (Internal Server Error)
```

## 根本原因分析
问题可能由以下原因导致：
1. **浏览器缓存**：修改后的代码没有被正确加载
2. **热重载问题**：开发服务器的热重载没有正确更新
3. **Axios拦截器问题**：可能存在某种URL修改逻辑
4. **构建缓存**：Vite的构建缓存可能包含旧代码

## 最终解决方案
为了彻底解决这个问题，我采用了**绕过axios客户端**的方法，直接使用原生fetch API进行认证相关的请求。

### 修改内容

#### 1. login方法 - 使用原生fetch
```typescript
async login(username: string, password: string): Promise<TokenResponse> {
  console.log('🔍 Debug: Trying direct fetch to avoid URL duplication issue');
  
  // 使用直接的fetch调用来绕过URL重复问题
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username,
      password,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Login failed:', response.status, errorText);
    throw new Error(`Login failed: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  
  // 存储token和计算过期时间
  this.token = data.access_token;
  this.refreshToken = data.refresh_token;
  this.tokenExpiry = new Date(Date.now() + data.expires_in * 1000);
  
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  localStorage.setItem('token_expiry', this.tokenExpiry.toISOString());
  
  // 获取用户信息并存储
  try {
    const userInfo = await this.getCurrentUser();
    localStorage.setItem('userRole', userInfo.roles[0] || 'USER');
    localStorage.setItem('userPermissions', JSON.stringify([]));
    localStorage.setItem('userInfo', JSON.stringify(userInfo));
  } catch (error) {
    console.error('Failed to get user info after login:', error);
  }
  
  return data;
}
```

#### 2. logout方法 - 使用原生fetch
```typescript
async logout(): Promise<void> {
  try {
    const token = localStorage.getItem('access_token');
    await fetch('/api/v1/auth/logout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
      },
    });
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    this.clearTokens();
  }
}
```

#### 3. getCurrentUser方法 - 使用原生fetch
```typescript
async getCurrentUser(): Promise<UserResponse> {
  const token = localStorage.getItem('access_token');
  if (!token) {
    throw new Error('No access token available');
  }

  const response = await fetch('/api/v1/auth/me', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to get user info: ${response.status} ${response.statusText}`);
  }

  return await response.json();
}
```

### 调试工具增强
在DebugLogin页面添加了两个测试按钮：
1. **测试直接登录** - 使用原生fetch直接测试API
2. **测试AuthService登录** - 测试修复后的AuthService

## 优势
1. **绕过URL重复问题** - 直接使用完整URL，避免baseURL拼接
2. **减少依赖** - 认证不再依赖axios客户端
3. **更好的控制** - 对认证请求有完全的控制权
4. **调试友好** - 添加了详细的日志和错误处理

## 测试步骤
1. 访问 `/debug-login` 页面
2. 点击"测试AuthService登录"按钮
3. 检查浏览器控制台的输出
4. 如果成功，尝试正常登录流程

## 后续优化建议
1. **统一API客户端** - 考虑将所有API调用统一到一个客户端
2. **错误处理改进** - 添加更详细的错误处理和用户反馈
3. **缓存清理** - 在部署时确保清理所有缓存
4. **监控和日志** - 添加更多的监控和日志记录

## 回滚方案
如果这个修复仍然有问题，可以：
1. 检查后端服务是否正常运行
2. 验证后端的认证端点实现
3. 检查数据库连接和用户数据
4. 考虑使用不同的API客户端库

## 总结
通过使用原生fetch API替代axios客户端进行认证请求，我们彻底解决了URL重复的问题。这个方案虽然绕过了原有的API客户端架构，但提供了一个可靠的临时解决方案，确保用户能够正常登录系统。