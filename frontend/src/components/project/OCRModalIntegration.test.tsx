import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { ConfigProvider } from 'antd';
import OCRProcessingTab from './OCRProcessingTab';
import { FileInfo } from '../../types';

// Mock the actual ModalContainer component behavior
vi.mock('../common/ModalContainer', () => ({
  default: ({ visible, onClose, title, width, centered, children, zIndex }: any) => {
    if (!visible) return null;
    
    // Simulate the positioning logic that ModalContainer would apply
    const mockSidebarWidth = 240; // Assume expanded sidebar
    const mockScreenWidth = 1200;
    const contentAreaWidth = mockScreenWidth - mockSidebarWidth;
    const modalWidth = typeof width === 'number' ? width : 520;
    const leftOffset = mockSidebarWidth + (contentAreaWidth - modalWidth) / 2;
    
    return (
      <div 
        data-testid="modal-container"
        style={{
          position: 'fixed',
          left: `${leftOffset}px`,
          top: '50%',
          transform: 'translateY(-50%)',
          width: `${modalWidth}px`,
          zIndex: zIndex || 1050,
          background: 'white',
          border: '1px solid #ccc',
          borderRadius: '8px',
          padding: '16px'
        }}
        role="dialog"
        aria-label={title}
      >
        <div data-testid="modal-header" style={{ marginBottom: '16px', fontWeight: 'bold' }}>
          {title}
        </div>
        <button 
          data-testid="modal-close" 
          onClick={onClose}
          style={{ position: 'absolute', top: '8px', right: '8px' }}
        >
          ×
        </button>
        <div data-testid="modal-content">
          {children}
        </div>
        {/* Simulate backdrop */}
        <div 
          data-testid="modal-backdrop"
          style={{
            position: 'fixed',
            top: 0,
            left: `${mockSidebarWidth}px`,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.45)',
            zIndex: zIndex ? zIndex - 1 : 1049
          }}
          onClick={onClose}
        />
      </div>
    );
  }
}));

// Mock the OCRProcessing component
vi.mock('../ocr', () => ({
  OCRProcessing: ({ file, onBack }: any) => (
    <div data-testid="ocr-processing" style={{ minHeight: '400px', padding: '16px' }}>
      <h3>OCR Processing Interface</h3>
      <p>Processing file: {file?.filename}</p>
      <p>File size: {file?.size} bytes</p>
      <p>MIME type: {file?.mimeType}</p>
      <div style={{ marginTop: '20px' }}>
        <button data-testid="ocr-back" onClick={onBack} style={{ marginRight: '8px' }}>
          Back to File List
        </button>
        <button data-testid="ocr-start" style={{ marginRight: '8px' }}>
          Start Processing
        </button>
        <button data-testid="ocr-config">
          Configure Engine
        </button>
      </div>
      <div style={{ marginTop: '20px', padding: '16px', background: '#f5f5f5', borderRadius: '4px' }}>
        <h4>Processing Status</h4>
        <div>Status: Ready to process</div>
        <div>Engine: Default OCR Engine</div>
        <div>Expected processing time: 2-5 minutes</div>
      </div>
    </div>
  )
}));

const mockFile: FileInfo = {
  id: '1',
  filename: 'sample-document.pdf',
  size: 2048576, // 2MB
  mimeType: 'application/pdf',
  ocrStatus: 'pending',
  createdAt: '2024-01-15T10:30:00Z',
  projectId: 'project-1'
};

