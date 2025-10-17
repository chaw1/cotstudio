import { useEffect, useRef, useCallback, useState } from 'react';

export interface RefreshConfig {
  /** 基础刷新间隔（毫秒），默认30秒 */
  baseInterval?: number;
  /** 最大刷新间隔（毫秒），默认5分钟 */
  maxInterval?: number;
  /** 错误时的退避倍数，默认2 */
  backoffMultiplier?: number;
  /** 最大重试次数，超过后停止自动刷新，默认10 */
  maxRetries?: number;
  /** 是否在页面不可见时暂停刷新，默认true */
  pauseOnHidden?: boolean;
  /** 是否在网络离线时暂停刷新，默认true */
  pauseOnOffline?: boolean;
  /** 成功后是否重置错误计数，默认true */
  resetOnSuccess?: boolean;
}

export interface RefreshState {
  /** 当前错误次数 */
  errorCount: number;
  /** 当前刷新间隔 */
  currentInterval: number;
  /** 是否正在刷新 */
  isRefreshing: boolean;
  /** 是否已暂停 */
  isPaused: boolean;
  /** 最后刷新时间 */
  lastRefreshTime: Date | null;
  /** 下次刷新时间 */
  nextRefreshTime: Date | null;
}

export interface UseDataRefreshReturn {
  /** 当前刷新状态 */
  refreshState: RefreshState;
  /** 手动触发刷新 */
  refresh: () => Promise<void>;
  /** 暂停自动刷新 */
  pause: () => void;
  /** 恢复自动刷新 */
  resume: () => void;
  /** 重置错误计数和间隔 */
  reset: () => void;
  /** 报告刷新成功 */
  reportSuccess: () => void;
  /** 报告刷新错误 */
  reportError: (error?: Error) => void;
}

/**
 * 数据刷新优化Hook
 * 提供智能刷新间隔调整、页面可见性检测、内存泄漏防护等功能
 */
