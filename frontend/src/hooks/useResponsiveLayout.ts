import { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  ResponsiveLayoutState, 
  ScreenSize, 
  LayoutStyles,
  LayoutDebugInfo 
} from '../types/layout';
import { 
  LAYOUT_CONFIG, 
  DEVICE_THRESHOLDS,
  DEBUG_CONFIG 
} from '../config/layout';

/**
 * 获取当前屏幕尺寸
 */
const getScreenSize = (): ScreenSize => ({
  width: window.innerWidth,
  height: window.innerHeight
});

/**
 * 根据屏幕宽度确定当前断点
 */
const getCurrentBreakpoint = (width: number): string => {
  const breakpoints = LAYOUT_CONFIG.breakpoints;
  
  if (width >= breakpoints.xxl) return 'xxl';
  if (width >= breakpoints.xl) return 'xl';
  if (width >= breakpoints.lg) return 'lg';
  if (width >= breakpoints.md) return 'md';
  if (width >= breakpoints.sm) return 'sm';
  return 'xs';
};

/**
 * 计算布局样式 - 针对无头部设计优化
 */
const calculateLayoutStyles = (
  screenSize: ScreenSize, 
  breakpoint: string,
  sidebarCollapsed: boolean
): LayoutStyles => {
  const { fixedAreas, contentSpacing } = LAYOUT_CONFIG;
  const { width, height } = screenSize;
  
  // 侧边栏宽度
  const sidebarWidth = sidebarCollapsed 
    ? fixedAreas.sidebar.collapsedWidth 
    : fixedAreas.sidebar.width;
  
  // 内容区域可用高度 - 无头部设计，使用全屏高度
  const contentHeight = height; // Full viewport height, no header or footer deduction
  
  // 根据断点调整间距
  const responsivePadding = breakpoint === 'xs' || breakpoint === 'sm' 
    ? contentSpacing.padding / 2 
    : contentSpacing.padding;
  
  const responsiveMargin = breakpoint === 'xs' || breakpoint === 'sm' 
    ? contentSpacing.margin / 2 
    : contentSpacing.margin;

  return {
    containerStyle: {
      minHeight: '100vh',
      background: '#f5f5f5',
      display: 'flex',
      flexDirection: 'column'
    },
    
    // 移除头部样式 - 无头部设计
    headerStyle: {
      height: 0, // No header in new design
      display: 'none' // Hide header completely
    },
    
    sidebarStyle: {
      width: sidebarWidth,
      position: 'fixed' as const,
      left: 0,
      top: 0,
      bottom: 0,
      height: '100vh', // Full viewport height
      zIndex: 1001,
      background: '#001529',
      transition: 'width 0.2s ease'
    },
    
    bodyStyle: {
      marginLeft: sidebarWidth,
      marginTop: 0, // No header margin
      minHeight: '100vh', // Full viewport height
      transition: 'margin-left 0.2s ease',
      display: 'flex',
      flexDirection: 'column' as const
    },
    
    workAreaStyle: {
      flex: 1,
      padding: `${responsivePadding}px`,
      margin: `${responsiveMargin}px`,
      background: '#ffffff',
      borderRadius: breakpoint === 'xs' ? '8px' : '12px',
      minHeight: `calc(100vh - ${responsiveMargin * 2}px)`, // Full height minus margins
      boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02)',
      border: '1px solid #f0f0f0',
      overflow: 'auto'
    },
    
    footerStyle: {
      height: 0, // No footer in header-less design
      display: 'none' // Hide footer completely
    }
  };
};

/**
 * 响应式布局Hook
 */
export const useResponsiveLayout = (initialCollapsed: boolean = false) => {
  const [screenSize, setScreenSize] = useState<ScreenSize>(getScreenSize);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(initialCollapsed);
  
  // 当前断点
  const currentBreakpoint = useMemo(() => 
    getCurrentBreakpoint(screenSize.width), 
    [screenSize.width]
  );
  
  // 设备类型判断
  const deviceType = useMemo(() => ({
    isMobile: screenSize.width <= DEVICE_THRESHOLDS.MOBILE_MAX,
    isTablet: screenSize.width >= DEVICE_THRESHOLDS.TABLET_MIN && 
              screenSize.width <= DEVICE_THRESHOLDS.TABLET_MAX,
    isDesktop: screenSize.width >= DEVICE_THRESHOLDS.DESKTOP_MIN
  }), [screenSize.width]);
  
  // 计算布局样式
  const layoutStyles = useMemo(() => 
    calculateLayoutStyles(screenSize, currentBreakpoint, sidebarCollapsed),
    [screenSize, currentBreakpoint, sidebarCollapsed]
  );
  
  // 处理窗口大小变化
  const handleResize = useCallback(() => {
    const newSize = getScreenSize();
    setScreenSize(newSize);
    
    // 在小屏幕上自动折叠侧边栏
    if (newSize.width <= DEVICE_THRESHOLDS.MOBILE_MAX && !sidebarCollapsed) {
      setSidebarCollapsed(true);
    }
  }, [sidebarCollapsed]);
  
  // 切换侧边栏状态
  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed(prev => !prev);
  }, []);
  
  // 设置侧边栏状态
  const setSidebarState = useCallback((collapsed: boolean) => {
    setSidebarCollapsed(collapsed);
  }, []);
  
  // 监听窗口大小变化
  useEffect(() => {
    let timeoutId: number;
    
    const debouncedResize = () => {
      clearTimeout(timeoutId);
      timeoutId = window.setTimeout(handleResize, 150);
    };
    
    window.addEventListener('resize', debouncedResize);
    
    return () => {
      window.removeEventListener('resize', debouncedResize);
      clearTimeout(timeoutId);
    };
  }, [handleResize]);
  
  // 调试信息
  const debugInfo: LayoutDebugInfo = useMemo(() => ({
    screenSize,
    breakpoint: currentBreakpoint,
    layoutDimensions: {
      header: LAYOUT_CONFIG.fixedAreas.header,
      sidebar: {
        width: sidebarCollapsed 
          ? LAYOUT_CONFIG.fixedAreas.sidebar.collapsedWidth 
          : LAYOUT_CONFIG.fixedAreas.sidebar.width,
        collapsedWidth: LAYOUT_CONFIG.fixedAreas.sidebar.collapsedWidth
      },
      footer: LAYOUT_CONFIG.fixedAreas.footer,
      content: LAYOUT_CONFIG.contentSpacing
    },
    calculatedStyles: layoutStyles
  }), [screenSize, currentBreakpoint, sidebarCollapsed, layoutStyles]);
  
  // 响应式布局状态
  const layoutState: ResponsiveLayoutState = {
    screenSize,
    currentBreakpoint,
    ...deviceType,
    layoutConfig: LAYOUT_CONFIG,
    layoutStyles,
    sidebarCollapsed
  };
  
  return {
    // 状态
    ...layoutState,
    
    // 操作方法
    toggleSidebar,
    setSidebarState,
    
    // 调试信息（仅开发环境）
    ...(DEBUG_CONFIG.enabled && { debugInfo })
  };
};

export default useResponsiveLayout;