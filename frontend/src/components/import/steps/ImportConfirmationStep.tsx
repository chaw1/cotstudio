/**
 * 导入确认步骤组件
 */
import React, { useState } from 'react';
import { 
  Card, 
  Button, 
  Table, 
  Tag, 
  Checkbox, 
  Radio, 
  Space, 
  Typography,
  Collapse,
  Alert,
  Tooltip,
  Modal,
  Input,
  Divider
} from 'antd';
import { 
  CheckOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  WarningOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import ModalContainer from '../../common/ModalContainer';
import { useImportStore } from '../../../stores/importStore';
import type { DataDifference, ConflictResolution } from '../../../services/importService';

const { Title, Text } = Typography;
const { Panel } = Collapse;
const { TextArea } = Input;

export const ImportConfirmationStep: React.FC = () => {
  const {
    differences,
    conflicts,
    selectedDifferences,
    conflictResolutions,
    loading,
    toggleDifference,
    selectAllDifferences,
    deselectAllDifferences,
    setConflictResolution,
    executeImport,
  } = useImportStore();

  const [conflictModalVisible, setConflictModalVisible] = useState(false);
  const [currentConflict, setCurrentConflict] = useState<DataDifference | null>(null);
  const [customValue, setCustomValue] = useState('');

  // 差异表格列定义
  const differenceColumns: ColumnsType<DataDifference> = [
    {
      title: '选择',
      key: 'select',
      width: 60,
      render: (_, record) => (
        <Checkbox
          checked={selectedDifferences.has(record.id)}
          onChange={() => toggleDifference(record.id)}
          disabled={record.type === 'conflict'}
        />
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 80,
      render: (type: string) => {
        const typeConfig = {
          new: { color: 'green', icon: <PlusOutlined />, text: '新增' },
          modified: { color: 'blue', icon: <EditOutlined />, text: '修改' },
          deleted: { color: 'red', icon: <DeleteOutlined />, text: '删除' },
          conflict: { color: 'orange', icon: <ExclamationCircleOutlined />, text: '冲突' },
        };
        const config = typeConfig[type as keyof typeof typeConfig];
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (category: string) => getCategoryDisplayName(category),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      width: 80,
      render: (severity: string) => {
        const severityConfig = {
          low: { color: 'default', text: '低' },
          normal: { color: 'processing', text: '中' },
          high: { color: 'error', text: '高' },
        };
        const config = severityConfig[severity as keyof typeof severityConfig] || severityConfig.normal;
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => {
        if (record.type === 'conflict') {
          return (
            <Button
              size="small"
              type="link"
              onClick={() => handleConflictResolution(record)}
            >
              解决冲突
            </Button>
          );
        }
        return null;
      },
    },
  ];

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

  // 处理冲突解决
  const handleConflictResolution = (conflict: DataDifference) => {
    setCurrentConflict(conflict);
    setConflictModalVisible(true);
    
    // 如果已有解决方案，预填充
    const existingResolution = conflictResolutions[conflict.id];
    if (existingResolution?.custom_value) {
      setCustomValue(existingResolution.custom_value);
    }
  };

  // 保存冲突解决方案
  const saveConflictResolution = (resolution: string, reason?: string) => {
    if (!currentConflict) return;

    const conflictResolution: ConflictResolution = {
      difference_id: currentConflict.id,
      resolution: resolution as any,
      custom_value: resolution === 'merge' ? customValue : undefined,
      reason,
    };

    setConflictResolution(currentConflict.id, conflictResolution);
    setConflictModalVisible(false);
    setCurrentConflict(null);
    setCustomValue('');
  };

  // 检查是否可以执行导入
  const canExecuteImport = () => {
    // 检查是否有未解决的冲突
    const unresolvedConflicts = conflicts.filter(
      conflict => !conflictResolutions[conflict.id]
    );
    
    return unresolvedConflicts.length === 0;
  };

  // 执行导入
  const handleExecuteImport = () => {
    Modal.confirm({
      title: '确认导入',
      content: `确定要导入 ${selectedDifferences.size} 个差异项吗？此操作不可撤销。`,
      onOk: executeImport,
    });
  };

  // 渲染冲突解决模态框
  const renderConflictModal = () => {
    if (!currentConflict) return null;

    return (
      <ModalContainer
        visible={conflictModalVisible}
        onClose={() => setConflictModalVisible(false)}
        title="解决数据冲突"
        width={600}
        footer={null}
      >
        <div className="space-y-4">
          <Alert
            message="发现数据冲突"
            description={currentConflict.description}
            type="warning"
            showIcon
          />

          <div>
            <Text strong>当前值:</Text>
            <div className="mt-1 p-2 bg-gray-50 rounded">
              <pre className="text-sm whitespace-pre-wrap">
                {JSON.stringify(currentConflict.current_value, null, 2)}
              </pre>
            </div>
          </div>

          <div>
            <Text strong>新值:</Text>
            <div className="mt-1 p-2 bg-gray-50 rounded">
              <pre className="text-sm whitespace-pre-wrap">
                {JSON.stringify(currentConflict.new_value, null, 2)}
              </pre>
            </div>
          </div>

          <div>
            <Text strong>解决方案:</Text>
            <Radio.Group className="mt-2 w-full">
              <Space direction="vertical" className="w-full">
                <Radio value="keep_current">
                  保留当前值
                </Radio>
                <Radio value="use_new">
                  使用新值
                </Radio>
                <Radio value="merge">
                  手动合并
                </Radio>
                <Radio value="skip">
                  跳过此项
                </Radio>
              </Space>
            </Radio.Group>

            <div className="mt-3">
              <Text>自定义值 (仅在选择"手动合并"时使用):</Text>
              <TextArea
                rows={4}
                value={customValue}
                onChange={(e) => setCustomValue(e.target.value)}
                placeholder="请输入合并后的值..."
                className="mt-1"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-2">
            <Button onClick={() => setConflictModalVisible(false)}>
              取消
            </Button>
            <Button 
              type="primary" 
              onClick={() => saveConflictResolution('keep_current')}
            >
              保留当前值
            </Button>
            <Button 
              type="primary" 
              onClick={() => saveConflictResolution('use_new')}
            >
              使用新值
            </Button>
          </div>
        </div>
      </ModalContainer>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <Title level={3}>确认导入设置</Title>
        <Text type="secondary">
          请检查并确认要导入的数据差异，解决所有冲突后即可开始导入。
        </Text>
      </div>

      {/* 操作栏 */}
      <Card>
        <div className="flex justify-between items-center">
          <Space>
            <Button onClick={selectAllDifferences}>
              全选
            </Button>
            <Button onClick={deselectAllDifferences}>
              取消全选
            </Button>
            <Text type="secondary">
              已选择 {selectedDifferences.size} / {differences.length} 项
            </Text>
          </Space>
          
          <Space>
            {conflicts.length > 0 && (
              <Alert
                message={`${conflicts.length} 个冲突待解决`}
                type="warning"
                showIcon
                banner
              />
            )}
          </Space>
        </div>
      </Card>

      {/* 差异列表 */}
      <Card title="数据差异列表">
        <Table
          columns={differenceColumns}
          dataSource={[...differences, ...conflicts]}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 项`,
          }}
          expandable={{
            expandedRowRender: (record) => (
              <div className="space-y-2">
                {record.field_name && (
                  <div>
                    <Text strong>字段:</Text> {record.field_name}
                  </div>
                )}
                {record.current_value !== undefined && (
                  <div>
                    <Text strong>当前值:</Text>
                    <pre className="mt-1 text-sm bg-gray-50 p-2 rounded">
                      {JSON.stringify(record.current_value, null, 2)}
                    </pre>
                  </div>
                )}
                {record.new_value !== undefined && (
                  <div>
                    <Text strong>新值:</Text>
                    <pre className="mt-1 text-sm bg-gray-50 p-2 rounded">
                      {JSON.stringify(record.new_value, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ),
          }}
        />
      </Card>

      {/* 冲突解决状态 */}
      {conflicts.length > 0 && (
        <Card title="冲突解决状态">
          <div className="space-y-2">
            {conflicts.map((conflict) => {
              const resolution = conflictResolutions[conflict.id];
              return (
                <div key={conflict.id} className="flex justify-between items-center p-3 border rounded">
                  <div>
                    <Text strong>{conflict.description}</Text>
                    <div className="text-sm text-gray-500">
                      {conflict.category} - {conflict.field_name}
                    </div>
                  </div>
                  <div>
                    {resolution ? (
                      <Tag color="green" icon={<CheckOutlined />}>
                        已解决: {resolution.resolution}
                      </Tag>
                    ) : (
                      <Tag color="orange" icon={<WarningOutlined />}>
                        待解决
                      </Tag>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* 导入按钮 */}
      <div className="flex justify-end">
        <Button
          type="primary"
          size="large"
          loading={loading}
          disabled={!canExecuteImport() || selectedDifferences.size === 0}
          onClick={handleExecuteImport}
        >
          开始导入 ({selectedDifferences.size} 项)
        </Button>
      </div>

      {/* 冲突解决模态框 */}
      {renderConflictModal()}
    </div>
  );
};