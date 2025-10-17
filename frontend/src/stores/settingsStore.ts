import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import {
  SystemSettings,
  LLMProviderConfig,
  OCREngineConfig,
  SystemPromptTemplate,
  COTGenerationConfig
} from '../types';
import settingsService from '../services/settingsService';

interface SettingsState {
  // 状态
  settings: SystemSettings | null;
  loading: boolean;
  error: string | null;
  
  // LLM提供商
  llmProviders: LLMProviderConfig[];
  defaultLLMProvider: string;
  
  // OCR引擎
  ocrEngines: OCREngineConfig[];
  defaultOCREngine: string;
  
  // 系统提示词
  systemPrompts: SystemPromptTemplate[];
  promptCategories: string[];
  
  // CoT生成配置
  cotGenerationConfig: COTGenerationConfig | null;
  
  // 操作
  loadSettings: () => Promise<void>;
  updateSettings: (settings: Partial<SystemSettings>) => Promise<void>;
  resetSettings: () => Promise<void>;
  
  // LLM提供商操作
  loadLLMProviders: () => Promise<void>;
  updateLLMProvider: (provider: string, config: LLMProviderConfig) => Promise<void>;
  setDefaultLLMProvider: (provider: string) => Promise<void>;
  validateLLMProvider: (provider: string, config: LLMProviderConfig) => Promise<boolean>;
  
  // OCR引擎操作
  loadOCREngines: () => Promise<void>;
  updateOCREngine: (engine: string, config: OCREngineConfig) => Promise<void>;
  setDefaultOCREngine: (engine: string) => Promise<void>;
  validateOCREngine: (engine: string, config: OCREngineConfig) => Promise<boolean>;
  
  // 系统提示词操作
  loadSystemPrompts: () => Promise<void>;
  updateSystemPrompt: (name: string, prompt: SystemPromptTemplate) => Promise<void>;
  addSystemPrompt: (prompt: SystemPromptTemplate) => Promise<void>;
  deleteSystemPrompt: (name: string) => Promise<void>;
  
  // CoT生成配置操作
  loadCOTGenerationConfig: () => Promise<void>;
  updateCOTGenerationConfig: (config: COTGenerationConfig) => Promise<void>;
  
  // 导入导出
  exportSettings: () => Promise<any>;
  importSettings: (settingsData: SystemSettings) => Promise<void>;
  
  // 清理
  clearError: () => void;
}

