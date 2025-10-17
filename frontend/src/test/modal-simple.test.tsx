import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ConfigProvider } from 'antd';
import { vi, describe, it, expect } from 'vitest';
import ModalContainer from '../components/common/ModalContainer';

// Mock the responsive layout hook
vi.mock('../hooks/useResponsiveLayout', () => ({
  useResponsiveLayout: () => ({
    isMobile: false,
    isTablet: false,
    screenSize: { width: 1200, height: 800 }
  })
}));

describe('ModalContainer Simple Test', () => {
  it('should render modal when visible', () => {
    const onClose = vi.fn();
    
    render(
      <ConfigProvider>
        <ModalContainer
          visible={true}
          onClose={onClose}
          title="Test Modal"
          width={600}
        >
          <div data-testid="modal-content">Modal Content</div>
        </ModalContainer>
      </ConfigProvider>
    );

    // Check if modal content is rendered
    expect(screen.getByTestId('modal-content')).toBeInTheDocument();
  });

  it('should not render when visible is false', () => {
    const onClose = vi.fn();
    
    render(
      <ConfigProvider>
        <ModalContainer
          visible={false}
          onClose={onClose}
          title="Test Modal"
          width={600}
        >
          <div data-testid="modal-content">Modal Content</div>
        </ModalContainer>
      </ConfigProvider>
    );

    // Modal should not be rendered
    expect(screen.queryByTestId('modal-content')).not.toBeInTheDocument();
  });

  it('should call onClose when close button is clicked', () => {
    const onClose = vi.fn();
    
    render(
      <ConfigProvider>
        <ModalContainer
          visible={true}
          onClose={onClose}
          title="Test Modal"
          width={600}
        >
          <div data-testid="modal-content">Modal Content</div>
        </ModalContainer>
      </ConfigProvider>
    );

    // Find and click the close button
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);

    expect(onClose).toHaveBeenCalled();
  });
});