import React, { useState } from 'react';
import {
  Card,
  List,
  Typography,
  Space,
  Button,
  Tag,
  Progress,
  Empty,
} from 'antd';
import {
  PlayCircleOutlined,
  EyeOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { FileInfo } from '../../types';
import { OCRProcessing } from '../ocr';
import ModalContainer from '../common/ModalContainer';

const { Text, Title } = Typography;

interface OCRProcessingTabProps {
  projectId: string;
  files: FileInfo[];
  onRefresh: () => void;
}

const OCRProcessingTab: React.FC<OCRProcessingTabProps> = ({
  files = [],
  onRefresh,
}) => {
  const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null);
  const [showOCRModal, setShowOCRModal] = useState(false);

  // 安全的文件数组
  const safeFiles = Array.isArray(files) 
    ? files.filter(f => f && typeof f === 'object' && f.filename) 
    : [];

  // 获取文件的OCR状态
  const getFileOCRStatus = (file: FileInfo): string => {
    if (!file) return 'pending';
    return file.ocrStatus || file.ocr_status || 'pending';
  };

  // 获取文件的MIME类型
  const getFileMimeType = (file: FileInfo): string => {
    if (!file) return 'unknown';
    return file.mimeType || file.mime_type || 'unknown';
  };

  // 获取文件图标 - 绝对安全版本
  const getFileIcon = (mimeType: string): string => {
    // 立即返回默认值，避免任何可能的错误
    if (!mimeType || mimeType === null || mimeType === undefined) {
      return '📄';
    }
    
    // 安全的字符串转换
    let typeStr = '';
    try {
      typeStr = String(mimeType).toLowerCase();
    } catch (e) {
      return '📄';
    }
    
    // 使用最安全的字符串匹配方法
    if (typeStr.search('pdf') >= 0) return '📄';
    if (typeStr.search('word') >= 0) return '📝';
    if (typeStr.search('doc') >= 0) return '📝';
    if (typeStr.search('image') >= 0) return '🖼️';
    if (typeStr.search('text') >= 0) return '📝';
    
    return '📄';
  };

  // 获取OCR状态图标
  const getOCRStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': 
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'processing': 
        return <ClockCircleOutlined style={{ color: '#1677ff' }} />;
      case 'failed': 
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default: 
        return <FileTextOutlined style={{ color: '#8c8c8c' }} />;
    }
  };

  // 获取OCR状态文本
  const getOCRStatusText = (status: string): string => {
    switch (status) {
      case 'completed': return '已完成';
      case 'processing': return '处理中';
      case 'failed': return '失败';
      default: return '待处理';
    }
  };

  // 获取OCR状态颜色
  const getOCRStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'processing';
      case 'failed': return 'error';
      default: return 'warning';
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 处理开始OCR
  const handleStartOCR = (file: FileInfo) => {
    setSelectedFile(file);
    setShowOCRModal(true);
  };

  // 处理查看切片
  const handleViewSlices = (file: FileInfo) => {
    setSelectedFile(file);
    setShowOCRModal(true);
  };

  // 关闭OCR模态框
  const handleCloseOCRModal = () => {
    setShowOCRModal(false);
    setSelectedFile(null);
    onRefresh();
  };

  // 计算统计数据
  const completedCount = safeFiles.filter(f => getFileOCRStatus(f) === 'completed').length;
  const processingCount = safeFiles.filter(f => getFileOCRStatus(f) === 'processing').length;
  const failedCount = safeFiles.filter(f => getFileOCRStatus(f) === 'failed').length;
  const totalProgress = safeFiles.length > 0 
    ? Math.round((completedCount / safeFiles.length) * 100) 
    : 0;

  return (
    <div>
      {/* 总体进度 */}
      <Card style={{ marginBottom: 16 }}>
        <Title level={5}>OCR处理总览</Title>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center' 
          }}>
            <Text>总体进度</Text>
            <Text strong>{completedCount}/{safeFiles.length} 个文件已完成</Text>
          </div>
          <Progress
            percent={totalProgress}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
          <Space wrap>
            <Tag color="success">已完成: {completedCount}</Tag>
            <Tag color="processing">处理中: {processingCount}</Tag>
            <Tag color="error">失败: {failedCount}</Tag>
            <Tag color="default">
              待处理: {safeFiles.length - completedCount - processingCount - failedCount}
            </Tag>
          </Space>
        </Space>
      </Card>

      {/* 文件列表 */}
      <Card title="文件OCR状态">
        {safeFiles.length === 0 ? (
          <Empty
            description="暂无文件"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <List
            dataSource={safeFiles}
            renderItem={(file) => (
              <List.Item
                actions={[
                  getFileOCRStatus(file) === 'completed' ? (
                    <Button
                      type="link"
                      icon={<EyeOutlined />}
                      onClick={() => handleViewSlices(file)}
                    >
                      查看切片
                    </Button>
                  ) : (
                    <Button
                      type="link"
                      icon={<PlayCircleOutlined />}
                      onClick={() => handleStartOCR(file)}
                      disabled={getFileOCRStatus(file) === 'processing'}
                    >
                      {getFileOCRStatus(file) === 'processing' ? '处理中...' : '开始OCR'}
                    </Button>
                  ),
                ]}
              >
                <List.Item.Meta
                  avatar={
                    <div style={{ fontSize: '24px' }}>
                      {(() => {
                        try {
                          const mimeType = getFileMimeType(file);
                          return getFileIcon(mimeType);
                        } catch (error) {
                          console.error('Error getting file icon:', error);
                          return '📄';
                        }
                      })()}
                    </div>
                  }
                  title={
                    <Space>
                      <span>{file.filename || '未知文件'}</span>
                      <Tag color={getOCRStatusColor(getFileOCRStatus(file))}>
                        {getOCRStatusIcon(getFileOCRStatus(file))}
                        <span style={{ marginLeft: 4 }}>
                          {getOCRStatusText(getFileOCRStatus(file))}
                        </span>
                      </Tag>
                    </Space>
                  }
                  description={
                    <Space direction="vertical" size="small">
                      <Text type="secondary">
                        大小: {formatFileSize(file.size || 0)} |{' '}
                        类型: {getFileMimeType(file)} |{' '}
                        上传时间: {(() => {
                          try {
                            const dateStr = file.createdAt || file.created_at || '';
                            return dateStr 
                              ? new Date(dateStr).toLocaleString('zh-CN') 
                              : '未知';
                          } catch {
                            return '未知';
                          }
                        })()}
                      </Text>
                      {getFileOCRStatus(file) === 'processing' && (
                        <Progress
                          percent={50}
                          size="small"
                          status="active"
                        />
                      )}
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>

      {/* OCR处理模态框 */}
      <ModalContainer
        visible={showOCRModal}
        onClose={handleCloseOCRModal}
        title={`OCR处理 - ${selectedFile?.filename || ''}`}
        width={900}
        centered={true}
        destroyOnClose={true}
        footer={null}
        zIndex={1050}
        maskClosable={false}
      >
        {selectedFile && (
          <OCRProcessing
            file={selectedFile}
            onBack={handleCloseOCRModal}
          />
        )}
      </ModalContainer>
    </div>
  );
};

export default OCRProcessingTab;