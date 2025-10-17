import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import KnowledgeGraphViewer from '../components/knowledge-graph/KnowledgeGraphViewer';

// Mock cytoscape
jest.mock('cytoscape', () => {
  const mockInstance = {
    destroy: jest.fn(),
    removeAllListeners: jest.fn(),
    elements: jest.fn(() => ({
      stop: jest.fn(),
      removeClass: jest.fn()
    })),
    on: jest.fn(),
    zoom: jest.fn(() => 1),
    pan: jest.fn(() => ({ x: 0, y: 0 })),
    fit: jest.fn(),
    layout: jest.fn(() => ({
      run: jest.fn()
    })),
    getElementById: jest.fn(() => ({
      length: 1,
      addClass: jest.fn(),
      connectedEdges: jest.fn(() => ({
        addClass: jest.fn()
      }))
    })),
    nodes: jest.fn(() => ({
      filter: jest.fn(() => [])
    })),
    png: jest.fn(() => new Blob())
  };

  return jest.fn(() => mockInstance);
});

// Mock services
jest.mock('../services/knowledgeGraphService', () => ({
  default: {
    getKnowledgeGraph: jest.fn(() => Promise.resolve({
      entities: [],
      relations: []
    }))
  }
}));

// Mock message utility
jest.mock('../utils/message', () => ({
  default: {
    error: jest.fn(),
    warning: jest.fn(),
    success: jest.fn()
  }
}));

describe('KnowledgeGraphViewer Cytoscape Fix', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should handle component unmounting without errors', async () => {
    const mockData = {
      nodes: [
        { id: '1', label: 'Node 1', type: 'Person' }
      ],
      edges: [
        { id: 'e1', source: '1', target: '2', type: 'knows' }
      ]
    };

    const { unmount } = render(
      <KnowledgeGraphViewer
        projectId="test"
        data={mockData}
        disableDataFetch={true}
      />
    );

    // Wait for component to initialize
    await waitFor(() => {
      expect(screen.getByText('知识图谱')).toBeInTheDocument();
    });

    // Unmount component - should not throw errors
    expect(() => {
      act(() => {
        unmount();
      });
    }).not.toThrow();
  });

  test('should handle empty data gracefully', async () => {
    const mockData = {
      nodes: [],
      edges: []
    };

    render(
      <KnowledgeGraphViewer
        projectId="test"
        data={mockData}
        disableDataFetch={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('知识图谱')).toBeInTheDocument();
    });

    // Should not crash with empty data
    expect(screen.getByText('知识图谱')).toBeInTheDocument();
  });

  test('should handle rapid re-renders without errors', async () => {
    const mockData = {
      nodes: [
        { id: '1', label: 'Node 1', type: 'Person' }
      ],
      edges: []
    };

    const { rerender } = render(
      <KnowledgeGraphViewer
        projectId="test1"
        data={mockData}
        disableDataFetch={true}
      />
    );

    // Rapidly change props
    for (let i = 0; i < 5; i++) {
      act(() => {
        rerender(
          <KnowledgeGraphViewer
            projectId={`test${i}`}
            data={mockData}
            disableDataFetch={true}
          />
        );
      });
    }

    await waitFor(() => {
      expect(screen.getByText('知识图谱')).toBeInTheDocument();
    });

    // Should handle rapid re-renders without crashing
    expect(screen.getByText('知识图谱')).toBeInTheDocument();
  });

  test('should handle layout changes safely', async () => {
    const mockData = {
      nodes: [
        { id: '1', label: 'Node 1', type: 'Person' },
        { id: '2', label: 'Node 2', type: 'Person' }
      ],
      edges: [
        { id: 'e1', source: '1', target: '2', type: 'knows' }
      ]
    };

    render(
      <KnowledgeGraphViewer
        projectId="test"
        data={mockData}
        disableDataFetch={true}
        initialLayout="cose"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('知识图谱')).toBeInTheDocument();
    });

    // Component should render without errors
    expect(screen.getByText('知识图谱')).toBeInTheDocument();
  });
});