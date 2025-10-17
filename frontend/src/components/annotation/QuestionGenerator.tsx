import React from 'react';
import { Card, Input, Button, Space, Typography } from 'antd';
import { BulbOutlined, EditOutlined } from '@ant-design/icons';

const { TextArea } = Input;
const { Title, Text } = Typography;

interface QuestionGeneratorProps {
  question: string;
  onQuestionChange: (value: string) => void;
  onGenerate: () => void;
  loading?: boolean;
  disabled?: boolean;
}

const QuestionGenerator: React.FC<QuestionGeneratorProps> = ({
  question,
  onQuestionChange,
  onGenerate,
  loading = false,
  disabled = false,
}) => {
  return (
    <Card size="small">
      <div style={{ marginBottom: '12px' }}>
        <Space>
          <Title level={5} style={{ margin: 0 }}>
            <EditOutlined /> 问题编辑
          </Title>
          <Button
            type="dashed"
            icon={<BulbOutlined />}
            onClick={onGenerate}
            loading={loading}
            disabled={disabled}
            size="small"
          >
            AI生成问题
          </Button>
        </Space>
        {disabled && (
          <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginTop: '4px' }}>
            请先选择文本切片
          </Text>
        )}
      </div>

      <TextArea
        value={question}
        onChange={(e) => onQuestionChange(e.target.value)}
        placeholder="请输入问题，或点击'AI生成问题'按钮自动生成..."
        rows={4}
        disabled={loading}
        style={{ resize: 'vertical' }}
      />

      <div style={{ marginTop: '8px' }}>
        <Text type="secondary" style={{ fontSize: '12px' }}>
          提示：问题应该具有学术水平，能够引导出高质量的Chain-of-Thought推理过程
        </Text>
      </div>
    </Card>
  );
};

export default QuestionGenerator;