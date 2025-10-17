import api from './api';
import { Project } from '../types';

export interface CreateProjectRequest {
  name: string;
  description?: string;
  tags?: string[];
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
  tags?: string[];
  status?: 'active' | 'archived' | 'draft';
}

export const projectService = {
  // 获取项目列表
  async getProjects(): Promise<Project[]> {
    return api.get('/projects');
  },

  // 获取项目详情
  async getProject(id: string): Promise<Project> {
    return api.get(`/projects/${id}`);
  },

  // 创建项目
  async createProject(data: CreateProjectRequest): Promise<Project> {
    return api.post('/projects', data);
  },

  // 更新项目
  async updateProject(id: string, data: UpdateProjectRequest): Promise<Project> {
    return api.put(`/projects/${id}`, data);
  },

  // 删除项目
  async deleteProject(id: string): Promise<void> {
    return api.delete(`/projects/${id}`);
  },
};