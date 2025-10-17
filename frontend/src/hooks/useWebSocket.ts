/**
 * WebSocket Hook for real-time task monitoring
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketMessage, TaskWebSocketMessage } from '../types/task';

interface UseWebSocketOptions {
  userId: string;
  onTaskUpdate?: (message: TaskWebSocketMessage) => void;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export const useWebSocket = (options: UseWebSocketOptions) => {
  const {
    userId,
    onTaskUpdate,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [subscribedTasks, setSubscribedTasks] = useState<Set<string>>(new Set());
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('connecting');
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/${userId}`;
    
    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setIsConnected(true);
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
        
        // 启动心跳
        startHeartbeat();
        
        onConnect?.();
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          // 处理任务更新消息
          if (message.type === 'task_update') {
            onTaskUpdate?.(message as TaskWebSocketMessage);
          }
          
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);
        setConnectionStatus('disconnected');
        stopHeartbeat();
        
        onDisconnect?.();
        
        // 自动重连
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      wsRef.current.onerror = (error) => {
        setConnectionStatus('error');
        onError?.(error);
      };

    } catch (error) {
      setConnectionStatus('error');
      console.error('Failed to create WebSocket connection:', error);
    }
  }, [userId, onConnect, onDisconnect, onError, onMessage, onTaskUpdate, reconnectInterval, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    stopHeartbeat();
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  const subscribeToTask = useCallback((taskId: string) => {
    const success = sendMessage({
      type: 'subscribe_task',
      task_id: taskId
    });
    
    if (success) {
      setSubscribedTasks(prev => new Set([...prev, taskId]));
    }
    
    return success;
  }, [sendMessage]);

  const unsubscribeFromTask = useCallback((taskId: string) => {
    const success = sendMessage({
      type: 'unsubscribe_task',
      task_id: taskId
    });
    
    if (success) {
      setSubscribedTasks(prev => {
        const newSet = new Set(prev);
        newSet.delete(taskId);
        return newSet;
      });
    }
    
    return success;
  }, [sendMessage]);

  const getSubscriptions = useCallback(() => {
    return sendMessage({
      type: 'get_subscriptions'
    });
  }, [sendMessage]);

  const startHeartbeat = useCallback(() => {
    heartbeatIntervalRef.current = setInterval(() => {
      sendMessage({ type: 'heartbeat' });
    }, 30000); // 30秒心跳
  }, [sendMessage]);

  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  // 自动连接
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      stopHeartbeat();
    };
  }, [stopHeartbeat]);

  return {
    isConnected,
    connectionStatus,
    subscribedTasks: Array.from(subscribedTasks),
    connect,
    disconnect,
    sendMessage,
    subscribeToTask,
    unsubscribeFromTask,
    getSubscriptions
  };
};