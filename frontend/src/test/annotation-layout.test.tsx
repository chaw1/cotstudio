import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { vi, describe, it, expect } from 'vitest';
import AnnotationWorkspace from '../components/annotation/AnnotationWorkspace';

// Mock the annotation hook
vi.mock('../hooks/useAnnotation', () => ({
  default: () => ({
    currentCOTItem: null,
    selectedSliceId: null,
    loading: false,
    generateQuestionLoading: false,
    generateCandidatesLoading: false,
    createCOTItem: vi.fn(),
    updateCOTItem: vi.fn(),
    generateQuestion: vi.fn(),
    generateCandidates: vi.fn(),
    selectSlice: vi.fn(),
    selectCOTItem: vi.fn(),
  })
}));

// Mock API calls
vi.mock('../services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [] })
  }
}));

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <ConfigProvider>
      {children}
    </ConfigProvider>
  </BrowserRouter>
);

describe('Annotation Layout Tests', () => {
  it('should render annotation workspace with proper layout', () => {
    render(
      <TestWrapper>
        <AnnotationWorkspace projectId="test-project" />
      </TestWrapper>
    );

    // Check if main components are rendered
    expect(screen.getByText('CoT标注工作台')).toBeInTheDocument();
    expect(screen.getByText('文本选择')).toBeInTheDocument();
    expect(screen.getByText('标注编辑')).toBeInTheDocument();
    
    // Check if action buttons are present
    expect(screen.getByText('新建标注')).toBeInTheDocument();
    expect(screen.getByText('保存')).toBeInTheDocument();
    expect(screen.getByText('重置')).toBeInTheDocument();
  });

  it('should have proper grid layout structure', () => {
    const { container } = render(
      <TestWrapper>
        <AnnotationWorkspace projectId="test-project" />
      </TestWrapper>
    );

    // Check if Row and Col components are used (they should have ant-row and ant-col classes)
    const rowElement = container.querySelector('.ant-row');
    expect(rowElement).toBeInTheDocument();
    
    const colElements = container.querySelectorAll('.ant-col');
    expect(colElements.length).toBeGreaterThanOrEqual(2); // Should have at least 2 columns
  });

  it('should render text selector and annotation editor in separate cards', () => {
    render(
      <TestWrapper>
        <AnnotationWorkspace projectId="test-project" />
      </TestWrapper>
    );

    // Both sections should be in separate cards
    const textSelectorCard = screen.getByText('文本选择').closest('.ant-card');
    const annotationCard = screen.getByText('标注编辑').closest('.ant-card');
    
    expect(textSelectorCard).toBeInTheDocument();
    expect(annotationCard).toBeInTheDocument();
    expect(textSelectorCard).not.toBe(annotationCard);
  });
});