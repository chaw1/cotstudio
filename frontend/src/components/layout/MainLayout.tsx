import React, { useEffect, useRef, useState, useMemo } from 'react';
import { Layout } from 'antd';
import Sidebar from './Sidebar';
import LayoutDebugger from './LayoutDebugger';
import { useResponsiveLayout } from '../../hooks/useResponsiveLayout';
import { useAccessibility, ScreenReaderOnly } from '../../hooks/useAccessibility';
import '../../styles/responsive-layout.css';
import '../../styles/accessibility.css';

const { Content } = Layout;

interface MainLayoutProps {
  children: React.ReactNode;
  enableDebugger?: boolean;
}

const MainLayout: React.FC<MainLayoutProps> = ({ 
  children, 
  enableDebugger = (import.meta as any).env?.DEV === true 
}) => {
  const {
    sidebarCollapsed,
    toggleSidebar,
    currentBreakpoint,
    isMobile,
    isTablet,
    isDesktop,
    debugInfo
  } = useResponsiveLayout();

  const { createSkipLink, announceToScreenReader } = useAccessibility();
  const mainContentRef = useRef<HTMLDivElement>(null);

  // 键盘快捷键支持和无障碍功能
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ctrl/Cmd + B 切换侧边栏
      if ((event.ctrlKey || event.metaKey) && event.key === 'b') {
        event.preventDefault();
        toggleSidebar();
        announceToScreenReader(
          sidebarCollapsed ? '侧边栏已展开' : '侧边栏已折叠'
        );
      }
      
      // Alt + M 跳转到主内容
      if (event.altKey && event.key === 'm') {
        event.preventDefault();
        if (mainContentRef.current) {
          mainContentRef.current.focus();
          announceToScreenReader('已跳转到主内容区域');
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [toggleSidebar, sidebarCollapsed, announceToScreenReader]);

  // 设置页面标题和语言
  useEffect(() => {
    document.documentElement.lang = 'zh-CN';
    if (!document.title.includes('COT Studio')) {
      document.title = 'COT Studio - 智能文档处理平台';
    }
  }, []);

  // Calculate sidebar width based on collapsed state and device type
  const sidebarWidth = useMemo(() => {
    if (isMobile && sidebarCollapsed) return 0;
    return sidebarCollapsed ? 80 : 240;
  }, [sidebarCollapsed, isMobile]);

  // Calculate content area dimensions for header-less design
  const contentAreaStyles = useMemo(() => {
    const baseStyles = {
      marginLeft: isMobile ? 0 : sidebarWidth, // No margin on mobile, full margin on desktop
      marginTop: 0, // No header in new design
      minHeight: '100vh', // Full viewport height
      height: '100vh', // Explicit height for proper layout
      background: '#f5f5f5',
      transition: 'margin-left 0.2s ease',
      position: 'relative' as const,
      overflow: 'auto' as const, // Allow scrolling within content area
      display: 'flex',
      flexDirection: 'column' as const
    };

    // Responsive padding based on screen size and device type
    const padding = (() => {
      if (isMobile) return '16px';
      if (isTablet) return '20px';
      return '24px';
    })();

    return {
      ...baseStyles,
      padding
    };
  }, [sidebarWidth, isMobile, isTablet]);

  // Sidebar styles with improved positioning for header-less design
  const sidebarStyles = useMemo(() => ({
    position: 'fixed' as const,
    left: 0,
    top: 0,
    width: sidebarWidth,
    height: '100vh', // Full viewport height
    zIndex: 1001,
    background: '#001529',
    borderRight: 'none',
    transform: isMobile && sidebarCollapsed ? 'translateX(-100%)' : 'translateX(0)',
    transition: 'all 0.2s ease',
    boxShadow: isMobile ? '2px 0 12px 0 rgba(0, 0, 0, 0.25)' : '2px 0 8px 0 rgba(29, 35, 41, 0.15)',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column' as const
  }), [sidebarWidth, isMobile, sidebarCollapsed]);

  return (
    <>
      {/* Skip links for keyboard navigation */}
      <ScreenReaderOnly>
        <nav aria-label="快速导航">
          <a href="#main-content" className="skip-link">
            跳转到主内容 (Alt+M)
          </a>
          <a href="#sidebar-navigation" className="skip-link">
            跳转到导航菜单
          </a>
        </nav>
      </ScreenReaderOnly>

      <div 
        className="main-layout-container" 
        style={{ minHeight: '100vh' }}
        role="application"
        aria-label="COT Studio 应用程序"
      >
        {/* Sidebar - Full height without header */}
        <div
          style={sidebarStyles}
          className="main-layout-sidebar debug-sidebar"
        >
          <Sidebar 
            collapsed={sidebarCollapsed}
            breakpoint={currentBreakpoint}
            isMobile={isMobile}
            onMobileClose={toggleSidebar}
          />
        </div>

        {/* Main content area - Header-less design with full height */}
        <main
          id="main-content"
          ref={mainContentRef}
          role="main"
          aria-label="主要内容区域"
          tabIndex={-1}
          style={contentAreaStyles}
          className="main-layout-content debug-content landmark-main"
        >
          <div className="fade-in responsive-content work-area-adaptive" style={{ flex: 1, overflow: 'auto' }}>
            {children}
          </div>
        </main>

        {/* Mobile overlay for sidebar - Full screen coverage */}
        {isMobile && !sidebarCollapsed && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              width: '100vw',
              height: '100vh',
              background: 'rgba(0, 0, 0, 0.4)',
              zIndex: 999,
              backdropFilter: 'blur(3px)',
              WebkitBackdropFilter: 'blur(3px)' // Safari support
            }}
            className="mobile-overlay"
            onClick={toggleSidebar}
            onTouchEnd={toggleSidebar} // Touch support
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleSidebar();
              }
            }}
            aria-label="关闭侧边栏遮罩层，按回车键或空格键关闭"
            role="button"
            tabIndex={0}
          />
        )}
      </div>

      {/* Layout debugger (development only) */}
      {enableDebugger && debugInfo && (
        <LayoutDebugger debugInfo={debugInfo} />
      )}
    </>
  );
};

export default MainLayout;