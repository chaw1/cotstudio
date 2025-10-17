/**
 * 工作节点信息面板
 */
import React from 'react';
import { Card, Table, Button, Tag, Progress, Space, Empty, Tooltip } from 'antd';
import { ReloadOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

import { WorkerInfo } from '../../types/task';

interface WorkerInfoPanelProps {
  workerInfo: WorkerInfo[];
  onRefresh: () => void;
}

const WorkerInfoPanel: React.FC<WorkerInfoPanelProps> = ({ workerInfo, onRefresh }) => {
  const columns: ColumnsType<WorkerInfo> = [
    {
      title: '工作节点',
      dataIndex: 'worker_name',
      key: 'worker_name',
      render: (name: string) => (
        <span className="font-mono text-sm">{name}</span>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const isOnline = status === 'online';
        return (
          <Tag 
            color={isOnline ? 'green' : 'red'}
            icon={isOnline ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}
          >
            {isOnline ? '在线' : '离线'}
          </Tag>
        );
      }
    },
    {
      title: '活跃任务',
      dataIndex: 'active_tasks',
      key: 'active_tasks',
      render: (count: number) => (
        <Tag color={count > 0 ? 'blue' : 'default'}>
          {count}
        </Tag>
      )
    },
    {
      title: '已处理任务',
      dataIndex: 'processed_tasks',
      key: 'processed_tasks',
      render: (count: number) => (
        <span className="font-medium">{count.toLocaleString()}</span>
      )
    },
    {
      title: '系统负载',
      dataIndex: 'load_average',
      key: 'load_average',
      render: (loadAvg: number[]) => {
        if (!loadAvg || loadAvg.length === 0) return '-';
        
        const [load1, load5, load15] = loadAvg;
        const maxLoad = Math.max(load1, load5, load15);
        
        // 根据负载确定颜色
        const getLoadColor = (load: number) => {
          if (load < 1) return '#52c41a'; // 绿色
          if (load < 2) return '#faad14'; // 黄色
          return '#f5222d'; // 红色
        };

        return (
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="text-xs w-8">1m:</span>
              <Progress
                percent={Math.min(load1 * 25, 100)}
                size="small"
                showInfo={false}
                strokeColor={getLoadColor(load1)}
                className="flex-1"
              />
              <span className="text-xs w-8">{load1.toFixed(2)}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs w-8">5m:</span>
              <Progress
                percent={Math.min(load5 * 25, 100)}
                size="small"
                showInfo={false}
                strokeColor={getLoadColor(load5)}
                className="flex-1"
              />
              <span className="text-xs w-8">{load5.toFixed(2)}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs w-8">15m:</span>
              <Progress
                percent={Math.min(load15 * 25, 100)}
                size="small"
                showInfo={false}
                strokeColor={getLoadColor(load15)}
                className="flex-1"
              />
              <span className="text-xs w-8">{load15.toFixed(2)}</span>
            </div>
          </div>
        );
      }
    },
    {
      title: '最后心跳',
      dataIndex: 'last_heartbeat',
      key: 'last_heartbeat',
      render: (timestamp: string) => {
        if (!timestamp) return '-';
        
        const heartbeatTime = dayjs(timestamp);
        const now = dayjs();
        const diffMinutes = now.diff(heartbeatTime, 'minute');
        
        let color = 'green';
        let text = '刚刚';
        
        if (diffMinutes > 5) {
          color = 'red';
          text = `${diffMinutes}分钟前`;
        } else if (diffMinutes > 2) {
          color = 'orange';
          text = `${diffMinutes}分钟前`;
        } else if (diffMinutes > 0) {
          text = `${diffMinutes}分钟前`;
        }
        
        return (
          <Tooltip title={heartbeatTime.format('YYYY-MM-DD HH:mm:ss')}>
            <Tag color={color}>{text}</Tag>
          </Tooltip>
        );
      }
    }
  ];

  if (workerInfo.length === 0) {
    return (
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">工作节点</h3>
          <Button icon={<ReloadOutlined />} onClick={onRefresh}>
            刷新
          </Button>
        </div>
        <Empty description="暂无工作节点信息" />
      </Card>
    );
  }

  // 计算总计
  const totalStats = workerInfo.reduce(
    (acc, worker) => ({
      online_workers: acc.online_workers + (worker.status === 'online' ? 1 : 0),
      total_active_tasks: acc.total_active_tasks + worker.active_tasks,
      total_processed_tasks: acc.total_processed_tasks + worker.processed_tasks
    }),
    { online_workers: 0, total_active_tasks: 0, total_processed_tasks: 0 }
  );

  return (
    <div className="space-y-4">
      {/* 总体统计 */}
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">工作节点总览</h3>
          <Button icon={<ReloadOutlined />} onClick={onRefresh}>
            刷新
          </Button>
        </div>
        
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{totalStats.online_workers}</div>
            <div className="text-gray-500">在线节点</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-600">{workerInfo.length}</div>
            <div className="text-gray-500">总节点数</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{totalStats.total_active_tasks}</div>
            <div className="text-gray-500">活跃任务</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {totalStats.total_processed_tasks.toLocaleString()}
            </div>
            <div className="text-gray-500">已处理任务</div>
          </div>
        </div>
      </Card>

      {/* 工作节点详情表格 */}
      <Card title="工作节点详情">
        <Table
          columns={columns}
          dataSource={workerInfo}
          rowKey="worker_name"
          pagination={false}
          size="small"
          rowClassName={(record) => 
            record.status === 'online' ? '' : 'bg-red-50'
          }
        />
      </Card>
    </div>
  );
};

export default WorkerInfoPanel;