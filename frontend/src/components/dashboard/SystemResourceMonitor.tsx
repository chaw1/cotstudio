import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Card, Progress, Space, Typography, Alert, Spin, Button } from 'antd';
import { 
  DesktopOutlined as CpuOutlined, 
  DatabaseOutlined, 
  HddOutlined, 
  CloudServerOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined,
  LoginOutlined,
  UserOutlined,
  GlobalOutlined
} from '@ant-design/icons';
import { apiClient, ApiError } from '../../utils/apiClient';
import { useResponsiveBreakpoint } from '../../hooks/useResponsiveBreakpoint';

const { Text } = Typography;

interface GPU {
  index: number;
  name: string;
  driver_version: string;
  memory_total_mb: number;
  memory_used_mb: number;
  memory_free_mb: number;
  utilization_percent: number;
  temperature_c: number;
}

interface SystemResources {
  timestamp: string;
  cpu: {
    percent: number;
    count: number;
    count_logical: number;
  };
  memory: {
    used: number;
    total: number;
    percent: number;
    available: number;
  };
  disk: {
    used: number;
    total: number;
    percent: number;
    free: number;
  };
  process: {
    pid: number;
    memory_percent: number;
    cpu_percent: number;
    num_threads: number;
    create_time: number;
  };
  network: {
    bytes_sent: number;
    bytes_recv: number;
    packets_sent: number;
    packets_recv: number;
  };
  database: {
    connections: number;
  };
  queue: {
    pending: number;
    active: number;
    failed: number;
    completed: number;
  };
  gpu?: {
    available: boolean;
    count?: number;
    gpus?: GPU[];
    cuda_version?: string;
    cudnn_version?: string;
    total_memory_gb?: number;
    used_memory_gb?: number;
    memory_percent?: number;
    error?: string;
  };
  system: {
    boot_time: number;
    uptime: number;
  };
  login_history?: {
    last_login_time: string;
    last_login_ip: string;
    last_login_location: string;
    recent_logins: number;
    active_sessions: number;
  };
}

interface SystemHealth {
  status: 'healthy' | 'moderate' | 'warning' | 'critical' | 'unknown';
  timestamp: string;
  summary: {
    cpu_percent: number;
    memory_percent: number;
    disk_percent: number;
    database_connections: number;
    queue_pending: number;
  };
}

