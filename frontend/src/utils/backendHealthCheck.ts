/**
 * 后端健康检查工具
 */

export interface HealthCheckResult {
  isHealthy: boolean;
  message: string;
  details?: any;
}

/**
 * 检查后端服务是否可用
 */
export async function checkBackendHealth(): Promise<HealthCheckResult> {
  try {
    // 尝试访问健康检查端点
    const response = await fetch('/api/v1/health', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      const data = await response.json();
      return {
        isHealthy: true,
        message: '后端服务正常',
        details: data
      };
    } else {
      return {
        isHealthy: false,
        message: `后端服务返回错误状态: ${response.status}`,
        details: { status: response.status, statusText: response.statusText }
      };
    }
  } catch (error) {
    return {
      isHealthy: false,
      message: '无法连接到后端服务',
      details: error
    };
  }
}

/**
 * 检查认证端点是否可用
 */
export async function checkAuthEndpoint(): Promise<HealthCheckResult> {
  try {
    // 尝试访问登录端点（不发送凭据，只检查端点是否存在）
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: 'test',
        password: 'test'
      })
    });

    // 即使认证失败，只要端点存在就说明服务正常
    if (response.status === 401 || response.status === 400) {
      return {
        isHealthy: true,
        message: '认证端点可用（认证失败是正常的）',
        details: { status: response.status }
      };
    } else if (response.status === 500) {
      return {
        isHealthy: false,
        message: '认证端点返回服务器错误',
        details: { status: response.status }
      };
    } else {
      return {
        isHealthy: true,
        message: '认证端点可用',
        details: { status: response.status }
      };
    }
  } catch (error) {
    return {
      isHealthy: false,
      message: '无法连接到认证端点',
      details: error
    };
  }
}

/**
 * 运行完整的后端健康检查
 */
export async function runFullHealthCheck(): Promise<{
  overall: boolean;
  checks: {
    backend: HealthCheckResult;
    auth: HealthCheckResult;
  }
}> {
  const [backendCheck, authCheck] = await Promise.all([
    checkBackendHealth(),
    checkAuthEndpoint()
  ]);

  return {
    overall: backendCheck.isHealthy && authCheck.isHealthy,
    checks: {
      backend: backendCheck,
      auth: authCheck
    }
  };
}