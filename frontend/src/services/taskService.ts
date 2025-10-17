/**
 * 任务监控服务
 */
import api from './api';
import {
  TaskMonitor,
  TaskStatistics,
  TaskQueueInfo,
  WorkerInfo,
  TaskFilterParams,
  TaskRetryRequest,
  TaskBatchOperation,
  TaskListResponse
} from '../types/task';

export class TaskService {
  /**
   * 获取任务列表
   */
  async getTasks(params?: TaskFilterParams): Promise<TaskListResponse> {
    const response = await api.get('/tasks', { params });
    return response;
  }

  /**
   * 获取单个任务详情
   */
  async getTask(taskId: string): Promise<TaskMonitor> {
    const response = await api.get(`/tasks/${taskId}`);
    return response;
  }

  /**
   * 获取任务统计信息
   */
  async getTaskStatistics(days: number = 7): Promise<TaskStatistics> {
    const response = await api.get('/tasks/statistics', {
      params: { days }
    });
    return response;
  }

  /**
   * 获取队列信息
   */
  async getQueueInfo(): Promise<TaskQueueInfo[]> {
    const response = await api.get('/tasks/queues');
    return response;
  }

  /**
   * 获取工作节点信息
   */
  async getWorkerInfo(): Promise<WorkerInfo[]> {
    const response = await api.get('/tasks/workers');
    return response;
  }

  /**
   * 重试任务
   */
  async retryTask(taskId: string, reason?: string): Promise<{ message: string; task_id: string }> {
    const response = await api.post(`/tasks/${taskId}/retry`, {
      task_id: taskId,
      reason
    });
    return response;
  }

  /**
   * 取消任务
   */
  async cancelTask(taskId: string, reason?: string): Promise<{ message: string; task_id: string }> {
    const response = await api.delete(`/tasks/${taskId}`, {
      data: { reason }
    });
    return response;
  }

  /**
   * 批量操作任务
   */
  async batchOperation(operation: TaskBatchOperation): Promise<{
    success: string[];
    failed: Array<{ task_id: string; error: string }>;
  }> {
    const response = await api.post('/tasks/batch', operation);
    return response;
  }

  /**
   * 获取活跃任务 (兼容旧API)
   */
  async getActiveTasks(): Promise<any[]> {
    const response = await api.get('/tasks/active');
    return response;
  }

  /**
   * 启动OCR任务
   */
  async startOcrTask(fileId: string, engine: string = 'paddleocr'): Promise<{
    task_id: string;
    message: string;
    status: string;
  }> {
    const response = await api.post('/tasks/ocr', null, {
      params: { file_id: fileId, engine }
    });
    return response;
  }

  /**
   * 停止OCR任务
   */
  async stopOcrTask(fileId: string): Promise<any> {
    const response = await api.post(`/ocr/stop/${fileId}`);
    return response;
  }

  /**
   * 启动LLM任务
   */
  async startLlmTask(sliceId: string, provider: string = 'openai'): Promise<{
    task_id: string;
    message: string;
    status: string;
  }> {
    const response = await api.post('/tasks/llm', null, {
      params: { slice_id: sliceId, provider }
    });
    return response;
  }

  /**
   * 启动知识图谱抽取任务
   */
  async startKgTask(cotItemId: string): Promise<{
    task_id: string;
    message: string;
    status: string;
  }> {
    const response = await api.post('/tasks/kg', null, {
      params: { cot_item_id: cotItemId }
    });
    return response;
  }

  /**
   * 轮询任务状态直到完成
   */
  async pollTaskStatus(
    taskId: string,
    onProgress?: (task: TaskMonitor) => void,
    interval: number = 2000
  ): Promise<TaskMonitor> {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const task = await this.getTask(taskId);
          
          if (onProgress) {
            onProgress(task);
          }

          if (task.is_completed) {
            resolve(task);
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

export const taskService = new TaskService();