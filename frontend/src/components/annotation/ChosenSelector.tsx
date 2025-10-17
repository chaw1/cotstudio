import React from 'react';
import { Button, Space, Typography } from 'antd';
import { CheckOutlined, CloseOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface ChosenSelectorProps {
  chosen: boolean;
  onChange: (chosen: boolean) => void;
  disabled?: boolean;
}

const ChosenSelector: React.FC<ChosenSelectorProps> = ({
  chosen,
  onChange,
  disabled = false,
}) => {
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ marginBottom: '8px' }}>
        <Text strong style={{ fontSize: '13px' }}>
          最佳答案
        </Text>
      </div>
      
      <Space>
        <Button
          type={chosen ? 'primary' : 'default'}
          icon={<CheckOutlined />}
          onClick={() => onChange(true)}
          disabled={disabled}
          size="small"
          style={{
            backgroundColor: chosen ? '#52c41a' : undefined,
            borderColor: chosen ? '#52c41a' : undefined,
            color: chosen ? '#fff' : undefined,
          }}
        >
          Y
        </Button>
        
        <Button
          type={!chosen ? 'primary' : 'default'}
          icon={<CloseOutlined />}
          onClick={() => onChange(false)}
          disabled={disabled}
          size="small"
          style={{
            backgroundColor: !chosen ? '#f5222d' : undefined,
            borderColor: !chosen ? '#f5222d' : undefined,
            color: !chosen ? '#fff' : undefined,
          }}
        >
          N
        </Button>
      </Space>
      
      <div style={{ marginTop: '4px' }}>
        <Text type="secondary" style={{ fontSize: '11px' }}>
          {chosen ? '已选为最佳' : '未选择'}
        </Text>
      </div>
    </div>
  );
};

export default ChosenSelector;