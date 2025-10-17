import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { ConfigProvider } from 'antd';
import OCRProcessingTab from './OCRProcessingTab';
import { FileInfo } from '../../types';

// Mock the useResponsiveLayout hook to test different sidebar states
const mockUseResponsiveLayout = vi.fn();
vi.mock('../../hooks/useResponsiveLayout', () => ({
  useResponsiveLayout: () => mockUseResponsiveLayout()
}));

// Mock the ModalContainer component to capture positioning props
const mockModalContainer = vi.fn();
vi.mock('../common/ModalContainer', () => ({
  default: (props: any) => {
    mockModalContainer(props);
    return props.visible ? (
      <div data-testid="modal-container" data-width={props.width} data-centered={props.centered}>
        <div data-testid="modal-header">{props.title}</div>
        <button data-testid="modal-close" onClick={props.onClose}>Close</button>
        <div data-testid="modal-content">{props.children}</div>
      </div>
    ) : null;
  }
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

const mockFile: FileInfo = {
  id: '1',
  filename: 'test-document.pdf',
  size: 1024000,
  mimeType: 'application/pdf',
  ocrStatus: 'pending',
  createdAt: '2024-01-01T00:00:00Z',
  projectId: 'project-1'
};

describe('OCR Modal Positioning Tests', () => {
  const defaultProps = {
    projectId: 'project-1',
    files: [mockFile],
    onRefresh: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should pass correct props to ModalContainer for expanded sidebar', async () => {
    // Mock expanded sidebar state
    mockUseResponsiveLayout.mockReturnValue({
      sidebarCollapsed: false,
      isMobile: false,
      isTablet: false,
      isDesktop: true,
      screenSize: { width: 1200, height: 800 },
      currentBreakpoint: 'lg',
      toggleSidebar: vi.fn(),
      setSidebarState: vi.fn(),
      layoutConfig: {},
      layoutStyles: {},
      debugInfo: {}
    });

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

    // Verify ModalContainer was called with correct props
    expect(mockModalContainer).toHaveBeenCalledWith(
      expect.objectContaining({
        visible: true,
        title: 'OCR处理 - test-document.pdf',
        width: 900,
        centered: true,
        destroyOnClose: true,
        footer: null,
        zIndex: 1300
      })
    );
  });

  it('should pass correct props to ModalContainer for collapsed sidebar', async () => {
    // Mock collapsed sidebar state
    mockUseResponsiveLayout.mockReturnValue({
      sidebarCollapsed: true,
      isMobile: false,
      isTablet: false,
      isDesktop: true,
      screenSize: { width: 1200, height: 800 },
      currentBreakpoint: 'lg',
      toggleSidebar: vi.fn(),
      setSidebarState: vi.fn(),
      layoutConfig: {},
      layoutStyles: {},
      debugInfo: {}
    });

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

    // Verify ModalContainer was called with correct props
    expect(mockModalContainer).toHaveBeenCalledWith(
      expect.objectContaining({
        visible: true,
        title: 'OCR处理 - test-document.pdf',
        width: 900,
        centered: true,
        destroyOnClose: true,
        footer: null,
        zIndex: 1300
      })
    );
  });

  it('should pass correct props to ModalContainer for mobile device', async () => {
    // Mock mobile device state
    mockUseResponsiveLayout.mockReturnValue({
      sidebarCollapsed: true,
      isMobile: true,
      isTablet: false,
      isDesktop: false,
      screenSize: { width: 375, height: 667 },
      currentBreakpoint: 'xs',
      toggleSidebar: vi.fn(),
      setSidebarState: vi.fn(),
      layoutConfig: {},
      layoutStyles: {},
      debugInfo: {}
    });

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

    // Verify ModalContainer was called with correct props
    expect(mockModalContainer).toHaveBeenCalledWith(
      expect.objectContaining({
        visible: true,
        title: 'OCR处理 - test-document.pdf',
        width: 900,
        centered: true,
        destroyOnClose: true,
        footer: null,
        zIndex: 1300
      })
    );
  });

  it('should render modal with correct attributes', async () => {
    mockUseResponsiveLayout.mockReturnValue({
      sidebarCollapsed: false,
      isMobile: false,
      isTablet: false,
      isDesktop: true,
      screenSize: { width: 1200, height: 800 },
      currentBreakpoint: 'lg',
      toggleSidebar: vi.fn(),
      setSidebarState: vi.fn(),
      layoutConfig: {},
      layoutStyles: {},
      debugInfo: {}
    });

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

    // Verify modal attributes
    const modalContainer = screen.getByTestId('modal-container');
    expect(modalContainer).toHaveAttribute('data-width', '900');
    expect(modalContainer).toHaveAttribute('data-centered', 'true');
  });

  it('should handle modal close correctly', async () => {
    mockUseResponsiveLayout.mockReturnValue({
      sidebarCollapsed: false,
      isMobile: false,
      isTablet: false,
      isDesktop: true,
      screenSize: { width: 1200, height: 800 },
      currentBreakpoint: 'lg',
      toggleSidebar: vi.fn(),
      setSidebarState: vi.fn(),
      layoutConfig: {},
      layoutStyles: {},
      debugInfo: {}
    });

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

    // Verify onRefresh was called
    expect(defaultProps.onRefresh).toHaveBeenCalled();
  });
});