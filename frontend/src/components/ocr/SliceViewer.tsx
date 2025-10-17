import React, { useState, useRef, useEffect } from 'react';
import {
  Card,
  Typography,
  Space,
  Tag,
  Button,
  Descriptions,
  Divider,
  Tooltip,
  message,
  Modal,
  Image,
} from 'antd';
import {
  FileTextOutlined,
  PictureOutlined,
  TableOutlined,
  CopyOutlined,
  FullscreenOutlined,
  HighlightOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { Slice } from '../../types';

const { Title, Text, Paragraph } = Typography;

interface SliceViewerProps {
  slice: Slice | null;
  originalFileUrl?: string;
  onHighlightInOriginal?: (slice: Slice) => void;
  onClose?: () => void;
}

const SliceViewer: React.FC<SliceViewerProps> = ({
  slice,
  originalFileUrl,
  onHighlightInOriginal,
  onClose,
}) => {
  const [showFullscreen, setShowFullscreen] = useState(false);
  const [highlightVisible, setHighlightVisible] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  // 如果没有选中的切片，显示空状态
  if (!slice) {
    return (
      <Card
        title="切片详情"
        style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
      >
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#8c8c8c',
          }}
        >
          <Space direction="vertical" align="center">
            <FileTextOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
            <Text type="secondary">请选择一个切片查看详情</Text>
          </Space>
        </div>
      </Card>
    );
  }

  // 获取切片类型信息
  const getSliceTypeInfo = (type: string) => {
    const typeMap = {
      paragraph: {
        icon: <FileTextOutlined style={{ color: '#1677ff' }} />,
        text: '段落',
        color: 'blue',
        description: '文档中的文本段落',
      },
      image: {
        icon: <PictureOutlined style={{ color: '#52c41a' }} />,
        text: '图像',
        color: 'green',
        description: '文档中的图片或图表',
      },
      table: {
        icon: <TableOutlined style={{ color: '#faad14' }} />,
        text: '表格',
        color: 'orange',
        description: '文档中的表格数据',
      },
    };
    return typeMap[type as keyof typeof typeMap] || {
      icon: <FileTextOutlined />,
      text: type,
      color: 'default',
      description: '未知类型',
    };
  };

  const typeInfo = getSliceTypeInfo(slice.sliceType);

  // 复制内容到剪贴板
  const handleCopyContent = async () => {
    try {
      await navigator.clipboard.writeText(slice.content);
      message.success('内容已复制到剪贴板');
    } catch (error) {
      message.error('复制失败');
    }
  };

  // 在原文件中高亮显示
  const handleHighlightInOriginal = () => {
    if (onHighlightInOriginal) {
      onHighlightInOriginal(slice);
      setHighlightVisible(true);
      setTimeout(() => setHighlightVisible(false), 3000);
    }
  };

  // 格式化内容显示
  const formatContent = (content: string, type: string) => {
    if (type === 'table') {
      // 如果是表格，尝试格式化显示
      const lines = content.split('\n');
      if (lines.length > 1) {
        return (
          <div style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
            {content}
          </div>
        );
      }
    }
    
    return (
      <Paragraph
        style={{
          whiteSpace: 'pre-wrap',
          lineHeight: 1.6,
          fontSize: '14px',
        }}
      >
        {content}
      </Paragraph>
    );
  };

  // 计算内容统计信息
  const getContentStats = () => {
    const charCount = slice.content.length;
    const wordCount = slice.content.split(/\s+/).filter(word => word.length > 0).length;
    const lineCount = slice.content.split('\n').length;
    
    return { charCount, wordCount, lineCount };
  };

  const stats = getContentStats();

  return (
    <>
      <Card
        title={
          <Space>
            {typeInfo.icon}
            <span>切片详情</span>
            <Tag color={typeInfo.color}>{typeInfo.text}</Tag>
          </Space>
        }
        extra={
          <Space>
            <Tooltip title="复制内容">
              <Button
                type="text"
                icon={<CopyOutlined />}
                onClick={handleCopyContent}
              />
            </Tooltip>
            {onHighlightInOriginal && (
              <Tooltip title="在原文件中高亮显示">
                <Button
                  type="text"
                  icon={<HighlightOutlined />}
                  onClick={handleHighlightInOriginal}
                  style={{
                    color: highlightVisible ? '#52c41a' : undefined,
                  }}
                />
              </Tooltip>
            )}
            <Tooltip title="全屏查看">
              <Button
                type="text"
                icon={<FullscreenOutlined />}
                onClick={() => setShowFullscreen(true)}
              />
            </Tooltip>
          </Space>
        }
        style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
        bodyStyle={{ flex: 1, display: 'flex', flexDirection: 'column' }}
      >
        {/* 基本信息 */}
        <Descriptions
          column={2}
          size="small"
          style={{ marginBottom: 16 }}
          bordered
        >
          <Descriptions.Item label="切片ID">
            <Text code style={{ fontSize: '12px' }}>
              {slice.id}
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label="类型">
            <Space>
              {typeInfo.icon}
              <Text>{typeInfo.text}</Text>
              <Tooltip title={typeInfo.description}>
                <InfoCircleOutlined style={{ color: '#8c8c8c' }} />
              </Tooltip>
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="页码">
            第 {slice.pageNumber} 页
          </Descriptions.Item>
          <Descriptions.Item label="位置">
            {slice.startOffset} - {slice.endOffset}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {new Date(slice.createdAt).toLocaleString('zh-CN')}
          </Descriptions.Item>
          <Descriptions.Item label="内容统计">
            <Space split={<Divider type="vertical" />}>
              <Text>{stats.charCount} 字符</Text>
              <Text>{stats.wordCount} 词</Text>
              <Text>{stats.lineCount} 行</Text>
            </Space>
          </Descriptions.Item>
        </Descriptions>

        <Divider />

        {/* 内容显示 */}
        <div
          ref={contentRef}
          style={{
            flex: 1,
            overflow: 'auto',
            padding: '16px',
            backgroundColor: '#fafafa',
            borderRadius: '8px',
            border: '1px solid #f0f0f0',
          }}
        >
          <Title level={5} style={{ marginBottom: 16 }}>
            切片内容
          </Title>
          {formatContent(slice.content, slice.sliceType)}
        </div>

        {/* 如果是图像类型，显示图像预览 */}
        {slice.sliceType === 'image' && originalFileUrl && (
          <div style={{ marginTop: 16 }}>
            <Title level={5}>图像预览</Title>
            <Image
              src={`${originalFileUrl}#page=${slice.pageNumber}&highlight=${slice.startOffset}-${slice.endOffset}`}
              alt="切片图像"
              style={{ maxWidth: '100%', maxHeight: '300px' }}
              placeholder={
                <div style={{ 
                  width: '100%', 
                  height: '200px', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  backgroundColor: '#f5f5f5',
                  border: '1px dashed #d9d9d9',
                  borderRadius: '8px',
                }}>
                  <Space direction="vertical" align="center">
                    <PictureOutlined style={{ fontSize: 32, color: '#d9d9d9' }} />
                    <Text type="secondary">图像加载中...</Text>
                  </Space>
                </div>
              }
            />
          </div>
        )}
      </Card>

      {/* 全屏模态框 */}
      <Modal
        title={
          <Space>
            {typeInfo.icon}
            <span>切片详情 - {typeInfo.text}</span>
          </Space>
        }
        open={showFullscreen}
        onCancel={() => setShowFullscreen(false)}
        width="90vw"
        style={{ top: 20 }}
        footer={[
          <Button key="copy" icon={<CopyOutlined />} onClick={handleCopyContent}>
            复制内容
          </Button>,
          <Button key="close" onClick={() => setShowFullscreen(false)}>
            关闭
          </Button>,
        ]}
      >
        <div style={{ maxHeight: '70vh', overflow: 'auto' }}>
          <Descriptions column={3} size="small" style={{ marginBottom: 16 }}>
            <Descriptions.Item label="切片ID">
              {slice.id}
            </Descriptions.Item>
            <Descriptions.Item label="页码">
              第 {slice.pageNumber} 页
            </Descriptions.Item>
            <Descriptions.Item label="位置">
              {slice.startOffset} - {slice.endOffset}
            </Descriptions.Item>
          </Descriptions>
          
          <Divider />
          
          <div
            style={{
              padding: '16px',
              backgroundColor: '#fafafa',
              borderRadius: '8px',
              border: '1px solid #f0f0f0',
            }}
          >
            {formatContent(slice.content, slice.sliceType)}
          </div>
        </div>
      </Modal>
    </>
  );
};

export default SliceViewer;