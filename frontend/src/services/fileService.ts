import api from './api';
import { FileInfo } from '../types';

export interface UploadResponse {
  fileId: string;
  filename: string;
  size: number;
  mimeType: string;
  ocrStatus: string;
}

export const fileService = {
  // 获取项目文件列表
  async getProjectFiles(projectId: string): Promise<FileInfo[]> {
    return api.get(`/projects/${projectId}/files`);
  },

  // 上传文件
  async uploadFile(
    projectId: string, 
    file: File, 
    onProgress?: (progress: number) => void
  ): Promise<UploadResponse> {
    return api.upload(`/projects/${projectId}/upload`, file, onProgress);
  },

  // 删除文件
  async deleteFile(fileId: string): Promise<void> {
    return api.delete(`/files/${fileId}`);
  },

  // 触发OCR处理
  async triggerOCR(fileId: string, ocrEngine?: string, engineConfig?: any): Promise<void> {
    const requestBody: any = { 
      file_id: fileId, 
      engine: ocrEngine || 'paddleocr',
      user_id: 'admin' // 临时使用固定用户ID
    };
    
    // 如果提供了引擎配置，添加到请求中
    if (engineConfig) {
      requestBody.config = engineConfig;
    }
    
    return api.post(`/ocr/process`, requestBody);
  },

  // 获取文件切片
  async getFileSlices(fileId: string): Promise<any[]> {
    try {
      const response = await api.get(`/ocr/slices/${fileId}?page=1&size=1000`);
      // 后端返回的是 ResponseModel 包装的数据
      if (response.data && response.data.slices) {
        return response.data.slices;
      }
      return [];
    } catch (error) {
      console.error('Failed to fetch file slices:', error);
      return [];
    }
  },

  // 获取OCR任务状态
  async getOCRTaskStatus(taskId: string): Promise<any> {
    return api.get(`/ocr/tasks/${taskId}`);
  },

  // 取消OCR任务
  async cancelOCRTask(taskId: string): Promise<void> {
    return api.post(`/ocr/tasks/${taskId}/cancel`);
  },

  // 获取文件OCR状态
  async getFileOCRStatus(fileId: string): Promise<any> {
    return api.get(`/ocr/status/${fileId}`);
  },

  // 停止文件OCR处理
  async stopFileOCR(fileId: string): Promise<any> {
    return api.post(`/ocr/stop/${fileId}`);
  },
};