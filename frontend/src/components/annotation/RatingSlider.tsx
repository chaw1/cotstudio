import React from 'react';
import { Slider, Typography, Space } from 'antd';
import { StarOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface RatingSliderProps {
  value: number;
  onChange: (value: number) => void;
  disabled?: boolean;
}

const RatingSlider: React.FC<RatingSliderProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  // 格式化显示值
  const formatValue = (val: number) => {
    return val.toFixed(1);
  };

  // 获取评分颜色
  const getScoreColor = (score: number) => {
    if (score >= 0.8) return '#52c41a'; // 绿色 - 优秀
    if (score >= 0.6) return '#faad14'; // 黄色 - 良好
    if (score >= 0.4) return '#fa8c16'; // 橙色 - 一般
    return '#f5222d'; // 红色 - 较差
  };

  // 获取评分等级
  const getScoreLevel = (score: number) => {
    if (score >= 0.8) return '优秀';
    if (score >= 0.6) return '良好';
    if (score >= 0.4) return '一般';
    return '较差';
  };

  return (
    <div style={{ width: '100%' }}>
      <div style={{ marginBottom: '8px' }}>
        <Space>
          <StarOutlined style={{ color: getScoreColor(value) }} />
          <Text strong style={{ fontSize: '13px' }}>
            评分:
          </Text>
          <Text 
            strong 
            style={{ 
              color: getScoreColor(value),
              fontSize: '14px',
              minWidth: '32px',
              textAlign: 'center',
            }}
          >
            {formatValue(value)}
          </Text>
          <Text 
            type="secondary" 
            style={{ 
              fontSize: '12px',
              color: getScoreColor(value),
            }}
          >
            ({getScoreLevel(value)})
          </Text>
        </Space>
      </div>
      
      <Slider
        min={0}
        max={1}
        step={0.1}
        value={value}
        onChange={onChange}
        disabled={disabled}
        tooltip={{
          formatter: (val) => `${formatValue(val || 0)} - ${getScoreLevel(val || 0)}`,
        }}
        trackStyle={{ backgroundColor: getScoreColor(value) }}
        handleStyle={{ borderColor: getScoreColor(value) }}
        marks={{
          0: {
            style: { fontSize: '11px', color: '#999' },
            label: '0.0',
          },
          0.5: {
            style: { fontSize: '11px', color: '#999' },
            label: '0.5',
          },
          1: {
            style: { fontSize: '11px', color: '#999' },
            label: '1.0',
          },
        }}
      />
      
      <div style={{ marginTop: '4px' }}>
        <Text type="secondary" style={{ fontSize: '11px' }}>
          拖动滑块调整评分 (0.0 - 1.0，步长 0.1)
        </Text>
      </div>
    </div>
  );
};

export default RatingSlider;