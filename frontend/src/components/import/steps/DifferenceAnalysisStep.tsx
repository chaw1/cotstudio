/**
 * 差异分析步骤组件
 */
import React, { useEffect } from 'react';
import { 
  Card, 
  Button, 
  Progress, 
  Alert, 
  Statistic, 
  Row, 
  Col, 
  Typography,
  Space,
  Spin
} from 'antd';
import { 
  BarChartOutlined as AnalysisOutlined,
  ArrowRightOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import { useImportStore } from '../../../stores/importStore';

const { Title, Text } = Typography;

export const DifferenceAnalysisStep: React.FC = () => {
  const {
    loading,
    currentTask,
    analysisResult,
    differences,
    conflicts,
    targetProjectId,
    importMode,
    analyzeDifferences,
    setCurrentStep,
  } = useImportStore();

  // 自动开始分析
  useEffect(() => {
    if (!analysisResult && !loading && !currentTask) {
      analyzeDifferences(targetProjectId);
    }
  }, [analysisResult, loading, currentTask, targetProjectId, analyzeDifferences]);

  // 渲染分析进度
  const renderAnalysisProgress = () => {
    if (!currentTask) return null;

    return (
      <Card className="mb-4">
        <div className="text-center">
          <Spin size="large" />
          <div className="mt-4">
            <Title level={4}>正在分析数据差异...</Title>
            <Text type="secondary">
              正在比较导入数据与{importMode === 'merge' ? '目标项目' : '系统'}数据的差异
            </Text>
            
            <div className="mt-4">
              <Progress 
                percent={Math.round(currentTask.progress)} 
                status={currentTask.status === 'failed' ? 'exception' : 'active'}
              />
              
              {currentTask.message && (
                <div className="mt-2 text-sm text-gray-600">
                  {currentTask.message}
                </div>
              )}
            </div>
          </div>
        </div>
      </Card>
    );
  };

  // 渲染统计信息
  const renderStatistics = () => {
    if (!analysisResult) return null;

    const stats = analysisResult.statistics;
    
    return (
      <Card title="差异统计" className="mb-4">
        <Row gutter={16}>
          <Col span={6}>
            <Statistic
              title="总差异数"
              value={stats.total_differences || 0}
              prefix={<AnalysisOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="新增项"
              value={stats.new_items || 0}
              prefix={<PlusOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="修改项"
              value={stats.modified_items || 0}
              prefix={<EditOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="冲突项"
              value={stats.total_conflicts || 0}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Col>
        </Row>
      </Card>
    );
  };

  // 渲染差异概览
  const renderDifferenceOverview = () => {
    if (!differences.length && !conflicts.length) {
      return (
        <Card>
          <div className="text-center py-8">
            <InfoCircleOutlined className="text-4xl text-blue-500 mb-4" />
            <Title level={4}>没有发现数据差异</Title>
            <Text type="secondary">
              导入的数据与现有数据完全一致，可以直接进行导入操作。
            </Text>
          </div>
        </Card>
      );
    }

    const categoryStats = differences.reduce((acc, diff) => {
      acc[diff.category] = (acc[diff.category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return (
      <Card title="差异概览" className="mb-4">
        <div className="space-y-4">
          {/* 按类别显示差异 */}
          {Object.entries(categoryStats).map(([category, count]) => (
            <div key={category} className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <div>
                <Text strong>{getCategoryDisplayName(category)}</Text>
                <div className="text-sm text-gray-500">
                  {count} 个差异项
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-500">
                  {getDifferenceTypeBreakdown(differences.filter(d => d.category === category))}
                </div>
              </div>
            </div>
          ))}

          {/* 冲突提示 */}
          {conflicts.length > 0 && (
            <Alert
              message={`发现 ${conflicts.length} 个冲突`}
              description="这些冲突需要在下一步中手动解决"
              type="warning"
              showIcon
              icon={<ExclamationCircleOutlined />}
            />
          )}
        </div>
      </Card>
    );
  };

  // 获取类别显示名称
  const getCategoryDisplayName = (category: string): string => {
    const categoryMap: Record<string, string> = {
      'project': '项目信息',
      'file': '文件',
      'cot_item': 'CoT 数据项',
      'candidate': '候选答案',
      'kg_entity': '知识图谱实体',
      'kg_relation': '知识图谱关系',
    };
    return categoryMap[category] || category;
  };

  // 获取差异类型分布
  const getDifferenceTypeBreakdown = (diffs: typeof differences): string => {
    const typeCount = diffs.reduce((acc, diff) => {
      acc[diff.type] = (acc[diff.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const parts = [];
    if (typeCount.new) parts.push(`新增 ${typeCount.new}`);
    if (typeCount.modified) parts.push(`修改 ${typeCount.modified}`);
    if (typeCount.deleted) parts.push(`删除 ${typeCount.deleted}`);
    
    return parts.join(', ');
  };

  // 检查是否可以继续
  const canProceed = () => {
    return analysisResult && currentTask?.status === 'completed';
  };

  // 处理继续操作
  const handleProceed = () => {
    setCurrentStep('confirm');
  };

  return (
    <div className="space-y-6">
      <div>
        <Title level={3}>数据差异分析</Title>
        <Text type="secondary">
          {importMode === 'merge' 
            ? '正在分析导入数据与目标项目的差异...' 
            : '正在验证导入数据的完整性...'}
        </Text>
      </div>

      {/* 分析进度 */}
      {loading && renderAnalysisProgress()}

      {/* 分析完成后的结果 */}
      {analysisResult && (
        <>
          {renderStatistics()}
          {renderDifferenceOverview()}
          
          <div className="flex justify-end">
            <Button
              type="primary"
              icon={<ArrowRightOutlined />}
              onClick={handleProceed}
              disabled={!canProceed()}
              size="large"
            >
              下一步：确认导入设置
            </Button>
          </div>
        </>
      )}

      {/* 分析失败 */}
      {currentTask?.status === 'failed' && (
        <Alert
          message="差异分析失败"
          description={currentTask.message || '未知错误'}
          type="error"
          showIcon
          action={
            <Button 
              size="small" 
              onClick={() => analyzeDifferences(targetProjectId)}
            >
              重试
            </Button>
          }
        />
      )}
    </div>
  );
};