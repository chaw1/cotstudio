/**
 * 数据导出页面
 */
import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Row, 
  Col, 
  Button, 
  Space, 
  message, 
  Modal,
  Divider
} from 'antd';
import { 
  ExportOutlined, 
  InboxOutlined, 
  SettingOutlined,
  HistoryOutlined
} from '@ant-design/icons';
import { useResponsiveBreakpoint } from '../hooks/useResponsiveBreakpoint';

import ProjectSelector from '../components/Export/ProjectSelector';
import FormatSelector from '../components/Export/FormatSelector';
import ExportOptions, { ExportOptionsData } from '../components/Export/ExportOptions';
import ExportProgress from '../components/Export/ExportProgress';
import ExportHistory from '../components/Export/ExportHistory';

import { 
  ExportFormat, 
  ExportRequest, 
  ExportTaskResponse, 
  Project 
} from '../types/export';
import exportService from '../services/exportService';

const { Title, Text } = Typography;

const Export: React.FC = () => {
  const { isMobile, isTablet } = useResponsiveBreakpoint();
  
  // 状态管理
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [selectedProjectInfo, setSelectedProjectInfo] = useState<Project | null>(null);
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>(ExportFormat.JSON);
  const [exportOptions, setExportOptions] = useState<ExportOptionsData>({
    include_metadata: true,
    include_files: false,
    include_kg_data: false,
    cot_status_filter: []
  });
  
  const [currentTask, setCurrentTask] = useState<ExportTaskResponse | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);

  // 处理项目选择
  const handleProjectChange = (projectId: string, project: Project) => {
    setSelectedProject(projectId);
    setSelectedProjectInfo(project);
    // 重置当前任务状态
    setCurrentTask(null);
  };

  // 处理格式选择
  const handleFormatChange = (format: ExportFormat) => {
    setSelectedFormat(format);
  };

  // 处理选项变更
  const handleOptionsChange = (options: ExportOptionsData) => {
    setExportOptions(options);
  };

  // 开始导出
  const handleStartExport = async () => {
    if (!selectedProject) {
      message.warning('请先选择要导出的项目');
      return;
    }

    const exportRequest: ExportRequest = {
      project_id: selectedProject,
      format: selectedFormat,
      ...exportOptions
    };

    try {
      setIsExporting(true);
      
      // 创建导出任务
      const task = await exportService.exportProject(exportRequest);
      setCurrentTask(task);
      
      message.success('导出任务已创建，正在处理...');
      
      // 开始轮询任务状态
      await exportService.pollTaskStatus(
        task.task_id,
        (updatedTask) => {
          setCurrentTask(updatedTask);
        }
      );
      
      message.success('导出完成！');
      
    } catch (error: any) {
      message.error('导出失败: ' + error.message);
      console.error('Export error:', error);
    } finally {
      setIsExporting(false);
    }
  };

  // 创建项目包
  const handleCreatePackage = async () => {
    if (!selectedProject) {
      message.warning('请先选择要导出的项目');
      return;
    }

    const exportRequest: ExportRequest = {
      project_id: selectedProject,
      format: selectedFormat,
      ...exportOptions
    };

    try {
      setIsExporting(true);
      
      const task = await exportService.createProjectPackage(exportRequest);
      setCurrentTask(task);
      
      message.success('项目包创建任务已启动...');
      
      await exportService.pollTaskStatus(
        task.task_id,
        (updatedTask) => {
          setCurrentTask(updatedTask);
        }
      );
      
      message.success('项目包创建完成！');
      
    } catch (error: any) {
      message.error('创建项目包失败: ' + error.message);
      console.error('Package creation error:', error);
    } finally {
      setIsExporting(false);
    }
  };

  // 取消导出任务
  const handleCancelTask = async () => {
    if (!currentTask) return;

    try {
      await exportService.cancelTask(currentTask.task_id);
      setCurrentTask(null);
      setIsExporting(false);
      message.success('任务已取消');
    } catch (error: any) {
      message.error('取消任务失败: ' + error.message);
    }
  };

  // 下载文件
  const handleDownload = (downloadUrl: string) => {
    window.open(downloadUrl, '_blank');
    message.success('文件下载已开始');
  };

  // 重置导出状态
  const handleReset = () => {
    setCurrentTask(null);
    setIsExporting(false);
  };

  // 检查是否可以开始导出
  const canStartExport = selectedProject && !isExporting;

  return (
    <div className="fade-in work-area-adaptive" style={{ 
      padding: isMobile ? '16px' : '24px',
      maxWidth: '100%',
      overflow: 'hidden'
    }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: isMobile ? '16px' : '24px' }}>
        <Title level={isMobile ? 3 : 2} style={{ margin: 0 }}>
          <ExportOutlined style={{ marginRight: '8px' }} />
          数据导出
        </Title>
        <Text type="secondary" style={{ 
          fontSize: isMobile ? '12px' : '14px',
          display: 'block',
          marginTop: '4px',
          lineHeight: 1.4
        }}>
          导出项目数据为不同格式的文件，支持多种导出选项和实时进度跟踪
        </Text>
      </div>

      <Row gutter={isMobile ? [16, 16] : [24, 24]}>
        {/* 左侧配置区域 */}
        <Col xs={24} lg={16} order={isMobile ? 1 : 1}>
          <Space 
            direction="vertical" 
            style={{ width: '100%' }} 
            size={isMobile ? 'middle' : 'large'}
          >
            {/* 项目选择 */}
            <ProjectSelector
              selectedProject={selectedProject}
              onProjectChange={handleProjectChange}
            />

            {/* 格式选择 */}
            <FormatSelector
              selectedFormat={selectedFormat}
              onFormatChange={handleFormatChange}
            />

            {/* 高级选项 */}
            <div>
              <Button
                type="link"
                icon={<SettingOutlined />}
                onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
                style={{ 
                  padding: 0, 
                  marginBottom: '12px',
                  fontSize: isMobile ? '12px' : '14px'
                }}
                size={isMobile ? 'small' : 'middle'}
              >
                {showAdvancedOptions ? '隐藏' : '显示'}高级选项
              </Button>
              
              {showAdvancedOptions && (
                <ExportOptions
                  options={exportOptions}
                  onOptionsChange={handleOptionsChange}
                />
              )}
            </div>

            {/* 操作按钮 */}
            <div style={{ 
              padding: isMobile ? '12px' : '16px', 
              backgroundColor: '#fafafa', 
              borderRadius: '8px',
              border: '1px solid #d9d9d9'
            }}>
              <Space 
                size={isMobile ? 'small' : 'middle'}
                direction={isMobile ? 'vertical' : 'horizontal'}
                style={{ width: isMobile ? '100%' : 'auto' }}
              >
                <Button
                  type="primary"
                  size={isMobile ? 'middle' : 'large'}
                  icon={<ExportOutlined />}
                  onClick={handleStartExport}
                  disabled={!canStartExport}
                  loading={isExporting}
                  className="modern-button"
                  style={{ width: isMobile ? '100%' : 'auto' }}
                >
                  开始导出
                </Button>

                <Button
                  size={isMobile ? 'middle' : 'large'}
                  icon={<InboxOutlined />}
                  onClick={handleCreatePackage}
                  disabled={!canStartExport}
                  loading={isExporting}
                  className="modern-button"
                  style={{ width: isMobile ? '100%' : 'auto' }}
                >
                  创建项目包
                </Button>
              </Space>

              <div style={{ 
                marginTop: '12px', 
                fontSize: isMobile ? '11px' : '12px', 
                color: '#666',
                lineHeight: 1.4
              }}>
                <div>• <strong>开始导出</strong>：导出选定格式的单个文件</div>
                <div>• <strong>创建项目包</strong>：创建包含多种格式和原始文件的完整项目包</div>
              </div>
            </div>
          </Space>
        </Col>

        {/* 右侧状态和历史区域 */}
        <Col xs={24} lg={8} order={isMobile ? 2 : 2}>
          <Space 
            direction="vertical" 
            style={{ width: '100%' }} 
            size={isMobile ? 'middle' : 'large'}
          >
            {/* 导出进度 */}
            {currentTask && (
              <ExportProgress
                task={currentTask}
                onCancel={handleCancelTask}
                onDownload={handleDownload}
                onReset={handleReset}
              />
            )}

            {/* 导出历史 */}
            <ExportHistory
              projectId={selectedProject}
              onRedownload={(item) => {
                message.success(`重新下载 ${exportService.getFormatDisplayName(item.format)} 文件`);
              }}
            />
          </Space>
        </Col>
      </Row>
    </div>
  );
};

export default Export;