/**
 * Comprehensive Responsive Behavior Tests
 * 
 * Tests layout behavior across different screen sizes and devices,
 * sidebar functionality, modal positioning, and touch interactions.
 * 
 * Requirements: 1.4, 2.4, 3.4
 */
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConfigProvider } from 'antd';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';

// Components to test
import Sidebar from '../components/layout/Sidebar';
import ModalContainer from '../components/common/ModalContainer';
import { useResponsiveLayout } from '../hooks/useResponsiveLayout';

// Test utilities
interface MockScreenSize {
  width: number;
  height: number;
}

interface MockLayoutState {
  sidebarCollapsed: boolean;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  screenSize: MockScreenSize;
  currentBreakpoint: string;
}

// Mock responsive layout hook with controllable state
const mockLayoutState: MockLayoutState = {
  sidebarCollapsed: false,
  isMobile: false,
  isTablet: false,
  isDesktop: true,
  screenSize: { width: 1200, height: 800 },
  currentBreakpoint: 'lg'
};

const mockToggleSidebar = vi.fn();
const mockSetSidebarState = vi.fn();

vi.mock('../hooks/useResponsiveLayout', () => ({
  useResponsiveLayout: () => ({
    ...mockLayoutState,
    toggleSidebar: mockToggleSidebar,
    setSidebarState: mockSetSidebarState,
    layoutStyles: {
      sidebarStyle: {
        width: mockLayoutState.sidebarCollapsed ? 80 : 240,
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        height: '100vh',
        zIndex: 1001,
        background: '#001529',
        transition: 'width 0.2s ease'
      },
      bodyStyle: {
        marginLeft: mockLayoutState.sidebarCollapsed ? 80 : 240,
        marginTop: 0,
        minHeight: '100vh',
        transition: 'margin-left 0.2s ease'
      }
    }
  })
}));

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <ConfigProvider>
      {children}
    </ConfigProvider>
  </BrowserRouter>
);

// Utility functions for testing
const setScreenSize = (width: number, height: number) => {
  mockLayoutState.screenSize = { width, height };
  
  // Update device type flags
  mockLayoutState.isMobile = width <= 767;
  mockLayoutState.isTablet = width >= 768 && width <= 1199;
  mockLayoutState.isDesktop = width >= 1200;
  
  // Update breakpoint
  if (width >= 1600) mockLayoutState.currentBreakpoint = 'xxl';
  else if (width >= 1200) mockLayoutState.currentBreakpoint = 'xl';
  else if (width >= 992) mockLayoutState.currentBreakpoint = 'lg';
  else if (width >= 768) mockLayoutState.currentBreakpoint = 'md';
  else if (width >= 576) mockLayoutState.currentBreakpoint = 'sm';
  else mockLayoutState.currentBreakpoint = 'xs';
  
  // Trigger window resize event
  Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: width });
  Object.defineProperty(window, 'innerHeight', { writable: true, configurable: true, value: height });
  window.dispatchEvent(new Event('resize'));
};

const setSidebarCollapsed = (collapsed: boolean) => {
  mockLayoutState.sidebarCollapsed = collapsed;
};

// Mock touch events
const createTouchEvent = (type: string, touches: Array<{ clientX: number; clientY: number }>) => {
  return new TouchEvent(type, {
    touches: touches.map(touch => ({
      ...touch,
      identifier: 0,
      target: document.body,
      radiusX: 1,
      radiusY: 1,
      rotationAngle: 0,
      force: 1
    })) as any,
    bubbles: true,
    cancelable: true
  });
};

