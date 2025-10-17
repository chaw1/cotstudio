/**
 * 导入服务
 */
import api from './api';

export interface ImportValidationResult {
  is_valid: boolean;
  file_format: string;
  metadata?: any;
  data_integrity: boolean;
  validation_errors: string[];
  warnings: string[];
  estimated_items: Record<string, number>;
}

export interface DataDifference {
  id: string;
  type: 'new' | 'modified' | 'deleted' | 'conflict';
  category: string;
  field_name?: string;
  current_value?: any;
  new_value?: any;
  description: string;
  severity: string;
}

export interface ImportAnalysisResult {
  is_valid: boolean;
  source_metadata: any;
  target_metadata?: any;
  differences: DataDifference[];
  conflicts: DataDifference[];
  validation_errors: string[];
  warnings: string[];
  statistics: Record<string, number>;
}

export interface ImportTaskResponse {
  task_id: string;
  status: 'pending' | 'analyzing' | 'comparing' | 'waiting_confirmation' | 'importing' | 'completed' | 'failed';
  progress: number;
  message?: string;
  created_at: string;
  completed_at?: string;
  differences_summary?: Record<string, number>;
}

export interface ImportConfirmation {
  task_id: string;
  confirmed_differences: string[];
  conflict_resolutions: Record<string, string>;
  import_settings: Record<string, any>;
}

export interface ImportResult {
  success: boolean;
  project_id: string;
  imported_items: Record<string, number>;
  skipped_items: Record<string, number>;
  errors: string[];
  warnings: string[];
  execution_time: number;
}

export interface ConflictResolution {
  difference_id: string;
  resolution: 'keep_current' | 'use_new' | 'merge' | 'skip';
  custom_value?: any;
  reason?: string;
}

export class ImportService {
  /**
   * 上传导入文件
   */
  async uploadImportFile(file: File): Promise<{ file_path: string; filename: string; size: number; message: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/import/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response;
  }

  /**
   * 验证导入文件
   */
  async validateImportFile(filePath: string): Promise<ImportTaskResponse> {
    const response = await api.post('/import/validate', null, {
      params: { file_path: filePath },
    });

    return response;
  }

  /**
   * 分析导入差异
   */
  async analyzeImportDifferences(
    filePath: string,
    targetProjectId?: string
  ): Promise<ImportTaskResponse> {
    const response = await api.post('/import/analyze', null, {
      params: {
        file_path: filePath,
        target_project_id: targetProjectId,
      },
    });

    return response;
  }

  /**
   * 执行导入操作
   */
  async executeImport(confirmation: ImportConfirmation): Promise<ImportTaskResponse> {
    const response = await api.post('/import/execute', confirmation);
    return response;
  }

  /**
   * 获取导入任务状态
   */
  async getImportTaskStatus(taskId: string): Promise<ImportTaskResponse> {
    const response = await api.get(`/import/tasks/${taskId}/status`);
    return response;
  }

  /**
   * 获取导入任务结果
   */
  async getImportTaskResult(taskId: string): Promise<any> {
    const response = await api.get(`/import/tasks/${taskId}/result`);
    return response;
  }

  /**
   * 取消导入任务
   */
  async cancelImportTask(taskId: string): Promise<{ message: string }> {
    const response = await api.delete(`/import/tasks/${taskId}`);
    return response;
  }

  /**
   * 清理导入文件
   */
  async cleanupImportFiles(filePaths: string[]): Promise<{ message: string }> {
    const response = await api.post('/import/cleanup', { file_paths: filePaths });
    return response;
  }

  /**
   * 获取导入历史
   */
  async getImportHistory(limit = 10, offset = 0): Promise<{
    items: any[];
    total: number;
    limit: number;
    offset: number;
  }> {
    const response = await api.get('/import/history', {
      params: { limit, offset },
    });

    return response;
  }

  /**
   * 获取支持的导入格式
   */
  async getSupportedFormats(): Promise<string[]> {
    const response = await api.get('/import/supported-formats');
    return response;
  }

  /**
   * 轮询任务状态直到完成
   */
  async pollTaskStatus(
    taskId: string,
    onProgress?: (status: ImportTaskResponse) => void,
    interval = 2000
  ): Promise<ImportTaskResponse> {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const status = await this.getImportTaskStatus(taskId);
          
          if (onProgress) {
            onProgress(status);
          }

          if (status.status === 'completed' || status.status === 'failed') {
            resolve(status);
          } else {
            setTimeout(poll, interval);
          }
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  }
}

export const importService = new ImportService();