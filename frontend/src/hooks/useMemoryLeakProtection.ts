import { useEffect, useRef, useCallback } from 'react';

export interface MemoryLeakProtectionConfig {
  /** 组件名称，用于调试 */
  componentName?: string;
  /** 是否启用调试日志 */
  enableDebugLog?: boolean;
  /** 最大允许的定时器数量 */
  maxTimers?: number;
  /** 最大允许的事件监听器数量 */
  maxEventListeners?: number;
}

export interface CleanupFunction {
  (): void;
}

export interface UseMemoryLeakProtectionReturn {
  /** 注册清理函数 */
  registerCleanup: (cleanup: CleanupFunction) => void;
  /** 注册定时器 */
  registerTimer: (timer: NodeJS.Timeout) => void;
  /** 注册事件监听器 */
  registerEventListener: (
    target: EventTarget,
    event: string,
    listener: EventListener,
    options?: boolean | AddEventListenerOptions
  ) => void;
  /** 手动清理所有资源 */
  cleanup: () => void;
  /** 获取当前资源统计 */
  getResourceStats: () => {
    timers: number;
    eventListeners: number;
    cleanupFunctions: number;
  };
}

/**
 * 内存泄漏防护Hook
 * 自动管理和清理组件的资源，防止内存泄漏
 */
export function useMemoryLeakProtection(
  config: MemoryLeakProtectionConfig = {}
): UseMemoryLeakProtectionReturn {
  const {
    componentName = 'UnknownComponent',
    enableDebugLog = false,
    maxTimers = 10,
    maxEventListeners = 20,
  } = config;

  // 资源追踪
  const cleanupFunctionsRef = useRef<Set<CleanupFunction>>(new Set());
  const timersRef = useRef<Set<NodeJS.Timeout>>(new Set());
  const eventListenersRef = useRef<Set<{
    target: EventTarget;
    event: string;
    listener: EventListener;
    options?: boolean | AddEventListenerOptions;
  }>>(new Set());

  const mountedRef = useRef(true);

  // 调试日志
  const debugLog = useCallback((message: string, data?: any) => {
    if (enableDebugLog) {
      console.log(`[MemoryLeakProtection:${componentName}] ${message}`, data || '');
    }
  }, [enableDebugLog, componentName]);

  // 警告日志
  const warnLog = useCallback((message: string, data?: any) => {
    console.warn(`[MemoryLeakProtection:${componentName}] ${message}`, data || '');
  }, [componentName]);

  // 注册清理函数
  const registerCleanup = useCallback((cleanup: CleanupFunction) => {
    if (!mountedRef.current) {
      debugLog('Component unmounted, skipping cleanup registration');
      return;
    }

    cleanupFunctionsRef.current.add(cleanup);
    debugLog('Registered cleanup function', { total: cleanupFunctionsRef.current.size });
  }, [debugLog]);

  // 注册定时器
  const registerTimer = useCallback((timer: NodeJS.Timeout) => {
    if (!mountedRef.current) {
      debugLog('Component unmounted, clearing timer immediately');
      clearTimeout(timer);
      return;
    }

    timersRef.current.add(timer);
    debugLog('Registered timer', { total: timersRef.current.size });

    // 检查定时器数量限制
    if (timersRef.current.size > maxTimers) {
      warnLog(`Too many timers registered (${timersRef.current.size}), possible memory leak`);
    }
  }, [debugLog, warnLog, maxTimers]);

  // 注册事件监听器
  const registerEventListener = useCallback((
    target: EventTarget,
    event: string,
    listener: EventListener,
    options?: boolean | AddEventListenerOptions
  ) => {
    if (!mountedRef.current) {
      debugLog('Component unmounted, skipping event listener registration');
      return;
    }

    // 添加事件监听器
    target.addEventListener(event, listener, options);

    // 记录用于清理
    const listenerInfo = { target, event, listener, options };
    eventListenersRef.current.add(listenerInfo);
    
    debugLog('Registered event listener', { 
      event, 
      target: target.constructor.name,
      total: eventListenersRef.current.size 
    });

    // 检查事件监听器数量限制
    if (eventListenersRef.current.size > maxEventListeners) {
      warnLog(`Too many event listeners registered (${eventListenersRef.current.size}), possible memory leak`);
    }
  }, [debugLog, warnLog, maxEventListeners]);

  // 清理所有资源
  const cleanup = useCallback(() => {
    debugLog('Starting cleanup', {
      timers: timersRef.current.size,
      eventListeners: eventListenersRef.current.size,
      cleanupFunctions: cleanupFunctionsRef.current.size,
    });

    // 清理定时器
    timersRef.current.forEach(timer => {
      try {
        clearTimeout(timer);
        clearInterval(timer);
      } catch (error) {
        warnLog('Error clearing timer', error);
      }
    });
    timersRef.current.clear();

    // 清理事件监听器
    eventListenersRef.current.forEach(({ target, event, listener, options }) => {
      try {
        target.removeEventListener(event, listener, options);
      } catch (error) {
        warnLog('Error removing event listener', { event, error });
      }
    });
    eventListenersRef.current.clear();

    // 执行清理函数
    cleanupFunctionsRef.current.forEach(cleanup => {
      try {
        cleanup();
      } catch (error) {
        warnLog('Error executing cleanup function', error);
      }
    });
    cleanupFunctionsRef.current.clear();

    debugLog('Cleanup completed');
  }, [debugLog, warnLog]);

  // 获取资源统计
  const getResourceStats = useCallback(() => ({
    timers: timersRef.current.size,
    eventListeners: eventListenersRef.current.size,
    cleanupFunctions: cleanupFunctionsRef.current.size,
  }), []);

  // 组件卸载时自动清理
  useEffect(() => {
    mountedRef.current = true;
    debugLog('Component mounted');

    return () => {
      mountedRef.current = false;
      debugLog('Component unmounting, starting cleanup');
      cleanup();
    };
  }, [cleanup, debugLog]);

  // 定期检查资源使用情况（仅在开发环境）
  useEffect(() => {
    if (!enableDebugLog || process.env.NODE_ENV === 'production') {
      return;
    }

    const checkInterval = setInterval(() => {
      const stats = getResourceStats();
      if (stats.timers > 0 || stats.eventListeners > 0 || stats.cleanupFunctions > 0) {
        debugLog('Resource usage check', stats);
      }
    }, 30000); // 每30秒检查一次

    return () => {
      clearInterval(checkInterval);
    };
  }, [enableDebugLog, getResourceStats, debugLog]);

  return {
    registerCleanup,
    registerTimer,
    registerEventListener,
    cleanup,
    getResourceStats,
  };
}