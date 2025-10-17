/**
 * 性能监控工具
 * 监控和优化前端性能
 * 需求: 4.1, 4.2, 4.3
 */
import React from 'react';

// 性能指标接口
interface PerformanceMetrics {
  // 页面加载时间
  pageLoadTime: number;
  // 首次内容绘制时间
  firstContentfulPaint: number;
  // 最大内容绘制时间
  largestContentfulPaint: number;
  // 首次输入延迟
  firstInputDelay: number;
  // 累积布局偏移
  cumulativeLayoutShift: number;
  // 内存使用情况
  memoryUsage?: {
    usedJSHeapSize: number;
    totalJSHeapSize: number;
    jsHeapSizeLimit: number;
  };
}

// 性能监控类
class PerformanceMonitor {
  private metrics: Partial<PerformanceMetrics> = {};
  private observers: PerformanceObserver[] = [];
  private isMonitoring = false;

  constructor() {
    this.initializeMonitoring();
  }

  // 初始化性能监控
  private initializeMonitoring() {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) {
      console.warn('Performance monitoring not supported in this environment');
      return;
    }

    this.isMonitoring = true;
    this.observeNavigationTiming();
    this.observePaintTiming();
    this.observeLargestContentfulPaint();
    this.observeFirstInputDelay();
    this.observeCumulativeLayoutShift();
    this.monitorMemoryUsage();
  }

  // 监控导航时间
  private observeNavigationTiming() {
    if ('performance' in window && 'getEntriesByType' in performance) {
      const navigationEntries = performance.getEntriesByType('navigation') as PerformanceNavigationTiming[];
      if (navigationEntries.length > 0) {
        const entry = navigationEntries[0];
        this.metrics.pageLoadTime = entry.loadEventEnd - entry.navigationStart;
      }
    }
  }

  // 监控绘制时间
  private observePaintTiming() {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.name === 'first-contentful-paint') {
            this.metrics.firstContentfulPaint = entry.startTime;
          }
        }
      });
      observer.observe({ entryTypes: ['paint'] });
      this.observers.push(observer);
    } catch (error) {
      console.warn('Paint timing observation failed:', error);
    }
  }

  // 监控最大内容绘制
  private observeLargestContentfulPaint() {
    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        this.metrics.largestContentfulPaint = lastEntry.startTime;
      });
      observer.observe({ entryTypes: ['largest-contentful-paint'] });
      this.observers.push(observer);
    } catch (error) {
      console.warn('LCP observation failed:', error);
    }
  }

  // 监控首次输入延迟
  private observeFirstInputDelay() {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.metrics.firstInputDelay = (entry as any).processingStart - entry.startTime;
        }
      });
      observer.observe({ entryTypes: ['first-input'] });
      this.observers.push(observer);
    } catch (error) {
      console.warn('FID observation failed:', error);
    }
  }

  // 监控累积布局偏移
  private observeCumulativeLayoutShift() {
    try {
      let clsValue = 0;
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value;
            this.metrics.cumulativeLayoutShift = clsValue;
          }
        }
      });
      observer.observe({ entryTypes: ['layout-shift'] });
      this.observers.push(observer);
    } catch (error) {
      console.warn('CLS observation failed:', error);
    }
  }

  // 监控内存使用
  private monitorMemoryUsage() {
    if ('memory' in performance) {
      const updateMemoryUsage = () => {
        const memory = (performance as any).memory;
        this.metrics.memoryUsage = {
          usedJSHeapSize: memory.usedJSHeapSize,
          totalJSHeapSize: memory.totalJSHeapSize,
          jsHeapSizeLimit: memory.jsHeapSizeLimit,
        };
      };

      updateMemoryUsage();
      // 每30秒更新一次内存使用情况
      setInterval(updateMemoryUsage, 30000);
    }
  }

  // 获取当前性能指标
  getMetrics(): Partial<PerformanceMetrics> {
    return { ...this.metrics };
  }

  // 记录自定义性能标记
  mark(name: string) {
    if ('performance' in window && 'mark' in performance) {
      performance.mark(name);
    }
  }

  // 测量两个标记之间的时间
  measure(name: string, startMark: string, endMark?: string) {
    if ('performance' in window && 'measure' in performance) {
      try {
        if (endMark) {
          performance.measure(name, startMark, endMark);
        } else {
          performance.measure(name, startMark);
        }
        
        const measures = performance.getEntriesByName(name, 'measure');
        return measures.length > 0 ? measures[measures.length - 1].duration : 0;
      } catch (error) {
        console.warn('Performance measure failed:', error);
        return 0;
      }
    }
    return 0;
  }

  // 清理性能条目
  clearMarks(name?: string) {
    if ('performance' in window && 'clearMarks' in performance) {
      performance.clearMarks(name);
    }
  }

  clearMeasures(name?: string) {
    if ('performance' in window && 'clearMeasures' in performance) {
      performance.clearMeasures(name);
    }
  }

  // 停止监控
  disconnect() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
    this.isMonitoring = false;
  }

  // 生成性能报告
  generateReport(): string {
    const metrics = this.getMetrics();
    const report = {
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      metrics,
      recommendations: this.generateRecommendations(metrics),
    };

    return JSON.stringify(report, null, 2);
  }

  // 生成性能建议
  private generateRecommendations(metrics: Partial<PerformanceMetrics>): string[] {
    const recommendations: string[] = [];

    if (metrics.pageLoadTime && metrics.pageLoadTime > 3000) {
      recommendations.push('页面加载时间过长，建议优化资源加载');
    }

    if (metrics.firstContentfulPaint && metrics.firstContentfulPaint > 2500) {
      recommendations.push('首次内容绘制时间过长，建议优化关键渲染路径');
    }

    if (metrics.largestContentfulPaint && metrics.largestContentfulPaint > 4000) {
      recommendations.push('最大内容绘制时间过长，建议优化主要内容加载');
    }

    if (metrics.firstInputDelay && metrics.firstInputDelay > 100) {
      recommendations.push('首次输入延迟过长，建议优化JavaScript执行');
    }

    if (metrics.cumulativeLayoutShift && metrics.cumulativeLayoutShift > 0.25) {
      recommendations.push('累积布局偏移过大，建议优化页面布局稳定性');
    }

    if (metrics.memoryUsage) {
      const memoryUsageRatio = metrics.memoryUsage.usedJSHeapSize / metrics.memoryUsage.jsHeapSizeLimit;
      if (memoryUsageRatio > 0.8) {
        recommendations.push('内存使用率过高，建议检查内存泄漏');
      }
    }

    return recommendations;
  }
}

