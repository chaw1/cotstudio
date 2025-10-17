/**
 * 性能优化组件包装器
 * 提供各种性能优化功能
 * 需求: 4.1, 4.2, 4.3
 */
import React, { memo, useMemo, useCallback, useRef, useEffect } from 'react';
import { performanceUtils, usePerformanceMonitoring } from '../../utils/performanceMonitor';

// 优化的组件属性
interface OptimizedComponentProps {
  children: React.ReactNode;
  // 组件名称，用于性能监控
  name?: string;
  // 是否启用性能监控
  enableMonitoring?: boolean;
  // 是否启用memo优化
  enableMemo?: boolean;
  // 自定义比较函数
  areEqual?: (prevProps: any, nextProps: any) => boolean;
  // 防抖延迟
  debounceDelay?: number;
  // 节流限制
  throttleLimit?: number;
  // 是否在空闲时渲染
  renderOnIdle?: boolean;
}

// 深度比较函数
const deepEqual = (obj1: any, obj2: any): boolean => {
  if (obj1 === obj2) return true;
  
  if (obj1 == null || obj2 == null) return false;
  
  if (typeof obj1 !== typeof obj2) return false;
  
  if (typeof obj1 !== 'object') return obj1 === obj2;
  
  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);
  
  if (keys1.length !== keys2.length) return false;
  
  for (const key of keys1) {
    if (!keys2.includes(key)) return false;
    if (!deepEqual(obj1[key], obj2[key])) return false;
  }
  
  return true;
};

// 优化的组件包装器
export const OptimizedComponent: React.FC<OptimizedComponentProps> = memo(({
  children,
  name = 'OptimizedComponent',
  enableMonitoring = false,
  enableMemo = true,
  areEqual,
  debounceDelay,
  throttleLimit,
  renderOnIdle = false,
}) => {
  const renderRef = useRef<() => void>();
  const [shouldRender, setShouldRender] = React.useState(!renderOnIdle);
  
  // 性能监控
  const { startRender, endRender, getStats } = usePerformanceMonitoring(name);
  
  // 开始渲染监控
  if (enableMonitoring) {
    startRender();
  }
  
  // 空闲时渲染
  useEffect(() => {
    if (renderOnIdle && !shouldRender) {
      performanceUtils.requestIdleCallback(() => {
        setShouldRender(true);
      });
    }
  }, [renderOnIdle, shouldRender]);
  
  // 防抖渲染
  const debouncedRender = useMemo(() => {
    if (debounceDelay) {
      return performanceUtils.debounce(() => {
        setShouldRender(true);
      }, debounceDelay);
    }
    return null;
  }, [debounceDelay]);
  
  // 节流渲染
  const throttledRender = useMemo(() => {
    if (throttleLimit) {
      return performanceUtils.throttle(() => {
        setShouldRender(true);
      }, throttleLimit);
    }
    return null;
  }, [throttleLimit]);
  
  // 处理渲染逻辑
  useEffect(() => {
    if (debouncedRender) {
      debouncedRender();
    } else if (throttledRender) {
      throttledRender();
    }
  }, [debouncedRender, throttledRender]);
  
  // 结束渲染监控
  useEffect(() => {
    if (enableMonitoring) {
      endRender();
      
      // 定期输出性能统计
      const stats = getStats();
      if (stats && stats.renderCount % 10 === 0) {
        console.log(`${name} Performance Stats:`, stats);
      }
    }
  });
  
  if (!shouldRender) {
    return null;
  }
  
  return <>{children}</>;
}, (prevProps, nextProps) => {
  // 使用自定义比较函数或深度比较
  if (prevProps.areEqual) {
    return prevProps.areEqual(prevProps, nextProps);
  }
  
  if (prevProps.enableMemo) {
    return deepEqual(prevProps, nextProps);
  }
  
  return false;
});

// 高阶组件版本
export const withOptimization = <P extends object>(
  Component: React.ComponentType<P>,
  options: Omit<OptimizedComponentProps, 'children'> = {}
) => {
  const OptimizedWrapper = memo(
    React.forwardRef<any, P>((props, ref) => (
      <OptimizedComponent {...options}>
        <Component {...props} ref={ref} />
      </OptimizedComponent>
    )),
    options.areEqual
  );
  
  OptimizedWrapper.displayName = `withOptimization(${Component.displayName || Component.name})`;
  
  return OptimizedWrapper;
};

// 列表项优化组件
interface OptimizedListItemProps {
  children: React.ReactNode;
  itemKey: string | number;
  isVisible?: boolean;
  onVisibilityChange?: (isVisible: boolean) => void;
}

export const OptimizedListItem: React.FC<OptimizedListItemProps> = memo(({
  children,
  itemKey,
  isVisible = true,
  onVisibilityChange,
}) => {
  const elementRef = useRef<HTMLDivElement>(null);
  const observerRef = useRef<IntersectionObserver>();
  
  useEffect(() => {
    if (!elementRef.current || !onVisibilityChange) return;
    
    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          onVisibilityChange(entry.isIntersecting);
        });
      },
      { threshold: 0.1 }
    );
    
    observerRef.current.observe(elementRef.current);
    
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [onVisibilityChange]);
  
  if (!isVisible) {
    return <div ref={elementRef} style={{ height: '1px' }} />;
  }
  
  return (
    <div ref={elementRef}>
      {children}
    </div>
  );
}, (prevProps, nextProps) => {
  return (
    prevProps.itemKey === nextProps.itemKey &&
    prevProps.isVisible === nextProps.isVisible
  );
});

// 图片懒加载组件
interface LazyImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  placeholder?: string;
  onLoad?: () => void;
  onError?: () => void;
}

export const LazyImage: React.FC<LazyImageProps> = memo(({
  src,
  placeholder,
  onLoad,
  onError,
  ...props
}) => {
  const [isLoaded, setIsLoaded] = React.useState(false);
  const [isInView, setIsInView] = React.useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  
  useEffect(() => {
    if (!imgRef.current) return;
    
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true);
            observer.disconnect();
          }
        });
      },
      { threshold: 0.1 }
    );
    
    observer.observe(imgRef.current);
    
    return () => observer.disconnect();
  }, []);
  
  const handleLoad = useCallback(() => {
    setIsLoaded(true);
    onLoad?.();
  }, [onLoad]);
  
  const handleError = useCallback(() => {
    onError?.();
  }, [onError]);
  
  return (
    <div ref={imgRef} style={{ position: 'relative' }}>
      {!isLoaded && placeholder && (
        <img
          src={placeholder}
          {...props}
          style={{
            ...props.style,
            filter: 'blur(5px)',
            transition: 'filter 0.3s',
          }}
        />
      )}
      {isInView && (
        <img
          src={src}
          {...props}
          onLoad={handleLoad}
          onError={handleError}
          style={{
            ...props.style,
            opacity: isLoaded ? 1 : 0,
            transition: 'opacity 0.3s',
            position: isLoaded ? 'static' : 'absolute',
            top: 0,
            left: 0,
          }}
        />
      )}
    </div>
  );
});

export default OptimizedComponent;