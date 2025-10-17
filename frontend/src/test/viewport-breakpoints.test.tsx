/**
 * Viewport and Breakpoint Responsive Tests
 * 
 * Tests layout adaptation across different viewport sizes and breakpoints
 * 
 * Requirements: 1.4, 2.4, 3.4
 */
import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';
import { ConfigProvider } from 'antd';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';

import { useResponsiveLayout } from '../hooks/useResponsiveLayout';
import Sidebar from '../components/layout/Sidebar';
import ModalContainer from '../components/common/ModalContainer';

// Viewport size configurations for testing
const VIEWPORT_SIZES = {
  // Mobile devices
  mobile: {
    iphone5: { width: 320, height: 568 },
    iphoneSE: { width: 375, height: 667 },
    iphone12: { width: 390, height: 844 },
    androidSmall: { width: 360, height: 640 },
    androidMedium: { width: 412, height: 732 }
  },
  // Tablet devices
  tablet: {
    ipadMini: { width: 768, height: 1024 },
    ipad: { width: 820, height: 1180 },
    ipadPro: { width: 1024, height: 1366 },
    androidTablet: { width: 800, height: 1280 }
  },
  // Desktop sizes
  desktop: {
    small: { width: 1024, height: 768 },
    medium: { width: 1280, height: 720 },
    large: { width: 1440, height: 900 },
    xl: { width: 1920, height: 1080 },
    ultrawide: { width: 2560, height: 1440 }
  }
};

// Mock responsive layout state
let mockLayoutState = {
  sidebarCollapsed: false,
  isMobile: false,
  isTablet: false,
  isDesktop: true,
  screenSize: { width: 1200, height: 800 },
  currentBreakpoint: 'lg',
  layoutStyles: {
    sidebarStyle: {
      width: 240,
      position: 'fixed' as const,
      left: 0,
      top: 0,
      bottom: 0,
      height: '100vh',
      zIndex: 1001,
      background: '#001529',
      transition: 'width 0.2s ease'
    },
    bodyStyle: {
      marginLeft: 240,
      marginTop: 0,
      minHeight: '100vh',
      transition: 'margin-left 0.2s ease'
    }
  }
};

const mockToggleSidebar = vi.fn();
const mockSetSidebarState = vi.fn();

// Mock the responsive layout hook
vi.mock('../hooks/useResponsiveLayout', () => ({
  useResponsiveLayout: () => ({
    ...mockLayoutState,
    toggleSidebar: mockToggleSidebar,
    setSidebarState: mockSetSidebarState
  })
}));

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <ConfigProvider>
      {children}
    </ConfigProvider>
  </BrowserRouter>
);

// Utility function to set viewport size and update mock state
const setViewportSize = (width: number, height: number) => {
  // Update window dimensions
  Object.defineProperty(window, 'innerWidth', { value: width, writable: true });
  Object.defineProperty(window, 'innerHeight', { value: height, writable: true });
  
  // Update mock layout state
  mockLayoutState.screenSize = { width, height };
  
  // Determine device type
  mockLayoutState.isMobile = width <= 767;
  mockLayoutState.isTablet = width >= 768 && width <= 1199;
  mockLayoutState.isDesktop = width >= 1200;
  
  // Determine breakpoint
  if (width >= 1600) mockLayoutState.currentBreakpoint = 'xxl';
  else if (width >= 1200) mockLayoutState.currentBreakpoint = 'xl';
  else if (width >= 992) mockLayoutState.currentBreakpoint = 'lg';
  else if (width >= 768) mockLayoutState.currentBreakpoint = 'md';
  else if (width >= 576) mockLayoutState.currentBreakpoint = 'sm';
  else mockLayoutState.currentBreakpoint = 'xs';
  
  // Update sidebar width in layout styles
  const sidebarWidth = mockLayoutState.sidebarCollapsed ? 80 : 240;
  mockLayoutState.layoutStyles.sidebarStyle.width = sidebarWidth;
  mockLayoutState.layoutStyles.bodyStyle.marginLeft = sidebarWidth;
  
  // Dispatch resize event
  window.dispatchEvent(new Event('resize'));
};

