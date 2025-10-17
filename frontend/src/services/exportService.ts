/**
 * 导出服务
 */
import api from './api';
import { 
  ExportRequest, 
  ExportTaskResponse, 
  ExportValidationResult, 
  ExportHistoryItem,
  Project,
  ExportFormat
} from '../types/export';

class ExportService {
  /**
   * 获取用户可访问的项目列表
   */
  async getProjects(): Promise<Project[]> {
    return api.get<Project[]>('/projects');
  }

  /**
   * 导出项目数据
   */
  async exportProject(request: ExportRequest): Promise<ExportTaskResponse> {
    return api.post<ExportTaskResponse>(`/export/projects/${request.project_id}/export`, request);
  }

  /**
   * 创建项目包
   */
  async createProjectPackage(request: ExportRequest): Promise<ExportTaskResponse> {
    return api.post<ExportTaskResponse>(`/export/projects/${request.project_id}/package`, request);
  }

  /**
   * 获取导出任务状态
   */
  async getTaskStatus(taskId: string): Promise<ExportTaskResponse> {
    return api.get<ExportTaskResponse>(`/export/tasks/${taskId}/status`);
  }

  /**
   * 取消导出任务
   */
  async cancelTask(taskId: string): Promise<{ message: string }> {
    return api.delete(`/export/tasks/${taskId}`);
  }

  /**
   * 下载导出文件
   */
  getDownloadUrl(filename: string): string {
    return `/api/v1/export/download/${filename}`;
  }

  /**
   * 验证导出文件
   */
  async validateExportFile(filePath: string): Promise<ExportValidationResult> {
    return api.post<ExportValidationResult>('/export/validate', { file_path: filePath });
  }

  /**
   * 获取支持的导出格式
   */
  async getSupportedFormats(): Promise<string[]> {
    return api.get<string[]>('/export/formats');
  }

  /**
   * 获取项目导出历史
   */
  async getExportHistory(projectId: string, limit = 10, offset = 0): Promise<{
    items: ExportHistoryItem[];
    total: number;
    limit: number;
    offset: number;
  }> {
    return api.get(`/export/projects/${projectId}/history`, {
      params: { limit, offset }
    });
  }

  /**
   * 轮询任务状态直到完成
   */
  async pollTaskStatus(
    taskId: string, 
    onProgress?: (task: ExportTaskResponse) => void,
    interval = 2000
  ): Promise<ExportTaskResponse> {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const task = await this.getTaskStatus(taskId);
          
          if (onProgress) {
            onProgress(task);
          }

          if (task.status === 'completed') {
            resolve(task);
          } else if (task.status === 'failed') {
            reject(new Error(task.message || '导出任务失败'));
          } else {
            // 继续轮询
            setTimeout(poll, interval);
          }
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  }

  /**
   * 格式化文件大小
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * 获取格式显示名称
   */
  getFormatDisplayName(format: ExportFormat): string {
    const names = {
      [ExportFormat.JSON]: 'JSON 格式',
      [ExportFormat.MARKDOWN]: 'Markdown 格式',
      [ExportFormat.LATEX]: 'LaTeX 格式',
      [ExportFormat.TXT]: '纯文本格式'
    };
    return names[format] || format;
  }

  /**
   * 获取状态显示名称
   */
  getStatusDisplayName(status: string): string {
    const names = {
      'pending': '等待中',
      'processing': '处理中',
      'completed': '已完成',
      'failed': '失败'
    };
    return names[status] || status;
  }
}

export default new ExportService();