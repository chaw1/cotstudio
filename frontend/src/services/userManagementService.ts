import api from './api';

// User management types
export interface UserRole {
  SUPER_ADMIN: 'super_admin';
  ADMIN: 'admin';
  USER: 'user';
  VIEWER: 'viewer';
}

export interface ProjectPermission {
  VIEW: 'view';
  CREATE: 'create';
  EDIT: 'edit';
  DELETE: 'delete';
  ADMIN: 'admin';
}

export interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  role: string;
  department?: string;
  is_active: boolean;
  is_superuser: boolean;
  last_login?: string;
  login_count: number;
  created_at: string;
  updated_at: string;
}

export interface UserCreateRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  role: string;
  department?: string;
  is_active: boolean;
}

export interface UserUpdateRequest {
  email?: string;
  full_name?: string;
  role?: string;
  department?: string;
  is_active?: boolean;
}

export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface UserSearchParams {
  page?: number;
  size?: number;
  search?: string;
  role?: string;
  department?: string;
  is_active?: boolean;
}

export interface PermissionGrantRequest {
  user_id: string;
  project_id: string;
  permissions: string[];
}

export interface PermissionRevokeRequest {
  user_id: string;
  project_id: string;
  permissions?: string[];
}

export interface Permission {
  id: string;
  user_id: string;
  project_id: string;
  permissions: string[];
  granted_by?: string;
  granted_at: string;
  user_username?: string;
  project_name?: string;
  granter_username?: string;
  created_at: string;
  updated_at: string;
}

export interface UserPermissionResponse {
  user: User;
  project_permissions: Permission[];
}

export interface UserStatsResponse {
  total_users: number;
  active_users: number;
  inactive_users: number;
  users_by_role: Record<string, number>;
  users_by_department: Record<string, number>;
  recent_logins: number;
}

class UserManagementService {
  // User CRUD operations
  async getUsers(params: UserSearchParams = {}): Promise<UserListResponse> {
    const searchParams = new URLSearchParams();
    
    if (params.page) searchParams.append('page', params.page.toString());
    if (params.size) searchParams.append('size', params.size.toString());
    if (params.search) searchParams.append('search', params.search);
    if (params.role) searchParams.append('role', params.role);
    if (params.department) searchParams.append('department', params.department);
    if (params.is_active !== undefined) searchParams.append('is_active', params.is_active.toString());
    
    return await api.get<UserListResponse>(`/user-management/users?${searchParams.toString()}`);
  }

  async getUser(userId: string): Promise<User> {
    return await api.get<User>(`/user-management/users/${userId}`);
  }

  async createUser(userData: UserCreateRequest): Promise<User> {
    return await api.post<User>('/user-management/users', userData);
  }

  async updateUser(userId: string, userData: UserUpdateRequest): Promise<User> {
    return await api.put<User>(`/user-management/users/${userId}`, userData);
  }

  async deleteUser(userId: string): Promise<{ message: string }> {
    return await api.delete<{ message: string }>(`/user-management/users/${userId}`);
  }

  async resetUserPassword(userId: string, newPassword: string): Promise<{ message: string }> {
    return await api.post<{ message: string }>(`/user-management/users/${userId}/reset-password`, {
      user_id: userId,
      new_password: newPassword
    });
  }

  // Permission management
  async grantPermission(permissionData: PermissionGrantRequest): Promise<Permission> {
    return await api.post<Permission>('/user-management/permissions/grant', permissionData);
  }

  async revokePermission(permissionData: PermissionRevokeRequest): Promise<{ message: string }> {
    return await api.delete<{ message: string }>('/user-management/permissions/revoke', {
      data: permissionData
    });
  }

  async getUserPermissions(userId: string): Promise<UserPermissionResponse> {
    return await api.get<UserPermissionResponse>(`/user-management/permissions/users/${userId}`);
  }

  // Statistics
  async getUserStats(): Promise<UserStatsResponse> {
    return await api.get<UserStatsResponse>('/user-management/users/stats');
  }
}

export const userManagementService = new UserManagementService();