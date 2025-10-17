/**
 * 导出选项配置组件
 */
import React from 'react';
import { Card, Checkbox, Select, Typography, Space, Divider } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;

export interface ExportOptionsData {
  include_metadata: boolean;
  include_files: boolean;
  include_kg_data: boolean;
  cot_status_filter: string[];
}

interface ExportOptionsProps {
  options: ExportOptionsData;
  onOptionsChange: (options: ExportOptionsData) => void;
}

const ExportOptions: React.FC<ExportOptionsProps> = ({
  options,
  onOptionsChange
}) => {
  const handleOptionChange = (key: keyof ExportOptionsData, value: any) => {
    onOptionsChange({
      ...options,
      [key]: value
    });
  };

  const cotStatusOptions = [
    { value: 'pending', label: '待处理' },
    { value: 'processing', label: '处理中' },
    { value: 'completed', label: '已完成' },
    { value: 'reviewed', label: '已审核' },
    { value: 'rejected', label: '已拒绝' }
  ];

  return (
    <Card title="导出选项" size="small">
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {/* 基础选项 */}
        <div>
          <Title level={5} style={{ margin: '0 0 12px 0', fontSize: '14px' }}>
            包含内容
          </Title>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Checkbox
              checked={options.include_metadata}
              onChange={(e) => handleOptionChange('include_metadata', e.target.checked)}
            >
              <span>包含元数据</span>
              <Text type="secondary" style={{ fontSize: '12px', marginLeft: '8px' }}>
                (项目信息、导出时间、统计数据等)
              </Text>
            </Checkbox>

            <Checkbox
              checked={options.include_files}
              onChange={(e) => handleOptionChange('include_files', e.target.checked)}
            >
              <span>包含原始文件</span>
              <Text type="secondary" style={{ fontSize: '12px', marginLeft: '8px' }}>
                (文件信息和内容，会增加导出包大小)
              </Text>
            </Checkbox>

            <Checkbox
              checked={options.include_kg_data}
              onChange={(e) => handleOptionChange('include_kg_data', e.target.checked)}
            >
              <span>包含知识图谱数据</span>
              <Text type="secondary" style={{ fontSize: '12px', marginLeft: '8px' }}>
                (实体、关系等图谱结构数据)
              </Text>
            </Checkbox>
          </Space>
        </div>

        <Divider style={{ margin: '12px 0' }} />

        {/* CoT状态过滤 */}
        <div>
          <Title level={5} style={{ margin: '0 0 12px 0', fontSize: '14px' }}>
            CoT数据过滤
          </Title>
          <div style={{ marginBottom: '8px' }}>
            <Text style={{ fontSize: '13px' }}>
              <InfoCircleOutlined style={{ marginRight: '4px', color: '#1890ff' }} />
              选择要导出的CoT数据状态（不选择则导出所有状态）
            </Text>
          </div>
          <Select
            mode="multiple"
            style={{ width: '100%' }}
            placeholder="选择要导出的状态"
            value={options.cot_status_filter}
            onChange={(value) => handleOptionChange('cot_status_filter', value)}
            allowClear
          >
            {cotStatusOptions.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        </div>

        {/* 导出提示 */}
        <div style={{ 
          padding: '12px', 
          backgroundColor: '#fffbe6', 
          borderRadius: '6px', 
          border: '1px solid #ffe58f' 
        }}>
          <Text style={{ fontSize: '12px', color: '#d48806' }}>
            <InfoCircleOutlined style={{ marginRight: '4px' }} />
            <strong>注意：</strong>
            包含原始文件和知识图谱数据会显著增加导出文件的大小和处理时间。
            如果只需要CoT数据，建议取消勾选这些选项。
          </Text>
        </div>
      </Space>
    </Card>
  );
};

export default ExportOptions;