import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import OCREngineSelector from './OCREngineSelector';
import SliceList from './SliceList';
import SliceViewer from './SliceViewer';

// Mock the file service
vi.mock('../../services/fileService', () => ({
  fileService: {
    triggerOCR: vi.fn(),
    getFileSlices: vi.fn(),
  },
}));

describe('OCR Components', () => {
  describe('OCREngineSelector', () => {
    it('renders OCR engine selector', () => {
      const mockOnStartOCR = vi.fn();
      render(
        <OCREngineSelector
          fileId="test-file-id"
          onStartOCR={mockOnStartOCR}
        />
      );
      
      expect(screen.getByText('OCR引擎配置')).toBeInTheDocument();
      expect(screen.getByText('开始OCR处理')).toBeInTheDocument();
    });
  });

  describe('SliceList', () => {
    it('renders empty slice list', () => {
      const mockOnSliceSelect = vi.fn();
      render(
        <SliceList
          fileId="test-file-id"
          slices={[]}
          onSliceSelect={mockOnSliceSelect}
        />
      );
      
      expect(screen.getByText('文档切片')).toBeInTheDocument();
      expect(screen.getByText('暂无切片数据')).toBeInTheDocument();
    });

    it('renders slice list with data', () => {
      const mockSlices = [
        {
          id: 'slice-1',
          fileId: 'file-1',
          content: 'Test slice content',
          startOffset: 0,
          endOffset: 100,
          sliceType: 'paragraph' as const,
          pageNumber: 1,
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z',
        },
      ];
      
      const mockOnSliceSelect = vi.fn();
      render(
        <SliceList
          fileId="test-file-id"
          slices={mockSlices}
          onSliceSelect={mockOnSliceSelect}
        />
      );
      
      expect(screen.getByText('文档切片')).toBeInTheDocument();
      expect(screen.getByText('Test slice content')).toBeInTheDocument();
    });
  });

  describe('SliceViewer', () => {
    it('renders empty state when no slice selected', () => {
      render(<SliceViewer slice={null} />);
      
      expect(screen.getByText('切片详情')).toBeInTheDocument();
      expect(screen.getByText('请选择一个切片查看详情')).toBeInTheDocument();
    });

    it('renders slice details when slice is selected', () => {
      const mockSlice = {
        id: 'slice-1',
        fileId: 'file-1',
        content: 'Test slice content for viewing',
        startOffset: 0,
        endOffset: 100,
        sliceType: 'paragraph' as const,
        pageNumber: 1,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      };
      
      render(<SliceViewer slice={mockSlice} />);
      
      expect(screen.getByText('切片详情')).toBeInTheDocument();
      expect(screen.getByText('Test slice content for viewing')).toBeInTheDocument();
      expect(screen.getByText('段落')).toBeInTheDocument();
    });
  });
});