const SystemResourceMonitor: React.FC = () => {
  const [resources, setResources] = useState<SystemResources | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  
  const { isMobile } = useResponsiveBreakpoint();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  // 获取系统资源数据
  const fetchSystemResources = useCallback(async () => {
    try {
      const result = await apiClient.get<{
        success: boolean;
        data: SystemResources;
      }>('/system/resources');
      
      if (mountedRef.current && result.success) {
        setResources(result.data);
        setLastUpdate(new Date());
        setError(null);
        setRetryCount(0);
      }
    } catch (err) {
      console.error('Error fetching system resources:', err);
      
      if (mountedRef.current) {
        if (err instanceof ApiError) {
          switch (err.status) {
            case 401:
              setError('认证失败，请重新登录');
              break;
            case 403:
              setError('权限不足，无法访问系统监控数据');
              break;
            case 500:
              setError('服务器内部错误，请稍后重试');
              break;
            case 0:
              setError('网络连接失败，请检查网络连接');
              break;
            default:
              setError(`请求失败: ${err.message}`);
          }
        } else {
          setError('未知错误，请重试');
        }
        
        setRetryCount(prev => prev + 1);
      }
    }
  }, []);

  // 获取系统健康状态
  const fetchSystemHealth = useCallback(async () => {
    try {
      const result = await apiClient.get<{
        success: boolean;
        data: SystemHealth;
      }>('/system/health');
      
      if (mountedRef.current && result.success) {
        setHealth(result.data);
      }
    } catch (err) {
      console.error('Error fetching system health:', err);
      // 健康状态获取失败不影响主要功能
    }
  }, []);

  // 获取所有数据
  const fetchData = useCallback(async () => {
    if (!mountedRef.current) return;
    
    setLoading(true);
    await Promise.all([
      fetchSystemResources(),
      fetchSystemHealth()
    ]);
    
    if (mountedRef.current) {
      setLoading(false);
    }
  }, [fetchSystemResources, fetchSystemHealth]);

  // 手动重试
  const handleRetry = useCallback(() => {
    setError(null);
    setRetryCount(0);
    fetchData();
  }, [fetchData]);

  // 设置自动刷新
  const setupAutoRefresh = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    // 根据重试次数调整刷新间隔
    const baseInterval = 30000; // 30秒
    const interval = Math.min(baseInterval * Math.pow(2, retryCount), 300000); // 最大5分钟

    intervalRef.current = setInterval(() => {
      if (mountedRef.current && document.visibilityState === 'visible') {
        fetchData();
      }
    }, interval);
  }, [fetchData, retryCount]);

  // 组件挂载时获取数据
  useEffect(() => {
    mountedRef.current = true;
    fetchData();
    
    return () => {
      mountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData]);

  // 设置自动刷新
  useEffect(() => {
    if (!error && resources) {
      setupAutoRefresh();
    }
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [setupAutoRefresh, error, resources]);

  // 页面可见性变化处理
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && !error) {
        fetchData();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [fetchData, error]);

  const formatBytes = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(2)} ${units[unitIndex]}`;
  };

  const getHealthColor = (status: string): string => {
    switch (status) {
      case 'healthy': return '#52c41a';
      case 'moderate': return '#faad14';
      case 'warning': return '#fa8c16';
      case 'critical': return '#ff4d4f';
      default: return '#d9d9d9';
    }
  };

  const getHealthText = (status: string): string => {
    switch (status) {
      case 'healthy': return '健康';
      case 'moderate': return '一般';
      case 'warning': return '警告';
      case 'critical': return '严重';
      default: return '未知';
    }
  };

  const getProgressColor = (percent: number): string => {
    if (percent >= 90) return '#ff4d4f';
    if (percent >= 70) return '#fa8c16';
    if (percent >= 50) return '#faad14';
    return '#52c41a';
  };

  // 加载状态
  if (loading && !resources) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: '16px' }}>
          <Text type="secondary">加载系统资源信息...</Text>
        </div>
      </div>
    );
  }

  // 错误状态
  if (error && !resources) {
    return (
      <Alert
        message="系统监控不可用"
        description={
          <div>
            <div style={{ marginBottom: '8px' }}>{error}</div>
            {retryCount > 0 && (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                已重试 {retryCount} 次
              </Text>
            )}
          </div>
        }
        type="error"
        showIcon
        icon={<ExclamationCircleOutlined />}
        action={
          <Button 
            size="small"
            type="primary"
            onClick={handleRetry}
            loading={loading}
          >
            重试
          </Button>
        }
      />
    );
  }

  return (
    <div>
      {/* 系统健康状态概览 */}
      {health && (
        <Card 
          className="modern-card" 
          style={{ marginBottom: '16px' }}
          size="small"
        >
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center' 
          }}>
            <Space>
              <Text strong>系统状态</Text>
              <Text 
                style={{ 
                  color: getHealthColor(health.status),
                  fontWeight: 'bold'
                }}
              >
                {getHealthText(health.status)}
              </Text>
            </Space>
            <Button
              size="small"
              icon={<ReloadOutlined spin={loading} />}
              onClick={handleRetry}
              disabled={loading}
            >
              刷新
            </Button>
          </div>
        </Card>
      )}

      {/* 资源指标 */}
      {resources && (
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          {/* CPU使用率 */}
          <div>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '8px' 
            }}>
              <Text style={{ fontSize: isMobile ? '12px' : '14px' }}>
                CPU使用率
              </Text>
              <Text style={{ fontSize: isMobile ? '12px' : '14px' }}>
                {resources.cpu.percent.toFixed(2)}%
              </Text>
            </div>
            <Progress 
              percent={resources.cpu.percent} 
              strokeColor={getProgressColor(resources.cpu.percent)}
              size={isMobile ? 'small' : 'default'}
              showInfo={false}
            />
          </div>

          {/* 内存使用率 */}
          <div>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '8px' 
            }}>
              <Text style={{ fontSize: isMobile ? '12px' : '14px' }}>
                内存使用率
              </Text>
              <Text style={{ fontSize: isMobile ? '12px' : '14px' }}>
                {formatBytes(resources.memory.used)} / {formatBytes(resources.memory.total)}
              </Text>
            </div>
            <Progress 
              percent={resources.memory.percent} 
              strokeColor={getProgressColor(resources.memory.percent)}
              size={isMobile ? 'small' : 'default'}
              showInfo={false}
            />
          </div>

          {/* 磁盘使用率 */}
          <div>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '8px' 
            }}>
              <Text style={{ fontSize: isMobile ? '12px' : '14px' }}>
                磁盘使用率
              </Text>
              <Text style={{ fontSize: isMobile ? '12px' : '14px' }}>
                {formatBytes(resources.disk.used)} / {formatBytes(resources.disk.total)}
              </Text>
            </div>
            <Progress 
              percent={resources.disk.percent} 
              strokeColor={getProgressColor(resources.disk.percent)}
              size={isMobile ? 'small' : 'default'}
              showInfo={false}
            />
          </div>

          {/* GPU状态 */}
          {resources.gpu && resources.gpu.available && (
            <div>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: '8px' 
              }}>
                <Text style={{ fontSize: isMobile ? '12px' : '14px' }}>
                  GPU显存使用率
                </Text>
                <Text style={{ fontSize: isMobile ? '12px' : '14px' }}>
                  {resources.gpu.used_memory_gb?.toFixed(2)} GB / {resources.gpu.total_memory_gb?.toFixed(2)} GB
                </Text>
              </div>
              <Progress 
                percent={resources.gpu.memory_percent || 0} 
                strokeColor={getProgressColor(resources.gpu.memory_percent || 0)}
                size={isMobile ? 'small' : 'default'}
                showInfo={false}
              />
              
              {/* GPU详细信息 */}
              <div style={{ 
                marginTop: '8px',
                padding: '8px',
                background: '#fafafa',
                borderRadius: '4px',
                fontSize: isMobile ? '11px' : '12px'
              }}>
                <Space direction="vertical" size={2} style={{ width: '100%' }}>
                  {resources.gpu.gpus && resources.gpu.gpus.map((gpu) => (
                    <div key={gpu.index}>
                      <Text strong>GPU {gpu.index}: </Text>
                      <Text>{gpu.name}</Text>
                      <div style={{ marginLeft: '12px', color: '#666' }}>
                        <Text>利用率: {gpu.utilization_percent}%</Text>
                        {' | '}
                        <Text>温度: {gpu.temperature_c}°C</Text>
                      </div>
                    </div>
                  ))}
                  {resources.gpu.cuda_version && resources.gpu.cuda_version !== 'N/A' && (
                    <Text type="secondary">CUDA: {resources.gpu.cuda_version}</Text>
                  )}
                  {resources.gpu.cudnn_version && resources.gpu.cudnn_version !== 'N/A' && (
                    <Text type="secondary"> | cuDNN: {resources.gpu.cudnn_version}</Text>
                  )}
                </Space>
              </div>
            </div>
          )}

          {/* 任务队列状态 */}
          <div>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '8px' 
            }}>
              <Text style={{ fontSize: isMobile ? '12px' : '14px' }}>
                任务队列
              </Text>
              <Text style={{ fontSize: isMobile ? '12px' : '14px' }}>
                {resources.queue.pending} 待处理
              </Text>
            </div>
            <Progress 
              percent={Math.min((resources.queue.pending / 10) * 100, 100)} 
              strokeColor="#faad14"
              size={isMobile ? 'small' : 'default'}
              showInfo={false}
            />
          </div>

          {/* 登录历史信息 */}
          {resources.login_history && (
            <div style={{ 
              borderTop: '1px solid #f0f0f0',
              paddingTop: '12px',
              marginTop: '8px'
            }}>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center',
                marginBottom: '8px' 
              }}>
                <LoginOutlined style={{ 
                  color: '#1677ff',
                  fontSize: isMobile ? '12px' : '14px',
                  marginRight: '6px'
                }} />
                <Text strong style={{ fontSize: isMobile ? '12px' : '14px' }}>
                  登录状态
                </Text>
              </div>
              
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  fontSize: isMobile ? '11px' : '12px'
                }}>
                  <Text type="secondary">
                    <UserOutlined style={{ marginRight: '4px' }} />
                    最近登录
                  </Text>
                  <Text style={{ color: '#262626' }}>
                    {new Date(resources.login_history.last_login_time).toLocaleString()}
                  </Text>
                </div>
                
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  fontSize: isMobile ? '11px' : '12px'
                }}>
                  <Text type="secondary">
                    <GlobalOutlined style={{ marginRight: '4px' }} />
                    登录位置
                  </Text>
                  <Text style={{ color: '#262626' }}>
                    {resources.login_history.last_login_location || resources.login_history.last_login_ip}
                  </Text>
                </div>
                
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  fontSize: isMobile ? '11px' : '12px'
                }}>
                  <Text type="secondary">活跃会话</Text>
                  <Text style={{ color: '#52c41a', fontWeight: 500 }}>
                    {resources.login_history.active_sessions} 个
                  </Text>
                </div>
              </Space>
            </div>
          )}
        </Space>
      )}

      {/* 最后更新时间 */}
      {lastUpdate && (
        <div style={{ 
          textAlign: 'center', 
          marginTop: '12px',
          fontSize: isMobile ? '10px' : '11px',
          color: '#8c8c8c'
        }}>
          最后更新: {lastUpdate.toLocaleTimeString()}
        </div>
      )}

      {/* 错误提示（当有数据但获取新数据失败时） */}
      {error && resources && (
        <Alert
          message="数据更新失败"
          description={error}
          type="warning"
          showIcon
          style={{ marginTop: '12px' }}
          action={
            <Button size="small" onClick={handleRetry}>
              重试
            </Button>
          }
        />
      )}
    </div>
  );
};

export default SystemResourceMonitor;