// 组件性能监控装饰器
export function withPerformanceMonitoring<P extends object>(
  Component: React.ComponentType<P>,
  componentName?: string
) {
  const name = componentName || Component.displayName || Component.name;
  
  return React.forwardRef<any, P>((props, ref) => {
    const renderStartTime = React.useRef<number>(0);
    
    React.useEffect(() => {
      // 组件挂载时记录
      performanceMonitor.mark(`${name}-mount-start`);
      
      return () => {
        // 组件卸载时记录
        performanceMonitor.mark(`${name}-unmount`);
        performanceMonitor.measure(`${name}-lifecycle`, `${name}-mount-start`, `${name}-unmount`);
      };
    }, []);

    React.useLayoutEffect(() => {
      renderStartTime.current = performance.now();
    });

    React.useEffect(() => {
      const renderTime = performance.now() - renderStartTime.current;
      if (renderTime > 16) { // 超过一帧的时间
        console.warn(`Component ${name} render time: ${renderTime.toFixed(2)}ms`);
      }
    });

    return <Component {...props} ref={ref} />;
  });
}

// React Hook for performance monitoring
export function usePerformanceMonitoring(componentName: string) {
  const renderCount = React.useRef(0);
  const renderTimes = React.useRef<number[]>([]);

  React.useEffect(() => {
    renderCount.current += 1;
  });

  const startRender = React.useCallback(() => {
    performanceMonitor.mark(`${componentName}-render-start`);
  }, [componentName]);

  const endRender = React.useCallback(() => {
    performanceMonitor.mark(`${componentName}-render-end`);
    const duration = performanceMonitor.measure(
      `${componentName}-render`,
      `${componentName}-render-start`,
      `${componentName}-render-end`
    );
    
    renderTimes.current.push(duration);
    
    // 保持最近100次渲染记录
    if (renderTimes.current.length > 100) {
      renderTimes.current.shift();
    }
  }, [componentName]);

  const getStats = React.useCallback(() => {
    const times = renderTimes.current;
    if (times.length === 0) return null;

    const avg = times.reduce((sum, time) => sum + time, 0) / times.length;
    const max = Math.max(...times);
    const min = Math.min(...times);

    return {
      renderCount: renderCount.current,
      averageRenderTime: avg,
      maxRenderTime: max,
      minRenderTime: min,
      recentRenderTimes: times.slice(-10), // 最近10次
    };
  }, []);

  return {
    startRender,
    endRender,
    getStats,
  };
}

// 全局性能监控实例
export const performanceMonitor = new PerformanceMonitor();

// 性能优化工具
export const performanceUtils = {
  // 防抖函数
  debounce: <T extends (...args: any[]) => any>(
    func: T,
    wait: number,
    immediate = false
  ): T => {
    let timeout: NodeJS.Timeout | null = null;
    
    return ((...args: Parameters<T>) => {
      const later = () => {
        timeout = null;
        if (!immediate) func(...args);
      };
      
      const callNow = immediate && !timeout;
      
      if (timeout) clearTimeout(timeout);
      timeout = setTimeout(later, wait);
      
      if (callNow) func(...args);
    }) as T;
  },

  // 节流函数
  throttle: <T extends (...args: any[]) => any>(
    func: T,
    limit: number
  ): T => {
    let inThrottle: boolean;
    
    return ((...args: Parameters<T>) => {
      if (!inThrottle) {
        func(...args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    }) as T;
  },

  // 空闲时执行
  requestIdleCallback: (callback: () => void, timeout = 5000) => {
    if ('requestIdleCallback' in window) {
      return window.requestIdleCallback(callback, { timeout });
    } else {
      return setTimeout(callback, 1);
    }
  },

  // 批量DOM更新
  batchDOMUpdates: (updates: (() => void)[]) => {
    performanceUtils.requestIdleCallback(() => {
      updates.forEach(update => update());
    });
  },

  // 图片懒加载
  createImageLazyLoader: () => {
    if ('IntersectionObserver' in window) {
      return new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement;
            const src = img.dataset.src;
            if (src) {
              img.src = src;
              img.removeAttribute('data-src');
            }
          }
        });
      });
    }
    return null;
  },
};

export default performanceMonitor;