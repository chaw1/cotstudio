/**
 * 完整工作流程端到端测试
 * 测试从项目创建到CoT标注的完整用户流程
 */
import { describe, it, expect, beforeEach, vi, beforeAll, afterAll } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import App from '../../App';
import { projectService } from '../../services/projectService';
import { fileService } from '../../services/fileService';
import { annotationService } from '../../services/annotationService';

// Mock services
vi.mock('../../services/projectService');
vi.mock('../../services/fileService');
vi.mock('../../services/annotationService');

const mockProjectService = vi.mocked(projectService);
const mockFileService = vi.mocked(fileService);
const mockAnnotationService = vi.mocked(annotationService);

// Test data
const mockProject = {
  id: 'test-project-1',
  name: 'AI技术研究项目',
  description: '人工智能技术发展研究',
  tags: ['AI', '机器学习'],
  status: 'active',
  created_at: '2024-01-01T00:00:00Z',
  file_count: 0,
  cot_count: 0
};

const mockFile = {
  id: 'test-file-1',
  filename: 'ai_research.txt',
  size: 1024,
  mime_type: 'text/plain',
  ocr_status: 'completed',
  created_at: '2024-01-01T00:00:00Z'
};

const mockSlices = [
  {
    id: 'slice-1',
    content: '人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质。',
    slice_type: 'paragraph',
    start_offset: 0,
    end_offset: 50,
    page_number: 1
  },
  {
    id: 'slice-2', 
    content: '机器学习是人工智能的一个重要分支，它通过算法使计算机能够从数据中学习。',
    slice_type: 'paragraph',
    start_offset: 51,
    end_offset: 100,
    page_number: 1
  }
];

