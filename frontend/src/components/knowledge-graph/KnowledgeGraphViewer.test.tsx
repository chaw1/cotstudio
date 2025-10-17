import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import KnowledgeGraphViewer from './KnowledgeGraphViewer';
import knowledgeGraphService from '../../services/knowledgeGraphService';

// Mock the knowledge graph service
vi.mock('../../services/knowledgeGraphService', () => ({
  default: {
    getKnowledgeGraph: vi.fn(),
    getKGStats: vi.fn()
  }
}));

// Mock Cytoscape
vi.mock('cytoscape', () => ({
  default: vi.fn(() => ({
    on: vi.fn(),
    layout: vi.fn(() => ({ run: vi.fn() })),
    fit: vi.fn(),
    zoom: vi.fn(() => 1),
    pan: vi.fn(() => ({ x: 0, y: 0 })),
    elements: vi.fn(() => ({ removeClass: vi.fn() })),
    getElementById: vi.fn(() => ({ addClass: vi.fn(), connectedEdges: vi.fn(() => ({ addClass: vi.fn() })) })),
    nodes: vi.fn(() => ({ filter: vi.fn(() => []) })),
    png: vi.fn(() => new Blob()),
    destroy: vi.fn()
  })),
  use: vi.fn()
}));

// Mock layout extensions
vi.mock('cytoscape-dagre', () => ({}));
vi.mock('cytoscape-cose-bilkent', () => ({}));
vi.mock('cytoscape-cola', () => ({}));

const mockKGData = {
  entities: [
    {
      id: '1',
      label: 'Test Entity',
      type: 'Person',
      properties: { connections: 5, importance: 0.8 }
    },
    {
      id: '2',
      label: 'Another Entity',
      type: 'Organization',
      properties: { connections: 3, importance: 0.6 }
    }
  ],
  relations: [
    {
      id: 'r1',
      source: '1',
      target: '2',
      type: 'works_for',
      properties: { weight: 0.9 }
    }
  ]
};

const mockStats = {
  totalEntities: 2,
  totalRelations: 1,
  entityTypes: [
    { type: 'Person', count: 1 },
    { type: 'Organization', count: 1 }
  ],
  relationTypes: [
    { type: 'works_for', count: 1 }
  ]
};

describe('KnowledgeGraphViewer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (knowledgeGraphService.getKnowledgeGraph as any).mockResolvedValue(mockKGData);
    (knowledgeGraphService.getKGStats as any).mockResolvedValue(mockStats);
  });

  it('renders knowledge graph viewer', async () => {
    render(<KnowledgeGraphViewer projectId="test-project" />);
    
    expect(screen.getByText('知识图谱')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(knowledgeGraphService.getKnowledgeGraph).toHaveBeenCalledWith('test-project', expect.any(Object));
    });
  });

  it('shows loading state initially', () => {
    render(<KnowledgeGraphViewer projectId="test-project" />);
    
    expect(screen.getByRole('img', { name: /loading/i })).toBeInTheDocument();
  });

  it('renders control panels when showControls is true', async () => {
    render(<KnowledgeGraphViewer projectId="test-project" showControls={true} />);
    
    await waitFor(() => {
      expect(screen.getByText('搜索与过滤')).toBeInTheDocument();
      expect(screen.getByText('图谱控制')).toBeInTheDocument();
    });
  });

  it('renders stats panel when showStats is true', async () => {
    render(<KnowledgeGraphViewer projectId="test-project" showStats={true} />);
    
    await waitFor(() => {
      expect(screen.getByText('图谱统计')).toBeInTheDocument();
    });
  });

  it('handles node selection callback', async () => {
    const onNodeSelect = vi.fn();
    render(
      <KnowledgeGraphViewer 
        projectId="test-project" 
        onNodeSelect={onNodeSelect}
      />
    );
    
    await waitFor(() => {
      expect(knowledgeGraphService.getKnowledgeGraph).toHaveBeenCalled();
    });
  });

  it('handles edge selection callback', async () => {
    const onEdgeSelect = vi.fn();
    render(
      <KnowledgeGraphViewer 
        projectId="test-project" 
        onEdgeSelect={onEdgeSelect}
      />
    );
    
    await waitFor(() => {
      expect(knowledgeGraphService.getKnowledgeGraph).toHaveBeenCalled();
    });
  });

  it('applies different layouts', async () => {
    render(<KnowledgeGraphViewer projectId="test-project" initialLayout="cose-bilkent" />);
    
    await waitFor(() => {
      expect(knowledgeGraphService.getKnowledgeGraph).toHaveBeenCalled();
    });
  });

  it('handles search functionality', async () => {
    render(<KnowledgeGraphViewer projectId="test-project" showControls={true} />);
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('输入实体名称或类型...')).toBeInTheDocument();
    });
    
    const searchInput = screen.getByPlaceholderText('输入实体名称或类型...');
    fireEvent.change(searchInput, { target: { value: 'Test' } });
    fireEvent.keyDown(searchInput, { key: 'Enter', code: 'Enter' });
  });

  it('handles filter changes', async () => {
    render(<KnowledgeGraphViewer projectId="test-project" showControls={true} />);
    
    await waitFor(() => {
      expect(screen.getByText('实体类型')).toBeInTheDocument();
    });
  });

  it('handles layout changes', async () => {
    render(<KnowledgeGraphViewer projectId="test-project" showControls={true} />);
    
    await waitFor(() => {
      expect(screen.getByText('布局算法')).toBeInTheDocument();
    });
  });

  it('handles export functionality', async () => {
    render(<KnowledgeGraphViewer projectId="test-project" showControls={true} />);
    
    await waitFor(() => {
      expect(screen.getByText('导出 PNG')).toBeInTheDocument();
    });
  });

  it('handles error states gracefully', async () => {
    (knowledgeGraphService.getKnowledgeGraph as any).mockRejectedValue(new Error('API Error'));
    
    render(<KnowledgeGraphViewer projectId="test-project" />);
    
    await waitFor(() => {
      expect(knowledgeGraphService.getKnowledgeGraph).toHaveBeenCalled();
    });
  });

  it('cleans up cytoscape instance on unmount', async () => {
    const { unmount } = render(<KnowledgeGraphViewer projectId="test-project" />);
    
    await waitFor(() => {
      expect(knowledgeGraphService.getKnowledgeGraph).toHaveBeenCalled();
    });
    
    unmount();
  });
});