import React, { useState, useEffect } from 'react';
import {
  Card,
  Progress,
  Steps,
  Typography,
  Space,
  Button,
  Alert,
  Descriptions,
  Tag,
  Timeline,
  Spin,
} from 'antd';
import {
  CheckCircleOutlined,
  LoadingOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
  EyeOutlined,
} from '@ant-design/icons';

const { Title, Text } = Typography;
const { Step } = Steps;

export interface OCRTask {
  id: string;
  fileId: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  engine: string;
  startTime: string;
  endTime?: string;
  error?: string;
  result?: {
    totalPages: number;
    processedPages: number;
    extractedText: number;
    detectedTables: number;
    detectedImages: number;
    slicesGenerated: number;
  };
  logs: Array<{
    timestamp: string;
    level: 'info' | 'warning' | 'error';
    message: string;
  }>;
}

interface OCRProgressProps {
  task: OCRTask;
  onRetry?: () => void;
  onViewSlices?: () => void;
  onCancel?: () => void;
}

const OCRProgress: React.FC<OCRProgressProps> = ({
  task,
  onRetry,
  onViewSlices,
  onCancel,
}) => {
  const [showLogs, setShowLogs] = useState(false);

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'processing';
      case 'failed':
        return 'exception';
      case 'pending':
        return 'normal';
      default:
        return 'normal';
    }
  };

  // 获取状态文本
  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '处理完成';
      case 'processing':
        return '正在处理';
      case 'failed':
        return '处理失败';
      case 'pending':
        return '等待处理';
      default:
        return status;
    }
  };

  // 获取状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'processing':
        return <LoadingOutlined style={{ color: '#1677ff' }} />;
      case 'failed':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'pending':
        return <ClockCircleOutlined style={{ color: '#faad14' }} />;
      default:
        return null;
    }
  };

  // 计算处理时间
  const getProcessingTime = () => {
    const start = new Date(task.startTime);
    const end = task.endTime ? new Date(task.endTime) : new Date();
    const diff = Math.floor((end.getTime() - start.getTime()) / 1000);
    
    if (diff < 60) {
      return `${diff}秒`;
    } else if (diff < 3600) {
      return `${Math.floor(diff / 60)}分${diff % 60}秒`;
    } else {
      return `${Math.floor(diff / 3600)}小时${Math.floor((diff % 3600) / 60)}分`;
    }
  };

  // 获取处理步骤
  const getProcessingSteps = () => {
    const steps = [
      {
        title: '文件解析',
        description: '解析文档结构和页面',
        status: task.progress > 0 ? 'finish' : 'wait',
      },
      {
        title: '文本识别',
        description: '提取文档中的文本内容',
        status: task.progress > 25 ? 'finish' : task.progress > 0 ? 'process' : 'wait',
      },
      {
        title: '结构分析',
        description: '识别表格、图像等结构元素',
        status: task.progress > 50 ? 'finish' : task.progress > 25 ? 'process' : 'wait',
      },
      {
        title: '内容切片',
        description: '将内容分割为可管理的片段',
        status: task.progress > 75 ? 'finish' : task.progress > 50 ? 'process' : 'wait',
      },
      {
        title: '完成处理',
        description: '生成最终结果',
        status: task.status === 'completed' ? 'finish' : task.progress > 75 ? 'process' : 'wait',
      },
    ];

    return steps;
  };

  return (
    <Card
      title={
        <Space>
          {getStatusIcon(task.status)}
          <span>OCR处理进度</span>
          <Tag color={getStatusColor(task.status)}>
            {getStatusText(task.status)}
          </Tag>
        </Space>
      }
      extra={
        <Space>
          {task.status === 'completed' && onViewSlices && (
            <Button
              type="primary"
              icon={<EyeOutlined />}
              onClick={onViewSlices}
            >
              查看切片
            </Button>
          )}
          {task.status === 'failed' && onRetry && (
            <Button
              icon={<ReloadOutlined />}
              onClick={onRetry}
            >
              重试
            </Button>
          )}
          {task.status === 'processing' && onCancel && (
            <Button
              danger
              onClick={onCancel}
            >
              取消
            </Button>
          )}
        </Space>
      }
    >
      {/* 基本信息 */}
      <Descriptions column={2} style={{ marginBottom: 24 }}>
        <Descriptions.Item label="文件名">
          {task.filename}
        </Descriptions.Item>
        <Descriptions.Item label="OCR引擎">
          {task.engine}
        </Descriptions.Item>
        <Descriptions.Item label="开始时间">
          {new Date(task.startTime).toLocaleString('zh-CN')}
        </Descriptions.Item>
        <Descriptions.Item label="处理时间">
          {getProcessingTime()}
        </Descriptions.Item>
      </Descriptions>

      {/* 进度条 */}
      <div style={{ marginBottom: 24 }}>
        <Progress
          percent={task.progress}
          status={getStatusColor(task.status) as any}
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068',
          }}
          showInfo={true}
        />
      </div>

      {/* 处理步骤 */}
      <Steps
        current={Math.floor(task.progress / 20)}
        size="small"
        style={{ marginBottom: 24 }}
      >
        {getProcessingSteps().map((step, index) => (
          <Step
            key={index}
            title={step.title}
            description={step.description}
            status={step.status as any}
          />
        ))}
      </Steps>

      {/* 错误信息 */}
      {task.status === 'failed' && task.error && (
        <Alert
          message="处理失败"
          description={task.error}
          type="error"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* 处理结果 */}
      {task.status === 'completed' && task.result && (
        <Card
          title="处理结果"
          size="small"
          style={{ marginBottom: 24 }}
        >
          <Descriptions column={3} size="small">
            <Descriptions.Item label="总页数">
              {task.result.totalPages}
            </Descriptions.Item>
            <Descriptions.Item label="已处理页数">
              {task.result.processedPages}
            </Descriptions.Item>
            <Descriptions.Item label="提取文本量">
              {task.result.extractedText.toLocaleString()} 字符
            </Descriptions.Item>
            <Descriptions.Item label="检测到表格">
              {task.result.detectedTables} 个
            </Descriptions.Item>
            <Descriptions.Item label="检测到图像">
              {task.result.detectedImages} 个
            </Descriptions.Item>
            <Descriptions.Item label="生成切片">
              {task.result.slicesGenerated} 个
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      {/* MinerU实时处理控制台 */}
      <Card
        title={
          <Space>
            <span>MinerU处理控制台</span>
            {task.status === 'processing' && (
              <LoadingOutlined style={{ color: '#1677ff' }} />
            )}
          </Space>
        }
        size="small"
        style={{ marginBottom: 16 }}
        bodyStyle={{
          padding: 0,
          backgroundColor: '#1e1e1e',
          color: '#d4d4d4',
          fontFamily: 'Consolas, Monaco, "Courier New", monospace',
          fontSize: '12px',
          lineHeight: '1.5',
        }}
      >
        <div
          style={{
            maxHeight: '400px',
            minHeight: '200px',
            overflowY: 'auto',
            overflowX: 'hidden',
            padding: '12px',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}
          ref={(el) => {
            // 自动滚动到底部显示最新日志
            if (el && task.status === 'processing') {
              el.scrollTop = el.scrollHeight;
            }
          }}
        >
          {task.logs.length === 0 ? (
            <div style={{ color: '#6a9955', fontStyle: 'italic' }}>
              # 等待MinerU引擎输出...
            </div>
          ) : (
            task.logs.map((log, index) => {
              const timeStr = new Date(log.timestamp).toLocaleTimeString('zh-CN', { 
                hour12: false 
              });
              
              // 根据日志级别设置颜色
              const getLogColor = () => {
                if (log.level === 'error') return '#f48771';
                if (log.level === 'warning') return '#dcdcaa';
                if (log.message.includes('✓') || log.message.includes('成功') || log.message.includes('完成')) {
                  return '#4ec9b0';
                }
                if (log.message.includes('开始') || log.message.includes('初始化')) {
                  return '#569cd6';
                }
                return '#d4d4d4';
              };
              
              // 高亮关键信息
              const formatMessage = (msg: string) => {
                // 数字高亮
                msg = msg.replace(/(\d+)/g, '<span style="color: #b5cea8">$1</span>');
                // 文件名高亮
                msg = msg.replace(/([^\s]+\.(pdf|png|jpg|jpeg|md))/gi, '<span style="color: #ce9178">$1</span>');
                // 成功标记高亮
                msg = msg.replace(/(✓|✅|成功|完成)/g, '<span style="color: #4ec9b0; font-weight: bold">$1</span>');
                // 错误标记高亮
                msg = msg.replace(/(✗|❌|失败|错误|ERROR)/g, '<span style="color: #f48771; font-weight: bold">$1</span>');
                // 警告标记高亮
                msg = msg.replace(/(⚠|WARNING|警告)/g, '<span style="color: #dcdcaa; font-weight: bold">$1</span>');
                return msg;
              };
              
              return (
                <div
                  key={index}
                  style={{
                    marginBottom: '4px',
                    paddingLeft: '8px',
                    borderLeft: `2px solid ${log.level === 'error' ? '#f48771' : log.level === 'warning' ? '#dcdcaa' : '#3794ff'}`,
                  }}
                >
                  <span style={{ color: '#858585', marginRight: '8px' }}>
                    [{timeStr}]
                  </span>
                  <span 
                    style={{ color: getLogColor() }}
                    dangerouslySetInnerHTML={{ __html: formatMessage(log.message) }}
                  />
                </div>
              );
            })
          )}
          
          {/* 处理中的动画提示 */}
          {task.status === 'processing' && (
            <div style={{ color: '#569cd6', marginTop: '8px', animation: 'blink 1.5s infinite' }}>
              ▸ 处理中...
            </div>
          )}
        </div>
        
        {/* CSS动画 */}
        <style>{`
          @keyframes blink {
            0%, 50%, 100% { opacity: 1; }
            25%, 75% { opacity: 0.5; }
          }
        `}</style>
      </Card>

      {/* 实时状态指示器 */}
      {task.status === 'processing' && (
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Spin indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />} />
          <Text style={{ marginLeft: 8, color: '#1677ff' }}>
            正在处理中，请稍候...
          </Text>
        </div>
      )}
    </Card>
  );
};

export default OCRProgress;