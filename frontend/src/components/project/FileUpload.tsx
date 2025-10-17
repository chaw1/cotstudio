import React, { useState, useCallback } from 'react';
import {
  Upload,
  Button,
  Progress,
  List,
  Card,
  Space,
  Tag,
  Popconfirm,
  Typography,
  Alert,
  App,
} from 'antd';
import {
  UploadOutlined,
  DeleteOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileMarkdownOutlined,
  FileOutlined,
  InboxOutlined,
} from '@ant-design/icons';
import { useDrop } from 'react-dnd';
import { NativeTypes } from 'react-dnd-html5-backend';
import { FileInfo } from '../../types';

const { Dragger } = Upload;
const { Title, Text } = Typography;

interface FileUploadProps {
  projectId: string;
  files: FileInfo[];
  loading: boolean;
  onUpload: (files: File[]) => Promise<void>;
  onDelete: (fileId: string) => Promise<void>;
  onRefresh: () => void;
}

interface UploadProgress {
  [key: string]: number;
}

const FileUpload: React.FC<FileUploadProps> = ({
  projectId,
  files,
  loading,
  onUpload,
  onDelete,
  onRefresh,
}) => {
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({});
  const [dragOver, setDragOver] = useState(false);
  const { message } = App.useApp();

  // 支持的文件类型
  const supportedTypes = [
    '.pdf',
    '.doc',
    '.docx',
    '.txt',
    '.md',
    '.tex',
    '.json',
  ];

  const maxFileSize = 100 * 1024 * 1024; // 100MB

  // 获取文件图标
  const getFileIcon = (file: FileInfo) => {
    const mimeType = file.mime_type || file.mimeType || '';
    const filename = file.filename || '';
    
    if (!mimeType) {
      // 如果没有MIME类型，根据文件名后缀判断
      if (filename.endsWith('.pdf')) return <FilePdfOutlined />;
      if (filename.endsWith('.doc') || filename.endsWith('.docx')) return <FileWordOutlined />;
      if (filename.endsWith('.md')) return <FileMarkdownOutlined />;
      if (filename.endsWith('.txt')) return <FileTextOutlined />;
      return <FileOutlined />;
    }
    
    try {
      if (mimeType.includes('pdf')) return <FilePdfOutlined />;
      if (mimeType.includes('word') || filename.endsWith('.doc') || filename.endsWith('.docx')) {
        return <FileWordOutlined />;
      }
      if (filename.endsWith('.md')) return <FileMarkdownOutlined />;
      if (mimeType.includes('text')) return <FileTextOutlined />;
      return <FileOutlined />;
    } catch (error) {
      return <FileOutlined />;
    }
  };

  // 获取OCR状态标签
  const getOCRStatusTag = (file: FileInfo) => {
    const status = file.ocr_status || file.ocrStatus || 'pending';
    const statusMap = {
      pending: { color: 'default', text: '待处理' },
      processing: { color: 'processing', text: '处理中' },
      completed: { color: 'success', text: '已完成' },
      failed: { color: 'error', text: '处理失败' },
    };
    
    const config = statusMap[status as keyof typeof statusMap] || statusMap.pending;
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 验证文件
  const validateFile = (file: File) => {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!supportedTypes.includes(extension)) {
      message.error(`不支持的文件类型: ${extension}`);
      return false;
    }
    
    if (file.size > maxFileSize) {
      message.error(`文件大小不能超过 ${formatFileSize(maxFileSize)}`);
      return false;
    }
    
    return true;
  };

  // 处理文件上传
  const handleUpload = async (fileList: File[]) => {
    const validFiles = fileList.filter(validateFile);
    
    if (validFiles.length === 0) {
      return;
    }

    try {
      await onUpload(validFiles);
      message.success(`成功上传 ${validFiles.length} 个文件`);
      // 不在这里调用 onRefresh，因为父组件的 onUpload 会处理刷新
    } catch (error) {
      message.error('文件上传失败');
    }
  };

  // 处理文件删除
  const handleDelete = async (fileId: string, filename: string) => {
    try {
      // 检查文件是否正在OCR处理中
      const fileToDelete = files.find(f => f.id === fileId);
      const isProcessing = fileToDelete && (
        fileToDelete.ocrStatus === 'processing' || 
        fileToDelete.ocr_status === 'processing'
      );

      if (isProcessing) {
        // 显示二次确认对话框
        const confirmed = window.confirm(
          `文件 "${filename}" 正在进行OCR处理中，删除将停止OCR进程。确定要删除吗？`
        );
        
        if (!confirmed) {
          return;
        }

        // 尝试停止OCR任务
        try {
          const { fileService: fileServiceImport } = await import('../../services/fileService');
          await fileServiceImport.stopFileOCR(fileId);
        } catch (error) {
          console.warn('Failed to stop OCR before deleting:', error);
          // 继续删除操作
        }
      }

      await onDelete(fileId);
      message.success(`文件 "${filename}" 删除成功`);
      onRefresh();
    } catch (error) {
      message.error('文件删除失败');
    }
  };

  // 拖拽处理
  const [{ isOver }, drop] = useDrop({
    accept: [NativeTypes.FILE],
    drop: (item: { files: File[] }) => {
      handleUpload(Array.from(item.files));
    },
    collect: (monitor) => ({
      isOver: monitor.isOver(),
    }),
  });

  const handleDragEnter = useCallback(() => {
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragOver(false);
  }, []);

  return (
    <div ref={drop}>
      <Card
        title={
          <Space>
            <Title level={4} style={{ margin: 0 }}>
              文件管理
            </Title>
            <Text type="secondary">({files.length} 个文件)</Text>
          </Space>
        }
        extra={
          <Button onClick={onRefresh} loading={loading}>
            刷新
          </Button>
        }
      >
        {/* 文件上传区域 */}
        <div
          style={{
            marginBottom: 24,
            border: isOver || dragOver ? '2px dashed #1890ff' : '2px dashed #d9d9d9',
            borderRadius: 6,
            backgroundColor: isOver || dragOver ? '#f0f8ff' : 'transparent',
            transition: 'all 0.3s',
          }}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
        >
          <Dragger
            name="files"
            multiple
            showUploadList={false}
            beforeUpload={() => false}
            onChange={(info) => {
              const files = info.fileList.map(file => file.originFileObj).filter(Boolean) as File[];
              if (files.length > 0) {
                handleUpload(files);
              }
            }}
            style={{ border: 'none', background: 'transparent' }}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined style={{ fontSize: 48, color: isOver || dragOver ? '#1890ff' : '#d9d9d9' }} />
            </p>
            <p className="ant-upload-text">
              点击或拖拽文件到此区域上传
            </p>
            <p className="ant-upload-hint">
              支持单个或批量上传。支持格式：{supportedTypes.join(', ')}
              <br />
              最大文件大小：{formatFileSize(maxFileSize)}
            </p>
          </Dragger>
        </div>

        {/* 支持格式提示 */}
        <Alert
          message="支持的文件格式"
          description={
            <Space wrap>
              <Tag>PDF</Tag>
              <Tag>Word (.doc, .docx)</Tag>
              <Tag>文本 (.txt)</Tag>
              <Tag>Markdown (.md)</Tag>
              <Tag>LaTeX (.tex)</Tag>
              <Tag>JSON (.json)</Tag>
            </Space>
          }
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        {/* 文件列表 */}
        <List
          loading={loading}
          dataSource={files}
          locale={{ emptyText: '暂无文件，请上传文件' }}
          renderItem={(file) => (
            <List.Item
              actions={[
                <Popconfirm
                  key="delete"
                  title="确认删除"
                  description={`确定要删除文件 "${file.filename}" 吗？`}
                  onConfirm={() => handleDelete(file.id, file.filename)}
                  okText="确认"
                  cancelText="取消"
                  okType="danger"
                >
                  <Button
                    type="text"
                    icon={<DeleteOutlined />}
                    danger
                    size="small"
                  />
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                avatar={getFileIcon(file)}
                title={
                  <Space>
                    <span>{file.filename}</span>
                    {getOCRStatusTag(file)}
                  </Space>
                }
                description={
                  <Space split="|">
                    <Text type="secondary">{formatFileSize(file.size)}</Text>
                    <Text type="secondary">{file.mime_type || file.mimeType}</Text>
                    <Text type="secondary">
                      {new Date((file as any).created_at || file.createdAt).toLocaleString('zh-CN')}
                    </Text>
                  </Space>
                }
              />
              
              {/* 上传进度 */}
              {uploadProgress[file.id] !== undefined && uploadProgress[file.id] < 100 && (
                <div style={{ width: 200, marginLeft: 16 }}>
                  <Progress percent={uploadProgress[file.id]} size="small" />
                </div>
              )}
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default FileUpload;