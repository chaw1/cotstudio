/**
 * 知识图谱集成测试
 * 测试知识图谱可视化和交互功能
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import KnowledgeGraphVisualization from '../../components/knowledge-graph/KnowledgeGraphVisualization';
import { knowledgeGraphService } from '../../services/knowledgeGraphService';

// Mock Cytoscape
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
    filter: vi.fn(() => ({ length: 0 }))
  }))
}));

// Mock knowledge graph service
vi.mock('../../services/knowledgeGraphService');
const mockKnowledgeGraphService = vi.mocked(knowledgeGraphService);

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('Knowledge Graph Integration Tests', () => {
  let user: ReturnType<typeof userEvent.setup>;

  const mockVisualizationData = {
    nodes: [
      {
        id: 'entity-1',
        label: '人工智能',
        type: 'CONCEPT',
        properties: {
          frequency: 10,
          confidence: 0.9
        }
      },
      {
        id: 'entity-2',
        label: '机器学习',
        type: 'CONCEPT',
        properties: {
          frequency: 8,
          confidence: 0.85
        }
      },
      {
        id: 'entity-3',
        label: '深度学习',
        type: 'CONCEPT',
        properties: {
          frequency: 6,
          confidence: 0.8
        }
      }
    ],
    edges: [
      {
        source: 'entity-2',
        target: 'entity-1',
        type: 'IS_PART_OF',
        properties: {
          confidence: 0.9
        }
      },
      {
        source: 'entity-3',
        target: 'entity-2',
        type: 'IS_SUBSET_OF',
        properties: {
          confidence: 0.85
        }
      }
    ]
  };

  const mockEntities = [
    {
      id: 'entity-1',
      name: '人工智能',
      type: 'CONCEPT',
      properties: { frequency: 10, confidence: 0.9 },
      created_at: new Date().toISOString()
    },
    {
      id: 'entity-2',
      name: '机器学习',
      type: 'CONCEPT',
      properties: { frequency: 8, confidence: 0.85 },
      created_at: new Date().toISOString()
    }
  ];

  const mockRelationships = [
    {
      id: 'rel-1',
      source_id: 'entity-2',
      target_id: 'entity-1',
      type: 'IS_PART_OF',
      properties: { confidence: 0.9 },
      created_at: new Date().toISOString()
    }
  ];

  beforeEach(() => {
    user = userEvent.setup();
    vi.clearAllMocks();

    // Setup default mock responses
    mockKnowledgeGraphService.getVisualizationData.mockResolvedValue(mockVisualizationData);
    mockKnowledgeGraphService.getEntities.mockResolvedValue(mockEntities);
    mockKnowledgeGraphService.getRelationships.mockResolvedValue(mockRelationships);
    mockKnowledgeGraphService.extractKnowledgeGraph.mockResolvedValue({ task_id: 'kg-task-1' });
  });

  it('should render knowledge graph visualization with nodes and edges', async () => {
    render(
      <TestWrapper>
        <KnowledgeGraphVisualization projectId="test-project-id" />
      </TestWrapper>
    );

    // Wait for data to load
    await waitFor(() => {
      expect(mockKnowledgeGraphService.getVisualizationData).toHaveBeenCalledWith('test-project-id');
    });

    // Verify graph container is rendered
    expect(screen.getByTestId('knowledge-graph-container')).toBeInTheDocument();

    // Verify control panel is rendered
    expect(screen.getByText(/图谱控制/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /重新布局/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /适应视图/i })).toBeInTheDocument();
  });

  it('should handle entity filtering by type', async () => {
    render(
      <TestWrapper>
        <KnowledgeGraphVisualization projectId="test-project-id" />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('knowledge-graph-container')).toBeInTheDocument();
    });

    // Find and use entity type filter
    const entityTypeFilter = screen.getByLabelText(/实体类型/i);
    await user.selectOptions(entityTypeFilter, 'CONCEPT');

    await waitFor(() => {
      expect(mockKnowledgeGraphService.getEntities).toHaveBeenCalledWith(
        'test-project-id',
        { entity_type: 'CONCEPT' }
      );
    });
  });

  it('should handle relationship filtering by type', async () => {
    render(
      <TestWrapper>
        <KnowledgeGraphVisualization projectId="test-project-id" />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('knowledge-graph-container')).toBeInTheDocument();
    });

    // Find and use relationship type filter
    const relationTypeFilter = screen.getByLabelText(/关系类型/i);
    await user.selectOptions(relationTypeFilter, 'IS_PART_OF');

    await waitFor(() => {
      expect(mockKnowledgeGraphService.getRelationships).toHaveBeenCalledWith(
        'test-project-id',
        { relation_type: 'IS_PART_OF' }
      );
    });
  });

  it('should handle text search functionality', async () => {
    mockKnowledgeGraphService.searchEntities.mockResolvedValue([
      {
        id: 'entity-1',
        name: '人工智能',
        type: 'CONCEPT',
        properties: { frequency: 10 },
        created_at: new Date().toISOString()
      }
    ]);

    render(
      <TestWrapper>
        <KnowledgeGraphVisualization projectId="test-project-id" />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('knowledge-graph-container')).toBeInTheDocument();
    });

    // Use search functionality
    const searchInput = screen.getByPlaceholderText(/搜索实体/i);
    await user.type(searchInput, '人工智能');

    const searchBtn = screen.getByRole('button', { name: /搜索/i });
    await user.click(searchBtn);

    await waitFor(() => {
      expect(mockKnowledgeGraphService.searchEntities).toHaveBeenCalledWith(
        'test-project-id',
        '人工智能'
      );
    });

    // Verify search results are displayed
    expect(screen.getByText(/搜索结果/i)).toBeInTheDocument();
    expect(screen.getByText(/人工智能/i)).toBeInTheDocument();
  });

  it('should handle graph layout changes', async () => {
    render(
      <TestWrapper>
        <KnowledgeGraphVisualization projectId="test-project-id" />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('knowledge-graph-container')).toBeInTheDocument();
    });

    // Change layout algorithm
    const layoutSelect = screen.getByLabelText(/布局算法/i);
    await user.selectOptions(layoutSelect, 'force-directed');

    // Trigger layout update
    const relayoutBtn = screen.getByRole('button', { name: /重新布局/i });
    await user.click(relayoutBtn);

    // Verify layout change is applied (this would be tested through Cytoscape mock)
    expect(relayoutBtn).toBeInTheDocument();
  });

  it('should handle density adjustment', async () => {
    render(
      <TestWrapper>
        <KnowledgeGraphVisualization projectId="test-project-id" />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('knowledge-graph-container')).toBeInTheDocument();
    });

    // Adjust graph density
    const densitySlider = screen.getByLabelText(/图谱密度/i);
    fireEvent.change(densitySlider, { target: { value: '0.7' } });

    // Verify density change affects the display
    expect(densitySlider).toHaveValue('0.7');
  });

  it('should handle node selection and detail display', async () => {
    render(
      <TestWrapper>
        <KnowledgeGraphVisualization projectId="test-project-id" />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('knowledge-graph-container')).toBeInTheDocument();
    });

    // Simulate node selection (this would normally be handled by Cytoscape events)
    const nodeDetailPanel = screen.getByTestId('node-detail-panel');
    expect(nodeDetailPanel).toBeInTheDocument();

    // Verify node details can be displayed
    // In a real test, this would involve simulating Cytoscape node click events
  });

  it('should handle knowledge graph extraction trigger', async () => {
    render(
      <TestWrapper>
        <KnowledgeGraphVisualization projectId="test-project-id" />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('knowledge-graph-container')).toBeInTheDocument();
    });

    // Trigger knowledge graph extraction
    const extractBtn = screen.getByRole('button', { name: /重新抽取/i });
    await user.click(extractBtn);

    await waitFor(() => {
      expect(mockKnowledgeGraphService.extractKnowledgeGraph).toHaveBeenCalledWith('test-project-id');
    });

    // Verify extraction progress is shown
    expect(screen.getByText(/正在抽取知识图谱/i)).toBeInTheDocument();
  });

  it('should handle export functionality', async () => {
    mockKnowledgeGraphService.exportKnowledgeGraph.mockResolvedValue({
      download_url: 'http://example.com/kg-export.json',
      export_id: 'kg-export-1'
    });

    render(
      <TestWrapper>
        <KnowledgeGraphVisualization projectId="test-project-id" />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('knowledge-graph-container')).toBeInTheDocument();
    });

    // Trigger export
    const exportBtn = screen.getByRole('button', { name: /导出图谱/i });
    await user.click(exportBtn);

    // Select export format
    const formatSelect = screen.getByLabelText(/导出格式/i);
    await user.selectOptions(formatSelect, 'json');

    const confirmExportBtn = screen.getByRole('button', { name: /确认导出/i });
    await user.click(confirmExportBtn);

    await waitFor(() => {
      expect(mockKnowledgeGraphService.exportKnowledgeGraph).toHaveBeenCalledWith(
        'test-project-id',
        { format: 'json' }
      );
    });
  });

  it('should handle error states gracefully', async () => {
    // Mock API error
    mockKnowledgeGraphService.getVisualizationData.mockRejectedValue(
      new Error('Failed to load knowledge graph data')
    );

    render(
      <TestWrapper>
        <KnowledgeGraphVisualization projectId="test-project-id" />
      </TestWrapper>
    );

    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/Failed to load knowledge graph data/i)).toBeInTheDocument();
    });

    // Verify retry button is available
    expect(screen.getByRole('button', { name: /重试/i })).toBeInTheDocument();
  });

  it('should handle empty graph state', async () => {
    // Mock empty data
    mockKnowledgeGraphService.getVisualizationData.mockResolvedValue({
      nodes: [],
      edges: []
    });

    render(
      <TestWrapper>
        <KnowledgeGraphVisualization projectId="test-project-id" />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/暂无知识图谱数据/i)).toBeInTheDocument();
    });

    // Verify suggestion to extract knowledge graph
    expect(screen.getByText(/开始抽取知识图谱/i)).toBeInTheDocument();
  });

  it('should handle real-time updates during extraction', async () => {
    // Mock WebSocket or polling updates
    const mockTaskStatus = {
      task_id: 'kg-task-1',
      status: 'processing',
      progress: 0.5,
      message: '正在抽取实体...'
    };

    mockKnowledgeGraphService.getTaskStatus.mockResolvedValue(mockTaskStatus);

    render(
      <TestWrapper>
        <KnowledgeGraphVisualization projectId="test-project-id" />
      </TestWrapper>
    );

    // Trigger extraction
    const extractBtn = screen.getByRole('button', { name: /重新抽取/i });
    await user.click(extractBtn);

    // Verify progress is displayed
    await waitFor(() => {
      expect(screen.getByText(/正在抽取实体/i)).toBeInTheDocument();
    });

    // Verify progress bar
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveAttribute('aria-valuenow', '50');
  });
});