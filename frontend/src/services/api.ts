import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { reportApiError, reportNetworkError } from '../utils/errorHandler';

// API响应接口
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
}

// API错误接口
export interface ApiError {
  error: string;
  message: string;
  timestamp: string;
}

class ApiClient {
  private instance: AxiosInstance;

  constructor() {
    this.instance = axios.create({
      baseURL: '/api/v1',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // 请求拦截器
    this.instance.interceptors.request.use(
      async (config) => {
        // 不需要认证的接口列表
        const noAuthUrls = ['/auth/login', '/auth/register', '/auth/refresh'];
        const isNoAuthUrl = noAuthUrls.some(url => config.url?.includes(url));
        
        if (!isNoAuthUrl) {
          // 直接从localStorage获取token，避免循环依赖
          const token = localStorage.getItem('access_token');
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          } else {
            // 如果无法获取有效token，重定向到登录页面
            window.location.href = '/login';
            return Promise.reject(new Error('Authentication required'));
          }
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error) => {
        // 处理认证错误
        if (error.response?.status === 401) {
          console.warn('Authentication failed, clearing tokens');
          // 直接清除localStorage中的token，避免循环依赖
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('token_expiry');
          window.location.href = '/login';
        }
        
        // 报告错误到全局错误处理器
        if (error.response) {
          // API 错误
          reportApiError(
            new Error(error.response.data?.message || error.message),
            error.config?.url || 'unknown',
            error.config?.method || 'unknown',
            error.response.status
          );
        } else if (error.request) {
          // 网络错误
          reportNetworkError(new Error('Network request failed'), error.config);
        } else {
          // 其他错误
          reportApiError(new Error(error.message), 'unknown', 'unknown');
        }
        
        // 处理其他错误
        const apiError: ApiError = error.response?.data || {
          error: 'NETWORK_ERROR',
          message: '网络连接错误',
          timestamp: new Date().toISOString(),
        };
        
        return Promise.reject(apiError);
      }
    );
  }

  // GET请求
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    // 强制禁用所有缓存,添加时间戳确保每次请求都是新的
    const timestamp = new Date().getTime();
    const separator = url.includes('?') ? '&' : '?';
    const urlWithTimestamp = `${url}${separator}_t=${timestamp}`;
    
    const finalConfig = {
      ...config,
      headers: {
        ...config?.headers,
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
      },
    };
    const response = await this.instance.get<T>(urlWithTimestamp, finalConfig);
    return response.data;
  }

  // POST请求
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post<T>(url, data, config);
    return response.data;
  }

  // PUT请求
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.put<T>(url, data, config);
    return response.data;
  }

  // DELETE请求
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete<T>(url, config);
    return response.data;
  }

  // 文件上传
  async upload<T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.instance.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });

    return response.data;
  }
}

const api = new ApiClient();
export default api;