import { useState, useEffect, useCallback } from 'react';

export interface NetworkStatus {
  /** 是否在线 */
  isOnline: boolean;
  /** 网络连接类型 */
  connectionType: string | null;
  /** 网络状态变化时间 */
  lastChanged: Date | null;
  /** 是否支持网络状态检测 */
  isSupported: boolean;
}

export interface UseNetworkStatusReturn extends NetworkStatus {
  /** 手动检查网络状态 */
  checkStatus: () => void;
}

/**
 * 网络状态检测Hook
 * 监控网络连接状态变化，用于优化数据刷新策略
 */
export function useNetworkStatus(): UseNetworkStatusReturn {
  const [networkStatus, setNetworkStatus] = useState<NetworkStatus>({
    isOnline: navigator.onLine,
    connectionType: null,
    lastChanged: null,
    isSupported: 'onLine' in navigator,
  });

  // 获取连接类型信息
  const getConnectionType = useCallback((): string | null => {
    // 检查是否支持Network Information API
    const connection = (navigator as any).connection || 
                      (navigator as any).mozConnection || 
                      (navigator as any).webkitConnection;
    
    if (connection) {
      return connection.effectiveType || connection.type || 'unknown';
    }
    
    return null;
  }, []);

  // 更新网络状态
  const updateNetworkStatus = useCallback((isOnline: boolean) => {
    const connectionType = getConnectionType();
    
    setNetworkStatus(prev => ({
      ...prev,
      isOnline,
      connectionType,
      lastChanged: new Date(),
    }));
  }, [getConnectionType]);

  // 手动检查网络状态
  const checkStatus = useCallback(() => {
    updateNetworkStatus(navigator.onLine);
  }, [updateNetworkStatus]);

  // 监听网络状态变化
  useEffect(() => {
    if (!networkStatus.isSupported) {
      return;
    }

    const handleOnline = () => {
      console.log('Network: Online');
      updateNetworkStatus(true);
    };

    const handleOffline = () => {
      console.log('Network: Offline');
      updateNetworkStatus(false);
    };

    // 监听连接类型变化
    const handleConnectionChange = () => {
      console.log('Network: Connection type changed');
      checkStatus();
    };

    // 添加事件监听器
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // 监听连接信息变化（如果支持）
    const connection = (navigator as any).connection || 
                      (navigator as any).mozConnection || 
                      (navigator as any).webkitConnection;
    
    if (connection) {
      connection.addEventListener('change', handleConnectionChange);
    }

    // 初始化连接类型
    const initialConnectionType = getConnectionType();
    if (initialConnectionType !== networkStatus.connectionType) {
      setNetworkStatus(prev => ({
        ...prev,
        connectionType: initialConnectionType,
      }));
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      
      if (connection) {
        connection.removeEventListener('change', handleConnectionChange);
      }
    };
  }, [networkStatus.isSupported, networkStatus.connectionType, updateNetworkStatus, checkStatus, getConnectionType]);

  return {
    ...networkStatus,
    checkStatus,
  };
}