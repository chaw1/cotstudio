/**
 * 队列信息面板
 */
import React from 'react';
import { Card, Table, Button, Progress, Tag, Space, Empty } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { ColumnsType } from 'antd/es/table';

import { TaskQueueInfo } from '../../types/task';

interface QueueInfoPanelProps {
  queueInfo: TaskQueueInfo[];
  onRefresh: () => void;
}

const QueueInfoPanel: React.FC<QueueInfoPanelProps> = ({ queueInfo, onRefresh }) => {
  const columns: ColumnsType<TaskQueueInfo> = [
    {
      title: '队列名称',
      dataIndex: 'queue_name',
      key: 'queue_name',
      render: (name: string) => (
        <Tag color="blue">{name}</Tag>
      )
    },
    {
      title: '活跃任务',
      dataIndex: 'active_tasks',
      key: 'active_tasks',
      render: (count: number) => (
        <Tag color="green">{count}</Tag>
      )
    },
    {
      title: '预定任务',
      dataIndex: 'scheduled_tasks',
      key: 'scheduled_tasks',
      render: (count: number) => (
        <Tag color="orange">{count}</Tag>
      )
    },
    {
      title: '保留任务',
      dataIndex: 'reserved_tasks',
      key: 'reserved_tasks',
      render: (count: number) => (
        <Tag color="purple">{count}</Tag>
      )
    },
    {
      title: '总任务数',
      dataIndex: 'total_tasks',
      key: 'total_tasks',
      render: (count: number) => (
        <span className="font-medium">{count}</span>
      )
    },
    {
      title: '负载分布',
      key: 'load_distribution',
      render: (_, record: TaskQueueInfo) => {
        const activePercent = record.total_tasks > 0 
          ? (record.active_tasks / record.total_tasks) * 100 
          : 0;
        const scheduledPercent = record.total_tasks > 0 
          ? (record.scheduled_tasks / record.total_tasks) * 100 
          : 0;
        const reservedPercent = record.total_tasks > 0 
          ? (record.reserved_tasks / record.total_tasks) * 100 
          : 0;

        return (
          <div className="w-32">
            <div className="text-xs text-gray-500 mb-1">
              活跃: {activePercent.toFixed(2)}%
            </div>
            <Progress
              percent={activePercent}
              size="small"
              showInfo={false}
              strokeColor="#52c41a"
            />
            <div className="text-xs text-gray-500 mb-1 mt-1">
              预定: {scheduledPercent.toFixed(2)}%
            </div>
            <Progress
              percent={scheduledPercent}
              size="small"
              showInfo={false}
              strokeColor="#fa8c16"
            />
            <div className="text-xs text-gray-500 mb-1 mt-1">
              保留: {reservedPercent.toFixed(0)}%
            </div>
            <Progress
              percent={reservedPercent}
              size="small"
              showInfo={false}
              strokeColor="#722ed1"
            />
          </div>
        );
      }
    }
  ];

  if (queueInfo.length === 0) {
    return (
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">队列信息</h3>
          <Button icon={<ReloadOutlined />} onClick={onRefresh}>
            刷新
          </Button>
        </div>
        <Empty description="暂无队列信息" />
      </Card>
    );
  }

  // 计算总计
  const totalStats = queueInfo.reduce(
    (acc, queue) => ({
      active_tasks: acc.active_tasks + queue.active_tasks,
      scheduled_tasks: acc.scheduled_tasks + queue.scheduled_tasks,
      reserved_tasks: acc.reserved_tasks + queue.reserved_tasks,
      total_tasks: acc.total_tasks + queue.total_tasks
    }),
    { active_tasks: 0, scheduled_tasks: 0, reserved_tasks: 0, total_tasks: 0 }
  );

  return (
    <div className="space-y-4">
      {/* 总体统计 */}
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">队列总览</h3>
          <Button icon={<ReloadOutlined />} onClick={onRefresh}>
            刷新
          </Button>
        </div>
        
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{totalStats.active_tasks}</div>
            <div className="text-gray-500">活跃任务</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{totalStats.scheduled_tasks}</div>
            <div className="text-gray-500">预定任务</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{totalStats.reserved_tasks}</div>
            <div className="text-gray-500">保留任务</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{totalStats.total_tasks}</div>
            <div className="text-gray-500">总任务数</div>
          </div>
        </div>
      </Card>

      {/* 队列详情表格 */}
      <Card title="队列详情">
        <Table
          columns={columns}
          dataSource={queueInfo}
          rowKey="queue_name"
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
};

export default QueueInfoPanel;