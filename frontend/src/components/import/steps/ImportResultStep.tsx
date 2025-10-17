/**
 * 导入结果步骤组件
 */
import React from 'react';
import { 
  Card, 
  Button, 
  Result, 
  Statistic, 
  Row, 
  Col, 
  Typography,
  Alert,
  Collapse,
  Tag,
  Space,
  Divider
} from 'antd';
import { 
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  BranchesOutlined
} from '@ant-design/icons';
import { useImportStore } from '../../../stores/importStore';
import { useNavigate } from 'react-router-dom';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

export const ImportResultStep: React.FC = () => {
  const {
    importResult,
    importMode,
    targetProjectId,
    newProjectName,
    reset,
  } = useImportStore();

  const navigate = useNavigate();

  if (!importResult) {
    return (
      <div className="text-center py-8">
        <InfoCircleOutlined className="text-4xl text-gray-400 mb-4" />
        <Title level={4}>没有导入结果</Title>
        <Text type="secondary">导入过程可能还未完成或出现了错误</Text>
      </div>
    );
  }

  // 渲染成功结果
  const renderSuccessResult = () => (
    <Result
      status="success"
      title="数据导入成功！"
      subTitle={`成功导入到项目${importMode === 'create_new' ? ` "${newProjectName}"` : ''}`}
      extra={[
        <Button 
          type="primary" 
          key="view"
          onClick={() => navigate(`/projects/${importResult.project_id}`)}
        >
          查看项目
        </Button>,
        <Button key="new" onClick={reset}>
          开始新的导入
        </Button>,
      ]}
    />
  );

  // 渲染失败结果
  const renderFailureResult = () => (
    <Result
      status="error"
      title="数据导入失败"
      subTitle="导入过程中遇到了一些问题，请查看详细信息"
      extra={[
        <Button type="primary" key="retry" onClick={reset}>
          重新开始
        </Button>,
      ]}
    />
  );

  // 渲染统计信息
  const renderStatistics = () => {
    const totalImported = Object.values(importResult.imported_items).reduce((sum, count) => sum + count, 0);
    const totalSkipped = Object.values(importResult.skipped_items).reduce((sum, count) => sum + count, 0);

    return (
      <Card title="导入统计" className="mb-4">
        <Row gutter={16}>
          <Col span={6}>
            <Statistic
              title="总导入项"
              value={totalImported}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="跳过项"
              value={totalSkipped}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="执行时间"
              value={importResult.execution_time}
              suffix="秒"
              prefix={<ClockCircleOutlined />}
              precision={2}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="错误数"
              value={importResult.errors.length}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: importResult.errors.length > 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Col>
        </Row>
      </Card>
    );
  };

  // 渲染详细统计
  const renderDetailedStats = () => {
    const hasImportedItems = Object.keys(importResult.imported_items).length > 0;
    const hasSkippedItems = Object.keys(importResult.skipped_items).length > 0;

    if (!hasImportedItems && !hasSkippedItems) return null;

    return (
      <Card title="详细统计" className="mb-4">
        <Row gutter={16}>
          {hasImportedItems && (
            <Col span={12}>
              <div className="space-y-2">
                <Title level={5}>
                  <CheckCircleOutlined className="text-green-500 mr-2" />
                  成功导入
                </Title>
                {Object.entries(importResult.imported_items).map(([type, count]) => (
                  <div key={type} className="flex justify-between items-center">
                    <span>{getItemTypeDisplayName(type)}</span>
                    <Tag color="green">{count}</Tag>
                  </div>
                ))}
              </div>
            </Col>
          )}
          
          {hasSkippedItems && (
            <Col span={12}>
              <div className="space-y-2">
                <Title level={5}>
                  <ExclamationCircleOutlined className="text-orange-500 mr-2" />
                  跳过项目
                </Title>
                {Object.entries(importResult.skipped_items).map(([type, count]) => (
                  <div key={type} className="flex justify-between items-center">
                    <span>{getItemTypeDisplayName(type)}</span>
                    <Tag color="orange">{count}</Tag>
                  </div>
                ))}
              </div>
            </Col>
          )}
        </Row>
      </Card>
    );
  };

  // 渲染错误和警告
  const renderErrorsAndWarnings = () => {
    const hasErrors = importResult.errors.length > 0;
    const hasWarnings = importResult.warnings.length > 0;

    if (!hasErrors && !hasWarnings) return null;

    return (
      <Card title="问题报告" className="mb-4">
        <Collapse>
          {hasErrors && (
            <Panel 
              header={
                <Space>
                  <ExclamationCircleOutlined className="text-red-500" />
                  <span>错误信息 ({importResult.errors.length})</span>
                </Space>
              } 
              key="errors"
            >
              <div className="space-y-2">
                {importResult.errors.map((error, index) => (
                  <Alert
                    key={index}
                    message={error}
                    type="error"
                    showIcon
                  />
                ))}
              </div>
            </Panel>
          )}
          
          {hasWarnings && (
            <Panel 
              header={
                <Space>
                  <ExclamationCircleOutlined className="text-orange-500" />
                  <span>警告信息 ({importResult.warnings.length})</span>
                </Space>
              } 
              key="warnings"
            >
              <div className="space-y-2">
                {importResult.warnings.map((warning, index) => (
                  <Alert
                    key={index}
                    message={warning}
                    type="warning"
                    showIcon
                  />
                ))}
              </div>
            </Panel>
          )}
        </Collapse>
      </Card>
    );
  };

  // 渲染导入信息
  const renderImportInfo = () => (
    <Card title="导入信息" className="mb-4">
      <div className="space-y-3">
        <div className="flex justify-between">
          <Text strong>导入模式:</Text>
          <Tag color="blue">
            {importMode === 'create_new' ? '创建新项目' : 
             importMode === 'merge' ? '合并到现有项目' : 
             '替换现有项目'}
          </Tag>
        </div>
        
        {importMode === 'create_new' && newProjectName && (
          <div className="flex justify-between">
            <Text strong>新项目名称:</Text>
            <Text>{newProjectName}</Text>
          </div>
        )}
        
        {importMode === 'merge' && targetProjectId && (
          <div className="flex justify-between">
            <Text strong>目标项目ID:</Text>
            <Text code>{targetProjectId}</Text>
          </div>
        )}
        
        <div className="flex justify-between">
          <Text strong>项目ID:</Text>
          <Text code>{importResult.project_id}</Text>
        </div>
      </div>
    </Card>
  );

  // 获取项目类型显示名称
  const getItemTypeDisplayName = (type: string): string => {
    const typeMap: Record<string, string> = {
      'files': '文件',
      'cot_items': 'CoT 数据项',
      'candidates': '候选答案',
      'kg_entities': '知识图谱实体',
      'kg_relations': '知识图谱关系',
      'slices': '文档切片',
    };
    return typeMap[type] || type;
  };

  return (
    <div className="space-y-6">
      <div>
        <Title level={3}>导入结果</Title>
        <Text type="secondary">
          数据导入已完成，以下是详细的执行结果。
        </Text>
      </div>

      {/* 主要结果 */}
      {importResult.success ? renderSuccessResult() : renderFailureResult()}

      {/* 统计信息 */}
      {renderStatistics()}

      {/* 详细统计 */}
      {renderDetailedStats()}

      {/* 导入信息 */}
      {renderImportInfo()}

      {/* 错误和警告 */}
      {renderErrorsAndWarnings()}

      {/* 建议操作 */}
      {importResult.success && (
        <Card>
          <Title level={4}>下一步建议</Title>
          <div className="space-y-2">
            <Paragraph>
              <FileTextOutlined className="mr-2" />
              查看导入的项目，验证数据的完整性和正确性
            </Paragraph>
            <Paragraph>
              <DatabaseOutlined className="mr-2" />
              如果导入了 CoT 数据，可以开始进行标注和评分工作
            </Paragraph>
            <Paragraph>
              <BranchesOutlined className="mr-2" />
              如果导入了知识图谱数据，可以查看和编辑图谱结构
            </Paragraph>
          </div>
        </Card>
      )}
    </div>
  );
};