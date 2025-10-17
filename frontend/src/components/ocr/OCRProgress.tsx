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

      {/* 处理日志 */}
      {task.logs.length > 0 && (
        <Card
          title="处理日志"
          size="small"
          extra={
            <Button
              type="link"
              onClick={() => setShowLogs(!showLogs)}
            >
              {showLogs ? '隐藏日志' : '显示日志'}
            </Button>
          }
        >
          {showLogs && (
            <Timeline
              mode="left"
              style={{ maxHeight: 300, overflowY: 'auto' }}
            >
              {task.logs.map((log, index) => (
                <Timeline.Item
                  key={index}
                  color={
                    log.level === 'error' ? 'red' :
                    log.level === 'warning' ? 'orange' : 'blue'
                  }
                  label={new Date(log.timestamp).toLocaleTimeString('zh-CN')}
                >
                  <Text
                    type={
                      log.level === 'error' ? 'danger' :
                      log.level === 'warning' ? 'warning' : 'secondary'
                    }
                  >
                    {log.message}
                  </Text>
                </Timeline.Item>
              ))}
            </Timeline>
          )}
        </Card>
      )}

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