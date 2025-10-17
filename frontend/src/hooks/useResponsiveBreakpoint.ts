import { useState, useEffect, useCallback, useMemo } from 'react';
import { DEVICE_THRESHOLDS, LAYOUT_CONFIG } from '../config/layout';

export interface ResponsiveBreakpoint {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isLargeDesktop: boolean;
  screenWidth: number;
  screenHeight: number;
  breakpoint: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl';
  orientation: 'portrait' | 'landscape';
  devicePixelRatio: number;
  isRetina: boolean;
  // 新增的响应式工具方法
  getResponsiveValue: <T>(values: ResponsiveValues<T>) => T;
  getSpacing: (size: 'xs' | 'sm' | 'md' | 'lg' | 'xl') => number;
  getFontSize: (size: 'xs' | 'sm' | 'md' | 'lg' | 'xl') => string;
  getGridCols: () => number;
}

export interface ResponsiveValues<T> {
  xs?: T;
  sm?: T;
  md?: T;
  lg?: T;
  xl?: T;
  xxl?: T;
  default: T;
}

// 响应式间距映射
const SPACING_MAP = {
  xs: { xs: 4, sm: 6, md: 8, lg: 12, xl: 16 },
  sm: { xs: 6, sm: 8, md: 12, lg: 16, xl: 20 },
  md: { xs: 8, sm: 12, md: 16, lg: 20, xl: 24 },
  lg: { xs: 12, sm: 16, md: 20, lg: 24, xl: 32 },
  xl: { xs: 16, sm: 20, md: 24, lg: 32, xl: 40 },
  xxl: { xs: 20, sm: 24, md: 32, lg: 40, xl: 48 }
};

// 响应式字体大小映射
const FONT_SIZE_MAP = {
  xs: { xs: '10px', sm: '11px', md: '12px', lg: '13px', xl: '14px' },
  sm: { xs: '11px', sm: '12px', md: '13px', lg: '14px', xl: '15px' },
  md: { xs: '12px', sm: '13px', md: '14px', lg: '15px', xl: '16px' },
  lg: { xs: '14px', sm: '15px', md: '16px', lg: '18px', xl: '20px' },
  xl: { xs: '16px', sm: '18px', md: '20px', lg: '22px', xl: '24px' },
  xxl: { xs: '18px', sm: '20px', md: '22px', lg: '24px', xl: '28px' }
};

// 响应式网格列数映射
const GRID_COLS_MAP = {
  xs: 1,
  sm: 2,
  md: 3,
  lg: 4,
  xl: 6,
  xxl: 8
};

/**
 * 增强的响应式断点Hook，提供完整的响应式设计支持
 */
