import { authService } from '../services/authService';

// 自定义错误类
export class ApiError extends Error {
  constructor(public status: number, message: string, public endpoint?: string) {
    super(message);
    this.name = 'ApiError';
  }
}

// API客户端类
class ApiClient {
  private baseURL = '/api/v1';

  async request<T>(url: string, options: RequestInit = {}): Promise<T> {
    // 获取有效token
    const token = await authService.getValidToken();
    
    if (!token) {
      // 重定向到登录页面
      window.location.href = '/login';
      throw new ApiError(401, 'Authentication required', url);
    }

    // 构建完整URL
    const fullUrl = url.startsWith('http') ? url : `${this.baseURL}${url}`;

    // 设置请求头
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    };

    try {
      const response = await fetch(fullUrl, {
        ...options,
        headers,
      });

      // 处理认证错误
      if (response.status === 401) {
        console.warn('Authentication failed, clearing tokens');
        authService.clearTokens();
        window.location.href = '/login';
        throw new ApiError(401, 'Authentication failed', url);
      }

      // 处理其他HTTP错误
      if (!response.ok) {
        let errorMessage = 'Request failed';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
          // 如果无法解析错误响应，使用默认消息
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        
        throw new ApiError(response.status, errorMessage, url);
      }

      // 解析响应
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return response.text() as unknown as T;
      }
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      // 网络错误或其他错误
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new ApiError(0, 'Network error or server unavailable', url);
      }
      
      throw new ApiError(0, error instanceof Error ? error.message : 'Unknown error', url);
    }
  }

  // 便捷方法
  async get<T>(url: string, options?: RequestInit): Promise<T> {
    return this.request<T>(url, { ...options, method: 'GET' });
  }

  async post<T>(url: string, data?: any, options?: RequestInit): Promise<T> {
    return this.request<T>(url, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(url: string, data?: any, options?: RequestInit): Promise<T> {
    return this.request<T>(url, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(url: string, options?: RequestInit): Promise<T> {
    return this.request<T>(url, { ...options, method: 'DELETE' });
  }

  async patch<T>(url: string, data?: any, options?: RequestInit): Promise<T> {
    return this.request<T>(url, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // 文件上传方法
  async upload<T>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
    const token = await authService.getValidToken();
    
    if (!token) {
      window.location.href = '/login';
      throw new ApiError(401, 'Authentication required', url);
    }

    const formData = new FormData();
    formData.append('file', file);

    const fullUrl = url.startsWith('http') ? url : `${this.baseURL}${url}`;

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = Math.round((event.loaded * 100) / event.total);
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch {
            resolve(xhr.responseText as unknown as T);
          }
        } else if (xhr.status === 401) {
          authService.clearTokens();
          window.location.href = '/login';
          reject(new ApiError(401, 'Authentication failed', url));
        } else {
          let errorMessage = 'Upload failed';
          try {
            const errorData = JSON.parse(xhr.responseText);
            errorMessage = errorData.detail || errorData.message || errorMessage;
          } catch {
            errorMessage = `HTTP ${xhr.status}: ${xhr.statusText}`;
          }
          reject(new ApiError(xhr.status, errorMessage, url));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new ApiError(0, 'Network error during upload', url));
      });

      xhr.open('POST', fullUrl);
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      xhr.send(formData);
    });
  }
}

// 导出单例实例
export const apiClient = new ApiClient();