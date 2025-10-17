import React, { useState, useEffect } from 'react';
import {
  Row,
  Col,
  Card,
  Typography,
  Space,
  Button,
  message,
  Spin,
  Alert,
  Tabs,
} from 'antd';
import {
  ArrowLeftOutlined,
  ReloadOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { FileInfo, Slice } from '../../types';
import OCREngineSelector, { OCREngineConfig } from './OCREngineSelector';
import OCRProgress, { OCRTask } from './OCRProgress';
import SliceList from './SliceList';
import SliceViewer from './SliceViewer';
import { fileService } from '../../services/fileService';
import { useAccessibility, ScreenReaderOnly } from '../../hooks/useAccessibility';
import '../../styles/accessibility.css';

const { Title } = Typography;

interface OCRProcessingProps {
  file: FileInfo;
  onBack: () => void;
}

const OCRProcessing: React.FC<OCRProcessingProps> = ({
  file,
  onBack,
}) => {
  const [activeTab, setActiveTab] = useState('config');
  const [ocrTask, setOcrTask] = useState<OCRTask | null>(null);
  const [slices, setSlices] = useState<Slice[]>([]);
  const [selectedSlice, setSelectedSlice] = useState<Slice | null>(null);
  const [loading, setLoading] = useState(false);
  const [slicesLoading, setSlicesLoading] = useState(false);
  
  const { announceToScreenReader, generateId, useKeyboardNavigation } = useAccessibility();
  const headingId = generateId('ocr-heading');
  const statusId = generateId('ocr-status');

  // 模拟WebSocket连接用于实时更新OCR进度
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (ocrTask && ocrTask.status === 'processing') {
      interval = setInterval(() => {
        // 模拟进度更新
        setOcrTask(prev => {
          if (!prev || prev.status !== 'processing') return prev;
          
          const newProgress = Math.min(prev.progress + Math.random() * 10, 95);
          const newLogs = [...prev.logs];
          
          // 随机添加日志
          if (Math.random() > 0.7) {
            newLogs.push({
              timestamp: new Date().toISOString(),
              level: 'info',
              message: getRandomLogMessage(newProgress),
            });
          }
          
          return {
            ...prev,
            progress: newProgress,
            logs: newLogs,
          };
        });
      }, 2000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [ocrTask]);

  // 获取随机日志消息
  const getRandomLogMessage = (progress: number): string => {
    const messages = [
      '正在解析文档结构...',
      '检测到文本区域',
      '正在识别文字内容...',
      '处理表格结构...',
      '提取图像信息...',
      '生成文档切片...',
      '优化识别结果...',
    ];
    
    if (progress < 20) return messages[0];
    if (progress < 40) return messages[1];
    if (progress < 60) return messages[2];
    if (progress < 80) return messages[3];
    return messages[Math.floor(Math.random() * messages.length)];
  };

  // 开始OCR处理
  const handleStartOCR = async (config: OCREngineConfig) => {
    setLoading(true);
    announceToScreenReader(`开始使用 ${config.engine} 引擎处理文件 ${file.filename}`, 'assertive');
    
    try {
      // 调用OCR服务
      await fileService.triggerOCR(file.id, config.engine);
      
      // 创建OCR任务对象
      const newTask: OCRTask = {
        id: `ocr_${file.id}_${Date.now()}`,
        fileId: file.id,
        filename: file.filename,
        status: 'processing',
        progress: 0,
        engine: config.engine,
        startTime: new Date().toISOString(),
        logs: [
          {
            timestamp: new Date().toISOString(),
            level: 'info',
            message: `开始使用 ${config.engine} 引擎处理文件`,
          },
        ],
      };
      
      setOcrTask(newTask);
      setActiveTab('progress');
      announceToScreenReader('OCR处理已开始，正在切换到进度页面');
      
      // 模拟处理完成
      setTimeout(() => {
        setOcrTask(prev => prev ? {
          ...prev,
          status: 'completed',
          progress: 100,
          endTime: new Date().toISOString(),
          result: {
            totalPages: 10,
            processedPages: 10,
            extractedText: 15420,
            detectedTables: 3,
            detectedImages: 5,
            slicesGenerated: 25,
          },
          logs: [
            ...prev.logs,
            {
              timestamp: new Date().toISOString(),
              level: 'info',
              message: 'OCR处理完成，生成25个切片',
            },
          ],
        } : null);
        
        announceToScreenReader('OCR处理已完成，生成了25个切片', 'assertive');
        // 加载切片数据
        loadSlices();
      }, 10000);
      
    } catch (error) {
      const errorMessage = '启动OCR处理失败';
      message.error(errorMessage);
      announceToScreenReader(errorMessage, 'assertive');
      setOcrTask(prev => prev ? {
        ...prev,
        status: 'failed',
        error: '处理失败：' + (error as Error).message,
      } : null);
    } finally {
      setLoading(false);
    }
  };

  // 加载切片数据
  const loadSlices = async () => {
    setSlicesLoading(true);
    try {
      const sliceData = await fileService.getFileSlices(file.id);
      setSlices(sliceData);
      setActiveTab('slices');
    } catch (error) {
      message.error('加载切片数据失败');
    } finally {
      setSlicesLoading(false);
    }
  };

  // 重试OCR处理
  const handleRetryOCR = () => {
    setOcrTask(null);
    setActiveTab('config');
  };

  // 查看切片
  const handleViewSlices = () => {
    loadSlices();
  };

  // 取消OCR处理
  const handleCancelOCR = () => {
    if (ocrTask) {
      setOcrTask({
        ...ocrTask,
        status: 'failed',
        error: '用户取消处理',
      });
    }
  };

  // 选择切片
  const handleSliceSelect = (slice: Slice) => {
    setSelectedSlice(slice);
    announceToScreenReader(`已选择切片：${slice.content.substring(0, 50)}...`);
  };

  // 高亮切片
  const handleSliceHighlight = (slice: Slice) => {
    // 这里可以实现在原文件中高亮显示的逻辑
    console.log('Highlighting slice:', slice.id);
  };

  // 在原文件中高亮显示切片
  const handleHighlightInOriginal = (slice: Slice) => {
    const message_text = `正在原文件中高亮显示切片 (页码: ${slice.pageNumber}, 位置: ${slice.startOffset}-${slice.endOffset})`;
    message.info(message_text);
    announceToScreenReader(message_text);
    // 这里可以实现具体的高亮逻辑
  };

  // 标签页切换处理
  const handleTabChange = (key: string) => {
    setActiveTab(key);
    announceToScreenReader(`已切换到${getTabLabel(key)}页面`);
  };

  const getTabLabel = (key: string): string => {
    const labels: Record<string, string> = {
      'config': '引擎配置',
      'progress': '处理进度',
      'slices': '切片管理'
    };
    return labels[key] || key;
  };

  // 键盘导航支持
  useKeyboardNavigation(
    // Escape - 返回上级
    onBack,
    // Enter - 在当前上下文中执行主要操作
    () => {
      if (activeTab === 'config' && !loading) {
        // 在配置页面，Enter键可以触发开始处理（如果有默认配置）
      } else if (activeTab === 'progress' && ocrTask?.status === 'completed') {
        handleViewSlices();
      }
    }
  );

  return (
    <div role="main" aria-labelledby={headingId}>
      {/* 头部 */}
      <Card style={{ marginBottom: 16 }} role="banner">
        <Space>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={onBack}
            aria-label="返回上一页"
          >
            返回
          </Button>
          <Title level={4} id={headingId} style={{ margin: 0 }}>
            OCR处理 - {file.filename}
          </Title>
        </Space>
      </Card>

      {/* 文件状态提示 */}
      {file.ocrStatus === 'completed' && (
        <Alert
          message="文件已完成OCR处理"
          description="您可以查看已生成的切片，或重新配置OCR引擎进行处理"
          type="success"
          showIcon
          role="status"
          aria-live="polite"
          style={{ marginBottom: 16 }}
          action={
            <Button 
              size="small" 
              onClick={loadSlices}
              aria-label="查看已生成的切片"
            >
              查看切片
            </Button>
          }
        />
      )}

      {file.ocrStatus === 'failed' && (
        <Alert
          message="OCR处理失败"
          description="请检查文件格式或重新配置OCR引擎"
          type="error"
          showIcon
          role="alert"
          aria-live="assertive"
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 主要内容 */}
      <Tabs
        activeKey={activeTab}
        onChange={handleTabChange}
        role="tablist"
        aria-label="OCR处理功能选项卡"
        items={[
          {
            key: 'config',
            label: (
              <Space>
                <SettingOutlined />
                <span>引擎配置</span>
              </Space>
            ),
            children: (
              <OCREngineSelector
                fileId={file.id}
                onStartOCR={handleStartOCR}
                loading={loading}
              />
            ),
          },
          {
            key: 'progress',
            label: (
              <Space>
                <ReloadOutlined />
                <span>处理进度</span>
              </Space>
            ),
            disabled: !ocrTask,
            children: ocrTask ? (
              <OCRProgress
                task={ocrTask}
                onRetry={handleRetryOCR}
                onViewSlices={handleViewSlices}
                onCancel={handleCancelOCR}
              />
            ) : (
              <Card>
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <Space direction="vertical">
                    <ReloadOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
                    <span style={{ color: '#8c8c8c' }}>暂无处理任务</span>
                  </Space>
                </div>
              </Card>
            ),
          },
          {
            key: 'slices',
            label: (
              <Space>
                <span>切片管理</span>
                {slices.length > 0 && (
                  <span style={{ 
                    backgroundColor: '#1677ff', 
                    color: 'white', 
                    borderRadius: '10px', 
                    padding: '2px 6px', 
                    fontSize: '12px' 
                  }}>
                    {slices.length}
                  </span>
                )}
              </Space>
            ),
            children: (
              <Row gutter={16}>
                <Col span={12}>
                  <SliceList
                    fileId={file.id}
                    slices={slices}
                    loading={slicesLoading}
                    onSliceSelect={handleSliceSelect}
                    onSliceHighlight={handleSliceHighlight}
                    selectedSliceId={selectedSlice?.id}
                  />
                </Col>
                <Col span={12}>
                  <SliceViewer
                    slice={selectedSlice}
                    originalFileUrl={`/api/files/${file.id}/preview`}
                    onHighlightInOriginal={handleHighlightInOriginal}
                  />
                </Col>
              </Row>
            ),
          },
        ]}
      />
    </div>
  );
};

export default OCRProcessing;