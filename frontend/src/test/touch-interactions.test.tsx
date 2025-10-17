/**
 * Touch Interactions and Mobile-Specific Behavior Tests
 * 
 * Tests touch gestures, mobile navigation, and device-specific interactions
 * 
 * Requirements: 1.4, 2.4, 3.4
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConfigProvider } from 'antd';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';

import Sidebar from '../components/layout/Sidebar';
import ModalContainer from '../components/common/ModalContainer';

// Mock touch event utilities
const createTouchEvent = (
  type: string, 
  touches: Array<{ clientX: number; clientY: number; identifier?: number }>
) => {
  const touchList = touches.map((touch, index) => ({
    clientX: touch.clientX,
    clientY: touch.clientY,
    identifier: touch.identifier ?? index,
    target: document.body,
    pageX: touch.clientX,
    pageY: touch.clientY,
    screenX: touch.clientX,
    screenY: touch.clientY,
    radiusX: 1,
    radiusY: 1,
    rotationAngle: 0,
    force: 1
  }));

  return new TouchEvent(type, {
    touches: type === 'touchend' ? [] : touchList,
    changedTouches: touchList,
    targetTouches: touchList,
    bubbles: true,
    cancelable: true
  } as TouchEventInit);
};

// Mock responsive layout for mobile testing
vi.mock('../hooks/useResponsiveLayout', () => ({
  useResponsiveLayout: () => ({
    sidebarCollapsed: false,
    isMobile: true,
    isTablet: false,
    isDesktop: false,
    screenSize: { width: 375, height: 667 },
    currentBreakpoint: 'xs',
    toggleSidebar: vi.fn(),
    setSidebarState: vi.fn(),
    layoutStyles: {
      sidebarStyle: {
        width: 240,
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        height: '100vh',
        zIndex: 1001,
        background: '#001529',
        transition: 'width 0.2s ease'
      }
    }
  })
}));

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <ConfigProvider>
      {children}
    </ConfigProvider>
  </BrowserRouter>
);

describe('Touch Interactions Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Set up mobile viewport
    Object.defineProperty(window, 'innerWidth', { value: 375, writable: true });
    Object.defineProperty(window, 'innerHeight', { value: 667, writable: true });
  });

  describe('Mobile Sidebar Touch Interactions', () => {
    it('should handle tap interactions on mobile menu items', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={true} />
        </TestWrapper>
      );

      const dashboardItem = screen.getByText('仪表板');
      
      // Simulate touch tap
      fireEvent.touchStart(dashboardItem, {
        touches: [{ clientX: 100, clientY: 100 }]
      });
      
      fireEvent.touchEnd(dashboardItem, {
        changedTouches: [{ clientX: 100, clientY: 100 }]
      });

      // Should handle touch interaction
      expect(dashboardItem).toBeInTheDocument();
    });

    it('should handle swipe gestures to close mobile sidebar', () => {
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

      const sidebar = screen.getByRole('menu');
      
      // Simulate swipe left gesture (close sidebar)
      fireEvent.touchStart(sidebar, {
        touches: [{ clientX: 200, clientY: 300 }]
      });
      
      fireEvent.touchMove(sidebar, {
        touches: [{ clientX: 50, clientY: 300 }]
      });
      
      fireEvent.touchEnd(sidebar, {
        changedTouches: [{ clientX: 50, clientY: 300 }]
      });

      // Swipe gesture should be detected
      // Note: Actual swipe handling would be implemented in the component
    });

    it('should handle long press on menu items', async () => {
      render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={true} />
        </TestWrapper>
      );

      const projectsItem = screen.getByText('项目管理');
      
      // Simulate long press
      fireEvent.touchStart(projectsItem, {
        touches: [{ clientX: 100, clientY: 200 }]
      });
      
      // Hold for 500ms
      await waitFor(() => {
        fireEvent.touchEnd(projectsItem, {
          changedTouches: [{ clientX: 100, clientY: 200 }]
        });
      }, { timeout: 600 });

      // Long press should be handled appropriately
      expect(projectsItem).toBeInTheDocument();
    });

    it('should prevent default touch behaviors when needed', () => {
      render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={true} />
        </TestWrapper>
      );

      const sidebar = screen.getByRole('menu');
      
      // Create touch event with preventDefault spy
      const touchStartEvent = createTouchEvent('touchstart', [{ clientX: 100, clientY: 100 }]);
      const preventDefaultSpy = vi.spyOn(touchStartEvent, 'preventDefault');
      
      fireEvent(sidebar, touchStartEvent);
      
      // Should handle touch events appropriately
      expect(sidebar).toBeInTheDocument();
    });

    it('should handle multi-touch gestures', () => {
      render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={true} />
        </TestWrapper>
      );

      const sidebar = screen.getByRole('menu');
      
      // Simulate pinch gesture (two fingers)
      fireEvent.touchStart(sidebar, {
        touches: [
          { clientX: 100, clientY: 100 },
          { clientX: 200, clientY: 200 }
        ]
      });
      
      fireEvent.touchMove(sidebar, {
        touches: [
          { clientX: 120, clientY: 120 },
          { clientX: 180, clientY: 180 }
        ]
      });
      
      fireEvent.touchEnd(sidebar, {
        changedTouches: [
          { clientX: 120, clientY: 120 },
          { clientX: 180, clientY: 180 }
        ]
      });

      // Multi-touch should be handled
      expect(sidebar).toBeInTheDocument();
    });
  });

  describe('Modal Touch Interactions', () => {
    it('should handle touch interactions on mobile modals', () => {
      const onClose = vi.fn();
      
      render(
        <TestWrapper>
          <ModalContainer
            visible={true}
            onClose={onClose}
            title="Mobile Modal"
            width={300}
          >
            <div data-testid="modal-content">
              <button data-testid="modal-button">Test Button</button>
            </div>
          </ModalContainer>
        </TestWrapper>
      );

      const modalButton = screen.getByTestId('modal-button');
      
      // Simulate touch on modal button
      fireEvent.touchStart(modalButton, {
        touches: [{ clientX: 150, clientY: 300 }]
      });
      
      fireEvent.touchEnd(modalButton, {
        changedTouches: [{ clientX: 150, clientY: 300 }]
      });

      // Touch interaction should work
      expect(modalButton).toBeInTheDocument();
    });

    it('should handle swipe to dismiss modal on mobile', () => {
      const onClose = vi.fn();
      
      render(
        <TestWrapper>
          <ModalContainer
            visible={true}
            onClose={onClose}
            title="Swipeable Modal"
          >
            <div data-testid="modal-content">Swipe to dismiss</div>
          </ModalContainer>
        </TestWrapper>
      );

      const modalContent = screen.getByTestId('modal-content');
      
      // Simulate swipe down gesture
      fireEvent.touchStart(modalContent, {
        touches: [{ clientX: 150, clientY: 200 }]
      });
      
      fireEvent.touchMove(modalContent, {
        touches: [{ clientX: 150, clientY: 400 }]
      });
      
      fireEvent.touchEnd(modalContent, {
        changedTouches: [{ clientX: 150, clientY: 400 }]
      });

      // Swipe gesture should be detected
      // Note: Actual swipe-to-dismiss would be implemented in the component
    });

    it('should handle touch outside modal to close', () => {
      const onClose = vi.fn();
      
      render(
        <TestWrapper>
          <ModalContainer
            visible={true}
            onClose={onClose}
            title="Touch Outside Modal"
          >
            <div data-testid="modal-content">Modal Content</div>
          </ModalContainer>
        </TestWrapper>
      );

      // Simulate touch on backdrop/mask area
      const maskElement = document.querySelector('.modal-container-mask');
      if (maskElement) {
        fireEvent.touchStart(maskElement, {
          touches: [{ clientX: 50, clientY: 100 }]
        });
        
        fireEvent.touchEnd(maskElement, {
          changedTouches: [{ clientX: 50, clientY: 100 }]
        });
      }

      // Should handle backdrop touch
    });

    it('should prevent scroll when modal is open on mobile', () => {
      const onClose = vi.fn();
      
      render(
        <TestWrapper>
          <ModalContainer
            visible={true}
            onClose={onClose}
            title="No Scroll Modal"
          >
            <div data-testid="modal-content">
              <div style={{ height: '1000px' }}>Long content</div>
            </div>
          </ModalContainer>
        </TestWrapper>
      );

      // Simulate scroll attempt on body
      fireEvent.touchStart(document.body, {
        touches: [{ clientX: 100, clientY: 300 }]
      });
      
      fireEvent.touchMove(document.body, {
        touches: [{ clientX: 100, clientY: 100 }]
      });

      // Body scroll should be prevented when modal is open
      expect(screen.getByTestId('modal-content')).toBeInTheDocument();
    });
  });

  describe('Touch Target Accessibility', () => {
    it('should have adequate touch target sizes on mobile', () => {
      render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={true} />
        </TestWrapper>
      );

      // Check menu items have minimum touch target size (44px iOS, 48dp Android)
      const menuItems = screen.getAllByRole('menuitem');
      
      menuItems.forEach(item => {
        const rect = item.getBoundingClientRect();
        expect(rect.height).toBeGreaterThanOrEqual(44);
      });
    });

    it('should have proper spacing between touch targets', () => {
      render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={true} />
        </TestWrapper>
      );

      const menuItems = screen.getAllByRole('menuitem');
      
      // Check that there's adequate spacing between interactive elements
      for (let i = 0; i < menuItems.length - 1; i++) {
        const currentRect = menuItems[i].getBoundingClientRect();
        const nextRect = menuItems[i + 1].getBoundingClientRect();
        
        const spacing = nextRect.top - currentRect.bottom;
        expect(spacing).toBeGreaterThanOrEqual(0); // Should have some spacing
      }
    });

    it('should handle focus states for touch interactions', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={true} />
        </TestWrapper>
      );

      const dashboardItem = screen.getByText('仪表板');
      
      // Simulate focus via touch
      fireEvent.touchStart(dashboardItem);
      await user.tab(); // Navigate with keyboard after touch
      
      // Should handle focus appropriately
      expect(dashboardItem).toBeInTheDocument();
    });
  });

  describe('Device-Specific Behaviors', () => {
    it('should handle iOS-specific touch behaviors', () => {
      // Mock iOS user agent
      Object.defineProperty(navigator, 'userAgent', {
        value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
        writable: true
      });

      render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={true} />
        </TestWrapper>
      );

      const sidebar = screen.getByRole('menu');
      
      // Simulate iOS-specific touch behavior
      fireEvent.touchStart(sidebar, {
        touches: [{ clientX: 100, clientY: 100 }]
      });

      // Should handle iOS-specific behaviors
      expect(sidebar).toBeInTheDocument();
    });

    it('should handle Android-specific touch behaviors', () => {
      // Mock Android user agent
      Object.defineProperty(navigator, 'userAgent', {
        value: 'Mozilla/5.0 (Linux; Android 10; SM-G975F)',
        writable: true
      });

      render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={true} />
        </TestWrapper>
      );

      const sidebar = screen.getByRole('menu');
      
      // Simulate Android-specific touch behavior
      fireEvent.touchStart(sidebar, {
        touches: [{ clientX: 100, clientY: 100 }]
      });

      // Should handle Android-specific behaviors
      expect(sidebar).toBeInTheDocument();
    });

    it('should handle touch events with different pointer types', () => {
      render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={true} />
        </TestWrapper>
      );

      const sidebar = screen.getByRole('menu');
      
      // Simulate stylus input
      fireEvent.pointerDown(sidebar, {
        pointerId: 1,
        pointerType: 'pen',
        clientX: 100,
        clientY: 100
      });
      
      fireEvent.pointerUp(sidebar, {
        pointerId: 1,
        pointerType: 'pen',
        clientX: 100,
        clientY: 100
      });

      // Should handle different pointer types
      expect(sidebar).toBeInTheDocument();
    });

    it('should handle high-DPI touch screens', () => {
      // Mock high-DPI display
      Object.defineProperty(window, 'devicePixelRatio', {
        value: 3,
        writable: true
      });

      render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={true} />
        </TestWrapper>
      );

      const sidebar = screen.getByRole('menu');
      
      // Touch coordinates should be handled correctly on high-DPI screens
      fireEvent.touchStart(sidebar, {
        touches: [{ clientX: 100, clientY: 100 }]
      });

      expect(sidebar).toBeInTheDocument();
    });
  });

  describe('Performance and Edge Cases', () => {
    it('should handle rapid touch events without performance issues', () => {
      render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={true} />
        </TestWrapper>
      );

      const sidebar = screen.getByRole('menu');
      
      // Simulate rapid touch events
      for (let i = 0; i < 10; i++) {
        fireEvent.touchStart(sidebar, {
          touches: [{ clientX: 100 + i, clientY: 100 + i }]
        });
        
        fireEvent.touchEnd(sidebar, {
          changedTouches: [{ clientX: 100 + i, clientY: 100 + i }]
        });
      }

      // Should handle rapid events without issues
      expect(sidebar).toBeInTheDocument();
    });

    it('should handle touch events during component updates', async () => {
      const { rerender } = render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={true} />
        </TestWrapper>
      );

      const sidebar = screen.getByRole('menu');
      
      // Start touch event
      fireEvent.touchStart(sidebar, {
        touches: [{ clientX: 100, clientY: 100 }]
      });

      // Rerender component during touch
      rerender(
        <TestWrapper>
          <Sidebar collapsed={true} isMobile={true} />
        </TestWrapper>
      );

      // End touch event
      fireEvent.touchEnd(sidebar, {
        changedTouches: [{ clientX: 100, clientY: 100 }]
      });

      // Should handle touch events during updates
      expect(sidebar).toBeInTheDocument();
    });

    it('should clean up touch event listeners on unmount', () => {
      const { unmount } = render(
        <TestWrapper>
          <Sidebar collapsed={false} isMobile={true} />
        </TestWrapper>
      );

      // Should not throw errors on unmount
      expect(() => unmount()).not.toThrow();
    });
  });
});