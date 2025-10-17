import api from './api';

export interface AuditLog {
  id: string;
  user_id?: string;
  event_type: string;
  severity: string;
  resource_type?: string;
  resource_id?: string;
  resource_name?: string;
  action: string;
  description?: string;
  details: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  success: boolean;
  error_message?: string;
  old_values: Record<string, any>;
  new_values: Record<string, any>;
  created_at: string;
}

export interface AuditLogQuery {
  user_id?: string;
  event_types?: string[];
  resource_type?: string;
  resource_id?: string;
  severity?: string;
  success?: boolean;
  start_date?: string;
  end_date?: string;
  ip_address?: string;
  search_text?: string;
}

export interface AuditLogListResponse {
  items: AuditLog[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface AuditStatistics {
  total_operations: number;
  failed_operations: number;
  success_rate: number;
  active_users: number;
  event_type_distribution: Record<string, number>;
  severity_distribution: Record<string, number>;
  resource_type_distribution: Record<string, number>;
  period: {
    start_date: string;
    end_date: string;
  };
}

export interface Role {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  role_type: string;
  permissions: string[];
  is_system_role: boolean;
  created_at: string;
  updated_at?: string;
}

export interface RoleCreate {
  name: string;
  display_name: string;
  description?: string;
  role_type: string;
  permissions: string[];
}

export interface RoleUpdate {
  display_name?: string;
  description?: string;
  permissions?: string[];
}

export interface Permission {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  resource_type: string;
  action: string;
  is_system_permission: boolean;
}

export interface UserRole {
  id: string;
  user_id: string;
  role_id: string;
  granted_by?: string;
  granted_at: string;
  expires_at?: string;
}

export interface UserRoleCreate {
  user_id: string;
  role_id: string;
  expires_at?: string;
}

export interface UserPermissions {
  user_id: string;
  roles: Array<UserRole & { role: Role }>;
  permissions: string[];
  project_permissions: any[];
}

export interface ProjectPermission {
  id: string;
  project_id: string;
  user_id?: string;
  role_id?: string;
  permission_type: string;
  granted_by?: string;
  granted_at: string;
}

export interface ProjectPermissionCreate {
  project_id: string;
  user_id?: string;
  role_id?: string;
  permission_type: string;
}

export interface PermissionCheck {
  user_id: string;
  permission: string;
  resource_type?: string;
  resource_id?: string;
}

export interface PermissionCheckResponse {
  has_permission: boolean;
  reason?: string;
}

class AuditService {
  // 审计日志相关方法
  async getAuditLogs(
    query: AuditLogQuery & { page?: number; size?: number }
  ): Promise<AuditLogListResponse> {
    const params = new URLSearchParams();

    if (query.page) params.append('page', query.page.toString());
    if (query.size) params.append('size', query.size.toString());
    if (query.user_id) params.append('user_id', query.user_id);
    if (query.event_types) {
      query.event_types.forEach(type => params.append('event_types', type));
    }
    if (query.resource_type) params.append('resource_type', query.resource_type);
    if (query.resource_id) params.append('resource_id', query.resource_id);
    if (query.severity) params.append('severity', query.severity);
    if (query.success !== undefined) params.append('success', query.success.toString());
    if (query.start_date) params.append('start_date', query.start_date);
    if (query.end_date) params.append('end_date', query.end_date);
    if (query.ip_address) params.append('ip_address', query.ip_address);
    if (query.search_text) params.append('search_text', query.search_text);

    const response = await api.get(`/audit/logs?${params}`);
    return response;
  }

  async getAuditLog(logId: string): Promise<AuditLog> {
    const response = await api.get(`/audit/logs/${logId}`);
    return response;
  }

  async getAuditStatistics(startDate?: string, endDate?: string): Promise<AuditStatistics> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await api.get(`/audit/statistics?${params}`);
    return response;
  }

  // 角色管理相关方法
  async getRoles(): Promise<Role[]> {
    const response = await api.get('/audit/roles');
    return response;
  }

  async getRole(roleId: string): Promise<Role> {
    const response = await api.get(`/audit/roles/${roleId}`);
    return response;
  }

  async createRole(roleData: RoleCreate): Promise<Role> {
    const response = await api.post('/audit/roles', roleData);
    return response;
  }

  async updateRole(roleId: string, roleData: RoleUpdate): Promise<Role> {
    const response = await api.put(`/audit/roles/${roleId}`, roleData);
    return response;
  }

  async deleteRole(roleId: string): Promise<void> {
    await api.delete(`/audit/roles/${roleId}`);
  }

  // 权限管理相关方法
  async getPermissions(resourceType?: string): Promise<Permission[]> {
    const params = resourceType ? `?resource_type=${resourceType}` : '';
    const response = await api.get(`/audit/permissions${params}`);
    return response;
  }

  async checkPermission(checkData: PermissionCheck): Promise<PermissionCheckResponse> {
    const response = await api.post('/audit/permissions/check', checkData);
    return response;
  }

  // 用户角色管理相关方法
  async assignRoleToUser(userId: string, roleData: UserRoleCreate): Promise<UserRole> {
    const response = await api.post(`/audit/users/${userId}/roles`, roleData);
    return response;
  }

  async revokeRoleFromUser(userId: string, roleId: string): Promise<void> {
    await api.delete(`/audit/users/${userId}/roles/${roleId}`);
  }

  async getUserPermissions(userId: string): Promise<UserPermissions> {
    const response = await api.get(`/audit/users/${userId}/permissions`);
    return response;
  }

  // 项目权限管理相关方法
  async grantProjectPermission(
    projectId: string,
    permissionData: ProjectPermissionCreate
  ): Promise<ProjectPermission> {
    const response = await api.post(`/audit/projects/${projectId}/permissions`, permissionData);
    return response;
  }

  async getProjectPermissions(projectId: string): Promise<ProjectPermission[]> {
    const response = await api.get(`/audit/projects/${projectId}/permissions`);
    return response;
  }

  async revokeProjectPermission(projectId: string, permissionId: string): Promise<void> {
    await api.delete(`/audit/projects/${projectId}/permissions/${permissionId}`);
  }

  // 批量操作相关方法
  async bulkAssignRoles(data: {
    user_ids: string[];
    role_id: string;
    expires_at?: string;
  }): Promise<{
    successful_assignments: string[];
    failed_assignments: Array<{ user_id: string; error: string }>;
  }> {
    const response = await api.post('/audit/roles/bulk-assign', data);
    return response;
  }

  // 导出审计日志
  async exportAuditLogs(query: AuditLogQuery, format: 'csv' | 'excel' = 'csv'): Promise<Blob> {
    const params = new URLSearchParams();

    if (query.user_id) params.append('user_id', query.user_id);
    if (query.event_types) {
      query.event_types.forEach(type => params.append('event_types', type));
    }
    if (query.resource_type) params.append('resource_type', query.resource_type);
    if (query.resource_id) params.append('resource_id', query.resource_id);
    if (query.severity) params.append('severity', query.severity);
    if (query.success !== undefined) params.append('success', query.success.toString());
    if (query.start_date) params.append('start_date', query.start_date);
    if (query.end_date) params.append('end_date', query.end_date);
    if (query.search_text) params.append('search_text', query.search_text);

    params.append('format', format);

    const response = await api.get(`/audit/logs/export?${params}`, {
      responseType: 'blob'
    });

    return response;
  }
}

export const auditService = new AuditService();