export const useResponsiveBreakpoint = (): ResponsiveBreakpoint => {
  const [screenSize, setScreenSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 1200,
    height: typeof window !== 'undefined' ? window.innerHeight : 800
  });

  const [devicePixelRatio, setDevicePixelRatio] = useState(
    typeof window !== 'undefined' ? window.devicePixelRatio : 1
  );

  useEffect(() => {
    const handleResize = () => {
      setScreenSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
      setDevicePixelRatio(window.devicePixelRatio);
    };

    let timeoutId: NodeJS.Timeout;
    const debouncedResize = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(handleResize, 100);
    };

    // 监听窗口大小变化
    window.addEventListener('resize', debouncedResize);
    
    // 监听设备像素比变化（用户缩放）
    const mediaQuery = window.matchMedia('(resolution: 1dppx)');
    const handlePixelRatioChange = () => {
      setDevicePixelRatio(window.devicePixelRatio);
    };
    
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handlePixelRatioChange);
    } else {
      // 兼容旧版浏览器
      mediaQuery.addListener(handlePixelRatioChange);
    }

    return () => {
      window.removeEventListener('resize', debouncedResize);
      clearTimeout(timeoutId);
      
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', handlePixelRatioChange);
      } else {
        mediaQuery.removeListener(handlePixelRatioChange);
      }
    };
  }, []);

  // 计算当前断点
  const breakpoint = useMemo((): ResponsiveBreakpoint['breakpoint'] => {
    const width = screenSize.width;
    if (width >= LAYOUT_CONFIG.breakpoints.xxl) return 'xxl';
    if (width >= LAYOUT_CONFIG.breakpoints.xl) return 'xl';
    if (width >= LAYOUT_CONFIG.breakpoints.lg) return 'lg';
    if (width >= LAYOUT_CONFIG.breakpoints.md) return 'md';
    if (width >= LAYOUT_CONFIG.breakpoints.sm) return 'sm';
    return 'xs';
  }, [screenSize.width]);

  // 设备类型判断
  const deviceTypes = useMemo(() => ({
    isMobile: screenSize.width <= DEVICE_THRESHOLDS.MOBILE_MAX,
    isTablet: screenSize.width >= DEVICE_THRESHOLDS.TABLET_MIN && 
              screenSize.width <= DEVICE_THRESHOLDS.TABLET_MAX,
    isDesktop: screenSize.width >= DEVICE_THRESHOLDS.DESKTOP_MIN,
    isLargeDesktop: screenSize.width >= LAYOUT_CONFIG.breakpoints.xxl
  }), [screenSize.width]);

  // 屏幕方向
  const orientation = useMemo((): 'portrait' | 'landscape' => {
    return screenSize.width > screenSize.height ? 'landscape' : 'portrait';
  }, [screenSize.width, screenSize.height]);

  // 是否为高分辨率屏幕
  const isRetina = useMemo(() => devicePixelRatio >= 2, [devicePixelRatio]);

  // 获取响应式值的方法
  const getResponsiveValue = useCallback(<T>(values: ResponsiveValues<T>): T => {
    return values[breakpoint] ?? values.default;
  }, [breakpoint]);

  // 获取响应式间距的方法
  const getSpacing = useCallback((size: 'xs' | 'sm' | 'md' | 'lg' | 'xl'): number => {
    return SPACING_MAP[breakpoint]?.[size] ?? SPACING_MAP.md[size];
  }, [breakpoint]);

  // 获取响应式字体大小的方法
  const getFontSize = useCallback((size: 'xs' | 'sm' | 'md' | 'lg' | 'xl'): string => {
    return FONT_SIZE_MAP[breakpoint]?.[size] ?? FONT_SIZE_MAP.md[size];
  }, [breakpoint]);

  // 获取响应式网格列数的方法
  const getGridCols = useCallback((): number => {
    return GRID_COLS_MAP[breakpoint] ?? GRID_COLS_MAP.md;
  }, [breakpoint]);

  return {
    ...deviceTypes,
    screenWidth: screenSize.width,
    screenHeight: screenSize.height,
    breakpoint,
    orientation,
    devicePixelRatio,
    isRetina,
    getResponsiveValue,
    getSpacing,
    getFontSize,
    getGridCols
  };
};

// 响应式样式生成工具
export const createResponsiveStyles = (
  breakpoint: ResponsiveBreakpoint['breakpoint'],
  isMobile: boolean
) => ({
  // 容器样式
  container: {
    padding: isMobile ? '12px' : '24px',
    maxWidth: '100%',
    margin: '0 auto'
  },
  
  // 卡片样式
  card: {
    borderRadius: isMobile ? '8px' : '12px',
    padding: isMobile ? '16px' : '24px',
    marginBottom: isMobile ? '12px' : '16px'
  },
  
  // 按钮样式
  button: {
    height: isMobile ? '36px' : '40px',
    fontSize: isMobile ? '14px' : '16px',
    padding: isMobile ? '0 12px' : '0 16px'
  },
  
  // 文本样式
  text: {
    title: {
      fontSize: isMobile ? '18px' : '24px',
      lineHeight: isMobile ? '24px' : '32px'
    },
    body: {
      fontSize: isMobile ? '14px' : '16px',
      lineHeight: isMobile ? '20px' : '24px'
    },
    caption: {
      fontSize: isMobile ? '12px' : '14px',
      lineHeight: isMobile ? '16px' : '20px'
    }
  },
  
  // 间距样式
  spacing: {
    xs: isMobile ? '4px' : '8px',
    sm: isMobile ? '8px' : '12px',
    md: isMobile ? '12px' : '16px',
    lg: isMobile ? '16px' : '24px',
    xl: isMobile ? '24px' : '32px'
  }
});

export default useResponsiveBreakpoint;