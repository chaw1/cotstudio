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
  async triggerOCR(fileId: string, ocrEngine?: string): Promise<void> {
    return api.post(`/ocr/process`, { 
      file_id: fileId, 
      engine: ocrEngine || 'paddleocr',
      user_id: 'admin' // 临时使用固定用户ID
    });
  },

  // 获取文件切片
  async getFileSlices(fileId: string): Promise<any[]> {
    // 模拟切片数据
    return new Promise((resolve) => {
      setTimeout(() => {
        const mockSlices = Array.from({ length: 25 }, (_, index) => ({
          id: `slice_${index + 1}`,
          fileId,
          content: `这是第 ${index + 1} 个切片的内容。这里包含了从原文档中提取的文本内容，可能是段落、表格或图像的描述信息。内容长度会根据实际的文档结构而变化，有些切片可能包含更多的文本，有些则相对较短。`,
          startOffset: index * 100,
          endOffset: (index + 1) * 100 - 1,
          sliceType: ['paragraph', 'image', 'table'][index % 3] as 'paragraph' | 'image' | 'table',
          pageNumber: Math.floor(index / 3) + 1,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }));
        resolve(mockSlices);
      }, 1000);
    });
  },

  // 获取OCR任务状态
  async getOCRTaskStatus(taskId: string): Promise<any> {
    return api.get(`/ocr/tasks/${taskId}`);
  },

  // 取消OCR任务
  async cancelOCRTask(taskId: string): Promise<void> {
    return api.post(`/ocr/tasks/${taskId}/cancel`);
  },
};