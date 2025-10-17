import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Settings from '../../pages/Settings';
import { useSettingsStore } from '../../stores/settingsStore';
import { SystemSettings, LLMProviderConfig, OCREngineConfig } from '../../types';

// Mock the settings store
vi.mock('../../stores/settingsStore');

const mockSettingsStore = {
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
  loadSettings: vi.fn(),
  updateSettings: vi.fn(),
  resetSettings: vi.fn(),
  clearError: vi.fn(),
  updateLLMProvider: vi.fn(),
  setDefaultLLMProvider: vi.fn(),
  validateLLMProvider: vi.fn(),
  updateOCREngine: vi.fn(),
  setDefaultOCREngine: vi.fn(),
  validateOCREngine: vi.fn(),
  updateSystemPrompt: vi.fn(),
  addSystemPrompt: vi.fn(),
  deleteSystemPrompt: vi.fn(),
  updateCOTGenerationConfig: vi.fn(),
  exportSettings: vi.fn(),
  importSettings: vi.fn()
};

const mockSettings: SystemSettings = {
  llm_providers: [
    {
      provider: 'openai',
      api_key: 'test-key',
      base_url: 'https://api.openai.com/v1',
      model: 'gpt-3.5-turbo',
      enabled: true,
      timeout: 60,
      max_retries: 3,
      retry_delay: 1.0
    },
    {
      provider: 'deepseek',
      api_key: 'test-deepseek-key',
      base_url: 'https://api.deepseek.com',
      model: 'deepseek-chat',
      enabled: true,
      timeout: 60,
      max_retries: 3,
      retry_delay: 1.0
    }
  ],
  default_llm_provider: 'deepseek',
  ocr_engines: [
    {
      engine: 'paddleocr',
      enabled: true,
      priority: 1,
      parameters: {
        use_angle_cls: true,
        lang: 'ch',
        use_gpu: false
      }
    },
    {
      engine: 'mineru',
      enabled: true,
      priority: 2,
      parameters: {
        layout_detection: true,
        formula_detection: true,
        table_detection: true
      }
    }
  ],
  default_ocr_engine: 'paddleocr',
  system_prompts: [
    {
      name: 'academic_question_generation',
      description: '学术级别问题生成模板',
      template: '基于以下文本内容，生成一个学术水平的问题：{text_content}',
      variables: ['text_content'],
      category: 'question_generation',
      is_default: true
    }
  ],
  cot_generation: {
    candidate_count: 3,
    question_max_length: 500,
    answer_max_length: 2000,
    enable_auto_generation: true,
    quality_threshold: 0.7
  }
};

describe('Settings Page', () => {
  beforeEach(() => {
    vi.mocked(useSettingsStore).mockReturnValue({
      ...mockSettingsStore,
      settings: mockSettings,
      llmProviders: mockSettings.llm_providers,
      defaultLLMProvider: mockSettings.default_llm_provider,
      ocrEngines: mockSettings.ocr_engines,
      defaultOCREngine: mockSettings.default_ocr_engine,
      systemPrompts: mockSettings.system_prompts,
      promptCategories: ['question_generation'],
      cotGenerationConfig: mockSettings.cot_generation
    });
  });

  it('renders settings page with all tabs', () => {
    render(<Settings />);
    
    expect(screen.getByText('系统设置')).toBeInTheDocument();
    expect(screen.getByText('LLM配置')).toBeInTheDocument();
    expect(screen.getByText('OCR引擎')).toBeInTheDocument();
    expect(screen.getByText('系统提示词')).toBeInTheDocument();
    expect(screen.getByText('CoT生成')).toBeInTheDocument();
    expect(screen.getByText('导入导出')).toBeInTheDocument();
  });

  it('loads settings on mount', () => {
    render(<Settings />);
    expect(mockSettingsStore.loadSettings).toHaveBeenCalled();
  });

  it('displays loading state', () => {
    vi.mocked(useSettingsStore).mockReturnValue({
      ...mockSettingsStore,
      loading: true,
      settings: null
    });

    render(<Settings />);
    expect(screen.getByText('加载系统设置中...')).toBeInTheDocument();
  });

  it('displays error state', () => {
    const errorMessage = '加载设置失败';
    vi.mocked(useSettingsStore).mockReturnValue({
      ...mockSettingsStore,
      error: errorMessage,
      settings: mockSettings
    });

    render(<Settings />);
    expect(screen.getByText('加载设置失败')).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('switches between tabs', async () => {
    render(<Settings />);
    
    // Click on OCR engine tab
    fireEvent.click(screen.getByText('OCR引擎'));
    await waitFor(() => {
      expect(screen.getByText('OCR引擎配置')).toBeInTheDocument();
    });

    // Click on system prompts tab
    fireEvent.click(screen.getByText('系统提示词'));
    await waitFor(() => {
      expect(screen.getByText('系统提示词管理')).toBeInTheDocument();
    });

    // Click on CoT generation tab
    fireEvent.click(screen.getByText('CoT生成'));
    await waitFor(() => {
      expect(screen.getByText('CoT生成配置')).toBeInTheDocument();
    });
  });
});

describe('LLM Provider Configuration', () => {
  beforeEach(() => {
    vi.mocked(useSettingsStore).mockReturnValue({
      ...mockSettingsStore,
      settings: mockSettings,
      llmProviders: mockSettings.llm_providers,
      defaultLLMProvider: mockSettings.default_llm_provider
    });
  });

  it('displays LLM providers', () => {
    render(<Settings />);
    
    expect(screen.getByText('OPENAI')).toBeInTheDocument();
    expect(screen.getByText('DEEPSEEK')).toBeInTheDocument();
    expect(screen.getByText('默认')).toBeInTheDocument(); // Default tag for deepseek
  });

  it('allows editing LLM provider', async () => {
    render(<Settings />);
    
    // Find and click edit button for OpenAI
    const editButtons = screen.getAllByText('编辑');
    fireEvent.click(editButtons[0]);
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('输入API密钥')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('https://api.example.com')).toBeInTheDocument();
    });
  });
});

