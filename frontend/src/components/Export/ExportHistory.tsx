/**
 * 导出历史记录组件
 */
import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Typography, Tag, Space, message, Tooltip } from 'antd';
import { 
  DownloadOutlined, 
  ReloadOutlined, 
  DeleteOutlined,
  FileTextOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { ExportHistoryItem, ExportStatus, ExportFormat } from '../../types/export';
import exportService from '../../services/exportService';

const { Title, Text } = Typography;

interface ExportHistoryProps {
  projectId?: string;
  onRedownload?: (item: ExportHistoryItem) => void;
}

const ExportHistory: React.FC<ExportHistoryProps> = ({
  projectId,
  onRedownload
}) => {
  const [history, setHistory] = useState<ExportHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });

  useEffect(() => {
    if (projectId) {
      loadHistory();
    }
  }, [projectId, pagination.current, pagination.pageSize]);

  const loadHistory = async () => {
    if (!projectId) return;

    try {
      setLoading(true);
      const response = await exportService.getExportHistory(
        projectId,
        pagination.pageSize,
        (pagination.current - 1) * pagination.pageSize
      );
      
      setHistory(response.items);
      setPagination(prev => ({
        ...prev,
        total: response.total
      }));
    } catch (error: any) {
      message.error('加载导出历史失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (item: ExportHistoryItem) => {
    if (item.download_url) {
      const link = document.createElement('a');
      link.href = item.download_url;
      link.download = `export_${item.format}_${item.id}.${item.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      if (onRedownload) {
        onRedownload(item);
      }
    }
  };

  const getStatusTag = (status: ExportStatus) => {
    const statusConfig = {
      [ExportStatus.PENDING]: { color: 'blue', text: '等待中' },
      [ExportStatus.PROCESSING]: { color: 'orange', text: '处理中' },
      [ExportStatus.COMPLETED]: { color: 'green', text: '已完成' },
      [ExportStatus.FAILED]: { color: 'red', text: '失败' }
    };
    
    const config = statusConfig[status] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const getFormatIcon = (format: ExportFormat) => {
    return <FileTextOutlined style={{ marginRight: '4px' }} />;
  };

  const columns = [
    {
      title: '格式',
      dataIndex: 'format',
      key: 'format',
      width: 100,
      render: (format: ExportFormat) => (
        <Space>
          {getFormatIcon(format)}
          <Text style={{ fontSize: '12px' }}>
            {exportService.getFormatDisplayName(format)}
          </Text>
        </Space>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: ExportStatus) => getStatusTag(status)
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size?: number) => (
        <Text style={{ fontSize: '12px' }}>
          {size ? exportService.formatFileSize(size) : '-'}
        </Text>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 140,
      render: (time: string) => (
        <Tooltip title={new Date(time).toLocaleString()}>
          <Text style={{ fontSize: '12px' }}>
            <ClockCircleOutlined style={{ marginRight: '4px' }} />
            {new Date(time).toLocaleDateString()}
          </Text>
        </Tooltip>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record: ExportHistoryItem) => (
        <Space size="small">
          {record.status === ExportStatus.COMPLETED && record.download_url ? (
            <Button
              type="link"
              size="small"
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(record)}
              style={{ padding: '0 4px' }}
            >
              下载
            </Button>
          ) : null}
          
          {record.status === ExportStatus.FAILED && (
            <Tooltip title={record.error_message || '导出失败'}>
              <Button
                type="link"
                size="small"
                danger
                style={{ padding: '0 4px' }}
              >
                查看错误
              </Button>
            </Tooltip>
          )}
        </Space>
      )
    }
  ];

  if (!projectId) {
    return (
      <Card title="导出历史" size="small">
        <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
          请先选择项目
        </div>
      </Card>
    );
  }

  return (
    <Card 
      title="导出历史" 
      size="small"
      extra={
        <Button
          size="small"
          icon={<ReloadOutlined />}
          onClick={loadHistory}
          loading={loading}
        >
          刷新
        </Button>
      }
    >
      <Table
        columns={columns}
        dataSource={history}
        rowKey="id"
        loading={loading}
        pagination={{
          ...pagination,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => 
            `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          onChange: (page, pageSize) => {
            setPagination(prev => ({
              ...prev,
              current: page,
              pageSize: pageSize || prev.pageSize
            }));
          }
        }}
        size="small"
        locale={{
          emptyText: '暂无导出记录'
        }}
      />
    </Card>
  );
};

export default ExportHistory;