describe('OCR Modal Integration Tests', () => {
  const defaultProps = {
    projectId: 'project-1',
    files: [mockFile],
    onRefresh: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock window dimensions
    Object.defineProperty(window, 'innerWidth', { value: 1200, writable: true });
    Object.defineProperty(window, 'innerHeight', { value: 800, writable: true });
  });

  it('should render modal with correct positioning and styling', async () => {
    render(
      <ConfigProvider>
        <OCRProcessingTab {...defaultProps} />
      </ConfigProvider>
    );

    // Open the OCR modal
    const startOCRButton = screen.getByRole('button', { name: /开始OCR/i });
    fireEvent.click(startOCRButton);

    await waitFor(() => {
      expect(screen.getByTestId('modal-container')).toBeInTheDocument();
    });

    // Verify modal positioning
    const modal = screen.getByTestId('modal-container');
    const modalStyles = window.getComputedStyle(modal);
    
    expect(modalStyles.position).toBe('fixed');
    expect(modalStyles.width).toBe('900px');
    expect(modalStyles.zIndex).toBe('1300');
    
    // Verify modal is positioned to avoid sidebar (left should be > 240px)
    const leftValue = parseInt(modalStyles.left);
    expect(leftValue).toBeGreaterThan(240);
  });

  it('should render backdrop that covers only content area', async () => {
    render(
      <ConfigProvider>
        <OCRProcessingTab {...defaultProps} />
      </ConfigProvider>
    );

    // Open the OCR modal
    const startOCRButton = screen.getByRole('button', { name: /开始OCR/i });
    fireEvent.click(startOCRButton);

    await waitFor(() => {
      expect(screen.getByTestId('modal-backdrop')).toBeInTheDocument();
    });

    // Verify backdrop positioning
    const backdrop = screen.getByTestId('modal-backdrop');
    const backdropStyles = window.getComputedStyle(backdrop);
    
    expect(backdropStyles.position).toBe('fixed');
    expect(backdropStyles.left).toBe('240px'); // Should start after sidebar
    expect(backdropStyles.top).toBe('0px');
    expect(backdropStyles.right).toBe('0px');
    expect(backdropStyles.bottom).toBe('0px');
  });

  it('should display OCR processing interface correctly', async () => {
    render(
      <ConfigProvider>
        <OCRProcessingTab {...defaultProps} />
      </ConfigProvider>
    );

    // Open the OCR modal
    const startOCRButton = screen.getByRole('button', { name: /开始OCR/i });
    fireEvent.click(startOCRButton);

    await waitFor(() => {
      expect(screen.getByTestId('ocr-processing')).toBeInTheDocument();
    });

    // Verify OCR processing interface content
    expect(screen.getByText('OCR Processing Interface')).toBeInTheDocument();
    expect(screen.getByText('Processing file: sample-document.pdf')).toBeInTheDocument();
    expect(screen.getByText('File size: 2048576 bytes')).toBeInTheDocument();
    expect(screen.getByText('MIME type: application/pdf')).toBeInTheDocument();
    
    // Verify action buttons are present
    expect(screen.getByTestId('ocr-back')).toBeInTheDocument();
    expect(screen.getByTestId('ocr-start')).toBeInTheDocument();
    expect(screen.getByTestId('ocr-config')).toBeInTheDocument();
    
    // Verify status information
    expect(screen.getByText('Processing Status')).toBeInTheDocument();
    expect(screen.getByText('Status: Ready to process')).toBeInTheDocument();
  });

  it('should close modal when clicking backdrop', async () => {
    render(
      <ConfigProvider>
        <OCRProcessingTab {...defaultProps} />
      </ConfigProvider>
    );

    // Open the OCR modal
    const startOCRButton = screen.getByRole('button', { name: /开始OCR/i });
    fireEvent.click(startOCRButton);

    await waitFor(() => {
      expect(screen.getByTestId('modal-backdrop')).toBeInTheDocument();
    });

    // Click backdrop to close modal
    const backdrop = screen.getByTestId('modal-backdrop');
    fireEvent.click(backdrop);

    await waitFor(() => {
      expect(screen.queryByTestId('modal-container')).not.toBeInTheDocument();
    });

    // Verify onRefresh was called
    expect(defaultProps.onRefresh).toHaveBeenCalled();
  });

  it('should close modal when clicking close button', async () => {
    render(
      <ConfigProvider>
        <OCRProcessingTab {...defaultProps} />
      </ConfigProvider>
    );

    // Open the OCR modal
    const startOCRButton = screen.getByRole('button', { name: /开始OCR/i });
    fireEvent.click(startOCRButton);

    await waitFor(() => {
      expect(screen.getByTestId('modal-close')).toBeInTheDocument();
    });

    // Click close button
    const closeButton = screen.getByTestId('modal-close');
    fireEvent.click(closeButton);

    await waitFor(() => {
      expect(screen.queryByTestId('modal-container')).not.toBeInTheDocument();
    });

    // Verify onRefresh was called
    expect(defaultProps.onRefresh).toHaveBeenCalled();
  });

  it('should close modal when clicking back button in OCR processing', async () => {
    render(
      <ConfigProvider>
        <OCRProcessingTab {...defaultProps} />
      </ConfigProvider>
    );

    // Open the OCR modal
    const startOCRButton = screen.getByRole('button', { name: /开始OCR/i });
    fireEvent.click(startOCRButton);

    await waitFor(() => {
      expect(screen.getByTestId('ocr-back')).toBeInTheDocument();
    });

    // Click back button in OCR processing component
    const backButton = screen.getByTestId('ocr-back');
    fireEvent.click(backButton);

    await waitFor(() => {
      expect(screen.queryByTestId('modal-container')).not.toBeInTheDocument();
    });

    // Verify onRefresh was called
    expect(defaultProps.onRefresh).toHaveBeenCalled();
  });

  it('should maintain modal state correctly during interactions', async () => {
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

    // Interact with OCR processing buttons (should not close modal)
    const configButton = screen.getByTestId('ocr-config');
    fireEvent.click(configButton);

    // Modal should still be open
    expect(screen.getByTestId('modal-container')).toBeInTheDocument();

    const startProcessingButton = screen.getByTestId('ocr-start');
    fireEvent.click(startProcessingButton);

    // Modal should still be open
    expect(screen.getByTestId('modal-container')).toBeInTheDocument();
  });
});