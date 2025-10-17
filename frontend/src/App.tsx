import React, { useEffect } from 'react';
import { RouterProvider } from 'react-router-dom';
import { ConfigProvider, theme, App as AntdApp } from 'antd';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import zhCN from 'antd/locale/zh_CN';
import router from './router';
import ErrorBoundary from './components/ErrorBoundary';
import { globalErrorHandler } from './utils/errorHandler';
import { QueryProvider } from './providers/QueryProvider';
import { performanceMonitor } from './utils/performanceMonitor';
import { withOptimization } from './components/Performance';
import { logContrastReport } from './utils/colorContrast';
import useAppMessage from './hooks/useAppMessage';
import './App.css';
import './styles/visual-enhancements.css';
import './styles/spacing-utilities.css';

// 现代化主题配置 - 基于设计文档的新色彩系统
const appTheme = {
  algorithm: theme.defaultAlgorithm,
  token: {
    // 主色调 - 现代蓝色系统
    colorPrimary: '#1677ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorInfo: '#1677ff',
    
    // 边框和分割线
    colorBorder: '#d9d9d9',
    colorBorderSecondary: '#f0f0f0',
    
    // 背景色系统
    colorBgContainer: '#ffffff',
    colorBgElevated: '#ffffff',
    colorBgLayout: '#f5f5f5',
    colorBgBase: '#ffffff',
    
    // 文字颜色系统
    colorText: '#262626',
    colorTextSecondary: '#8c8c8c',
    colorTextTertiary: '#bfbfbf',
    colorTextQuaternary: '#d9d9d9',
    
    // 圆角系统
    borderRadius: 8,
    borderRadiusLG: 12,
    borderRadiusSM: 6,
    borderRadiusXS: 4,
    
    // 字体系统
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif',
    fontSize: 14,
    fontSizeLG: 16,
    fontSizeSM: 12,
    fontSizeXL: 18,
    fontSizeHeading1: 24,
    fontSizeHeading2: 20,
    fontSizeHeading3: 18,
    fontSizeHeading4: 16,
    
    // 间距系统 (基于8px网格)
    marginXS: 8,
    marginSM: 12,
    margin: 16,
    marginMD: 20,
    marginLG: 24,
    marginXL: 32,
    marginXXL: 48,
    
    paddingXS: 8,
    paddingSM: 12,
    padding: 16,
    paddingMD: 20,
    paddingLG: 24,
    paddingXL: 32,
    paddingXXL: 48,
    
    // 阴影系统
    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)',
    boxShadowSecondary: '0 6px 16px 0 rgba(0, 0, 0, 0.08), 0 3px 6px -4px rgba(0, 0, 0, 0.12), 0 9px 28px 8px rgba(0, 0, 0, 0.05)',
    boxShadowTertiary: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02)',
    
    // 控件高度系统
    controlHeight: 36,
    controlHeightLG: 40,
    controlHeightSM: 28,
    controlHeightXS: 24,
    
    // 线条宽度
    lineWidth: 1,
    lineWidthBold: 2,
    
    // 动画时长
    motionDurationFast: '0.1s',
    motionDurationMid: '0.2s',
    motionDurationSlow: '0.3s',
  },
  components: {
    Layout: {
      headerBg: 'transparent', // No header in new design
      siderBg: '#001529', // 深色导航栏背景
      bodyBg: '#f5f5f5',
      headerHeight: 0, // Header-less design
      headerPadding: '0',
      siderWidth: 240,
      triggerBg: '#001529',
      triggerColor: '#ffffff',
    },
    Menu: {
      itemBg: 'transparent',
      itemSelectedBg: 'rgba(255, 255, 255, 0.1)',
      itemSelectedColor: '#ffffff',
      itemHoverBg: 'rgba(255, 255, 255, 0.08)',
      itemColor: 'rgba(255, 255, 255, 0.85)',
      itemActiveBg: 'rgba(255, 255, 255, 0.15)',
      subMenuItemBg: 'transparent',
      darkItemBg: 'transparent',
      darkItemSelectedBg: 'rgba(255, 255, 255, 0.1)',
      darkItemSelectedColor: '#ffffff',
      darkItemHoverBg: 'rgba(255, 255, 255, 0.08)',
      darkItemColor: 'rgba(255, 255, 255, 0.85)',
    },
    Card: {
      borderRadiusLG: 12,
      boxShadowTertiary: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02)',
      paddingLG: 24,
      padding: 16,
      paddingSM: 12,
    },
    Button: {
      borderRadius: 8,
      controlHeight: 36,
      controlHeightLG: 40,
      controlHeightSM: 28,
      paddingInline: 16,
      paddingInlineLG: 20,
      paddingInlineSM: 12,
      fontWeight: 500,
    },
    Input: {
      borderRadius: 8,
      controlHeight: 36,
      paddingInline: 12,
      fontSize: 14,
    },
    Table: {
      borderRadiusLG: 12,
      headerBg: '#fafafa',
      headerColor: '#262626',
      headerSortActiveBg: '#f0f0f0',
      bodySortBg: '#fafafa',
      rowHoverBg: '#f5f5f5',
      padding: 16,
      paddingSM: 12,
    },
    Modal: {
      borderRadiusLG: 12,
      paddingLG: 24,
      padding: 16,
      paddingSM: 12,
    },
    Drawer: {
      borderRadiusLG: 12,
      paddingLG: 24,
      padding: 16,
    },
    Tabs: {
      borderRadius: 8,
      padding: 16,
      paddingSM: 12,
    },
    Form: {
      itemMarginBottom: 16,
      verticalLabelPadding: '0 0 8px',
    },
  },
};

// 内部组件，用于初始化App消息实例
const AppContent: React.FC = () => {
  // 初始化App消息实例
  useAppMessage();
  
  return (
    <DndProvider backend={HTML5Backend}>
      <RouterProvider router={router} />
    </DndProvider>
  );
};

function App() {
  useEffect(() => {
    // 初始化全局错误处理器（它会自动设置）
    globalErrorHandler;
    
    // 开始性能监控
    performanceMonitor.mark('app-start');
    
    // 在开发环境中验证颜色对比度（已禁用以避免循环日志）
    // if (process.env.NODE_ENV === 'development') {
    //   // 延迟执行以确保样式已加载
    //   setTimeout(() => {
    //     logContrastReport();
    //   }, 1000);
    // }
    
    return () => {
      // 应用卸载时生成性能报告
      if (process.env.NODE_ENV === 'development') {
        console.log('Performance Report:', performanceMonitor.generateReport());
      }
    };
  }, []);

  return (
    <ErrorBoundary>
      <QueryProvider>
        <ConfigProvider 
          locale={zhCN} 
          theme={appTheme}
        >
          <AntdApp>
            <AppContent />
          </AntdApp>
        </ConfigProvider>
      </QueryProvider>
    </ErrorBoundary>
  );
}

// 使用性能优化包装App组件
const OptimizedApp = withOptimization(App, {
  name: 'App',
  enableMonitoring: process.env.NODE_ENV === 'development',
  enableMemo: true,
});

export default OptimizedApp;