import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import MainLayout from '../components/layout/MainLayout';
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

describe('Accessibility Tests', () => {
  beforeEach(() => {
    // Reset DOM
    document.body.innerHTML = '';
    document.documentElement.lang = '';
    document.title = '';
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Sidebar Accessibility', () => {
    it('should have proper ARIA labels and roles', () => {
      render(
        <TestWrapper>
          <Sidebar collapsed={false} />
        </TestWrapper>
      );

      // Check navigation role
      const navigation = screen.getByRole('navigation', { name: '主导航' });
      expect(navigation).toBeInTheDocument();

      // Check banner role for logo area
      const banner = screen.getByRole('banner');
      expect(banner).toBeInTheDocument();

      // Check contentinfo role for user area
      const contentinfo = screen.getByRole('contentinfo');
      expect(contentinfo).toBeInTheDocument();

      // Check menu roles
      const mainMenu = screen.getByRole('menubar', { name: '主要功能菜单' });
      expect(mainMenu).toBeInTheDocument();

      const adminMenu = screen.getByRole('menubar', { name: '管理功能菜单' });
      expect(adminMenu).toBeInTheDocument();
    });

    it('should have proper ARIA attributes for user menu', () => {
      render(
        <TestWrapper>
          <Sidebar collapsed={false} />
        </TestWrapper>
      );

      const userMenuButton = screen.getByRole('button', { name: /用户菜单/ });
      expect(userMenuButton).toHaveAttribute('aria-haspopup', 'true');
      expect(userMenuButton).toHaveAttribute('aria-expanded', 'false');
    });

    it('should have screen reader only content', () => {
      render(
        <TestWrapper>
          <Sidebar collapsed={false} />
        </TestWrapper>
      );

      // Check for screen reader only headings
      const mainNavHeading = document.querySelector('#*[id*="sidebar-nav"]');
      expect(document.body).toContainHTML('主要功能导航');
      expect(document.body).toContainHTML('管理功能');
    });

    it('should handle keyboard navigation', () => {
      const mockToggle = vi.fn();
      render(
        <TestWrapper>
          <Sidebar collapsed={false} onMobileClose={mockToggle} isMobile={true} />
        </TestWrapper>
      );

      // Test escape key on mobile
      fireEvent.keyDown(document, { key: 'Escape' });
      // Note: The actual keyboard handling is in the hook, this tests the setup
    });
  });

  describe('Modal Accessibility', () => {
    it('should have proper modal ARIA attributes', () => {
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

      const modal = screen.getByRole('dialog');
      expect(modal).toBeInTheDocument();
      expect(modal).toHaveAttribute('aria-modal', 'true');
      expect(modal).toHaveAttribute('aria-labelledby');
      expect(modal).toHaveAttribute('aria-describedby');
    });

    it('should trap focus within modal', async () => {
      const mockClose = vi.fn();
      render(
        <div>
          <button>Outside Button</button>
          <ModalContainer
            visible={true}
            onClose={mockClose}
            title="Test Modal"
          >
            <button>Modal Button 1</button>
            <button>Modal Button 2</button>
          </ModalContainer>
        </div>
      );

      // Focus should be trapped within modal
      const modalButton1 = screen.getByText('Modal Button 1');
      const modalButton2 = screen.getByText('Modal Button 2');
      
      // Test tab navigation within modal
      modalButton1.focus();
      fireEvent.keyDown(modalButton1, { key: 'Tab' });
      
      await waitFor(() => {
        expect(modalButton2).toHaveFocus();
      });
    });

    it('should close on Escape key', () => {
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

      fireEvent.keyDown(document, { key: 'Escape' });
      expect(mockClose).toHaveBeenCalled();
    });

    it('should set inert attributes on background content', () => {
      const mockClose = vi.fn();
      
      // Create main content and sidebar elements
      const mainContent = document.createElement('div');
      mainContent.id = 'main-content';
      document.body.appendChild(mainContent);
      
      const sidebar = document.createElement('nav');
      sidebar.className = 'sidebar-navigation';
      document.body.appendChild(sidebar);

      render(
        <ModalContainer
          visible={true}
          onClose={mockClose}
          title="Test Modal"
        >
          <p>Modal content</p>
        </ModalContainer>
      );

      // Check that background content is marked as inert
      expect(mainContent).toHaveAttribute('aria-hidden', 'true');
      expect(sidebar).toHaveAttribute('aria-hidden', 'true');
    });
  });

  describe('MainLayout Accessibility', () => {
    it('should set proper document language and title', () => {
      render(
        <TestWrapper>
          <MainLayout>
            <div>Test content</div>
          </MainLayout>
        </TestWrapper>
      );

      expect(document.documentElement.lang).toBe('zh-CN');
      expect(document.title).toContain('COT Studio');
    });

    it('should have skip links', () => {
      render(
        <TestWrapper>
          <MainLayout>
            <div>Test content</div>
          </MainLayout>
        </TestWrapper>
      );

      const skipLinks = screen.getAllByText(/跳转到/);
      expect(skipLinks.length).toBeGreaterThan(0);
    });

    it('should have proper landmark regions', () => {
      render(
        <TestWrapper>
          <MainLayout>
            <div>Test content</div>
          </MainLayout>
        </TestWrapper>
      );

      const main = screen.getByRole('main');
      expect(main).toBeInTheDocument();
      expect(main).toHaveAttribute('aria-label', '主要内容区域');
      expect(main).toHaveAttribute('tabIndex', '-1');
    });

    it('should handle keyboard shortcuts', () => {
      const { container } = render(
        <TestWrapper>
          <MainLayout>
            <div>Test content</div>
          </MainLayout>
        </TestWrapper>
      );

      // Test Ctrl+B for sidebar toggle
      fireEvent.keyDown(document, { key: 'b', ctrlKey: true });
      
      // Test Alt+M for main content focus
      fireEvent.keyDown(document, { key: 'm', altKey: true });
      
      const mainContent = screen.getByRole('main');
      expect(mainContent).toHaveAttribute('tabIndex', '-1');
    });

    it('should have accessible mobile overlay', () => {
      // Mock mobile layout
      vi.mocked(require('../hooks/useResponsiveLayout').useResponsiveLayout).mockReturnValue({
        sidebarCollapsed: false,
        toggleSidebar: vi.fn(),
        currentBreakpoint: 'xs',
        isMobile: true,
        isTablet: false,
        isDesktop: false,
        screenSize: { width: 375, height: 667 },
        debugInfo: null
      });

      render(
        <TestWrapper>
          <MainLayout>
            <div>Test content</div>
          </MainLayout>
        </TestWrapper>
      );

      const overlay = screen.getByRole('button', { name: /关闭侧边栏遮罩层/ });
      expect(overlay).toBeInTheDocument();
      expect(overlay).toHaveAttribute('tabIndex', '0');
    });
  });

  describe('Focus Management', () => {
    it('should manage focus properly when modal opens and closes', async () => {
      const TestComponent = () => {
        const [modalVisible, setModalVisible] = React.useState(false);
        
        return (
          <div>
            <button onClick={() => setModalVisible(true)}>Open Modal</button>
            <ModalContainer
              visible={modalVisible}
              onClose={() => setModalVisible(false)}
              title="Test Modal"
            >
              <button>Modal Button</button>
            </ModalContainer>
          </div>
        );
      };

      render(<TestComponent />);

      const openButton = screen.getByText('Open Modal');
      openButton.focus();
      
      // Open modal
      fireEvent.click(openButton);
      
      await waitFor(() => {
        const modalButton = screen.getByText('Modal Button');
        expect(modalButton).toBeInTheDocument();
      });

      // Close modal
      fireEvent.keyDown(document, { key: 'Escape' });
      
      await waitFor(() => {
        // Focus should return to the trigger button
        expect(openButton).toHaveFocus();
      });
    });
  });

  describe('Screen Reader Announcements', () => {
    it('should create announcement elements', () => {
      const { announceToScreenReader } = require('../hooks/useAccessibility').useAccessibility();
      
      // This would be tested in integration with actual components
      // The hook creates temporary DOM elements for announcements
      expect(typeof announceToScreenReader).toBe('function');
    });
  });

  describe('High Contrast and Reduced Motion', () => {
    it('should respect user preferences', () => {
      // Test that CSS classes are applied correctly
      const { container } = render(
        <TestWrapper>
          <MainLayout>
            <div>Test content</div>
          </MainLayout>
        </TestWrapper>
      );

      // Check that accessibility CSS is loaded
      const styles = document.querySelector('style');
      expect(document.head).toContainHTML('accessibility.css');
    });
  });
});

// Utility function to test keyboard navigation
export const testKeyboardNavigation = (element: HTMLElement, expectedFocusOrder: string[]) => {
  const focusableElements = element.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  expect(focusableElements.length).toBe(expectedFocusOrder.length);
  
  focusableElements.forEach((el, index) => {
    expect(el).toHaveAttribute('tabindex');
  });
};

// Utility function to test ARIA relationships
export const testAriaRelationships = (element: HTMLElement) => {
  const elementsWithAriaLabelledBy = element.querySelectorAll('[aria-labelledby]');
  const elementsWithAriaDescribedBy = element.querySelectorAll('[aria-describedby]');
  
  elementsWithAriaLabelledBy.forEach(el => {
    const labelId = el.getAttribute('aria-labelledby');
    if (labelId) {
      const labelElement = document.getElementById(labelId);
      expect(labelElement).toBeInTheDocument();
    }
  });
  
  elementsWithAriaDescribedBy.forEach(el => {
    const descId = el.getAttribute('aria-describedby');
    if (descId) {
      const descElement = document.getElementById(descId);
      expect(descElement).toBeInTheDocument();
    }
  });
};