export const useSettingsStore = create<SettingsState>()(
  devtools(
    (set, get) => ({
      // 初始状态
      settings: null,
      loading: false,
      error: null,
      llmProviders: [],
      defaultLLMProvider: '',
      ocrEngines: [],
      defaultOCREngine: '',
      systemPrompts: [],
      promptCategories: [],
      cotGenerationConfig: null,

      // 加载设置
      loadSettings: async () => {
        set({ loading: true, error: null });
        try {
          const settings = await settingsService.getSettings();
          set({
            settings,
            llmProviders: settings.llm_providers,
            defaultLLMProvider: settings.default_llm_provider,
            ocrEngines: settings.ocr_engines,
            defaultOCREngine: settings.default_ocr_engine,
            systemPrompts: settings.system_prompts,
            promptCategories: [...new Set(settings.system_prompts.map(p => p.category))],
            cotGenerationConfig: settings.cot_generation,
            loading: false
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '加载设置失败',
            loading: false
          });
        }
      },

      // 更新设置
      updateSettings: async (settingsUpdate: Partial<SystemSettings>) => {
        set({ loading: true, error: null });
        try {
          const updatedSettings = await settingsService.updateSettings(settingsUpdate);
          set({
            settings: updatedSettings,
            llmProviders: updatedSettings.llm_providers,
            defaultLLMProvider: updatedSettings.default_llm_provider,
            ocrEngines: updatedSettings.ocr_engines,
            defaultOCREngine: updatedSettings.default_ocr_engine,
            systemPrompts: updatedSettings.system_prompts,
            promptCategories: [...new Set(updatedSettings.system_prompts.map(p => p.category))],
            cotGenerationConfig: updatedSettings.cot_generation,
            loading: false
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '更新设置失败',
            loading: false
          });
        }
      },

      // 重置设置
      resetSettings: async () => {
        set({ loading: true, error: null });
        try {
          const defaultSettings = await settingsService.resetSettings();
          set({
            settings: defaultSettings,
            llmProviders: defaultSettings.llm_providers,
            defaultLLMProvider: defaultSettings.default_llm_provider,
            ocrEngines: defaultSettings.ocr_engines,
            defaultOCREngine: defaultSettings.default_ocr_engine,
            systemPrompts: defaultSettings.system_prompts,
            promptCategories: [...new Set(defaultSettings.system_prompts.map(p => p.category))],
            cotGenerationConfig: defaultSettings.cot_generation,
            loading: false
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '重置设置失败',
            loading: false
          });
        }
      },

      // LLM提供商操作
      loadLLMProviders: async () => {
        try {
          const response = await settingsService.getLLMProviders();
          set({
            llmProviders: response.providers,
            defaultLLMProvider: response.default_provider
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '加载LLM提供商失败'
          });
        }
      },

      updateLLMProvider: async (provider: string, config: LLMProviderConfig) => {
        const { settings } = get();
        if (!settings) return;

        const updatedProviders = settings.llm_providers.map(p =>
          p.provider === provider ? config : p
        );

        await get().updateSettings({ llm_providers: updatedProviders });
      },

      setDefaultLLMProvider: async (provider: string) => {
        await get().updateSettings({ default_llm_provider: provider });
      },

      validateLLMProvider: async (provider: string, config: LLMProviderConfig) => {
        try {
          const result = await settingsService.validateLLMProvider(provider, config);
          return result.valid;
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '验证LLM提供商失败'
          });
          return false;
        }
      },

      // OCR引擎操作
      loadOCREngines: async () => {
        try {
          const response = await settingsService.getOCREngines();
          set({
            ocrEngines: response.engines,
            defaultOCREngine: response.default_engine
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '加载OCR引擎失败'
          });
        }
      },

      updateOCREngine: async (engine: string, config: OCREngineConfig) => {
        const { settings } = get();
        if (!settings) return;

        const updatedEngines = settings.ocr_engines.map(e =>
          e.engine === engine ? config : e
        );

        await get().updateSettings({ ocr_engines: updatedEngines });
      },

      setDefaultOCREngine: async (engine: string) => {
        await get().updateSettings({ default_ocr_engine: engine });
      },

      validateOCREngine: async (engine: string, config: OCREngineConfig) => {
        try {
          const result = await settingsService.validateOCREngine(engine, config);
          return result.valid;
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '验证OCR引擎失败'
          });
          return false;
        }
      },

      // 系统提示词操作
      loadSystemPrompts: async () => {
        try {
          const response = await settingsService.getSystemPrompts();
          set({
            systemPrompts: response.prompts,
            promptCategories: response.categories
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '加载系统提示词失败'
          });
        }
      },

      updateSystemPrompt: async (name: string, prompt: SystemPromptTemplate) => {
        const { settings } = get();
        if (!settings) return;

        const updatedPrompts = settings.system_prompts.map(p =>
          p.name === name ? prompt : p
        );

        await get().updateSettings({ system_prompts: updatedPrompts });
      },

      addSystemPrompt: async (prompt: SystemPromptTemplate) => {
        const { settings } = get();
        if (!settings) return;

        const updatedPrompts = [...settings.system_prompts, prompt];
        await get().updateSettings({ system_prompts: updatedPrompts });
      },

      deleteSystemPrompt: async (name: string) => {
        const { settings } = get();
        if (!settings) return;

        const updatedPrompts = settings.system_prompts.filter(p => p.name !== name);
        await get().updateSettings({ system_prompts: updatedPrompts });
      },

      // CoT生成配置操作
      loadCOTGenerationConfig: async () => {
        try {
          const config = await settingsService.getCOTGenerationConfig();
          set({ cotGenerationConfig: config });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '加载CoT生成配置失败'
          });
        }
      },

      updateCOTGenerationConfig: async (config: COTGenerationConfig) => {
        await get().updateSettings({ cot_generation: config });
      },

      // 导入导出
      exportSettings: async () => {
        try {
          return await settingsService.exportSettings();
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '导出设置失败'
          });
          throw error;
        }
      },

      importSettings: async (settingsData: SystemSettings) => {
        set({ loading: true, error: null });
        try {
          const importedSettings = await settingsService.importSettings(settingsData);
          set({
            settings: importedSettings,
            llmProviders: importedSettings.llm_providers,
            defaultLLMProvider: importedSettings.default_llm_provider,
            ocrEngines: importedSettings.ocr_engines,
            defaultOCREngine: importedSettings.default_ocr_engine,
            systemPrompts: importedSettings.system_prompts,
            promptCategories: [...new Set(importedSettings.system_prompts.map(p => p.category))],
            cotGenerationConfig: importedSettings.cot_generation,
            loading: false
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '导入设置失败',
            loading: false
          });
        }
      },

      // 清理错误
      clearError: () => set({ error: null })
    }),
    {
      name: 'settings-store'
    }
  )
);