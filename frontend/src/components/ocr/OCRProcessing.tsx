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

  // 轮询后端获取真实的OCR状态
  useEffect(() => {
    let interval: NodeJS.Timeout;
    let pollCount = 0;
    
    if (ocrTask && ocrTask.status === 'processing') {
      interval = setInterval(async () => {
        try {
          pollCount++;
          
          // 获取文件最新OCR状态
          const statusData = await fileService.getFileOCRStatus(file.id);
          
          // 根据轮询次数添加状态更新日志
          const addStatusLog = (message: string, level: 'info' | 'warning' | 'error' = 'info') => {
            setOcrTask(prev => prev ? {
              ...prev,
              logs: [
                ...prev.logs,
                {
                  timestamp: new Date().toISOString(),
                  level,
                  message,
                },
              ],
            } : null);
          };
          
          // 定期添加心跳日志(每15秒一次)
          if (pollCount % 7 === 0 && statusData.ocr_status === 'PROCESSING') {
            addStatusLog(`▸ MinerU引擎正在处理中... (已处理${Math.floor(pollCount * 2 / 60)}分${(pollCount * 2) % 60}秒)`);
          }
          
          // 检查OCR状态
          if (statusData.ocr_status === 'COMPLETED') {
            // OCR完成,获取切片数量
            const slicesData = await fileService.getFileSlices(file.id);
            
            setOcrTask(prev => prev ? {
              ...prev,
              status: 'completed',
              progress: 100,
              endTime: new Date().toISOString(),
              result: {
                totalPages: slicesData.length || 0,
                processedPages: slicesData.length || 0,
                extractedText: statusData.ocr_result?.length || 0,
                detectedTables: 0,
                detectedImages: 0,
                slicesGenerated: slicesData.length || 0,
              },
              logs: [
                ...prev.logs,
                {
                  timestamp: new Date().toISOString(),
                  level: 'info',
                  message: `✓ OCR处理完成！生成${slicesData.length || 0}个切片，提取${statusData.ocr_result?.length || 0}个字符`,
                },
              ],
            } : null);
            
            announceToScreenReader(`OCR处理已完成，生成了${slicesData.length || 0}个切片`, 'assertive');
            // 加载切片数据
            loadSlices();
          } else if (statusData.ocr_status === 'FAILED') {
            // OCR失败
            const errorMsg = statusData.ocr_result || 'OCR处理失败';
            
            setOcrTask(prev => prev ? {
              ...prev,
              status: 'failed',
              progress: 0,
              endTime: new Date().toISOString(),
              error: errorMsg,
              logs: [
                ...prev.logs,
                {
                  timestamp: new Date().toISOString(),
                  level: 'error',
                  message: `✗ OCR处理失败: ${errorMsg}`,
                },
                {
                  timestamp: new Date().toISOString(),
                  level: 'error',
                  message: '请检查PDF文件格式或尝试更换OCR引擎',
                },
              ],
            } : null);
            
            message.error(`OCR处理失败: ${errorMsg}`);
            announceToScreenReader('OCR处理失败', 'assertive');
          }
          // 如果还在处理中(PROCESSING),继续轮询
        } catch (error) {
          console.error('获取OCR状态失败:', error);
          setOcrTask(prev => prev ? {
            ...prev,
            logs: [
              ...prev.logs,
              {
                timestamp: new Date().toISOString(),
                level: 'warning',
                message: `⚠ 轮询状态时出错: ${error}`,
              },
            ],
          } : null);
        }
      }, 2000); // 每2秒轮询一次
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [ocrTask, file.id]);

  // 开始OCR处理
  const handleStartOCR = async (config: OCREngineConfig) => {
    setLoading(true);
    announceToScreenReader(`开始使用 ${config.engine} 引擎处理文件 ${file.filename}`, 'assertive');
    
    try {
      // 准备引擎配置参数
      const engineConfig: any = {};
      
      // 如果是MinerU引擎，添加专用配置
      if (config.engine === 'mineru') {
        engineConfig.use_gpu = config.use_gpu;
        engineConfig.recognition_mode = config.recognition_mode;
        engineConfig.backend = config.backend;
        engineConfig.device = config.device;
        engineConfig.batch_size = config.batch_size;
        engineConfig.output_format = config.output_format;
      }
      
      // 调用OCR服务
      await fileService.triggerOCR(file.id, config.engine, engineConfig);
      
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