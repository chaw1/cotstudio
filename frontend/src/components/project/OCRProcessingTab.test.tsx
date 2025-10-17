import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { ConfigProvider } from 'antd';
import OCRProcessingTab from './OCRProcessingTab';
import { FileInfo } from '../../types';

// Mock the ModalContainer component
vi.mock('../common/ModalContainer', () => ({
  default: ({ visible, onClose, title, children }: any) => (
    visible ? (
      <div data-testid="modal-container" role="dialog" aria-label={title}>
        <div data-testid="modal-header">{title}</div>
        <button data-testid="modal-close" onClick={onClose}>Close</button>
        <div data-testid="modal-content">{children}</div>
      </div>
    ) : null
  )
}));

// Mock the OCRProcessing component
vi.mock('../ocr', () => ({
  OCRProcessing: ({ file, onBack }: any) => (
    <div data-testid="ocr-processing">
      <div>Processing file: {file?.filename}</div>
      <button data-testid="ocr-back" onClick={onBack}>Back</button>
    </div>
  )
}));

const mockFiles: FileInfo[] = [
  {
    id: '1',
    filename: 'test-document.pdf',
    size: 1024000,
    mimeType: 'application/pdf',
    ocrStatus: 'pending',
    createdAt: '2024-01-01T00:00:00Z',
    projectId: 'project-1'
  },
  {
    id: '2',
    filename: 'completed-document.pdf',
    size: 2048000,
    mimeType: 'application/pdf',
    ocrStatus: 'completed',
    createdAt: '2024-01-02T00:00:00Z',
    projectId: 'project-1'
  }
];

describe('OCRProcessingTab Modal Positioning', () => {
  const defaultProps = {
    projectId: 'project-1',
    files: mockFiles,
    onRefresh: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render OCR processing tab with file list', () => {
    render(
      <ConfigProvider>
        <OCRProcessingTab {...defaultProps} />
      </ConfigProvider>
    );

    expect(screen.getByText('OCR处理总览')).toBeInTheDocument();
    expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
    expect(screen.getByText('completed-document.pdf')).toBeInTheDocument();
  });

  it('should open OCR modal when starting OCR for a file', async () => {
    render(
      <ConfigProvider>
        <OCRProcessingTab {...defaultProps} />
      </ConfigProvider>
    );

    // Find and click the "开始OCR" button for the first file
    const startOCRButton = screen.getByRole('button', { name: /开始OCR/i });
    fireEvent.click(startOCRButton);

    // Wait for modal to appear
    await waitFor(() => {
      expect(screen.getByTestId('modal-container')).toBeInTheDocument();
    });

    // Verify modal content
    expect(screen.getByTestId('modal-header')).toHaveTextContent('OCR处理 - test-document.pdf');
    expect(screen.getByTestId('ocr-processing')).toBeInTheDocument();
    expect(screen.getByText('Processing file: test-document.pdf')).toBeInTheDocument();
  });

  it('should open OCR modal when viewing slices for completed file', async () => {
    render(
      <ConfigProvider>
        <OCRProcessingTab {...defaultProps} />
      </ConfigProvider>
    );

    // Find and click the "查看切片" button for the completed file
    const viewSlicesButton = screen.getByRole('button', { name: /查看切片/i });
    fireEvent.click(viewSlicesButton);

    // Wait for modal to appear
    await waitFor(() => {
      expect(screen.getByTestId('modal-container')).toBeInTheDocument();
    });

    // Verify modal content
    expect(screen.getByTestId('modal-header')).toHaveTextContent('OCR处理 - completed-document.pdf');
    expect(screen.getByTestId('ocr-processing')).toBeInTheDocument();
    expect(screen.getByText('Processing file: completed-document.pdf')).toBeInTheDocument();
  });

  it('should close OCR modal when close button is clicked', async () => {
    render(
      <ConfigProvider>
        <OCRProcessingTab {...defaultProps} />
      </ConfigProvider>
    );

    // Open modal
    const startOCRButton = screen.getByRole('button', { name: /开始OCR/i });
    fireEvent.click(startOCRButton);

    await waitFor(() => {
      expect(screen.getByTestId('modal-container')).toBeInTheDocument();
    });

    // Close modal
    const closeButton = screen.getByTestId('modal-close');
    fireEvent.click(closeButton);

    // Wait for modal to disappear
    await waitFor(() => {
      expect(screen.queryByTestId('modal-container')).not.toBeInTheDocument();
    });
  });

  it('should close OCR modal when back button in OCR processing is clicked', async () => {
    render(
      <ConfigProvider>
        <OCRProcessingTab {...defaultProps} />
      </ConfigProvider>
    );

    // Open modal
    const startOCRButton = screen.getByRole('button', { name: /开始OCR/i });
    fireEvent.click(startOCRButton);

    await waitFor(() => {
      expect(screen.getByTestId('modal-container')).toBeInTheDocument();
    });

    // Click back button in OCR processing component
    const backButton = screen.getByTestId('ocr-back');
    fireEvent.click(backButton);

    // Wait for modal to disappear
    await waitFor(() => {
      expect(screen.queryByTestId('modal-container')).not.toBeInTheDocument();
    });

    // Verify onRefresh was called
    expect(defaultProps.onRefresh).toHaveBeenCalled();
  });

  it('should handle empty file list gracefully', () => {
    render(
      <ConfigProvider>
        <OCRProcessingTab {...defaultProps} files={[]} />
      </ConfigProvider>
    );

    expect(screen.getByText('暂无文件')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /开始OCR/i })).not.toBeInTheDocument();
  });

  it('should display correct file statistics', () => {
    const mixedFiles: FileInfo[] = [
      ...mockFiles,
      {
        id: '3',
        filename: 'processing-document.pdf',
        size: 1500000,
        mimeType: 'application/pdf',
        ocrStatus: 'processing',
        createdAt: '2024-01-03T00:00:00Z',
        projectId: 'project-1'
      },
      {
        id: '4',
        filename: 'failed-document.pdf',
        size: 500000,
        mimeType: 'application/pdf',
        ocrStatus: 'failed',
        createdAt: '2024-01-04T00:00:00Z',
        projectId: 'project-1'
      }
    ];

    render(
      <ConfigProvider>
        <OCRProcessingTab {...defaultProps} files={mixedFiles} />
      </ConfigProvider>
    );

    // Check statistics
    expect(screen.getByText('1/4 个文件已完成')).toBeInTheDocument();
    expect(screen.getByText('已完成: 1')).toBeInTheDocument();
    expect(screen.getByText('处理中: 1')).toBeInTheDocument();
    expect(screen.getByText('失败: 1')).toBeInTheDocument();
    expect(screen.getByText('待处理: 1')).toBeInTheDocument();
  });
});