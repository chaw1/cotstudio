/**
 * 导出进度显示组件
 */
import React from 'react';
import { Card, Progress, Typography, Button, Space, Alert, Spin } from 'antd';
import { 
  CheckCircleOutlined, 
  CloseCircleOutlined, 
  LoadingOutlined, 
  DownloadOutlined,
  StopOutlined 
} from '@ant-design/icons';
import { ExportTaskResponse, ExportStatus } from '../../types/export';
import exportService from '../../services/exportService';

const { Title, Text } = Typography;

interface ExportProgressProps {
  task: ExportTaskResponse | null;
  onCancel?: () => void;
  onDownload?: (url: string) => void;
  onReset?: () => void;
}

const ExportProgress: React.FC<ExportProgressProps> = ({
  task,
  onCancel,
  onDownload,
  onReset
}) => {
  if (!task) {
    return null;
  }

  const getStatusIcon = (status: ExportStatus) => {
    switch (status) {
      case ExportStatus.PENDING:
        return <LoadingOutlined style={{ color: '#1890ff' }} />;
      case ExportStatus.PROCESSING:
        return <LoadingOutlined style={{ color: '#1890ff' }} />;
      case ExportStatus.COMPLETED:
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case ExportStatus.FAILED:
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <LoadingOutlined />;
    }
  };

  const getStatusColor = (status: ExportStatus) => {
    switch (status) {
      case ExportStatus.PENDING:
        return '#1890ff';
      case ExportStatus.PROCESSING:
        return '#1890ff';
      case ExportStatus.COMPLETED:
        return '#52c41a';
      case ExportStatus.FAILED:
        return '#ff4d4f';
      default:
        return '#d9d9d9';
    }
  };

  const getProgressStatus = (status: ExportStatus) => {
    switch (status) {
      case ExportStatus.COMPLETED:
        return 'success';
      case ExportStatus.FAILED:
        return 'exception';
      default:
        return 'active';
    }
  };

  const handleDownload = () => {
    if (task.download_url && onDownload) {
      onDownload(task.download_url);
    }
  };

  const handleCancel = async () => {
    if (onCancel) {
      onCancel();
    }
  };

  return (
    <Card title="导出进度" size="small">
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {/* 状态显示 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {getStatusIcon(task.status)}
          <Text strong style={{ color: getStatusColor(task.status) }}>
            {exportService.getStatusDisplayName(task.status)}
          </Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            任务ID: {task.task_id.substring(0, 8)}...
          </Text>
        </div>

        {/* 进度条 */}
        <Progress
          percent={Math.round(task.progress)}
          status={getProgressStatus(task.status)}
          strokeColor={getStatusColor(task.status)}
          showInfo={true}
        />

        {/* 状态消息 */}
        {task.message && (
          <div style={{ 
            padding: '8px 12px', 
            backgroundColor: '#f5f5f5', 
            borderRadius: '4px',
            fontSize: '12px'
          }}>
            {task.message}
          </div>
        )}

        {/* 时间信息 */}
        <div style={{ fontSize: '12px', color: '#666' }}>
          <div>开始时间: {new Date(task.created_at).toLocaleString()}</div>
          {task.completed_at && (
            <div>完成时间: {new Date(task.completed_at).toLocaleString()}</div>
          )}
        </div>

        {/* 操作按钮 */}
        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
          {task.status === ExportStatus.PENDING || task.status === ExportStatus.PROCESSING ? (
            <Button
              size="small"
              icon={<StopOutlined />}
              onClick={handleCancel}
              danger
            >
              取消任务
            </Button>
          ) : null}

          {task.status === ExportStatus.COMPLETED && task.download_url ? (
            <Button
              type="primary"
              size="small"
              icon={<DownloadOutlined />}
              onClick={handleDownload}
            >
              下载文件
            </Button>
          ) : null}

          {(task.status === ExportStatus.COMPLETED || task.status === ExportStatus.FAILED) && onReset ? (
            <Button
              size="small"
              onClick={onReset}
            >
              重新导出
            </Button>
          ) : null}
        </div>

        {/* 错误信息 */}
        {task.status === ExportStatus.FAILED && (
          <Alert
            message="导出失败"
            description={task.message || '导出过程中发生未知错误'}
            type="error"
            showIcon
          />
        )}

        {/* 成功信息 */}
        {task.status === ExportStatus.COMPLETED && (
          <Alert
            message="导出成功"
            description="文件已准备就绪，点击下载按钮获取文件"
            type="success"
            showIcon
          />
        )}
      </Space>
    </Card>
  );
};

export default ExportProgress;