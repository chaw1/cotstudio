/**
 * 前端测试环境设置
 */
import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn(() => ({
  disconnect: vi.fn(),
  observe: vi.fn(),
  unobserve: vi.fn(),
}));

// Mock ResizeObserver
global.ResizeObserver = vi.fn(() => ({
  disconnect: vi.fn(),
  observe: vi.fn(),
  unobserve: vi.fn(),
}));

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.sessionStorage = sessionStorageMock;

// Mock URL.createObjectURL
global.URL.createObjectURL = vi.fn(() => 'mocked-url');
global.URL.revokeObjectURL = vi.fn();

// Mock File and FileReader
global.File = class MockFile {
  constructor(
    public chunks: BlobPart[],
    public name: string,
    public options?: FilePropertyBag
  ) {}
  
  get size() {
    return this.chunks.reduce((size, chunk) => {
      if (typeof chunk === 'string') return size + chunk.length;
      if (chunk instanceof ArrayBuffer) return size + chunk.byteLength;
      return size + (chunk as any).length;
    }, 0);
  }
  
  get type() {
    return this.options?.type || '';
  }
};

global.FileReader = class MockFileReader {
  result: string | ArrayBuffer | null = null;
  error: DOMException | null = null;
  readyState: number = 0;
  onload: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onerror: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onloadend: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;

  readAsText(file: Blob) {
    setTimeout(() => {
      this.result = 'mocked file content';
      this.readyState = 2;
      if (this.onload) {
        this.onload({} as ProgressEvent<FileReader>);
      }
    }, 0);
  }

  readAsDataURL(file: Blob) {
    setTimeout(() => {
      this.result = 'data:text/plain;base64,bW9ja2VkIGZpbGUgY29udGVudA==';
      this.readyState = 2;
      if (this.onload) {
        this.onload({} as ProgressEvent<FileReader>);
      }
    }, 0);
  }

  abort() {
    this.readyState = 2;
  }

  addEventListener() {}
  removeEventListener() {}
  dispatchEvent() { return true; }
};

// Mock Cytoscape for knowledge graph tests
vi.mock('cytoscape', () => ({
  default: vi.fn(() => ({
    add: vi.fn(),
    remove: vi.fn(),
    layout: vi.fn(() => ({ run: vi.fn() })),
    fit: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
    destroy: vi.fn(),
    elements: vi.fn(() => ({ length: 0 })),
    nodes: vi.fn(() => ({ length: 0 })),
    edges: vi.fn(() => ({ length: 0 })),
    style: vi.fn(),
    zoom: vi.fn(),
    pan: vi.fn(),
    center: vi.fn(),
    getElementById: vi.fn(),
    filter: vi.fn(() => ({ length: 0 })),
    json: vi.fn(() => ({ elements: [] })),
    mount: vi.fn(),
    unmount: vi.fn(),
  }))
}));

// Mock Ant Design components that might cause issues in tests
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd');
  return {
    ...actual,
    Upload: {
      ...actual.Upload,
      Dragger: ({ children, ...props }: any) => {
        const div = document.createElement('div');
        div.setAttribute('data-testid', 'upload-dragger');
        return div;
      },
    },
  };
});

// Global test utilities
global.testUtils = {
  // 创建模拟的项目数据
  createMockProject: (overrides = {}) => ({
    id: 'test-project-id',
    name: 'Test Project',
    description: 'Test Description',
    owner: 'test-user',
    status: 'active',
    created_at: new Date().toISOString(),
    file_count: 0,
    cot_count: 0,
    tags: [],
    ...overrides,
  }),

  // 创建模拟的文件数据
  createMockFile: (overrides = {}) => ({
    file_id: 'test-file-id',
    filename: 'test.txt',
    size: 1024,
    mime_type: 'text/plain',
    ocr_status: 'pending',
    created_at: new Date().toISOString(),
    ...overrides,
  }),

  // 创建模拟的CoT数据
  createMockCoTItem: (overrides = {}) => ({
    id: 'test-cot-id',
    project_id: 'test-project-id',
    slice_id: 'test-slice-id',
    question: 'Test question?',
    status: 'draft',
    created_at: new Date().toISOString(),
    candidates: [
      {
        id: 'candidate-1',
        text: 'Test answer',
        chain_of_thought: 'Test reasoning',
        score: 0.8,
        chosen: true,
        rank: 1,
      },
    ],
    ...overrides,
  }),

  // 创建模拟的切片数据
  createMockSlice: (overrides = {}) => ({
    id: 'test-slice-id',
    content: 'Test slice content',
    start_offset: 0,
    end_offset: 20,
    slice_type: 'paragraph',
    page_number: 1,
    ...overrides,
  }),

  // 等待异步操作完成
  waitForAsync: () => new Promise(resolve => setTimeout(resolve, 0)),

  // 模拟API响应
  mockApiResponse: (data: any, status = 200) => ({
    status,
    ok: status >= 200 && status < 300,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  }),
};

// 设置测试超时
vi.setConfig({
  testTimeout: 10000, // 10秒
});

// 在每个测试前清理模拟
beforeEach(() => {
  vi.clearAllMocks();
  localStorageMock.clear();
  sessionStorageMock.clear();
});

// 全局错误处理
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
});

console.log('🧪 测试环境设置完成');