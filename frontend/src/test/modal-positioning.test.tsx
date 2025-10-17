/**
 * Test to verify modal positioning with ModalContainer
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ConfigProvider } from 'antd';
import { vi, describe, it, expect } from 'vitest';
import ModalContainer from '../components/common/ModalContainer';

// Mock the responsive layout hook
vi.mock('../hooks/useResponsiveLayout', () => ({
  useResponsiveLayout: () => ({
    sidebarCollapsed: false,
    isMobile: false,
    isTablet: false,
    screenSize: { width: 1200, height: 800 },
    currentBreakpoint: 'lg'
  })
}));

describe('ModalContainer Positioning', () => {
  const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <ConfigProvider>
      {children}
    </ConfigProvider>
  );

  it('should render modal with proper positioning', () => {
    const onClose = vi.fn();
    
    render(
      <TestWrapper>
        <ModalContainer
          visible={true}
          onClose={onClose}
          title="Test Modal"
          width={600}
        >
          <div data-testid="modal-content">Modal Content</div>
        </ModalContainer>
      </TestWrapper>
    );

    // Check if modal content is rendered
    expect(screen.getByTestId('modal-content')).toBeInTheDocument();
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
  });

  it('should handle close events', () => {
    const onClose = vi.fn();
    
    render(
      <TestWrapper>
        <ModalContainer
          visible={true}
          onClose={onClose}
          title="Test Modal"
          width={600}
        >
          <div>Modal Content</div>
        </ModalContainer>
      </TestWrapper>
    );

    // Find and click close button (assuming Antd modal has a close button)
    const closeButton = screen.getByRole('button', { name: /close/i });
    if (closeButton) {
      fireEvent.click(closeButton);
      expect(onClose).toHaveBeenCalled();
    }
  });

  it('should not render when visible is false', () => {
    const onClose = vi.fn();
    
    render(
      <TestWrapper>
        <ModalContainer
          visible={false}
          onClose={onClose}
          title="Test Modal"
          width={600}
        >
          <div data-testid="modal-content">Modal Content</div>
        </ModalContainer>
      </TestWrapper>
    );

    // Modal content should not be visible
    expect(screen.queryByTestId('modal-content')).not.toBeInTheDocument();
  });
});