/**
 * 导入向导组件
 */
import React, { useEffect } from 'react';
import { Steps, Card, Button, Space, Alert, Spin } from 'antd';
import { ArrowLeftOutlined, ArrowRightOutlined } from '@ant-design/icons';
import { useImportStore } from '../../stores/importStore';
import { FileUploadStep } from './steps/FileUploadStep';
import { DifferenceAnalysisStep } from './steps/DifferenceAnalysisStep';
import { ImportConfirmationStep } from './steps/ImportConfirmationStep';
import { ImportResultStep } from './steps/ImportResultStep';

const { Step } = Steps;

export const ImportWizard: React.FC = () => {
  const {
    currentStep,
    loading,
    error,
    currentTask,
    setCurrentStep,
    clearError,
    reset,
    cancelTask,
  } = useImportStore();

  // 步骤配置
  const steps = [
    {
      key: 'upload',
      title: '上传文件',
      description: '选择并上传导入文件',
    },
    {
      key: 'analyze',
      title: '分析差异',
      description: '分析数据差异和冲突',
    },
    {
      key: 'confirm',
      title: '确认导入',
      description: '确认导入设置和解决冲突',
    },
    {
      key: 'complete',
      title: '导入完成',
      description: '查看导入结果',
    },
  ];

  const currentStepIndex = steps.findIndex(step => step.key === currentStep);

  // 渲染当前步骤内容
  const renderStepContent = () => {
    switch (currentStep) {
      case 'upload':
      case 'validate':
        return <FileUploadStep />;
      case 'analyze':
        return <DifferenceAnalysisStep />;
      case 'confirm':
        return <ImportConfirmationStep />;
      case 'import':
        return (
          <div className="text-center py-8">
            <Spin size="large" />
            <div className="mt-4">
              <h3>正在导入数据...</h3>
              <p>请耐心等待，这可能需要几分钟时间</p>
              {currentTask && (
                <div className="mt-4">
                  <div className="text-sm text-gray-600">
                    进度: {Math.round(currentTask.progress)}%
                  </div>
                  {currentTask.message && (
                    <div className="text-sm text-gray-500 mt-1">
                      {currentTask.message}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      case 'complete':
        return <ImportResultStep />;
      default:
        return null;
    }
  };

  // 处理步骤导航
  const handleStepChange = (step: number) => {
    const stepKey = steps[step]?.key;
    if (stepKey && !loading) {
      setCurrentStep(stepKey as any);
    }
  };

  // 处理取消操作
  const handleCancel = async () => {
    if (currentTask && (currentTask.status === 'pending' || currentTask.status === 'analyzing' || currentTask.status === 'importing')) {
      await cancelTask();
    }
    reset();
  };

  // 清理错误状态
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        clearError();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold">数据导入</h1>
          <Space>
            <Button 
              icon={<ArrowLeftOutlined />} 
              onClick={handleCancel}
              disabled={loading}
            >
              取消
            </Button>
          </Space>
        </div>

        {/* 步骤指示器 */}
        <Steps
          current={currentStepIndex}
          onChange={handleStepChange}
          className="mb-6"
        >
          {steps.map((step, index) => (
            <Step
              key={step.key}
              title={step.title}
              description={step.description}
              disabled={loading || index > currentStepIndex + 1}
            />
          ))}
        </Steps>

        {/* 错误提示 */}
        {error && (
          <Alert
            message="操作失败"
            description={error}
            type="error"
            showIcon
            closable
            onClose={clearError}
            className="mb-4"
          />
        )}

        {/* 任务状态提示 */}
        {currentTask && currentTask.status === 'failed' && (
          <Alert
            message="任务执行失败"
            description={currentTask.message || '未知错误'}
            type="error"
            showIcon
            className="mb-4"
          />
        )}
      </div>

      {/* 步骤内容 */}
      <Card className="min-h-96">
        {renderStepContent()}
      </Card>

      {/* 底部操作栏 */}
      <div className="mt-6 flex justify-between">
        <div>
          {currentStepIndex > 0 && currentStep !== 'import' && (
            <Button
              onClick={() => handleStepChange(currentStepIndex - 1)}
              disabled={loading}
            >
              上一步
            </Button>
          )}
        </div>
        
        <div>
          {currentStep === 'complete' && (
            <Button type="primary" onClick={reset}>
              开始新的导入
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};