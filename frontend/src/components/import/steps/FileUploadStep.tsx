/**
 * 文件上传步骤组件
 */
import React, { useState } from 'react';
import { 
  Upload, 
  Button, 
  Card, 
  Radio, 
  Input, 
  Select, 
  Space, 
  Alert, 
  Progress,
  Typography,
  Divider
} from 'antd';
import { 
  InboxOutlined, 
  UploadOutlined, 
  FileTextOutlined,
  CheckCircleOutlined 
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { useImportStore } from '../../../stores/importStore';
import { useProjectStore } from '../../../stores/projectStore';

const { Dragger } = Upload;
const { Title, Text } = Typography;
const { Option } = Select;

export const FileUploadStep: React.FC = () => {
  const {
    uploadedFile,
    filePath,
    loading,
    error,
    currentTask,
    importMode,
    targetProjectId,
    newProjectName,
    uploadFile,
    validateFile,
    setImportMode,
    setTargetProject,
    setNewProjectName,
  } = useImportStore();

  const { projects } = useProjectStore();
  const [fileList, setFileList] = useState<any[]>([]);

  // 文件上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.json,.zip',
    fileList,
    beforeUpload: (file) => {
      // 检查文件类型
      const isValidType = file.type === 'application/json' || 
                         file.type === 'application/zip' ||
                         file.name.endsWith('.json') ||
                         file.name.endsWith('.zip');
      
      if (!isValidType) {
        alert('只支持 JSON 和 ZIP 格式的文件！');
        return false;
      }

      // 检查文件大小 (100MB)
      const isValidSize = file.size / 1024 / 1024 < 100;
      if (!isValidSize) {
        alert('文件大小不能超过 100MB！');
        return false;
      }

      // 上传文件
      uploadFile(file);
      setFileList([file]);
      return false; // 阻止默认上传行为
    },
    onRemove: () => {
      setFileList([]);
    },
  };

  // 处理验证文件
  const handleValidateFile = async () => {
    if (!filePath) return;
    await validateFile();
  };

  // 渲染上传区域
  const renderUploadArea = () => {
    if (uploadedFile && filePath) {
      return (
        <Card className="mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileTextOutlined className="text-2xl text-blue-500" />
              <div>
                <div className="font-medium">{uploadedFile.name}</div>
                <div className="text-sm text-gray-500">
                  {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                </div>
              </div>
            </div>
            <CheckCircleOutlined className="text-2xl text-green-500" />
          </div>
        </Card>
      );
    }

    return (
      <Dragger {...uploadProps} className="mb-4">
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p className="ant-upload-hint">
          支持 JSON 和 ZIP 格式的导出文件，文件大小不超过 100MB
        </p>
      </Dragger>
    );
  };

  // 渲染导入模式选择
  const renderImportModeSelection = () => {
    return (
      <Card title="导入模式" className="mb-4">
        <Radio.Group 
          value={importMode} 
          onChange={(e) => setImportMode(e.target.value)}
          className="w-full"
        >
          <Space direction="vertical" className="w-full">
            <Radio value="create_new">
              <div>
                <div className="font-medium">创建新项目</div>
                <div className="text-sm text-gray-500">
                  将导入的数据创建为一个新的项目
                </div>
              </div>
            </Radio>
            
            <Radio value="merge">
              <div>
                <div className="font-medium">合并到现有项目</div>
                <div className="text-sm text-gray-500">
                  将导入的数据合并到现有项目中
                </div>
              </div>
            </Radio>
            
            <Radio value="replace" disabled>
              <div>
                <div className="font-medium">替换现有项目（暂不支持）</div>
                <div className="text-sm text-gray-500">
                  完全替换现有项目的数据
                </div>
              </div>
            </Radio>
          </Space>
        </Radio.Group>

        {/* 新项目名称输入 */}
        {importMode === 'create_new' && (
          <div className="mt-4">
            <Text strong>新项目名称:</Text>
            <Input
              placeholder="请输入新项目名称"
              value={newProjectName || ''}
              onChange={(e) => setNewProjectName(e.target.value)}
              className="mt-2"
            />
          </div>
        )}

        {/* 目标项目选择 */}
        {importMode === 'merge' && (
          <div className="mt-4">
            <Text strong>目标项目:</Text>
            <Select
              placeholder="请选择要合并的目标项目"
              value={targetProjectId}
              onChange={setTargetProject}
              className="w-full mt-2"
              showSearch
              filterOption={(input, option) =>
                (option?.children as unknown as string)
                  ?.toLowerCase()
                  ?.includes(input.toLowerCase())
              }
            >
              {projects.map((project) => (
                <Option key={project.id} value={project.id}>
                  {project.name}
                </Option>
              ))}
            </Select>
          </div>
        )}
      </Card>
    );
  };

  // 渲染验证状态
  const renderValidationStatus = () => {
    if (!currentTask) return null;

    return (
      <Card title="文件验证" className="mb-4">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span>验证状态:</span>
            <span className={`font-medium ${
              currentTask.status === 'completed' ? 'text-green-600' :
              currentTask.status === 'failed' ? 'text-red-600' :
              'text-blue-600'
            }`}>
              {currentTask.status === 'completed' ? '验证完成' :
               currentTask.status === 'failed' ? '验证失败' :
               '验证中...'}
            </span>
          </div>
          
          {currentTask.status !== 'completed' && currentTask.status !== 'failed' && (
            <Progress percent={Math.round(currentTask.progress)} />
          )}
          
          {currentTask.message && (
            <div className="text-sm text-gray-600">
              {currentTask.message}
            </div>
          )}
        </div>
      </Card>
    );
  };

  // 检查是否可以进行下一步
  const canProceed = () => {
    if (!uploadedFile || !filePath) return false;
    if (importMode === 'create_new' && !newProjectName?.trim()) return false;
    if (importMode === 'merge' && !targetProjectId) return false;
    return currentTask?.status === 'completed';
  };

  return (
    <div className="space-y-6">
      <div>
        <Title level={3}>上传导入文件</Title>
        <Text type="secondary">
          请选择要导入的项目数据文件。支持通过导出功能生成的 JSON 或 ZIP 格式文件。
        </Text>
      </div>

      {renderUploadArea()}
      
      {uploadedFile && filePath && (
        <>
          {renderImportModeSelection()}
          
          <Divider />
          
          <div className="flex justify-between items-center">
            <div>
              {!currentTask && (
                <Alert
                  message="请先验证文件"
                  description="在继续之前，需要验证文件格式和内容的有效性"
                  type="info"
                  showIcon
                />
              )}
            </div>
            
            <Space>
              {!currentTask ? (
                <Button
                  type="primary"
                  icon={<UploadOutlined />}
                  onClick={handleValidateFile}
                  loading={loading}
                  disabled={!uploadedFile || !filePath}
                >
                  验证文件
                </Button>
              ) : (
                <Button
                  type="primary"
                  disabled={!canProceed()}
                  onClick={() => {
                    // 这里会由父组件处理步骤切换
                  }}
                >
                  下一步：分析差异
                </Button>
              )}
            </Space>
          </div>
          
          {renderValidationStatus()}
        </>
      )}
    </div>
  );
};