import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import KnowledgeGraphPage from '../../pages/KnowledgeGraphPage';
import knowledgeGraphService from '../../services/knowledgeGraphService';

// Mock the knowledge graph service
vi.mock('../../services/knowledgeGraphService', () => ({
  default: {
    getKnowledgeGraph: vi.fn(),
    getKGStats: vi.fn()
  }
}));

// Mock Cytoscape and its extensions
vi.mock('cytoscape', () => ({
  default: vi.fn(() => ({
    on: vi.fn(),
    layout: vi.fn(() => ({ run: vi.fn() })),
    fit: vi.fn(),
    zoom: vi.fn(() => 1),
    pan: vi.fn(() => ({ x: 0, y: 0 })),
    elements: vi.fn(() => ({ removeClass: vi.fn() })),
    getElementById: vi.fn(() => ({ 
      addClass: vi.fn(), 
      connectedEdges: vi.fn(() => ({ addClass: vi.fn() })) 
    })),
    nodes: vi.fn(() => ({ filter: vi.fn(() => []) })),
    png: vi.fn(() => new Blob()),
    destroy: vi.fn()
  })),
  use: vi.fn()
}));

vi.mock('cytoscape-dagre', () => ({}));
vi.mock('cytoscape-cose-bilkent', () => ({}));
vi.mock('cytoscape-cola', () => ({}));

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ projectId: 'test-project-123' })
  };
});

const mockKGData = {
  entities: [
    {
      id: 'entity-1',
      label: 'Test Entity 1',
      type: 'Person',
      properties: { 
        connections: 5, 
        importance: 0.8,
        confidence: 0.9
      }
    },
    {
      id: 'entity-2',
      label: 'Test Entity 2',
      type: 'Organization',
      properties: { 
        connections: 3, 
        importance: 0.6,
        confidence: 0.7
      }
    },
    {
      id: 'entity-3',
      label: 'Test Concept',
      type: 'Concept',
      properties: { 
        connections: 8, 
        importance: 0.9,
        confidence: 0.8
      }
    }
  ],
  relations: [
    {
      id: 'relation-1',
      source: 'entity-1',
      target: 'entity-2',
      type: 'works_for',
      properties: { weight: 0.9, confidence: 0.8 }
    },
    {
      id: 'relation-2',
      source: 'entity-1',
      target: 'entity-3',
      type: 'knows_about',
      properties: { weight: 0.7, confidence: 0.6 }
    }
  ]
};

const mockStats = {
  totalEntities: 3,
  totalRelations: 2,
  entityTypes: [
    { type: 'Person', count: 1 },
    { type: 'Organization', count: 1 },
    { type: 'Concept', count: 1 }
  ],
  relationTypes: [
    { type: 'works_for', count: 1 },
    { type: 'knows_about', count: 1 }
  ]
};

describe('Knowledge Graph Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (knowledgeGraphService.getKnowledgeGraph as any).mockResolvedValue(mockKGData);
    (knowledgeGraphService.getKGStats as any).mockResolvedValue(mockStats);
  });

  it('renders knowledge graph page with project ID', async () => {
    render(
      <BrowserRouter>
        <KnowledgeGraphPage />
      </BrowserRouter>
    );

    expect(screen.getByText('知识图谱可视化')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(knowledgeGraphService.getKnowledgeGraph).toHaveBeenCalledWith(
        'test-project-123',
        expect.any(Object)
      );
    });
  });

  it('displays control panels and stats', async () => {
    render(
      <BrowserRouter>
        <KnowledgeGraphPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('搜索与过滤')).toBeInTheDocument();
      expect(screen.getByText('图谱控制')).toBeInTheDocument();
      expect(screen.getByText('图谱统计')).toBeInTheDocument();
    });
  });

  it('shows entity type filters', async () => {
    render(
      <BrowserRouter>
        <KnowledgeGraphPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('实体类型')).toBeInTheDocument();
      expect(screen.getByText('关系类型')).toBeInTheDocument();
    });
  });

  it('displays layout options', async () => {
    render(
      <BrowserRouter>
        <KnowledgeGraphPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('布局算法')).toBeInTheDocument();
    });
  });

  it('shows export functionality', async () => {
    render(
      <BrowserRouter>
        <KnowledgeGraphPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('导出 PNG')).toBeInTheDocument();
      expect(screen.getByText('导出 JPG')).toBeInTheDocument();
    });
  });

  it('displays search functionality', async () => {
    render(
      <BrowserRouter>
        <KnowledgeGraphPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText('输入实体名称或类型...')).toBeInTheDocument();
    });
  });

  it('shows statistics when loaded', async () => {
    render(
      <BrowserRouter>
        <KnowledgeGraphPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('节点数量')).toBeInTheDocument();
      expect(screen.getByText('边数量')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    (knowledgeGraphService.getKnowledgeGraph as any).mockRejectedValue(
      new Error('API Error')
    );

    render(
      <BrowserRouter>
        <KnowledgeGraphPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(knowledgeGraphService.getKnowledgeGraph).toHaveBeenCalled();
    });
  });

  it('loads stats independently', async () => {
    render(
      <BrowserRouter>
        <KnowledgeGraphPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(knowledgeGraphService.getKGStats).toHaveBeenCalledWith('test-project-123');
    });
  });

  it('provides filter options based on data', async () => {
    render(
      <BrowserRouter>
        <KnowledgeGraphPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      // Should show quick filter buttons
      expect(screen.getByText('人物')).toBeInTheDocument();
      expect(screen.getByText('组织')).toBeInTheDocument();
      expect(screen.getByText('概念')).toBeInTheDocument();
    });
  });
});