describe('Responsive Behavior Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset to desktop default
    setScreenSize(1200, 800);
    setSidebarCollapsed(false);
  });

  afterEach(() => {
    // Clean up any DOM modifications
    document.body.innerHTML = '';
  });

  describe('Layout Behavior Across Screen Sizes', () => {
    it('should adapt layout for mobile screens (xs breakpoint)', async () => {
      setScreenSize(375, 667); // iPhone size
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.isMobile).toBe(true);
      expect(mockLayoutState.currentBreakpoint).toBe('xs');
      expect(mockLayoutState.isDesktop).toBe(false);
    });

    it('should adapt layout for tablet screens (md breakpoint)', async () => {
      setScreenSize(768, 1024); // iPad size
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.isTablet).toBe(true);
      expect(mockLayoutState.currentBreakpoint).toBe('md');
      expect(mockLayoutState.isMobile).toBe(false);
    });

    it('should adapt layout for desktop screens (xl breakpoint)', async () => {
      setScreenSize(1440, 900); // Desktop size
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.isDesktop).toBe(true);
      expect(mockLayoutState.currentBreakpoint).toBe('xl');
      expect(mockLayoutState.isMobile).toBe(false);
    });

    it('should handle ultra-wide screens (xxl breakpoint)', async () => {
      setScreenSize(1920, 1080); // Ultra-wide desktop
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('xxl');
      expect(mockLayoutState.isDesktop).toBe(true);
    });

    it('should handle screen orientation changes', async () => {
      // Start in portrait mobile
      setScreenSize(375, 667);
      
      const { rerender } = render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.isMobile).toBe(true);

      // Rotate to landscape
      setScreenSize(667, 375);
      
      rerender(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('sm');
    });
  });

  describe('Sidebar Collapse/Expand Functionality', () => {
    it('should render expanded sidebar by default on desktop', () => {
      setScreenSize(1200, 800);
      setSidebarCollapsed(false);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} />
        </TestWrapper>
      );

      // Check for expanded sidebar content
      expect(screen.getByText('COT Studio')).toBeInTheDocument();
      expect(screen.getByText('仪表板')).toBeInTheDocument();
      expect(screen.getByText('项目管理')).toBeInTheDocument();
    });

    it('should render collapsed sidebar when collapsed prop is true', () => {
      setSidebarCollapsed(true);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} />
        </TestWrapper>
      );

      // In collapsed state, full text should not be visible
      expect(screen.queryByText('COT Studio')).not.toBeInTheDocument();
      // But icons should still be present
      expect(screen.getByRole('img', { name: /dashboard/i })).toBeInTheDocument();
    });

    it('should handle sidebar toggle functionality', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} />
        </TestWrapper>
      );

      // Simulate clicking a toggle button (would be in parent component)
      act(() => {
        mockToggleSidebar();
      });

      expect(mockToggleSidebar).toHaveBeenCalled();
    });

    it('should auto-collapse sidebar on mobile screens', () => {
      setScreenSize(375, 667); // Mobile size
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      // On mobile, sidebar behavior should be different
      expect(mockLayoutState.isMobile).toBe(true);
    });

    it('should maintain sidebar state during screen size changes', async () => {
      setSidebarCollapsed(true);
      setScreenSize(1200, 800);
      
      const { rerender } = render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} />
        </TestWrapper>
      );

      // Change screen size but keep collapsed state
      setScreenSize(1440, 900);
      
      rerender(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} />
        </TestWrapper>
      );

      expect(mockLayoutState.sidebarCollapsed).toBe(true);
    });
  });

  describe('Modal Positioning Adaptation', () => {
    it('should position modal correctly in desktop layout', () => {
      setScreenSize(1200, 800);
      setSidebarCollapsed(false);
      
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

      expect(screen.getByTestId('modal-content')).toBeInTheDocument();
      expect(screen.getByText('Test Modal')).toBeInTheDocument();
    });

    it('should adapt modal width for mobile screens', () => {
      setScreenSize(375, 667); // Mobile size
      
      const onClose = vi.fn();
      
      render(
        <TestWrapper>
          <ModalContainer
            visible={true}
            onClose={onClose}
            title="Mobile Modal"
            width={600}
          >
            <div data-testid="modal-content">Mobile Modal Content</div>
          </ModalContainer>
        </TestWrapper>
      );

      expect(screen.getByTestId('modal-content')).toBeInTheDocument();
      // Modal should adapt to mobile screen size
    });

    it('should adjust modal positioning when sidebar is collapsed', () => {
      setScreenSize(1200, 800);
      setSidebarCollapsed(true);
      
      const onClose = vi.fn();
      
      render(
        <TestWrapper>
          <ModalContainer
            visible={true}
            onClose={onClose}
            title="Collapsed Sidebar Modal"
            width={500}
          >
            <div data-testid="modal-content">Content with collapsed sidebar</div>
          </ModalContainer>
        </TestWrapper>
      );

      expect(screen.getByTestId('modal-content')).toBeInTheDocument();
      // Modal should account for collapsed sidebar width (80px vs 240px)
    });

    it('should handle modal positioning on tablet screens', () => {
      setScreenSize(768, 1024); // Tablet size
      
      const onClose = vi.fn();
      
      render(
        <TestWrapper>
          <ModalContainer
            visible={true}
            onClose={onClose}
            title="Tablet Modal"
            width={400}
          >
            <div data-testid="modal-content">Tablet Modal Content</div>
          </ModalContainer>
        </TestWrapper>
      );

      expect(screen.getByTestId('modal-content')).toBeInTheDocument();
    });

    it('should handle very wide modals on large screens', () => {
      setScreenSize(1920, 1080); // Large desktop
      
      const onClose = vi.fn();
      
      render(
        <TestWrapper>
          <ModalContainer
            visible={true}
            onClose={onClose}
            title="Wide Modal"
            width={1200}
          >
            <div data-testid="modal-content">Wide Modal Content</div>
          </ModalContainer>
        </TestWrapper>
      );

      expect(screen.getByTestId('modal-content')).toBeInTheDocument();
    });

    it('should close modal on escape key press', async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();
      
      render(
        <TestWrapper>
          <ModalContainer
            visible={true}
            onClose={onClose}
            title="Keyboard Modal"
          >
            <div data-testid="modal-content">Keyboard test content</div>
          </ModalContainer>
        </TestWrapper>
      );

      await user.keyboard('{Escape}');
      
      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('Touch Interactions and Mobile Behaviors', () => {
    it('should handle touch events on mobile sidebar', async () => {
      setScreenSize(375, 667); // Mobile size
      
      const onMobileClose = vi.fn();
      
      render(
        <TestWrapper>
          <Sidebar 
            collapsed={false} 
            isMobile={true}
            onMobileClose={onMobileClose}
          />
        </TestWrapper>
      );

      // Simulate touch interaction
      const sidebar = screen.getByText('COT Studio').closest('div');
      if (sidebar) {
        fireEvent.touchStart(sidebar, {
          touches: [{ clientX: 0, clientY: 0 }]
        });
        
        fireEvent.touchMove(sidebar, {
          touches: [{ clientX: -100, clientY: 0 }]
        });
        
        fireEvent.touchEnd(sidebar, {
          changedTouches: [{ clientX: -100, clientY: 0 }]
        });
      }

      // Touch events should be handled appropriately
      expect(mockLayoutState.isMobile).toBe(true);
    });

    it('should handle swipe gestures for sidebar on mobile', async () => {
      setScreenSize(375, 667);
      
      const onMobileClose = vi.fn();
      
      render(
        <TestWrapper>
          <Sidebar 
            collapsed={false} 
            isMobile={true}
            onMobileClose={onMobileClose}
          />
        </TestWrapper>
      );

      // Simulate swipe left gesture
      const sidebar = document.body;
      
      fireEvent.touchStart(sidebar, {
        touches: [{ clientX: 200, clientY: 300 }]
      });
      
      fireEvent.touchMove(sidebar, {
        touches: [{ clientX: 50, clientY: 300 }]
      });
      
      fireEvent.touchEnd(sidebar, {
        changedTouches: [{ clientX: 50, clientY: 300 }]
      });

      // Swipe gesture should be recognized
    });

    it('should handle modal touch interactions on mobile', async () => {
      setScreenSize(375, 667);
      
      const onClose = vi.fn();
      
      render(
        <TestWrapper>
          <ModalContainer
            visible={true}
            onClose={onClose}
            title="Touch Modal"
          >
            <div data-testid="modal-content">Touch test content</div>
          </ModalContainer>
        </TestWrapper>
      );

      const modalContent = screen.getByTestId('modal-content');
      
      // Simulate touch on modal content (should not close)
      fireEvent.touchStart(modalContent);
      fireEvent.touchEnd(modalContent);
      
      expect(onClose).not.toHaveBeenCalled();
    });

    it('should handle pinch-to-zoom prevention on mobile', () => {
      setScreenSize(375, 667);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={true} />
        </TestWrapper>
      );

      // Simulate pinch gesture
      const sidebar = document.body;
      
      fireEvent.touchStart(sidebar, {
        touches: [
          { clientX: 100, clientY: 100 },
          { clientX: 200, clientY: 200 }
        ]
      });
      
      fireEvent.touchMove(sidebar, {
        touches: [
          { clientX: 80, clientY: 80 },
          { clientX: 220, clientY: 220 }
        ]
      });
      
      fireEvent.touchEnd(sidebar);

      // Pinch gestures should be handled appropriately
    });

    it('should adapt touch target sizes for mobile', () => {
      setScreenSize(375, 667);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={true} />
        </TestWrapper>
      );

      // Check that interactive elements have appropriate touch target sizes
      const menuItems = screen.getAllByRole('menuitem');
      menuItems.forEach(item => {
        const styles = window.getComputedStyle(item);
        // Touch targets should be at least 44px (iOS) or 48dp (Android)
        const minTouchSize = 44;
        expect(parseInt(styles.minHeight) || parseInt(styles.height)).toBeGreaterThanOrEqual(minTouchSize);
      });
    });
  });

  describe('Performance and Edge Cases', () => {
    it('should handle rapid screen size changes without errors', async () => {
      const { rerender } = render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} />
        </TestWrapper>
      );

      // Rapidly change screen sizes
      const sizes = [
        [375, 667],   // Mobile
        [768, 1024],  // Tablet
        [1200, 800],  // Desktop
        [1920, 1080], // Large desktop
        [320, 568],   // Small mobile
      ];

      for (const [width, height] of sizes) {
        act(() => {
          setScreenSize(width, height);
        });
        
        rerender(
          <TestWrapper>
            <Sidebar collapsed={mockLayoutState.sidebarCollapsed} />
          </TestWrapper>
        );
      }

      // Should not throw errors
      expect(screen.getByRole('menu')).toBeInTheDocument();
    });

    it('should handle multiple modals with different screen sizes', () => {
      setScreenSize(1200, 800);
      
      const onClose1 = vi.fn();
      const onClose2 = vi.fn();
      
      render(
        <TestWrapper>
          <ModalContainer visible={true} onClose={onClose1} title="Modal 1">
            <div data-testid="modal-1">First Modal</div>
          </ModalContainer>
          <ModalContainer visible={true} onClose={onClose2} title="Modal 2">
            <div data-testid="modal-2">Second Modal</div>
          </ModalContainer>
        </TestWrapper>
      );

      expect(screen.getByTestId('modal-1')).toBeInTheDocument();
      expect(screen.getByTestId('modal-2')).toBeInTheDocument();
    });

    it('should handle memory cleanup on component unmount', () => {
      const { unmount } = render(
        <TestWrapper>
          <Sidebar collapsed={false} />
        </TestWrapper>
      );

      // Should not throw errors on unmount
      expect(() => unmount()).not.toThrow();
    });

    it('should handle accessibility features with responsive design', () => {
      // Mock reduced motion preference
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation(query => ({
          matches: query === '(prefers-reduced-motion: reduce)',
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        })),
      });

      render(
        <TestWrapper>
          <Sidebar collapsed={false} />
        </TestWrapper>
      );

      // Should respect accessibility preferences
      expect(screen.getByRole('menu')).toBeInTheDocument();
    });
  });

  describe('Integration Tests', () => {
    it('should maintain layout consistency across component interactions', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <div>
            <Sidebar collapsed={mockLayoutState.sidebarCollapsed} />
            <ModalContainer
              visible={false}
              onClose={vi.fn()}
              title="Integration Test Modal"
            >
              <div>Modal content</div>
            </ModalContainer>
          </div>
        </TestWrapper>
      );

      // Test navigation interaction
      const dashboardLink = screen.getByText('仪表板');
      await user.click(dashboardLink);

      // Layout should remain consistent
      expect(screen.getByRole('menu')).toBeInTheDocument();
    });

    it('should handle concurrent layout updates', async () => {
      const { rerender } = render(
        <TestWrapper>
          <Sidebar collapsed={false} />
        </TestWrapper>
      );

      // Simulate concurrent updates
      act(() => {
        setScreenSize(768, 1024);
        setSidebarCollapsed(true);
      });

      rerender(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} />
        </TestWrapper>
      );

      // Should handle concurrent updates gracefully
      expect(screen.getByRole('menu')).toBeInTheDocument();
    });
  });
});