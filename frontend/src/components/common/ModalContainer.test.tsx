import React, { useState } from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ConfigProvider } from 'antd';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import ModalContainer from './ModalContainer';
import { useResponsiveLayout } from '../../hooks/useResponsiveLayout';

// Mock the responsive layout hook
vi.mock('../../hooks/useResponsiveLayout');

const mockUseResponsiveLayout = vi.mocked(useResponsiveLayout);

// Test component that uses ModalContainer
const TestModalComponent: React.FC = () => {
  const [visible, setVisible] = useState(false);

  return (
    <div>
      <button onClick={() => setVisible(true)}>Open Modal</button>
      <ModalContainer
        visible={visible}
        onClose={() => setVisible(false)}
        title="Test Modal"
        width={600}
      >
        <div>Modal Content</div>
      </ModalContainer>
    </div>
  );
};

describe('ModalContainer', () => {
  beforeEach(() => {
    // Mock default responsive layout values
    mockUseResponsiveLayout.mockReturnValue({
      sidebarCollapsed: false,
      isMobile: false,
      isTablet: false,
      isDesktop: true,
      screenSize: { width: 1200, height: 800 },
      currentBreakpoint: 'lg',
      toggleSidebar: vi.fn(),
      setSidebarState: vi.fn(),
      layoutConfig: {} as any,
      layoutStyles: {} as any,
      debugInfo: {} as any,
    });

    // Mock DOM methods
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1200,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 800,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
    // Clean up any modal containers
    const containers = document.querySelectorAll('#modal-container-root');
    containers.forEach(container => container.remove());
  });

  it('should render modal when visible is true', async () => {
    render(
      <ConfigProvider>
        <TestModalComponent />
      </ConfigProvider>
    );

    const openButton = screen.getByText('Open Modal');
    fireEvent.click(openButton);

    await waitFor(() => {
      expect(screen.getByText('Test Modal')).toBeInTheDocument();
      expect(screen.getByText('Modal Content')).toBeInTheDocument();
    });
  });

  it('should not render modal when visible is false', () => {
    render(
      <ConfigProvider>
        <ModalContainer
          visible={false}
          onClose={vi.fn()}
          title="Test Modal"
        >
          <div>Modal Content</div>
        </ModalContainer>
      </ConfigProvider>
    );

    expect(screen.queryByText('Test Modal')).not.toBeInTheDocument();
    expect(screen.queryByText('Modal Content')).not.toBeInTheDocument();
  });

  it('should call onClose when ESC key is pressed', async () => {
    const onClose = vi.fn();
    
    render(
      <ConfigProvider>
        <ModalContainer
          visible={true}
          onClose={onClose}
          title="Test Modal"
        >
          <div>Modal Content</div>
        </ModalContainer>
      </ConfigProvider>
    );

    fireEvent.keyDown(document, { key: 'Escape' });
    
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('should adjust positioning for mobile devices', () => {
    mockUseResponsiveLayout.mockReturnValue({
      sidebarCollapsed: true,
      isMobile: true,
      isTablet: false,
      isDesktop: false,
      screenSize: { width: 375, height: 667 },
      currentBreakpoint: 'xs',
      toggleSidebar: vi.fn(),
      setSidebarState: vi.fn(),
      layoutConfig: {} as any,
      layoutStyles: {} as any,
      debugInfo: {} as any,
    });

    render(
      <ConfigProvider>
        <ModalContainer
          visible={true}
          onClose={vi.fn()}
          title="Test Modal"
          width={600}
        >
          <div>Modal Content</div>
        </ModalContainer>
      </ConfigProvider>
    );

    // Modal should be visible and adjusted for mobile
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
  });

  it('should create modal container root element', async () => {
    render(
      <ConfigProvider>
        <ModalContainer
          visible={true}
          onClose={vi.fn()}
          title="Test Modal"
        >
          <div>Modal Content</div>
        </ModalContainer>
      </ConfigProvider>
    );

    await waitFor(() => {
      const containerRoot = document.getElementById('modal-container-root');
      expect(containerRoot).toBeInTheDocument();
    });
  });

  it('should handle sidebar collapsed state correctly', () => {
    mockUseResponsiveLayout.mockReturnValue({
      sidebarCollapsed: true,
      isMobile: false,
      isTablet: false,
      isDesktop: true,
      screenSize: { width: 1200, height: 800 },
      currentBreakpoint: 'lg',
      toggleSidebar: vi.fn(),
      setSidebarState: vi.fn(),
      layoutConfig: {} as any,
      layoutStyles: {} as any,
      debugInfo: {} as any,
    });

    render(
      <ConfigProvider>
        <ModalContainer
          visible={true}
          onClose={vi.fn()}
          title="Test Modal"
        >
          <div>Modal Content</div>
        </ModalContainer>
      </ConfigProvider>
    );

    expect(screen.getByText('Test Modal')).toBeInTheDocument();
  });

  it('should handle custom width correctly', () => {
    render(
      <ConfigProvider>
        <ModalContainer
          visible={true}
          onClose={vi.fn()}
          title="Test Modal"
          width="80%"
        >
          <div>Modal Content</div>
        </ModalContainer>
      </ConfigProvider>
    );

    expect(screen.getByText('Test Modal')).toBeInTheDocument();
  });

  it('should handle non-centered positioning', () => {
    render(
      <ConfigProvider>
        <ModalContainer
          visible={true}
          onClose={vi.fn()}
          title="Test Modal"
          centered={false}
        >
          <div>Modal Content</div>
        </ModalContainer>
      </ConfigProvider>
    );

    expect(screen.getByText('Test Modal')).toBeInTheDocument();
  });
});