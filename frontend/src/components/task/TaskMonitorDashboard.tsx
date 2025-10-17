/**
 * 任务监控仪表板
 */
import React, { useEffect, useState } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Table,
  Tag,
  Button,
  Space,
  Tooltip,
  Modal,
  Input,
  Select,
  DatePicker,
  message,
  Tabs,
  Badge,
  Spin
} from 'antd';
import ModalContainer from '../common/ModalContainer';
import {
  ReloadOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  RedoOutlined,
  ExclamationCircleOutlined,
  EyeOutlined,
  FilterOutlined
} from '@ant-design/icons';
import { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

import { useTaskStore } from '../../stores/taskStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import {
  TaskMonitor,
  TaskStatus,
  TaskType,
  TaskPriority,
  TASK_STATUS_COLORS,
  TASK_PRIORITY_COLORS,
  TASK_TYPE_NAMES,
  TASK_STATUS_NAMES,
  TASK_PRIORITY_NAMES
} from '../../types/task';
import TaskDetailModal from './TaskDetailModal';
import TaskStatisticsChart from './TaskStatisticsChart';
import QueueInfoPanel from './QueueInfoPanel';
import WorkerInfoPanel from './WorkerInfoPanel';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface TaskMonitorDashboardProps {
  userId: string;
}