const mockCOTData = {
  id: 'cot-1',
  question: '什么是人工智能？请详细解释其定义和主要特征。',
  candidates: [
    {
      id: 'candidate-1',
      text: '人工智能是计算机科学的分支，旨在创造智能机器。',
      chain_of_thought: '首先，我需要理解人工智能的基本定义...',
      score: 0.9,
      chosen: true,
      rank: 1
    },
    {
      id: 'candidate-2',
      text: 'AI是模拟人类智能的技术。',
      chain_of_thought: '人工智能的核心是模拟人类的思维过程...',
      score: 0.8,
      chosen: false,
      rank: 2
    },
    {
      id: 'candidate-3',
      text: '人工智能包括机器学习和深度学习等技术。',
      chain_of_thought: '从技术角度来看，人工智能涵盖多个子领域...',
      score: 0.7,
      chosen: false,
      rank: 3
    }
  ],
  status: 'draft'
};

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Complete Workflow E2E Tests', () => {
  let user: ReturnType<typeof userEvent.setup>;

  beforeAll(() => {
    // Setup global mocks
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });

    // Mock file API
    global.File = class MockFile {
      constructor(public content: string[], public name: string, public options?: any) {}
    } as any;

    global.FileReader = class MockFileReader {
      result: string | null = null;
      onload: ((event: any) => void) | null = null;
      
      readAsText(file: File) {
        setTimeout(() => {
          this.result = 'Mock file content';
          if (this.onload) {
            this.onload({ target: { result: this.result } });
          }
        }, 0);
      }
    } as any;
  });

  beforeEach(() => {
    user = userEvent.setup();
    
    // Reset all mocks
    vi.clearAllMocks();
    
    // Setup default mock implementations
    mockProjectService.getProjects.mockResolvedValue([]);
    mockProjectService.createProject.mockResolvedValue(mockProject);
    mockProjectService.getProject.mockResolvedValue(mockProject);
    
    mockFileService.uploadFile.mockResolvedValue(mockFile);
    mockFileService.getFileSlices.mockResolvedValue(mockSlices);
    
    mockAnnotationService.generateCOT.mockResolvedValue(mockCOTData);
    mockAnnotationService.updateCOTAnnotation.mockResolvedValue(mockCOTData);
  });

  afterAll(() => {
    vi.restoreAllMocks();
  });

  it('should complete full project creation to CoT annotation workflow', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Step 1: Navigate to projects page
    expect(screen.getByText(/COT Studio/i)).toBeInTheDocument();
    
    // Step 2: Create new project
    const createProjectButton = screen.getByRole('button', { name: /创建项目|新建项目|Create Project/i });
    await user.click(createProjectButton);

    // Fill project form
    const projectNameInput = screen.getByLabelText(/项目名称|Project Name/i);
    await user.type(projectNameInput, mockProject.name);

    const projectDescInput = screen.getByLabelText(/项目描述|Description/i);
    await user.type(projectDescInput, mockProject.description);

    // Submit project creation
    const submitButton = screen.getByRole('button', { name: /确定|创建|Create/i });
    await user.click(submitButton);

    // Wait for project creation
    await waitFor(() => {
      expect(mockProjectService.createProject).toHaveBeenCalledWith({
        name: mockProject.name,
        description: mockProject.description,
        tags: expect.any(Array)
      });
    });

    // Step 3: Upload file
    // Mock file input
    const fileInput = screen.getByLabelText(/上传文件|Upload File/i);
    const testFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
    
    await user.upload(fileInput, testFile);

    // Wait for file upload
    await waitFor(() => {
      expect(mockFileService.uploadFile).toHaveBeenCalledWith(
        mockProject.id,
        expect.any(FormData)
      );
    });

    // Step 4: Navigate to annotation workspace
    const annotationButton = screen.getByRole('button', { name: /标注|Annotation/i });
    await user.click(annotationButton);

    // Step 5: Select text slice for annotation
    await waitFor(() => {
      expect(screen.getByText(/选择文本片段/i)).toBeInTheDocument();
    });

    const firstSlice = screen.getByText(mockSlices[0].content);
    await user.click(firstSlice);

    // Step 6: Generate CoT question and answers
    const generateButton = screen.getByRole('button', { name: /生成问题|Generate Question/i });
    await user.click(generateButton);

    await waitFor(() => {
      expect(mockAnnotationService.generateCOT).toHaveBeenCalledWith({
        project_id: mockProject.id,
        slice_id: mockSlices[0].id
      });
    });

    // Step 7: Verify CoT candidates are displayed
    await waitFor(() => {
      expect(screen.getByText(mockCOTData.question)).toBeInTheDocument();
      expect(screen.getByText(mockCOTData.candidates[0].text)).toBeInTheDocument();
    });

    // Step 8: Annotate CoT candidates
    // Test drag and drop reordering (simplified)
    const candidateItems = screen.getAllByTestId(/candidate-item/i);
    expect(candidateItems).toHaveLength(3);

    // Test scoring
    const scoreSliders = screen.getAllByRole('slider');
    await user.click(scoreSliders[0]); // Set score for first candidate

    // Test chosen selection
    const chosenButtons = screen.getAllByRole('button', { name: /选择|Choose/i });
    await user.click(chosenButtons[0]); // Mark first candidate as chosen

    // Step 9: Save annotation
    const saveButton = screen.getByRole('button', { name: /保存|Save/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockAnnotationService.updateCOTAnnotation).toHaveBeenCalledWith(
        mockCOTData.id,
        expect.objectContaining({
          candidates: expect.arrayContaining([
            expect.objectContaining({
              chosen: true,
              score: expect.any(Number)
            })
          ])
        })
      );
    });

    // Step 10: Verify completion
    expect(screen.getByText(/标注已保存|Annotation Saved/i)).toBeInTheDocument();
  }, 30000); // 30 second timeout for complex E2E test

  it('should handle file upload errors gracefully', async () => {
    // Mock file upload failure
    mockFileService.uploadFile.mockRejectedValue(new Error('Upload failed'));

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Create project first
    const createProjectButton = screen.getByRole('button', { name: /创建项目|Create Project/i });
    await user.click(createProjectButton);

    const projectNameInput = screen.getByLabelText(/项目名称|Project Name/i);
    await user.type(projectNameInput, 'Test Project');

    const submitButton = screen.getByRole('button', { name: /确定|创建|Create/i });
    await user.click(submitButton);

    // Try to upload file
    const fileInput = screen.getByLabelText(/上传文件|Upload File/i);
    const testFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
    
    await user.upload(fileInput, testFile);

    // Verify error handling
    await waitFor(() => {
      expect(screen.getByText(/上传失败|Upload Failed/i)).toBeInTheDocument();
    });
  });

  it('should handle OCR processing failures', async () => {
    // Mock OCR processing failure
    mockFileService.getFileSlices.mockRejectedValue(new Error('OCR processing failed'));

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Navigate to a project with uploaded file
    mockProjectService.getProjects.mockResolvedValue([mockProject]);
    
    // Simulate OCR failure
    const ocrButton = screen.getByRole('button', { name: /处理OCR|Process OCR/i });
    await user.click(ocrButton);

    await waitFor(() => {
      expect(screen.getByText(/OCR处理失败|OCR Processing Failed/i)).toBeInTheDocument();
    });
  });

  it('should handle LLM service errors', async () => {
    // Mock LLM service failure
    mockAnnotationService.generateCOT.mockRejectedValue(new Error('LLM service unavailable'));

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Navigate to annotation workspace
    // ... (setup steps)

    const generateButton = screen.getByRole('button', { name: /生成问题|Generate Question/i });
    await user.click(generateButton);

    await waitFor(() => {
      expect(screen.getByText(/生成失败|Generation Failed/i)).toBeInTheDocument();
    });
  });

  it('should support drag and drop file upload', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Find drop zone
    const dropZone = screen.getByTestId('file-drop-zone');
    
    // Simulate drag and drop
    const testFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
    
    fireEvent.dragEnter(dropZone);
    fireEvent.dragOver(dropZone);
    fireEvent.drop(dropZone, {
      dataTransfer: {
        files: [testFile]
      }
    });

    await waitFor(() => {
      expect(mockFileService.uploadFile).toHaveBeenCalled();
    });
  });

  it('should display real-time progress updates', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Mock WebSocket connection for real-time updates
    const mockWebSocket = {
      send: vi.fn(),
      close: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn()
    };

    // @ts-ignore
    global.WebSocket = vi.fn(() => mockWebSocket);

    // Trigger an operation that should show progress
    const processButton = screen.getByRole('button', { name: /开始处理|Start Processing/i });
    await user.click(processButton);

    // Simulate progress updates
    const progressCallback = mockWebSocket.addEventListener.mock.calls
      .find(call => call[0] === 'message')?.[1];

    if (progressCallback) {
      progressCallback({
        data: JSON.stringify({
          type: 'progress',
          progress: 50,
          message: 'Processing...'
        })
      });
    }

    await waitFor(() => {
      expect(screen.getByText(/50%/)).toBeInTheDocument();
    });
  });

  it('should maintain state across navigation', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Create project and navigate away
    const createProjectButton = screen.getByRole('button', { name: /创建项目|Create Project/i });
    await user.click(createProjectButton);

    // Fill form
    const projectNameInput = screen.getByLabelText(/项目名称|Project Name/i);
    await user.type(projectNameInput, 'State Test Project');

    // Navigate to different page
    const settingsLink = screen.getByRole('link', { name: /设置|Settings/i });
    await user.click(settingsLink);

    // Navigate back
    const projectsLink = screen.getByRole('link', { name: /项目|Projects/i });
    await user.click(projectsLink);

    // Verify state is maintained
    expect(screen.getByDisplayValue('State Test Project')).toBeInTheDocument();
  });

  it('should handle keyboard navigation', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Test keyboard navigation through CoT candidates
    const candidateItems = screen.getAllByTestId(/candidate-item/i);
    
    // Focus first item
    candidateItems[0].focus();
    
    // Navigate with arrow keys
    fireEvent.keyDown(candidateItems[0], { key: 'ArrowDown' });
    expect(candidateItems[1]).toHaveFocus();

    // Select with Enter
    fireEvent.keyDown(candidateItems[1], { key: 'Enter' });
    
    // Verify selection
    expect(candidateItems[1]).toHaveAttribute('aria-selected', 'true');
  });

  it('should validate form inputs', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Try to create project without required fields
    const createProjectButton = screen.getByRole('button', { name: /创建项目|Create Project/i });
    await user.click(createProjectButton);

    const submitButton = screen.getByRole('button', { name: /确定|创建|Create/i });
    await user.click(submitButton);

    // Verify validation errors
    await waitFor(() => {
      expect(screen.getByText(/项目名称不能为空|Project name is required/i)).toBeInTheDocument();
    });
  });
});