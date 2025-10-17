/**
 * 任务详情模态框
 */
import React from 'react';
import {
  Descriptions,
  Tag,
  Progress,
  Button,
  Space,
  Divider,
  Typography,
  Alert,
  Timeline,
  Card
} from 'antd';
import {
  RedoOutlined,
  StopOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';

import {
  TaskMonitor,
  TaskStatus,
  TASK_STATUS_COLORS,
  TASK_PRIORITY_COLORS,
  TASK_TYPE_NAMES,
  TASK_STATUS_NAMES,
  TASK_PRIORITY_NAMES
} from '../../types/task';
import ModalContainer from '../common/ModalContainer';

dayjs.extend(duration);

const { Text, Paragraph } = Typography;

interface TaskDetailModalProps {
  visible: boolean;
  task: TaskMonitor | null;
  onClose: () => void;
  onRetry: (taskId: string) => void;
  onCancel: (taskId: string) => void;
}

const TaskDetailModal: React.FC<TaskDetailModalProps> = ({
  visible,
  task,
  onClose,
  onRetry,
  onCancel
}) => {
  if (!task) return null;

  // 格式化执行时间
  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    const d = dayjs.duration(seconds, 'seconds');
    if (seconds < 60) {
      return `${seconds}秒`;
    } else if (seconds < 3600) {
      return `${d.minutes()}分${d.seconds()}秒`;
    } else {
      return `${d.hours()}时${d.minutes()}分${d.seconds()}秒`;
    }
  };

  // 获取状态图标
  const getStatusIcon = (status: TaskStatus) => {
    switch (status) {
      case TaskStatus.PENDING:
        return <ClockCircleOutlined className="text-blue-500" />;
      case TaskStatus.PROGRESS:
        return <ClockCircleOutlined className="text-orange-500" />;
      case TaskStatus.SUCCESS:
        return <CheckCircleOutlined className="text-green-500" />;
      case TaskStatus.FAILURE:
        return <CloseCircleOutlined className="text-red-500" />;
      case TaskStatus.RETRY:
        return <RedoOutlined className="text-purple-500" />;
      case TaskStatus.REVOKED:
        return <ExclamationCircleOutlined className="text-gray-500" />;
      default:
        return <ClockCircleOutlined />;
    }
  };

  // 渲染时间线
  const renderTimeline = () => {
    const items = [];

    items.push({
      dot: <ClockCircleOutlined className="text-blue-500" />,
      children: (
        <div>
          <Text strong>任务创建</Text>
          <br />
          <Text type="secondary">{dayjs(task.created_at).format('YYYY-MM-DD HH:mm:ss')}</Text>
        </div>
      )
    });

    if (task.started_at) {
      items.push({
        dot: <ClockCircleOutlined className="text-orange-500" />,
        children: (
          <div>
            <Text strong>开始执行</Text>
            <br />
            <Text type="secondary">{dayjs(task.started_at).format('YYYY-MM-DD HH:mm:ss')}</Text>
          </div>
        )
      });
    }

    if (task.completed_at) {
      items.push({
        dot: getStatusIcon(task.status),
        children: (
          <div>
            <Text strong>
              {task.status === TaskStatus.SUCCESS ? '执行完成' : 
               task.status === TaskStatus.FAILURE ? '执行失败' : '任务结束'}
            </Text>
            <br />
            <Text type="secondary">{dayjs(task.completed_at).format('YYYY-MM-DD HH:mm:ss')}</Text>
          </div>
        )
      });
    }

    return <Timeline items={items} />;
  };

  // 渲染参数
  const renderParameters = () => {
    if (!task.parameters) return <Text type="secondary">无参数</Text>;

    return (
      <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto max-h-40">
        {JSON.stringify(task.parameters, null, 2)}
      </pre>
    );
  };

  // 渲染结果
  const renderResult = () => {
    if (!task.result) return <Text type="secondary">无结果数据</Text>;

    return (
      <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto max-h-40">
        {JSON.stringify(task.result, null, 2)}
      </pre>
    );
  };

  // 渲染错误信息
  const renderErrorInfo = () => {
    if (!task.error_info) return null;

    return (
      <Alert
        message="错误信息"
        description={
          <pre className="text-xs overflow-auto max-h-40">
            {JSON.stringify(task.error_info, null, 2)}
          </pre>
        }
        type="error"
        showIcon
      />
    );
  };

  return (
    <ModalContainer
      visible={visible}
      onClose={onClose}
      title={
        <div className="flex items-center space-x-2">
          {getStatusIcon(task.status)}
          <span>任务详情</span>
          <Tag color={TASK_STATUS_COLORS[task.status]}>
            {TASK_STATUS_NAMES[task.status]}
          </Tag>
        </div>
      }
      width={800}
      footer={
        <Space>
          {task.can_retry && (
            <Button
              type="primary"
              icon={<RedoOutlined />}
              onClick={() => {
                onRetry(task.task_id);
                onClose();
              }}
            >
              重试任务
            </Button>
          )}
          
          {task.is_active && (
            <Button
              danger
              icon={<StopOutlined />}
              onClick={() => {
                onCancel(task.task_id);
                onClose();
              }}
            >
              取消任务
            </Button>
          )}
          
          <Button onClick={onClose}>关闭</Button>
        </Space>
      }
    >
      <div className="space-y-6">
        {/* 基本信息 */}
        <Card title="基本信息" size="small">
          <Descriptions column={2} size="small">
            <Descriptions.Item label="任务ID">
              <Text code>{task.task_id}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="任务名称">
              {task.task_name}
            </Descriptions.Item>
            <Descriptions.Item label="任务类型">
              <Tag color="blue">{TASK_TYPE_NAMES[task.task_type]}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="优先级">
              <Tag color={TASK_PRIORITY_COLORS[task.priority]}>
                {TASK_PRIORITY_NAMES[task.priority]}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="用户ID">
              {task.user_id}
            </Descriptions.Item>
            <Descriptions.Item label="队列名称">
              {task.queue_name}
            </Descriptions.Item>
            <Descriptions.Item label="工作节点">
              {task.worker_name || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="关键任务">
              <Tag color={task.is_critical ? 'red' : 'default'}>
                {task.is_critical ? '是' : '否'}
              </Tag>
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* 执行进度 */}
        <Card title="执行进度" size="small">
          <div className="space-y-3">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span>进度</span>
                <span>{task.progress}%</span>
              </div>
              <Progress
                percent={task.progress}
                status={task.status === TaskStatus.FAILURE ? 'exception' : 'active'}
              />
            </div>
            
            {task.current_step && (
              <div>
                <Text strong>当前步骤：</Text>
                <Text>{task.current_step}</Text>
                {task.total_steps && (
                  <Text type="secondary"> ({task.total_steps} 步骤)</Text>
                )}
              </div>
            )}
            
            {task.message && (
              <div>
                <Text strong>状态消息：</Text>
                <Paragraph>{task.message}</Paragraph>
              </div>
            )}
          </div>
        </Card>

        {/* 时间信息 */}
        <Card title="时间信息" size="small">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Descriptions column={1} size="small">
                <Descriptions.Item label="创建时间">
                  {dayjs(task.created_at).format('YYYY-MM-DD HH:mm:ss')}
                </Descriptions.Item>
                <Descriptions.Item label="开始时间">
                  {task.started_at ? dayjs(task.started_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="完成时间">
                  {task.completed_at ? dayjs(task.completed_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="预估时长">
                  {formatDuration(task.estimated_duration)}
                </Descriptions.Item>
                <Descriptions.Item label="实际时长">
                  {formatDuration(task.actual_duration)}
                </Descriptions.Item>
              </Descriptions>
            </div>
            
            <div>
              {renderTimeline()}
            </div>
          </div>
        </Card>

        {/* 重试信息 */}
        {task.retry_count > 0 && (
          <Card title="重试信息" size="small">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="重试次数">
                {task.retry_count} / {task.max_retries}
              </Descriptions.Item>
              <Descriptions.Item label="重试延迟">
                {task.retry_delay}秒
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}

        {/* 任务参数 */}
        <Card title="任务参数" size="small">
          {renderParameters()}
        </Card>

        {/* 执行结果 */}
        {task.result && (
          <Card title="执行结果" size="small">
            {renderResult()}
          </Card>
        )}

        {/* 错误信息 */}
        {task.error_info && renderErrorInfo()}
      </div>
    </ModalContainer>
  );
};

export default TaskDetailModal;