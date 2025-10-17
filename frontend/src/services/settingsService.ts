import api from './api';
import {
  SystemSettings,
  LLMProviderConfig,
  OCREngineConfig,
  SystemPromptTemplate,
  COTGenerationConfig,
  SettingsValidationResult
} from '../types';

export interface SettingsResponse {
  settings: SystemSettings;
  message: string;
}

export interface LLMProvidersResponse {
  providers: LLMProviderConfig[];
  default_provider: string;
  enabled_providers: LLMProviderConfig[];
}

export interface OCREnginesResponse {
  engines: OCREngineConfig[];
  default_engine: string;
  enabled_engines: OCREngineConfig[];
}

export interface SystemPromptsResponse {
  prompts: SystemPromptTemplate[];
  categories: string[];
}

export interface SystemPromptsByCategoryResponse {
  prompts: SystemPromptTemplate[];
  default_prompt?: SystemPromptTemplate;
  category: string;
}

export interface SettingsExportResponse {
  settings: SystemSettings;
  export_time: string;
  version: string;
}

class SettingsService {
  // 获取系统设置
  async getSettings(): Promise<SystemSettings> {
    const response = await api.get<SettingsResponse>('/settings');
    return response.settings;
  }

  // 更新系统设置
  async updateSettings(settings: Partial<SystemSettings>): Promise<SystemSettings> {
    const response = await api.put<SettingsResponse>('/settings', settings);
    return response.settings;
  }

  // 重置系统设置
  async resetSettings(): Promise<SystemSettings> {
    const response = await api.post<SettingsResponse>('/settings/reset');
    return response.settings;
  }

  // LLM提供商相关
  async getLLMProviders(): Promise<LLMProvidersResponse> {
    return await api.get<LLMProvidersResponse>('/settings/llm-providers');
  }

  async getLLMProvider(provider: string): Promise<LLMProviderConfig> {
    return await api.get<LLMProviderConfig>(`/settings/llm-providers/${provider}`);
  }

  async validateLLMProvider(provider: string, config: LLMProviderConfig): Promise<SettingsValidationResult> {
    return await api.post<SettingsValidationResult>(`/settings/llm-providers/${provider}/validate`, config);
  }

  // OCR引擎相关
  async getOCREngines(): Promise<OCREnginesResponse> {
    return await api.get<OCREnginesResponse>('/settings/ocr-engines');
  }

  async getOCREngine(engine: string): Promise<OCREngineConfig> {
    return await api.get<OCREngineConfig>(`/settings/ocr-engines/${engine}`);
  }

  async validateOCREngine(engine: string, config: OCREngineConfig): Promise<SettingsValidationResult> {
    return await api.post<SettingsValidationResult>(`/settings/ocr-engines/${engine}/validate`, config);
  }

  // 系统提示词相关
  async getSystemPrompts(): Promise<SystemPromptsResponse> {
    return await api.get<SystemPromptsResponse>('/settings/system-prompts');
  }

  async getSystemPromptsByCategory(category: string): Promise<SystemPromptsByCategoryResponse> {
    return await api.get<SystemPromptsByCategoryResponse>(`/settings/system-prompts/category/${category}`);
  }

  async getSystemPrompt(name: string): Promise<SystemPromptTemplate> {
    return await api.get<SystemPromptTemplate>(`/settings/system-prompts/${name}`);
  }

  // CoT生成配置
  async getCOTGenerationConfig(): Promise<COTGenerationConfig> {
    return await api.get<COTGenerationConfig>('/settings/cot-generation');
  }

  // 导入导出
  async exportSettings(): Promise<SettingsExportResponse> {
    return await api.get<SettingsExportResponse>('/settings/export');
  }

  async importSettings(settingsData: SystemSettings): Promise<SystemSettings> {
    const response = await api.post<SettingsResponse>('/settings/import', settingsData);
    return response.settings;
  }
}

export const settingsService = new SettingsService();
export default settingsService;