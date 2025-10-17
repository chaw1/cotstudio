/**
 * Test to verify modal footer rendering
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { ConfigProvider, Button } from 'antd';
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

describe('ModalContainer Footer', () => {
  const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <ConfigProvider>
      {children}
    </ConfigProvider>
  );

  it('should render footer buttons correctly', () => {
    const onClose = vi.fn();
    const onSubmit = vi.fn();
    
    const footer = [
      <Button key="cancel" onClick={onClose}>
        取消
      </Button>,
      <Button key="submit" type="primary" onClick={onSubmit}>
        创建
      </Button>
    ];
    
    render(
      <TestWrapper>
        <ModalContainer
          visible={true}
          onClose={onClose}
          title="Test Modal"
          width={600}
          footer={footer}
        >
          <div data-testid="modal-content">Modal Content</div>
        </ModalContainer>
      </TestWrapper>
    );

    // Check if footer buttons are rendered (accounting for Antd's letter spacing)
    expect(screen.getByText(/取\s*消/)).toBeInTheDocument();
    expect(screen.getByText(/创\s*建/)).toBeInTheDocument();
  });

  it('should render without footer when footer is null', () => {
    const onClose = vi.fn();
    
    render(
      <TestWrapper>
        <ModalContainer
          visible={true}
          onClose={onClose}
          title="Test Modal"
          width={600}
          footer={null}
        >
          <div data-testid="modal-content">Modal Content</div>
        </ModalContainer>
      </TestWrapper>
    );

    // Check if modal content is rendered but no footer buttons
    expect(screen.getByTestId('modal-content')).toBeInTheDocument();
    expect(screen.queryByText('取消')).not.toBeInTheDocument();
    expect(screen.queryByText('创建')).not.toBeInTheDocument();
  });
});