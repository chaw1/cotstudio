/**
 * 懒加载工具
 * 实现组件懒加载和代码分割
 * 需求: 4.1, 4.2, 4.3
 */
import React, { Suspense, ComponentType } from 'react';
import { Spin } from 'antd';

// 加载状态组件
const LoadingSpinner: React.FC<{ size?: 'small' | 'default' | 'large' }> = ({ 
  size = 'default' 
}) => (
  <div 
    style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '200px',
      width: '100%'
    }}
  >
    <Spin size={size} />
  </div>
);

// 页面级加载组件
const PageLoadingSpinner: React.FC = () => (
  <div 
    style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '60vh',
      width: '100%'
    }}
  >
    <Spin size="large" />
  </div>
);

// 懒加载高阶组件
export const withLazyLoading = <P extends object>(
  Component: ComponentType<P>,
  fallback?: React.ReactNode
) => {
  const LazyComponent = React.forwardRef<any, P>((props, ref) => (
    <Suspense fallback={fallback || <LoadingSpinner />}>
      <Component {...props} ref={ref} />
    </Suspense>
  ));

  LazyComponent.displayName = `withLazyLoading(${Component.displayName || Component.name})`;
  
  return LazyComponent;
};

// 页面级懒加载高阶组件
export const withPageLazyLoading = <P extends object>(
  Component: ComponentType<P>
) => {
  return withLazyLoading(Component, <PageLoadingSpinner />);
};

// 预加载函数
export const preloadComponent = (componentImport: () => Promise<any>) => {
  // 在空闲时间预加载组件
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(() => {
      componentImport();
    });
  } else {
    // 降级到setTimeout
    setTimeout(() => {
      componentImport();
    }, 100);
  }
};

// 路由级别的预加载
export const preloadRouteComponent = (
  routePath: string,
  componentImport: () => Promise<any>
) => {
  // 当鼠标悬停在导航链接上时预加载
  const handleMouseEnter = () => {
    preloadComponent(componentImport);
  };

  // 返回事件处理器
  return { onMouseEnter: handleMouseEnter };
};

// 懒加载组件工厂
export const createLazyComponent = (
  importFn: () => Promise<{ default: ComponentType<any> }>,
  fallback?: React.ReactNode
) => {
  const LazyComponent = React.lazy(importFn);
  
  return React.forwardRef<any, any>((props, ref) => (
    <Suspense fallback={fallback || <LoadingSpinner />}>
      <LazyComponent {...props} ref={ref} />
    </Suspense>
  ));
};

// 页面级懒加载组件工厂
export const createLazyPageComponent = (
  importFn: () => Promise<{ default: ComponentType<any> }>
) => {
  return createLazyComponent(importFn, <PageLoadingSpinner />);
};

// 条件懒加载 - 只在满足条件时才加载组件
export const createConditionalLazyComponent = (
  importFn: () => Promise<{ default: ComponentType<any> }>,
  condition: () => boolean,
  fallback?: React.ReactNode
) => {
  return React.forwardRef<any, any>((props, ref) => {
    if (!condition()) {
      return fallback || null;
    }

    const LazyComponent = React.lazy(importFn);
    
    return (
      <Suspense fallback={fallback || <LoadingSpinner />}>
        <LazyComponent {...props} ref={ref} />
      </Suspense>
    );
  });
};

// 批量预加载
export const batchPreloadComponents = (
  componentImports: Array<() => Promise<any>>,
  delay = 100
) => {
  componentImports.forEach((importFn, index) => {
    setTimeout(() => {
      preloadComponent(importFn);
    }, delay * index);
  });
};

export default {
  withLazyLoading,
  withPageLazyLoading,
  preloadComponent,
  preloadRouteComponent,
  createLazyComponent,
  createLazyPageComponent,
  createConditionalLazyComponent,
  batchPreloadComponents,
  LoadingSpinner,
  PageLoadingSpinner
};