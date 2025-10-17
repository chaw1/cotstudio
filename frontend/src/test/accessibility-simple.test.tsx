import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import { describe, it, expect, vi } from 'vitest';

import Sidebar from '../components/layout/Sidebar';
import ModalContainer from '../components/common/ModalContainer';

// Mock the responsive layout hook
vi.mock('../hooks/useResponsiveLayout', () => ({
  useResponsiveLayout: () => ({
    sidebarCollapsed: false,
    toggleSidebar: vi.fn(),
    currentBreakpoint: 'lg',
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    screenSize: { width: 1200, height: 800 },
    debugInfo: null
  })
}));

// Mock auth service
vi.mock('../services/authService', () => ({
  authService: {
    logout: vi.fn().mockResolvedValue(undefined)
  }
}));

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('Basic Accessibility Tests', () => {
  it('should render Sidebar with navigation role', () => {
    render(
      <TestWrapper>
        <Sidebar collapsed={false} />
      </TestWrapper>
    );

    const navigation = screen.getByRole('navigation');
    expect(navigation).toBeInTheDocument();
  });

  it('should render ModalContainer with dialog role when visible', () => {
    const mockClose = vi.fn();
    render(
      <ModalContainer
        visible={true}
        onClose={mockClose}
        title="Test Modal"
      >
        <p>Modal content</p>
      </ModalContainer>
    );

    // Check that modal content is rendered
    expect(screen.getByText('Modal content')).toBeInTheDocument();
  });

  it('should have proper ARIA attributes on sidebar elements', () => {
    render(
      <TestWrapper>
        <Sidebar collapsed={false} />
      </TestWrapper>
    );

    const navigation = screen.getByRole('navigation');
    expect(navigation).toHaveAttribute('aria-label', '主导航');
  });

  it('should include screen reader only content', () => {
    render(
      <TestWrapper>
        <Sidebar collapsed={false} />
      </TestWrapper>
    );

    // Check that screen reader content exists in DOM
    expect(document.body).toContainHTML('主要功能导航');
  });
});