const TaskMonitorDashboard: React.FC<TaskMonitorDashboardProps> = ({ userId }) => {
  const {
    tasks,
    selectedTask,
    statistics,
    queueInfo,
    workerInfo,
    loading,
    error,
    filters,
    total,
    isWebSocketConnected,
    fetchTasks,
    fetchStatistics,
    fetchQueueInfo,
    fetchWorkerInfo,
    setFilters,
    retryTask,
    cancelTask,
    batchOperation,
    handleTaskUpdate,
    setWebSocketConnected,
    setSelectedTask
  } = useTaskStore();

  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [filterModalVisible, setFilterModalVisible] = useState(false);
  const [retryModalVisible, setRetryModalVisible] = useState(false);
  const [retryReason, setRetryReason] = useState('');
  const [retryTaskId, setRetryTaskId] = useState<string>('');
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  // WebSocket连接
  const { isConnected, subscribeToTask, unsubscribeFromTask } = useWebSocket({
    userId,
    onTaskUpdate: handleTaskUpdate,
    onConnect: () => {
      setWebSocketConnected(true);
      message.success('实时连接已建立');
    },
    onDisconnect: () => {
      setWebSocketConnected(false);
      message.warning('实时连接已断开');
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
      message.error('实时连接出现错误');
    }
  });

  // 初始化数据
  useEffect(() => {
    fetchTasks();
    fetchStatistics();
    fetchQueueInfo();
    fetchWorkerInfo();
  }, []);

  // 设置自动刷新
  useEffect(() => {
    const interval = setInterval(() => {
      if (!isConnected) {
        fetchTasks();
        fetchQueueInfo();
        fetchWorkerInfo();
      }
    }, 30000); // 30秒刷新一次

    setRefreshInterval(interval);

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [isConnected, fetchTasks, fetchQueueInfo, fetchWorkerInfo]);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [refreshInterval]);

  // 订阅活跃任务的实时更新
  useEffect(() => {
    const activeTasks = tasks.filter(task => task.is_active);
    
    activeTasks.forEach(task => {
      subscribeToTask(task.task_id);
    });

    return () => {
      activeTasks.forEach(task => {
        unsubscribeFromTask(task.task_id);
      });
    };
  }, [tasks, subscribeToTask, unsubscribeFromTask]);

  // 表格列定义
  const columns: ColumnsType<TaskMonitor> = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 120,
      render: (text: string) => (
        <Tooltip title={text}>
          <span className="font-mono text-xs">{text.slice(0, 8)}...</span>
        </Tooltip>
      )
    },
    {
      title: '任务名称',
      dataIndex: 'task_name',
      key: 'task_name',
      width: 150,
      ellipsis: true
    },
    {
      title: '类型',
      dataIndex: 'task_type',
      key: 'task_type',
      width: 100,
      render: (type: TaskType) => (
        <Tag color="blue">{TASK_TYPE_NAMES[type]}</Tag>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: TaskStatus) => (
        <Tag color={TASK_STATUS_COLORS[status]}>
          {TASK_STATUS_NAMES[status]}
        </Tag>
      )
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority: TaskPriority) => (
        <Tag color={TASK_PRIORITY_COLORS[priority]}>
          {TASK_PRIORITY_NAMES[priority]}
        </Tag>
      )
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 120,
      render: (progress: number, record: TaskMonitor) => (
        <div>
          <Progress
            percent={progress}
            size="small"
            status={record.status === TaskStatus.FAILURE ? 'exception' : 'active'}
            showInfo={false}
          />
          <span className="text-xs text-gray-500">{progress}%</span>
        </div>
      )
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
      render: (text: string) => (
        <Tooltip title={text}>
          <span>{text}</span>
        </Tooltip>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (text: string) => (
        <span className="text-xs">{dayjs(text).format('MM-DD HH:mm')}</span>
      )
    },
    {
      title: '执行时间',
      dataIndex: 'execution_time',
      key: 'execution_time',
      width: 80,
      render: (time: number) => (
        <span className="text-xs">
          {time ? `${Math.floor(time / 60)}:${(time % 60).toString().padStart(2, '0')}` : '-'}
        </span>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record: TaskMonitor) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewTask(record)}
            />
          </Tooltip>
          
          {record.can_retry && (
            <Tooltip title="重试">
              <Button
                type="text"
                size="small"
                icon={<RedoOutlined />}
                onClick={() => handleRetryTask(record.task_id)}
              />
            </Tooltip>
          )}
          
          {record.is_active && (
            <Tooltip title="取消">
              <Button
                type="text"
                size="small"
                danger
                icon={<StopOutlined />}
                onClick={() => handleCancelTask(record.task_id)}
              />
            </Tooltip>
          )}
        </Space>
      )
    }
  ];

  // 处理查看任务详情
  const handleViewTask = (task: TaskMonitor) => {
    setSelectedTask(task);
    setDetailModalVisible(true);
  };

  // 处理重试任务
  const handleRetryTask = (taskId: string) => {
    setRetryTaskId(taskId);
    setRetryModalVisible(true);
  };

  // 确认重试任务
  const confirmRetryTask = async () => {
    try {
      await retryTask(retryTaskId, retryReason);
      message.success('任务重试已启动');
      setRetryModalVisible(false);
      setRetryReason('');
      setRetryTaskId('');
    } catch (error) {
      message.error('重试任务失败');
    }
  };

  // 处理取消任务
  const handleCancelTask = (taskId: string) => {
    Modal.confirm({
      title: '确认取消任务',
      icon: <ExclamationCircleOutlined />,
      content: '确定要取消这个任务吗？此操作不可撤销。',
      onOk: async () => {
        try {
          await cancelTask(taskId);
          message.success('任务已取消');
        } catch (error) {
          message.error('取消任务失败');
        }
      }
    });
  };

  // 处理批量操作
  const handleBatchOperation = (operation: 'cancel' | 'retry') => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要操作的任务');
      return;
    }

    const operationText = operation === 'cancel' ? '取消' : '重试';
    
    Modal.confirm({
      title: `确认批量${operationText}`,
      icon: <ExclamationCircleOutlined />,
      content: `确定要${operationText}选中的 ${selectedRowKeys.length} 个任务吗？`,
      onOk: async () => {
        try {
          await batchOperation(selectedRowKeys, operation);
          message.success(`批量${operationText}操作完成`);
          setSelectedRowKeys([]);
        } catch (error) {
          message.error(`批量${operationText}操作失败`);
        }
      }
    });
  };

  // 刷新数据
  const handleRefresh = () => {
    fetchTasks();
    fetchStatistics();
    fetchQueueInfo();
    fetchWorkerInfo();
  };

  // 渲染统计卡片
  const renderStatisticsCards = () => {
    if (!statistics) return null;

    return (
      <Row gutter={16} className="mb-6">
        <Col span={6}>
          <Card>
            <Statistic
              title="总任务数"
              value={statistics.total_tasks}
              prefix={<PlayCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃任务"
              value={statistics.active_tasks}
              prefix={<Badge status="processing" />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="成功率"
              value={statistics.success_rate * 100}
              precision={1}
              suffix="%"
              prefix={<Badge status="success" />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均执行时间"
              value={statistics.average_duration || 0}
              precision={1}
              suffix="秒"
              prefix={<Badge status="default" />}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  return (
    <div className="p-6">
      {/* 页面标题和操作 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">任务监控</h1>
          <div className="flex items-center mt-2 space-x-4">
            <Badge
              status={isConnected ? 'success' : 'error'}
              text={isConnected ? '实时连接正常' : '实时连接断开'}
            />
            {error && (
              <span className="text-red-500 text-sm">{error}</span>
            )}
          </div>
        </div>
        
        <Space>
          <Button
            icon={<FilterOutlined />}
            onClick={() => setFilterModalVisible(true)}
          >
            筛选
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      </div>

      {/* 统计卡片 */}
      {renderStatisticsCards()}

      {/* 主要内容 */}
      <Tabs 
        defaultActiveKey="tasks"
        items={[
          {
            key: 'tasks',
            label: '任务列表',
            children: (
              <Card>
                {/* 批量操作工具栏 */}
                {selectedRowKeys.length > 0 && (
                  <div className="mb-4 p-3 bg-blue-50 rounded">
                    <Space>
                      <span>已选择 {selectedRowKeys.length} 个任务</span>
                      <Button
                        size="small"
                        icon={<RedoOutlined />}
                        onClick={() => handleBatchOperation('retry')}
                      >
                        批量重试
                      </Button>
                      <Button
                        size="small"
                        danger
                        icon={<StopOutlined />}
                        onClick={() => handleBatchOperation('cancel')}
                      >
                        批量取消
                      </Button>
                      <Button
                        size="small"
                        onClick={() => setSelectedRowKeys([])}
                      >
                        取消选择
                      </Button>
                    </Space>
                  </div>
                )}

                {/* 任务表格 */}
                <Table
                  columns={columns}
                  dataSource={tasks}
                  rowKey="task_id"
                  loading={loading}
                  pagination={{
                    current: Math.floor(filters.offset! / filters.limit!) + 1,
                    pageSize: filters.limit,
                    total,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                    onChange: (page, pageSize) => {
                      setFilters({
                        offset: (page - 1) * pageSize!,
                        limit: pageSize
                      });
                    }
                  }}
                  rowSelection={{
                    selectedRowKeys,
                    onChange: (selectedRowKeys: React.Key[]) => {
                      setSelectedRowKeys(selectedRowKeys.map(key => String(key)));
                    },
                    getCheckboxProps: (record) => ({
                      disabled: !record.is_active && !record.can_retry
                    })
                  }}
                  scroll={{ x: 1200 }}
                />
              </Card>
            )
          },
          {
            key: 'statistics',
            label: '统计图表',
            children: <TaskStatisticsChart statistics={statistics} />
          },
          {
            key: 'queues',
            label: '队列信息',
            children: <QueueInfoPanel queueInfo={queueInfo} onRefresh={fetchQueueInfo} />
          },
          {
            key: 'workers',
            label: '工作节点',
            children: <WorkerInfoPanel workerInfo={workerInfo} onRefresh={fetchWorkerInfo} />
          }
        ]}
      />

      {/* 任务详情模态框 */}
      <TaskDetailModal
        visible={detailModalVisible}
        task={selectedTask}
        onClose={() => {
          setDetailModalVisible(false);
          setSelectedTask(null);
        }}
        onRetry={handleRetryTask}
        onCancel={handleCancelTask}
      />

      {/* 重试确认模态框 */}
      <ModalContainer
        visible={retryModalVisible}
        onClose={() => {
          setRetryModalVisible(false);
          setRetryReason('');
          setRetryTaskId('');
        }}
        title="重试任务"
        footer={[
          <Button key="cancel" onClick={() => {
            setRetryModalVisible(false);
            setRetryReason('');
            setRetryTaskId('');
          }}>
            取消
          </Button>,
          <Button key="ok" type="primary" onClick={confirmRetryTask}>
            确定
          </Button>
        ]}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">重试原因（可选）</label>
            <Input.TextArea
              value={retryReason}
              onChange={(e) => setRetryReason(e.target.value)}
              placeholder="请输入重试原因..."
              rows={3}
            />
          </div>
        </div>
      </ModalContainer>
    </div>
  );
};

export default TaskMonitorDashboard;