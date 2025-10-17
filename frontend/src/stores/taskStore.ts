/**
 * 任务监控状态管理
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import {
  TaskMonitor,
  TaskStatistics,
  TaskQueueInfo,
  WorkerInfo,
  TaskFilterParams,
  TaskListResponse,
  TaskWebSocketMessage
} from '../types/task';
import { taskService } from '../services/taskService';

interface TaskStore {
  // 状态
  tasks: TaskMonitor[];
  selectedTask: TaskMonitor | null;
  statistics: TaskStatistics | null;
  queueInfo: TaskQueueInfo[];
  workerInfo: WorkerInfo[];
  
  // 加载状态
  loading: boolean;
  error: string | null;
  
  // 过滤和分页
  filters: TaskFilterParams;
  total: number;
  
  // WebSocket连接状态
  isWebSocketConnected: boolean;
  subscribedTasks: Set<string>;
  
  // Actions
  setTasks: (tasks: TaskMonitor[]) => void;
  setSelectedTask: (task: TaskMonitor | null) => void;
  setStatistics: (statistics: TaskStatistics) => void;
  setQueueInfo: (queueInfo: TaskQueueInfo[]) => void;
  setWorkerInfo: (workerInfo: WorkerInfo[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setFilters: (filters: Partial<TaskFilterParams>) => void;
  setWebSocketConnected: (connected: boolean) => void;
  
  // 异步操作
  fetchTasks: () => Promise<void>;
  fetchTask: (taskId: string) => Promise<void>;
  fetchStatistics: (days?: number) => Promise<void>;
  fetchQueueInfo: () => Promise<void>;
  fetchWorkerInfo: () => Promise<void>;
  retryTask: (taskId: string, reason?: string) => Promise<void>;
  cancelTask: (taskId: string, reason?: string) => Promise<void>;
  batchOperation: (taskIds: string[], operation: 'cancel' | 'retry', reason?: string) => Promise<{ success: string[]; failed: Array<{ task_id: string; error: string; }> }>;
  
  // WebSocket相关
  handleTaskUpdate: (message: TaskWebSocketMessage) => void;
  subscribeToTask: (taskId: string) => void;
  unsubscribeFromTask: (taskId: string) => void;
  
  // 工具方法
  getTaskById: (taskId: string) => TaskMonitor | undefined;
  getActiveTasksCount: () => number;
  getFailedTasksCount: () => number;
  reset: () => void;
}

const initialFilters: TaskFilterParams = {
  limit: 50,
  offset: 0,
  order_by: 'created_at',
  order_desc: true
};

export const useTaskStore = create<TaskStore>()(
  devtools(
    (set, get) => ({
      // 初始状态
      tasks: [],
      selectedTask: null,
      statistics: null,
      queueInfo: [],
      workerInfo: [],
      loading: false,
      error: null,
      filters: initialFilters,
      total: 0,
      isWebSocketConnected: false,
      subscribedTasks: new Set(),

      // Setters
      setTasks: (tasks) => set({ tasks }),
      setSelectedTask: (task) => set({ selectedTask: task }),
      setStatistics: (statistics) => set({ statistics }),
      setQueueInfo: (queueInfo) => set({ queueInfo }),
      setWorkerInfo: (workerInfo) => set({ workerInfo }),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
      setFilters: (newFilters) => set((state) => ({
        filters: { ...state.filters, ...newFilters }
      })),
      setWebSocketConnected: (connected) => set({ isWebSocketConnected: connected }),

      // 异步操作
      fetchTasks: async () => {
        const { filters, setLoading, setError } = get();
        
        try {
          setLoading(true);
          setError(null);
          
          const response: TaskListResponse = await taskService.getTasks(filters);
          
          set({
            tasks: response.items,
            total: response.total
          });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : '获取任务列表失败';
          setError(errorMessage);
          console.error('Failed to fetch tasks:', error);
        } finally {
          setLoading(false);
        }
      },

      fetchTask: async (taskId: string) => {
        const { setLoading, setError } = get();
        
        try {
          setLoading(true);
          setError(null);
          
          const task = await taskService.getTask(taskId);
          
          set({ selectedTask: task });
          
          // 更新任务列表中的对应项
          set((state) => ({
            tasks: state.tasks.map(t => t.task_id === taskId ? task : t)
          }));
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : '获取任务详情失败';
          setError(errorMessage);
          console.error('Failed to fetch task:', error);
        } finally {
          setLoading(false);
        }
      },

      fetchStatistics: async (days = 7) => {
        const { setError } = get();
        
        try {
          setError(null);
          
          const statistics = await taskService.getTaskStatistics(days);
          set({ statistics });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : '获取统计信息失败';
          setError(errorMessage);
          console.error('Failed to fetch statistics:', error);
        }
      },

      fetchQueueInfo: async () => {
        const { setError } = get();
        
        try {
          setError(null);
          
          const queueInfo = await taskService.getQueueInfo();
          set({ queueInfo });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : '获取队列信息失败';
          setError(errorMessage);
          console.error('Failed to fetch queue info:', error);
        }
      },

      fetchWorkerInfo: async () => {
        const { setError } = get();
        
        try {
          setError(null);
          
          const workerInfo = await taskService.getWorkerInfo();
          set({ workerInfo });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : '获取工作节点信息失败';
          setError(errorMessage);
          console.error('Failed to fetch worker info:', error);
        }
      },

      retryTask: async (taskId: string, reason?: string) => {
        const { setError, fetchTasks } = get();
        
        try {
          setError(null);
          
          await taskService.retryTask(taskId, reason);
          
          // 刷新任务列表
          await fetchTasks();
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : '重试任务失败';
          setError(errorMessage);
          console.error('Failed to retry task:', error);
          throw error;
        }
      },

      cancelTask: async (taskId: string, reason?: string) => {
        const { setError, fetchTasks } = get();
        
        try {
          setError(null);
          
          await taskService.cancelTask(taskId, reason);
          
          // 刷新任务列表
          await fetchTasks();
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : '取消任务失败';
          setError(errorMessage);
          console.error('Failed to cancel task:', error);
          throw error;
        }
      },

      batchOperation: async (taskIds: string[], operation: 'cancel' | 'retry', reason?: string) => {
        const { setError, fetchTasks } = get();
        
        try {
          setError(null);
          
          const result = await taskService.batchOperation({
            task_ids: taskIds,
            operation,
            reason
          });
          
          // 如果有失败的操作，显示错误信息
          if (result.failed.length > 0) {
            const failedMessages = result.failed.map(f => `${f.task_id}: ${f.error}`).join(', ');
            setError(`部分操作失败: ${failedMessages}`);
          }
          
          // 刷新任务列表
          await fetchTasks();
          
          return result;
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : '批量操作失败';
          setError(errorMessage);
          console.error('Failed to perform batch operation:', error);
          throw error;
        }
      },

      // WebSocket相关
      handleTaskUpdate: (message: TaskWebSocketMessage) => {
        const { tasks, selectedTask } = get();
        
        // 更新任务列表中的对应项
        const updatedTasks = tasks.map(task => {
          if (task.task_id === message.task_id) {
            return {
              ...task,
              status: message.status,
              progress: message.progress || task.progress,
              message: message.message || task.message,
              updated_at: message.timestamp
            };
          }
          return task;
        });
        
        set({ tasks: updatedTasks });
        
        // 如果当前选中的任务被更新，也要更新选中任务
        if (selectedTask?.task_id === message.task_id) {
          set({
            selectedTask: {
              ...selectedTask,
              status: message.status,
              progress: message.progress || selectedTask.progress,
              message: message.message || selectedTask.message,
              updated_at: message.timestamp
            }
          });
        }
      },

      subscribeToTask: (taskId: string) => {
        set((state) => ({
          subscribedTasks: new Set([...state.subscribedTasks, taskId])
        }));
      },

      unsubscribeFromTask: (taskId: string) => {
        set((state) => {
          const newSubscribedTasks = new Set(state.subscribedTasks);
          newSubscribedTasks.delete(taskId);
          return { subscribedTasks: newSubscribedTasks };
        });
      },

      // 工具方法
      getTaskById: (taskId: string) => {
        const { tasks } = get();
        return tasks.find(task => task.task_id === taskId);
      },

      getActiveTasksCount: () => {
        const { tasks } = get();
        return tasks.filter(task => task.is_active).length;
      },

      getFailedTasksCount: () => {
        const { tasks } = get();
        return tasks.filter(task => task.status === 'FAILURE').length;
      },

      reset: () => {
        set({
          tasks: [],
          selectedTask: null,
          statistics: null,
          queueInfo: [],
          workerInfo: [],
          loading: false,
          error: null,
          filters: initialFilters,
          total: 0,
          subscribedTasks: new Set()
        });
      }
    }),
    {
      name: 'task-store'
    }
  )
);