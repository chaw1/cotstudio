// Common types
export interface BaseEntity {
  id: string;
  createdAt?: string;
  updatedAt?: string;
  created_at?: string; // 后端使用的字段名
  updated_at?: string; // 后端使用的字段名
}

// Project types
export interface Project extends BaseEntity {
  name: string;
  description?: string;
  owner_id: string;
  owner_name?: string;
  status: 'active' | 'archived' | 'draft';
  tags: string[];
  fileCount?: number; // 兼容旧字段名
  cotCount?: number;  // 兼容旧字段名
  file_count?: number; // 后端使用的字段名
  cot_count?: number;  // 后端使用的字段名
  kg_count?: number;   // 知识图谱实体数量
}

// File types
export interface FileInfo extends BaseEntity {
  projectId?: string;         // 兼容旧字段名
  project_id?: string;        // 后端使用的字段名
  filename: string;
  original_filename?: string; // 后端使用的字段名
  filePath?: string;          // 兼容旧字段名
  file_path?: string;         // 后端使用的字段名
  fileHash?: string;          // 兼容旧字段名
  file_hash?: string;         // 后端使用的字段名
  size: number;
  mimeType?: string;          // 兼容旧字段名
  mime_type?: string;         // 后端使用的字段名
  ocrStatus?: 'pending' | 'processing' | 'completed' | 'failed'; // 兼容旧字段名
  ocr_status?: 'pending' | 'processing' | 'completed' | 'failed'; // 后端使用的字段名
  ocr_engine?: string;
  slice_count?: number;
}

// OCR types
export interface OCRTaskStatus {
  taskId: string;
  fileId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  engine: string;
  startTime: string;
  endTime?: string;
  error?: string;
  result?: {
    totalPages: number;
    processedPages: number;
    extractedText: number;
    detectedTables: number;
    detectedImages: number;
    slicesGenerated: number;
  };
}

// Task monitoring types
export * from './task';

// Layout types
export * from './layout';

// Slice types
export interface Slice extends BaseEntity {
  fileId: string;
  content: string;
  startOffset: number;
  endOffset: number;
  sliceType: 'paragraph' | 'image' | 'table';
  pageNumber: number;
}

// CoT types
export interface COTCandidate {
  id: string;
  text: string;
  chainOfThought: string;
  score: number;
  chosen: boolean;
  rank: number;
}

export interface COTItem extends BaseEntity {
  projectId: string;
  sliceId: string;
  question: string;
  candidates: COTCandidate[];
  status: 'draft' | 'reviewed' | 'approved';
  createdBy: string;
}

// Knowledge Graph types
export interface KGEntity {
  id: string;
  label: string;
  type: string;
  properties: Record<string, any>;
}

export interface KGRelation {
  id: string;
  source: string;
  target: string;
  type: string;
  properties: Record<string, any>;
}

// User types
export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'editor' | 'viewer';
}

// API types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
}

export interface ApiError {
  error: string;
  message: string;
  timestamp: string;
}

// Settings types
export interface LLMProviderConfig {
  provider: string;
  api_key?: string;
  base_url: string;
  model: string;
  enabled: boolean;
  timeout: number;
  max_retries: number;
  retry_delay: number;
}

export interface OCREngineConfig {
  engine: string;
  enabled: boolean;
  priority: number;
  parameters: Record<string, any>;
}

export interface SystemPromptTemplate {
  name: string;
  description?: string;
  template: string;
  variables: string[];
  category: string;
  is_default: boolean;
}

export interface COTGenerationConfig {
  candidate_count: number;
  question_max_length: number;
  answer_max_length: number;
  enable_auto_generation: boolean;
  quality_threshold: number;
}

export interface SystemSettings {
  llm_providers: LLMProviderConfig[];
  default_llm_provider: string;
  ocr_engines: OCREngineConfig[];
  default_ocr_engine: string;
  system_prompts: SystemPromptTemplate[];
  cot_generation: COTGenerationConfig;
}

export interface SettingsValidationResult {
  valid: boolean;
  message: string;
  details: Record<string, any>;
}

// UI types
export interface MenuItem {
  key: string;
  label: string;
  icon?: React.ReactNode;
  children?: MenuItem[];
}

export interface TableColumn {
  key: string;
  title: string;
  dataIndex: string;
  width?: number;
  render?: (value: any, record: any) => React.ReactNode;
}