describe('OCR Engine Configuration', () => {
  beforeEach(() => {
    vi.mocked(useSettingsStore).mockReturnValue({
      ...mockSettingsStore,
      settings: mockSettings,
      ocrEngines: mockSettings.ocr_engines,
      defaultOCREngine: mockSettings.default_ocr_engine
    });
  });

  it('displays OCR engines', () => {
    render(<Settings />);
    
    // Switch to OCR tab
    fireEvent.click(screen.getByText('OCR引擎'));
    
    expect(screen.getByText('PADDLEOCR')).toBeInTheDocument();
    expect(screen.getByText('MINERU')).toBeInTheDocument();
    expect(screen.getByText('优先级: 1')).toBeInTheDocument();
    expect(screen.getByText('优先级: 2')).toBeInTheDocument();
  });

  it('shows engine descriptions', () => {
    render(<Settings />);
    
    fireEvent.click(screen.getByText('OCR引擎'));
    
    expect(screen.getByText(/PaddleOCR是百度开源的OCR工具/)).toBeInTheDocument();
    expect(screen.getByText(/MinerU是专门针对学术文档的OCR工具/)).toBeInTheDocument();
  });
});

describe('System Prompt Management', () => {
  beforeEach(() => {
    vi.mocked(useSettingsStore).mockReturnValue({
      ...mockSettingsStore,
      settings: mockSettings,
      systemPrompts: mockSettings.system_prompts,
      promptCategories: ['question_generation']
    });
  });

  it('displays system prompts', () => {
    render(<Settings />);
    
    fireEvent.click(screen.getByText('系统提示词'));
    
    expect(screen.getByText('academic_question_generation')).toBeInTheDocument();
    expect(screen.getByText('学术级别问题生成模板')).toBeInTheDocument();
  });

  it('allows adding new prompt', () => {
    render(<Settings />);
    
    fireEvent.click(screen.getByText('系统提示词'));
    
    const addButton = screen.getByText('添加模板');
    expect(addButton).toBeInTheDocument();
    
    fireEvent.click(addButton);
    // Modal should open (would need more detailed testing for modal content)
  });
});

describe('CoT Generation Configuration', () => {
  beforeEach(() => {
    vi.mocked(useSettingsStore).mockReturnValue({
      ...mockSettingsStore,
      settings: mockSettings,
      cotGenerationConfig: mockSettings.cot_generation
    });
  });

  it('displays CoT generation settings', () => {
    render(<Settings />);
    
    fireEvent.click(screen.getByText('CoT生成'));
    
    expect(screen.getByText('候选答案数量')).toBeInTheDocument();
    expect(screen.getByText('问题最大长度')).toBeInTheDocument();
    expect(screen.getByText('答案最大长度')).toBeInTheDocument();
    expect(screen.getByText('质量阈值')).toBeInTheDocument();
  });

  it('shows current configuration values', () => {
    render(<Settings />);
    
    fireEvent.click(screen.getByText('CoT生成'));
    
    // Check if form fields have correct values
    const candidateCountInput = screen.getByDisplayValue('3');
    const questionLengthInput = screen.getByDisplayValue('500');
    const answerLengthInput = screen.getByDisplayValue('2000');
    
    expect(candidateCountInput).toBeInTheDocument();
    expect(questionLengthInput).toBeInTheDocument();
    expect(answerLengthInput).toBeInTheDocument();
  });
});

describe('Import/Export Functionality', () => {
  beforeEach(() => {
    vi.mocked(useSettingsStore).mockReturnValue({
      ...mockSettingsStore,
      settings: mockSettings,
      exportSettings: vi.fn().mockResolvedValue({
        settings: mockSettings,
        export_time: '2024-01-01T00:00:00Z',
        version: '1.0'
      })
    });
  });

  it('displays import/export options', () => {
    render(<Settings />);
    
    fireEvent.click(screen.getByText('导入导出'));
    
    expect(screen.getByText('导出设置')).toBeInTheDocument();
    expect(screen.getByText('选择设置文件')).toBeInTheDocument();
    expect(screen.getByText('重置为默认设置')).toBeInTheDocument();
  });

  it('shows current settings overview', () => {
    render(<Settings />);
    
    fireEvent.click(screen.getByText('导入导出'));
    
    expect(screen.getByText('当前设置概览')).toBeInTheDocument();
    expect(screen.getByText('2个 (默认: deepseek)')).toBeInTheDocument();
    expect(screen.getByText('2个 (默认: paddleocr)')).toBeInTheDocument();
  });
});