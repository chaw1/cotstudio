/**
 * 任务监控相关类型定义
 */

export enum TaskStatus {
  PENDING = 'PENDING',
  PROGRESS = 'PROGRESS',
  SUCCESS = 'SUCCESS',
  FAILURE = 'FAILURE',
  RETRY = 'RETRY',
  REVOKED = 'REVOKED'
}

export enum TaskType {
  OCR_PROCESSING = 'ocr_processing',
  LLM_PROCESSING = 'llm_processing',
  KG_EXTRACTION = 'kg_extraction',
  FILE_PROCESSING = 'file_processing',
  EXPORT_PROCESSING = 'export_processing',
  IMPORT_PROCESSING = 'import_processing',
  HEALTH_CHECK = 'health_check'
}

export enum TaskPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export interface TaskMonitor {
  id: string;
  task_id: string;
  task_name: string;
  task_type: TaskType;
  status: TaskStatus;
  priority: TaskPriority;
  
  // 进度信息
  progress: number;
  current_step?: string;
  total_steps?: number;
  
  // 执行信息
  user_id: string;
  worker_name?: string;
  queue_name: string;
  
  // 时间信息
  created_at: string;
  started_at?: string;
  completed_at?: string;
  updated_at: string;
  
  // 执行时间统计
  estimated_duration?: number;
  actual_duration?: number;
  execution_time?: number;
  
  // 任务参数和结果
  parameters?: Record<string, any>;
  result?: Record<string, any>;
  error_info?: Record<string, any>;
  
  // 重试信息
  retry_count: number;
  max_retries: number;
  retry_delay: number;
  
  // 状态消息
  message?: string;
  
  // 标记和标签
  tags?: Record<string, any>;
  is_critical: boolean;
  
  // 计算属性
  is_active: boolean;
  is_completed: boolean;
  can_retry: boolean;
}

export interface TaskStatistics {
  total_tasks: number;
  active_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  success_rate: number;
  average_duration?: number;
  
  // 按类型统计
  by_type: Record<string, number>;
  // 按状态统计
  by_status: Record<string, number>;
  // 按优先级统计
  by_priority: Record<string, number>;
}

export interface TaskQueueInfo {
  queue_name: string;
  active_tasks: number;
  scheduled_tasks: number;
  reserved_tasks: number;
  total_tasks: number;
}

export interface WorkerInfo {
  worker_name: string;
  status: string;
  active_tasks: number;
  processed_tasks: number;
  load_average: number[];
  last_heartbeat?: string;
}

export interface TaskFilterParams {
  status?: TaskStatus[];
  task_type?: TaskType[];
  priority?: TaskPriority[];
  user_id?: string;
  queue_name?: string;
  is_critical?: boolean;
  created_after?: string;
  created_before?: string;
  limit?: number;
  offset?: number;
  order_by?: string;
  order_desc?: boolean;
}

export interface TaskRetryRequest {
  task_id: string;
  reason?: string;
}

export interface TaskBatchOperation {
  task_ids: string[];
  operation: 'cancel' | 'retry' | 'delete';
  reason?: string;
}

export interface TaskWebSocketMessage {
  type: string;
  task_id: string;
  user_id: string;
  status: TaskStatus;
  progress?: number;
  message?: string;
  timestamp: string;
  data?: Record<string, any>;
}

export interface TaskListResponse {
  items: TaskMonitor[];
  total: number;
  limit: number;
  offset: number;
}

// WebSocket 消息类型
export interface WebSocketMessage {
  type: 'connection_established' | 'task_update' | 'subscription_confirmed' | 'unsubscription_confirmed' | 'subscriptions_list' | 'heartbeat_ack' | 'error' | 'pong';
  task_id?: string;
  user_id?: string;
  status?: TaskStatus;
  progress?: number;
  message?: string;
  timestamp: string;
  data?: Record<string, any>;
  task_ids?: string[];
}

// 任务状态颜色映射
export const TASK_STATUS_COLORS: Record<TaskStatus, string> = {
  [TaskStatus.PENDING]: 'blue',
  [TaskStatus.PROGRESS]: 'orange',
  [TaskStatus.SUCCESS]: 'green',
  [TaskStatus.FAILURE]: 'red',
  [TaskStatus.RETRY]: 'purple',
  [TaskStatus.REVOKED]: 'gray'
};

// 任务优先级颜色映射
export const TASK_PRIORITY_COLORS: Record<TaskPriority, string> = {
  [TaskPriority.LOW]: 'gray',
  [TaskPriority.NORMAL]: 'blue',
  [TaskPriority.HIGH]: 'orange',
  [TaskPriority.CRITICAL]: 'red'
};

// 任务类型显示名称
export const TASK_TYPE_NAMES: Record<TaskType, string> = {
  [TaskType.OCR_PROCESSING]: 'OCR处理',
  [TaskType.LLM_PROCESSING]: 'LLM处理',
  [TaskType.KG_EXTRACTION]: '知识图谱抽取',
  [TaskType.FILE_PROCESSING]: '文件处理',
  [TaskType.EXPORT_PROCESSING]: '导出处理',
  [TaskType.IMPORT_PROCESSING]: '导入处理',
  [TaskType.HEALTH_CHECK]: '健康检查'
};

// 任务状态显示名称
export const TASK_STATUS_NAMES: Record<TaskStatus, string> = {
  [TaskStatus.PENDING]: '等待中',
  [TaskStatus.PROGRESS]: '进行中',
  [TaskStatus.SUCCESS]: '成功',
  [TaskStatus.FAILURE]: '失败',
  [TaskStatus.RETRY]: '重试中',
  [TaskStatus.REVOKED]: '已取消'
};

// 任务优先级显示名称
export const TASK_PRIORITY_NAMES: Record<TaskPriority, string> = {
  [TaskPriority.LOW]: '低',
  [TaskPriority.NORMAL]: '普通',
  [TaskPriority.HIGH]: '高',
  [TaskPriority.CRITICAL]: '紧急'
};