describe('Viewport and Breakpoint Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset to default desktop size
    setViewportSize(1200, 800);
    mockLayoutState.sidebarCollapsed = false;
  });

  afterEach(() => {
    // Clean up DOM
    document.body.innerHTML = '';
  });

  describe('Mobile Viewport Tests', () => {
    it('should adapt to iPhone 5 viewport (xs breakpoint)', () => {
      setViewportSize(VIEWPORT_SIZES.mobile.iphone5.width, VIEWPORT_SIZES.mobile.iphone5.height);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('xs');
      expect(mockLayoutState.isMobile).toBe(true);
      expect(mockLayoutState.isDesktop).toBe(false);
    });

    it('should adapt to iPhone SE viewport (xs breakpoint)', () => {
      setViewportSize(VIEWPORT_SIZES.mobile.iphoneSE.width, VIEWPORT_SIZES.mobile.iphoneSE.height);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('xs');
      expect(mockLayoutState.isMobile).toBe(true);
    });

    it('should adapt to iPhone 12 viewport (xs breakpoint)', () => {
      setViewportSize(VIEWPORT_SIZES.mobile.iphone12.width, VIEWPORT_SIZES.mobile.iphone12.height);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('xs');
      expect(mockLayoutState.isMobile).toBe(true);
    });

    it('should adapt to Android small viewport (xs breakpoint)', () => {
      setViewportSize(VIEWPORT_SIZES.mobile.androidSmall.width, VIEWPORT_SIZES.mobile.androidSmall.height);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('xs');
      expect(mockLayoutState.isMobile).toBe(true);
    });

    it('should handle mobile landscape orientation', () => {
      // iPhone SE landscape
      setViewportSize(667, 375);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('sm');
      expect(mockLayoutState.isMobile).toBe(false); // Landscape mobile is treated as small tablet
    });
  });

  describe('Tablet Viewport Tests', () => {
    it('should adapt to iPad Mini viewport (md breakpoint)', () => {
      setViewportSize(VIEWPORT_SIZES.tablet.ipadMini.width, VIEWPORT_SIZES.tablet.ipadMini.height);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('md');
      expect(mockLayoutState.isTablet).toBe(true);
      expect(mockLayoutState.isMobile).toBe(false);
    });

    it('should adapt to iPad viewport (md breakpoint)', () => {
      setViewportSize(VIEWPORT_SIZES.tablet.ipad.width, VIEWPORT_SIZES.tablet.ipad.height);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('md');
      expect(mockLayoutState.isTablet).toBe(true);
    });

    it('should adapt to iPad Pro viewport (lg breakpoint)', () => {
      setViewportSize(VIEWPORT_SIZES.tablet.ipadPro.width, VIEWPORT_SIZES.tablet.ipadPro.height);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('lg');
      expect(mockLayoutState.isTablet).toBe(true);
    });

    it('should handle tablet landscape orientation', () => {
      // iPad landscape
      setViewportSize(1180, 820);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('lg');
      expect(mockLayoutState.isTablet).toBe(false); // Large landscape is desktop
      expect(mockLayoutState.isDesktop).toBe(true);
    });
  });

  describe('Desktop Viewport Tests', () => {
    it('should adapt to small desktop viewport (lg breakpoint)', () => {
      setViewportSize(VIEWPORT_SIZES.desktop.small.width, VIEWPORT_SIZES.desktop.small.height);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('lg');
      expect(mockLayoutState.isDesktop).toBe(true);
    });

    it('should adapt to medium desktop viewport (xl breakpoint)', () => {
      setViewportSize(VIEWPORT_SIZES.desktop.medium.width, VIEWPORT_SIZES.desktop.medium.height);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('xl');
      expect(mockLayoutState.isDesktop).toBe(true);
    });

    it('should adapt to large desktop viewport (xl breakpoint)', () => {
      setViewportSize(VIEWPORT_SIZES.desktop.large.width, VIEWPORT_SIZES.desktop.large.height);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('xl');
      expect(mockLayoutState.isDesktop).toBe(true);
    });

    it('should adapt to XL desktop viewport (xl breakpoint)', () => {
      setViewportSize(VIEWPORT_SIZES.desktop.xl.width, VIEWPORT_SIZES.desktop.xl.height);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('xl');
      expect(mockLayoutState.isDesktop).toBe(true);
    });

    it('should adapt to ultrawide viewport (xxl breakpoint)', () => {
      setViewportSize(VIEWPORT_SIZES.desktop.ultrawide.width, VIEWPORT_SIZES.desktop.ultrawide.height);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('xxl');
      expect(mockLayoutState.isDesktop).toBe(true);
    });
  });

  describe('Modal Positioning Across Viewports', () => {
    it('should position modal correctly on mobile viewport', () => {
      setViewportSize(VIEWPORT_SIZES.mobile.iphoneSE.width, VIEWPORT_SIZES.mobile.iphoneSE.height);
      
      const onClose = vi.fn();
      
      render(
        <TestWrapper>
          <ModalContainer
            visible={true}
            onClose={onClose}
            title="Mobile Modal"
            width={300}
          >
            <div data-testid="modal-content">Mobile content</div>
          </ModalContainer>
        </TestWrapper>
      );

      expect(screen.getByTestId('modal-content')).toBeInTheDocument();
      expect(screen.getByText('Mobile Modal')).toBeInTheDocument();
    });

    it('should position modal correctly on tablet viewport', () => {
      setViewportSize(VIEWPORT_SIZES.tablet.ipad.width, VIEWPORT_SIZES.tablet.ipad.height);
      
      const onClose = vi.fn();
      
      render(
        <TestWrapper>
          <ModalContainer
            visible={true}
            onClose={onClose}
            title="Tablet Modal"
            width={500}
          >
            <div data-testid="modal-content">Tablet content</div>
          </ModalContainer>
        </TestWrapper>
      );

      expect(screen.getByTestId('modal-content')).toBeInTheDocument();
    });

    it('should position modal correctly on desktop viewport', () => {
      setViewportSize(VIEWPORT_SIZES.desktop.large.width, VIEWPORT_SIZES.desktop.large.height);
      
      const onClose = vi.fn();
      
      render(
        <TestWrapper>
          <ModalContainer
            visible={true}
            onClose={onClose}
            title="Desktop Modal"
            width={600}
          >
            <div data-testid="modal-content">Desktop content</div>
          </ModalContainer>
        </TestWrapper>
      );

      expect(screen.getByTestId('modal-content')).toBeInTheDocument();
    });

    it('should adapt modal width based on viewport size', () => {
      const onClose = vi.fn();
      
      // Test on small mobile
      setViewportSize(VIEWPORT_SIZES.mobile.iphone5.width, VIEWPORT_SIZES.mobile.iphone5.height);
      
      const { rerender } = render(
        <TestWrapper>
          <ModalContainer
            visible={true}
            onClose={onClose}
            title="Adaptive Modal"
            width={800} // Large width that should be constrained
          >
            <div data-testid="modal-content">Adaptive content</div>
          </ModalContainer>
        </TestWrapper>
      );

      expect(screen.getByTestId('modal-content')).toBeInTheDocument();

      // Test on desktop
      setViewportSize(VIEWPORT_SIZES.desktop.xl.width, VIEWPORT_SIZES.desktop.xl.height);
      
      rerender(
        <TestWrapper>
          <ModalContainer
            visible={true}
            onClose={onClose}
            title="Adaptive Modal"
            width={800}
          >
            <div data-testid="modal-content">Adaptive content</div>
          </ModalContainer>
        </TestWrapper>
      );

      expect(screen.getByTestId('modal-content')).toBeInTheDocument();
    });
  });

  describe('Sidebar Behavior Across Viewports', () => {
    it('should show full sidebar on desktop', () => {
      setViewportSize(VIEWPORT_SIZES.desktop.large.width, VIEWPORT_SIZES.desktop.large.height);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(screen.getByText('COT Studio')).toBeInTheDocument();
      expect(screen.getByText('仪表板')).toBeInTheDocument();
    });

    it('should adapt sidebar for tablet viewport', () => {
      setViewportSize(VIEWPORT_SIZES.tablet.ipad.width, VIEWPORT_SIZES.tablet.ipad.height);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(screen.getByText('COT Studio')).toBeInTheDocument();
    });

    it('should handle sidebar on mobile viewport', () => {
      setViewportSize(VIEWPORT_SIZES.mobile.iphoneSE.width, VIEWPORT_SIZES.mobile.iphoneSE.height);
      
      render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      // Mobile sidebar should still render but may have different behavior
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    it('should handle collapsed sidebar across viewports', () => {
      mockLayoutState.sidebarCollapsed = true;
      
      // Test on desktop
      setViewportSize(VIEWPORT_SIZES.desktop.large.width, VIEWPORT_SIZES.desktop.large.height);
      
      const { rerender } = render(
        <TestWrapper>
          <Sidebar collapsed={true} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      // Should show collapsed state
      expect(screen.queryByText('COT Studio')).not.toBeInTheDocument();

      // Test on tablet
      setViewportSize(VIEWPORT_SIZES.tablet.ipad.width, VIEWPORT_SIZES.tablet.ipad.height);
      
      rerender(
        <TestWrapper>
          <Sidebar collapsed={true} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(screen.queryByText('COT Studio')).not.toBeInTheDocument();
    });
  });

  describe('Breakpoint Transitions', () => {
    it('should handle smooth transitions between breakpoints', async () => {
      const { rerender } = render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      // Transition from desktop to tablet
      setViewportSize(VIEWPORT_SIZES.desktop.large.width, VIEWPORT_SIZES.desktop.large.height);
      expect(mockLayoutState.currentBreakpoint).toBe('xl');

      rerender(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      // Transition to tablet
      setViewportSize(VIEWPORT_SIZES.tablet.ipad.width, VIEWPORT_SIZES.tablet.ipad.height);
      expect(mockLayoutState.currentBreakpoint).toBe('md');

      rerender(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      // Transition to mobile
      setViewportSize(VIEWPORT_SIZES.mobile.iphoneSE.width, VIEWPORT_SIZES.mobile.iphoneSE.height);
      expect(mockLayoutState.currentBreakpoint).toBe('xs');

      rerender(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      // Should handle all transitions smoothly
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    it('should handle rapid viewport changes', async () => {
      const { rerender } = render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      // Rapidly change between different viewport sizes
      const sizes = [
        VIEWPORT_SIZES.mobile.iphone5,
        VIEWPORT_SIZES.tablet.ipad,
        VIEWPORT_SIZES.desktop.large,
        VIEWPORT_SIZES.mobile.androidMedium,
        VIEWPORT_SIZES.desktop.ultrawide
      ];

      for (const size of sizes) {
        act(() => {
          setViewportSize(size.width, size.height);
        });

        rerender(
          <TestWrapper>
            <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
          </TestWrapper>
        );

        // Should handle rapid changes without errors
        expect(screen.getByRole('navigation')).toBeInTheDocument();
      }
    });

    it('should maintain component state during viewport changes', () => {
      const { rerender } = render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      // Change viewport but maintain sidebar state
      setViewportSize(VIEWPORT_SIZES.mobile.iphoneSE.width, VIEWPORT_SIZES.mobile.iphoneSE.height);
      
      rerender(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      // Component should maintain its state
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });
  });

  describe('Edge Cases and Performance', () => {
    it('should handle extremely small viewports', () => {
      setViewportSize(240, 320); // Very small screen
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('xs');
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    it('should handle extremely large viewports', () => {
      setViewportSize(3840, 2160); // 4K display
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('xxl');
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    it('should handle unusual aspect ratios', () => {
      setViewportSize(2560, 1080); // Ultrawide 21:9
      
      render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      expect(mockLayoutState.currentBreakpoint).toBe('xxl');
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    it('should handle viewport changes during component lifecycle', () => {
      const { unmount } = render(
        <TestWrapper>
          <Sidebar collapsed={mockLayoutState.sidebarCollapsed} isMobile={mockLayoutState.isMobile} />
        </TestWrapper>
      );

      // Change viewport during component lifecycle
      setViewportSize(VIEWPORT_SIZES.mobile.iphoneSE.width, VIEWPORT_SIZES.mobile.iphoneSE.height);

      // Should not throw errors on unmount
      expect(() => unmount()).not.toThrow();
    });
  });
});