export function useDataRefresh(
  refreshFunction: () => Promise<void>,
  config: RefreshConfig = {}
): UseDataRefreshReturn {
  const {
    baseInterval = 30000, // 30秒
    maxInterval = 300000, // 5分钟
    backoffMultiplier = 2,
    maxRetries = 10,
    pauseOnHidden = true,
    pauseOnOffline = true,
    resetOnSuccess = true,
  } = config;

  // 状态管理
  const [refreshState, setRefreshState] = useState<RefreshState>({
    errorCount: 0,
    currentInterval: baseInterval,
    isRefreshing: false,
    isPaused: false,
    lastRefreshTime: null,
    nextRefreshTime: null,
  });

  // Refs用于避免闭包问题
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);
  const refreshFunctionRef = useRef(refreshFunction);
  const configRef = useRef(config);
  const stateRef = useRef(refreshState);

  // 更新refs
  useEffect(() => {
    refreshFunctionRef.current = refreshFunction;
    configRef.current = config;
    stateRef.current = refreshState;
  }, [refreshFunction, config, refreshState]);

  // 计算下次刷新间隔
  const calculateNextInterval = useCallback((errorCount: number): number => {
    if (errorCount === 0) return baseInterval;
    
    const exponentialBackoff = baseInterval * Math.pow(backoffMultiplier, errorCount);
    return Math.min(exponentialBackoff, maxInterval);
  }, [baseInterval, backoffMultiplier, maxInterval]);

  // 检查是否应该暂停刷新
  const shouldPause = useCallback((): boolean => {
    // 检查页面可见性
    if (pauseOnHidden && document.visibilityState === 'hidden') {
      return true;
    }

    // 检查网络状态
    if (pauseOnOffline && !navigator.onLine) {
      return true;
    }

    // 检查是否超过最大重试次数
    if (stateRef.current.errorCount >= maxRetries) {
      return true;
    }

    return false;
  }, [pauseOnHidden, pauseOnOffline, maxRetries]);

  // 清理定时器
  const clearTimer = useCallback(() => {
    if (intervalRef.current) {
      clearTimeout(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // 设置下次刷新
  const scheduleNextRefresh = useCallback(() => {
    if (!mountedRef.current) return;

    clearTimer();

    const currentState = stateRef.current;
    
    // 检查是否应该暂停
    if (shouldPause() || currentState.isPaused) {
      setRefreshState(prev => ({
        ...prev,
        nextRefreshTime: null,
      }));
      return;
    }

    const nextRefreshTime = new Date(Date.now() + currentState.currentInterval);
    
    setRefreshState(prev => ({
      ...prev,
      nextRefreshTime,
    }));

    intervalRef.current = setTimeout(() => {
      if (mountedRef.current && !shouldPause() && !stateRef.current.isPaused) {
        refresh();
      }
    }, currentState.currentInterval);
  }, [shouldPause, clearTimer]);

  // 执行刷新
  const refresh = useCallback(async () => {
    if (!mountedRef.current || stateRef.current.isRefreshing) {
      return;
    }

    setRefreshState(prev => ({
      ...prev,
      isRefreshing: true,
      lastRefreshTime: new Date(),
    }));

    try {
      await refreshFunctionRef.current();
      
      if (mountedRef.current) {
        // 刷新成功，重置错误计数（如果配置允许）
        const shouldReset = configRef.current.resetOnSuccess ?? resetOnSuccess;
        const newErrorCount = shouldReset ? 0 : stateRef.current.errorCount;
        const newInterval = calculateNextInterval(newErrorCount);

        setRefreshState(prev => ({
          ...prev,
          errorCount: newErrorCount,
          currentInterval: newInterval,
          isRefreshing: false,
        }));

        // 安排下次刷新
        setTimeout(scheduleNextRefresh, 0);
      }
    } catch (error) {
      console.error('Data refresh failed:', error);
      
      if (mountedRef.current) {
        reportError(error as Error);
      }
    }
  }, [calculateNextInterval, scheduleNextRefresh, resetOnSuccess]);

  // 报告刷新成功
  const reportSuccess = useCallback(() => {
    if (!mountedRef.current) return;

    const shouldReset = configRef.current.resetOnSuccess ?? resetOnSuccess;
    const newErrorCount = shouldReset ? 0 : stateRef.current.errorCount;
    const newInterval = calculateNextInterval(newErrorCount);

    setRefreshState(prev => ({
      ...prev,
      errorCount: newErrorCount,
      currentInterval: newInterval,
      isRefreshing: false,
    }));

    scheduleNextRefresh();
  }, [calculateNextInterval, scheduleNextRefresh, resetOnSuccess]);

  // 报告刷新错误
  const reportError = useCallback((error?: Error) => {
    if (!mountedRef.current) return;

    const newErrorCount = stateRef.current.errorCount + 1;
    const newInterval = calculateNextInterval(newErrorCount);

    setRefreshState(prev => ({
      ...prev,
      errorCount: newErrorCount,
      currentInterval: newInterval,
      isRefreshing: false,
    }));

    // 如果未超过最大重试次数，安排下次刷新
    if (newErrorCount < maxRetries) {
      setTimeout(scheduleNextRefresh, 0);
    } else {
      console.warn(`Max retries (${maxRetries}) reached, stopping auto refresh`);
      setRefreshState(prev => ({
        ...prev,
        nextRefreshTime: null,
      }));
    }
  }, [calculateNextInterval, scheduleNextRefresh, maxRetries]);

  // 暂停自动刷新
  const pause = useCallback(() => {
    clearTimer();
    setRefreshState(prev => ({
      ...prev,
      isPaused: true,
      nextRefreshTime: null,
    }));
  }, [clearTimer]);

  // 恢复自动刷新
  const resume = useCallback(() => {
    setRefreshState(prev => ({
      ...prev,
      isPaused: false,
    }));
    
    // 延迟调度以确保状态更新
    setTimeout(scheduleNextRefresh, 0);
  }, [scheduleNextRefresh]);

  // 重置状态
  const reset = useCallback(() => {
    clearTimer();
    setRefreshState({
      errorCount: 0,
      currentInterval: baseInterval,
      isRefreshing: false,
      isPaused: false,
      lastRefreshTime: null,
      nextRefreshTime: null,
    });
    
    // 延迟调度以确保状态更新
    setTimeout(scheduleNextRefresh, 0);
  }, [clearTimer, baseInterval, scheduleNextRefresh]);

  // 页面可见性变化处理
  useEffect(() => {
    if (!pauseOnHidden) return;

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        // 页面变为可见，立即刷新一次然后恢复正常调度
        if (!stateRef.current.isPaused && mountedRef.current) {
          refresh();
        }
      } else {
        // 页面变为隐藏，清除定时器
        clearTimer();
        setRefreshState(prev => ({
          ...prev,
          nextRefreshTime: null,
        }));
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [pauseOnHidden, refresh, clearTimer]);

  // 网络状态变化处理
  useEffect(() => {
    if (!pauseOnOffline) return;

    const handleOnline = () => {
      // 网络恢复，立即刷新一次
      if (!stateRef.current.isPaused && mountedRef.current) {
        refresh();
      }
    };

    const handleOffline = () => {
      // 网络断开，清除定时器
      clearTimer();
      setRefreshState(prev => ({
        ...prev,
        nextRefreshTime: null,
      }));
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [pauseOnOffline, refresh, clearTimer]);

  // 组件挂载时开始刷新
  useEffect(() => {
    mountedRef.current = true;
    
    // 立即执行一次刷新
    refresh();

    return () => {
      // 组件卸载时清理
      mountedRef.current = false;
      clearTimer();
    };
  }, [refresh, clearTimer]);

  // 返回接口
  return {
    refreshState,
    refresh,
    pause,
    resume,
    reset,
    reportSuccess,
    reportError,
  };
}