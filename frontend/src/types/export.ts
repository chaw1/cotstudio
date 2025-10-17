/**
 * 导出相关类型定义
 */

export enum ExportFormat {
  JSON = 'json',
  MARKDOWN = 'markdown',
  LATEX = 'latex',
  TXT = 'txt'
}

export enum ExportStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export interface ExportRequest {
  project_id: string;
  format: ExportFormat;
  include_metadata?: boolean;
  include_files?: boolean;
  include_kg_data?: boolean;
  cot_status_filter?: string[];
}

export interface ExportTaskResponse {
  task_id: string;
  status: ExportStatus;
  progress: number;
  message?: string;
  download_url?: string;
  created_at: string;
  completed_at?: string;
}

export interface ExportValidationResult {
  is_valid: boolean;
  total_items: number;
  validation_errors: string[];
  warnings: string[];
  checksum: string;
}

export interface ExportHistoryItem {
  id: string;
  project_id: string;
  format: ExportFormat;
  status: ExportStatus;
  file_size?: number;
  download_url?: string;
  created_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
  tags?: string[];
  project_type: string;
  status: string;
}