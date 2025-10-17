import { ResponsiveLayoutConfig } from '../types/layout';

// 响应式布局配置常量
export const LAYOUT_CONFIG: ResponsiveLayoutConfig = {
  // 断点配置
  breakpoints: {
    xs: 0,      // 手机竖屏
    sm: 576,    // 手机横屏
    md: 768,    // 平板竖屏
    lg: 992,    // 平板横屏/小屏笔记本
    xl: 1200,   // 桌面显示器
    xxl: 1600   // 大屏显示器
  },
  
  // 固定区域尺寸（不随分辨率变化）
  fixedAreas: {
    header: { 
      height: 0 // Header-less design
    },
    sidebar: { 
      width: 240,
      collapsedWidth: 80
    },
    footer: { 
      height: 48 
    }
  },
  
  // 动态区域配置（随分辨率调整）
  dynamicAreas: {
    workArea: { 
      minWidth: 800, 
      flex: 1 
    },
    projectPanel: { 
      minWidth: 300, 
      maxWidth: 400 
    },
    visualArea: { 
      minWidth: 600, 
      flex: 2 
    }
  },
  
  // 内容间距配置
  contentSpacing: {
    padding: 24,
    margin: 20
  }
};

// 断点名称映射
export const BREAKPOINT_NAMES = {
  0: 'xs',
  576: 'sm', 
  768: 'md',
  992: 'lg',
  1200: 'xl',
  1600: 'xxl'
} as const;

// 设备类型判断阈值
export const DEVICE_THRESHOLDS = {
  MOBILE_MAX: 767,
  TABLET_MIN: 768,
  TABLET_MAX: 1199,
  DESKTOP_MIN: 1200
} as const;

// 布局调试配置
export const DEBUG_CONFIG = {
  enabled: false, // 关闭调试模式
  showGrid: false,
  showBreakpoints: false,
  showDimensions: false,
  overlayOpacity: 0.1
} as const;