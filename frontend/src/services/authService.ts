import api from './api';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  user_id: string;
  username: string;
  email: string;
  roles: string[];
}

class AuthService {
  private static instance: AuthService;
  private token: string | null = null;
  private refreshToken: string | null = null;
  private tokenExpiry: Date | null = null;
  private refreshPromise: Promise<void> | null = null;
  
  // 版本标识 - 用于调试
  public readonly version = 'FIXED_FETCH_VERSION_2.0';

  static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
      console.log('🚀 AuthService instance created, version:', AuthService.instance.version);
    }
    return AuthService.instance;
  }

  async login(username: string, password: string): Promise<TokenResponse> {
    console.log('🚀 NEW LOGIN METHOD: Using direct fetch instead of axios');
    console.log('🚀 Login URL: /api/v1/auth/login');
    console.log('🚀 Username:', username);
    
    try {
      const requestBody = {
        username,
        password,
      };
      
      console.log('🚀 Request body:', JSON.stringify(requestBody));
      
      // 使用直接的fetch调用，路径应该是 /api/v1/auth/login（代理会处理）
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      console.log('🚀 Response status:', response.status);
      console.log('🚀 Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('🚀 Login failed:', response.status, errorText);
        console.error('🚀 Full response:', {
          status: response.status,
          statusText: response.statusText,
          headers: Object.fromEntries(response.headers.entries()),
          body: errorText
        });
        throw new Error(`Login failed: ${response.status} ${response.statusText} - ${errorText}`);
      }

      const data = await response.json();
      console.log('🚀 Login response data:', data);
      
      // 存储token和计算过期时间
      this.token = data.access_token;
      this.refreshToken = data.refresh_token;
      this.tokenExpiry = new Date(Date.now() + data.expires_in * 1000);
      
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('token_expiry', this.tokenExpiry.toISOString());
      
      console.log('🚀 Tokens stored successfully');
      
      // 获取用户信息并存储到localStorage
      try {
        const userInfo = await this.getCurrentUser();
        localStorage.setItem('userRole', userInfo.roles[0] || 'USER');
        localStorage.setItem('userPermissions', JSON.stringify([])); // 暂时为空，后续可以扩展
        localStorage.setItem('userInfo', JSON.stringify(userInfo));
        console.log('🚀 User info stored successfully');
      } catch (error) {
        console.error('🚀 Failed to get user info after login:', error);
      }
      
      return data;
    } catch (error) {
      console.error('🚀 Login method error:', error);
      throw error;
    }
  }

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

  // 获取有效token，自动处理刷新
  async getValidToken(): Promise<string | null> {
    // 检查token是否存在
    if (!this.token) {
      this.token = localStorage.getItem('access_token');
      this.refreshToken = localStorage.getItem('refresh_token');
      const expiryStr = localStorage.getItem('token_expiry');
      if (expiryStr) {
        this.tokenExpiry = new Date(expiryStr);
      }
    }

    if (!this.token) {
      return null;
    }

    // 检查token是否即将过期（提前5分钟刷新）
    if (this.isTokenExpiring()) {
      try {
        await this.refreshAccessToken();
      } catch (error) {
        console.error('Token refresh failed:', error);
        this.clearTokens();
        return null;
      }
    }

    return this.token;
  }

  // 检查token是否即将过期
  private isTokenExpiring(): boolean {
    if (!this.tokenExpiry) {
      // 尝试解析token获取过期时间
      try {
        if (this.token) {
          const payload = JSON.parse(atob(this.token.split('.')[1]));
          this.tokenExpiry = new Date(payload.exp * 1000);
        }
      } catch {
        return true; // 无法解析则认为过期
      }
    }
    
    if (!this.tokenExpiry) {
      return true;
    }

    // 提前5分钟刷新token
    const fiveMinutesFromNow = new Date(Date.now() + 5 * 60 * 1000);
    return this.tokenExpiry <= fiveMinutesFromNow;
  }

  // 刷新访问token
  private async refreshAccessToken(): Promise<void> {
    // 如果已经有刷新请求在进行中，等待它完成
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    if (!this.refreshToken) {
      this.refreshToken = localStorage.getItem('refresh_token');
    }

    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    this.refreshPromise = this.performTokenRefresh();
    
    try {
      await this.refreshPromise;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async performTokenRefresh(): Promise<void> {
    const response = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh_token: this.refreshToken
      })
    });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    
    this.token = data.access_token;
    this.refreshToken = data.refresh_token;
    this.tokenExpiry = new Date(Date.now() + data.expires_in * 1000);
    
    localStorage.setItem('access_token', this.token);
    localStorage.setItem('refresh_token', this.refreshToken);
    localStorage.setItem('token_expiry', this.tokenExpiry.toISOString());
  }

  // 清理tokens
  clearTokens(): void {
    this.token = null;
    this.refreshToken = null;
    this.tokenExpiry = null;
    this.refreshPromise = null;
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_expiry');
    localStorage.removeItem('userRole');
    localStorage.removeItem('userPermissions');
    localStorage.removeItem('userInfo');
  }

  isAuthenticated(): boolean {
    const token = localStorage.getItem('access_token');
    if (!token) {
      return false;
    }

    // 检查token是否过期
    const expiryStr = localStorage.getItem('token_expiry');
    if (expiryStr) {
      const expiry = new Date(expiryStr);
      if (expiry <= new Date()) {
        this.clearTokens();
        return false;
      }
    }

    return true;
  }

  getToken(): string | null {
    return localStorage.getItem('access_token');
  }
}

export const authService = AuthService.getInstance();