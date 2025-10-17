import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  InputNumber,
  Switch,
  Slider,
  Button,
  Space,
  message,
  Alert,
  Row,
  Col,
  Divider,
  Tooltip
} from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import { COTGenerationConfig as COTGenerationConfigType } from '../../types';
import { useSettingsStore } from '../../stores/settingsStore';

interface COTGenerationConfigProps {
  onConfigChange?: (config: COTGenerationConfigType) => void;
}

const COTGenerationConfig: React.FC<COTGenerationConfigProps> = ({ onConfigChange }) => {
  const {
    cotGenerationConfig,
    loading,
    error,
    updateCOTGenerationConfig,
    clearError
  } = useSettingsStore();

  const [form] = Form.useForm();
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    if (error) {
      message.error(error);
      clearError();
    }
  }, [error, clearError]);

  useEffect(() => {
    if (cotGenerationConfig) {
      form.setFieldsValue(cotGenerationConfig);
      onConfigChange?.(cotGenerationConfig);
    }
  }, [cotGenerationConfig, form, onConfigChange]);

  const handleFormChange = () => {
    setHasChanges(true);
  };

  const handleSave = async (values: COTGenerationConfigType) => {
    try {
      await updateCOTGenerationConfig(values);
      setHasChanges(false);
      message.success('CoT生成配置已更新');
    } catch (error) {
      message.error('更新CoT生成配置失败');
    }
  };

  const handleReset = () => {
    if (cotGenerationConfig) {
      form.setFieldsValue(cotGenerationConfig);
      setHasChanges(false);
    }
  };

  if (!cotGenerationConfig) {
    return <div>加载中...</div>;
  }

  return (
    <div>
      <Alert
        message="CoT生成配置"
        description="配置Chain-of-Thought数据生成的相关参数，包括候选答案数量、文本长度限制等。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Card title="生成参数配置">
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          onValuesChange={handleFormChange}
          initialValues={cotGenerationConfig}
        >
          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                name="candidate_count"
                label={
                  <Space>
                    候选答案数量
                    <Tooltip title="为每个问题生成的候选答案数量，建议2-5个">
                      <InfoCircleOutlined />
                    </Tooltip>
                  </Space>
                }
                rules={[
                  { required: true, message: '请设置候选答案数量' },
                  { type: 'number', min: 2, max: 5, message: '候选答案数量必须在2-5之间' }
                ]}
              >
                <InputNumber
                  min={2}
                  max={5}
                  style={{ width: '100%' }}
                  placeholder="输入候选答案数量"
                />
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item
                name="enable_auto_generation"
                label={
                  <Space>
                    启用自动生成
                    <Tooltip title="是否在文本切片完成后自动生成CoT问题和答案">
                      <InfoCircleOutlined />
                    </Tooltip>
                  </Space>
                }
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                name="question_max_length"
                label={
                  <Space>
                    问题最大长度
                    <Tooltip title="生成问题的最大字符数，建议50-1000字符">
                      <InfoCircleOutlined />
                    </Tooltip>
                  </Space>
                }
                rules={[
                  { required: true, message: '请设置问题最大长度' },
                  { type: 'number', min: 50, max: 1000, message: '问题长度必须在50-1000字符之间' }
                ]}
              >
                <InputNumber
                  min={50}
                  max={1000}
                  style={{ width: '100%' }}
                  placeholder="输入问题最大长度"
                  addonAfter="字符"
                />
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item
                name="answer_max_length"
                label={
                  <Space>
                    答案最大长度
                    <Tooltip title="生成答案的最大字符数，建议100-5000字符">
                      <InfoCircleOutlined />
                    </Tooltip>
                  </Space>
                }
                rules={[
                  { required: true, message: '请设置答案最大长度' },
                  { type: 'number', min: 100, max: 5000, message: '答案长度必须在100-5000字符之间' }
                ]}
              >
                <InputNumber
                  min={100}
                  max={5000}
                  style={{ width: '100%' }}
                  placeholder="输入答案最大长度"
                  addonAfter="字符"
                />
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          <Row gutter={24}>
            <Col span={24}>
              <Form.Item
                name="quality_threshold"
                label={
                  <Space>
                    质量阈值
                    <Tooltip title="生成内容的质量阈值，低于此阈值的内容将被过滤">
                      <InfoCircleOutlined />
                    </Tooltip>
                  </Space>
                }
                rules={[
                  { required: true, message: '请设置质量阈值' },
                  { type: 'number', min: 0, max: 1, message: '质量阈值必须在0-1之间' }
                ]}
              >
                <div>
                  <Slider
                    min={0}
                    max={1}
                    step={0.1}
                    marks={{
                      0: '0.0',
                      0.3: '0.3',
                      0.5: '0.5',
                      0.7: '0.7',
                      1: '1.0'
                    }}
                    tooltip={{
                      formatter: (value) => `${value?.toFixed(1)}`
                    }}
                  />
                  <div style={{ marginTop: 8, color: '#666', fontSize: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>低质量</span>
                      <span>中等质量</span>
                      <span>高质量</span>
                    </div>
                  </div>
                </div>
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                disabled={!hasChanges}
              >
                保存配置
              </Button>
              <Button
                onClick={handleReset}
                disabled={!hasChanges}
              >
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Card title="配置说明" style={{ marginTop: 16 }}>
        <Row gutter={16}>
          <Col span={12}>
            <h4>候选答案数量</h4>
            <p>为每个问题生成的候选答案数量。更多的候选答案可以提供更多选择，但会增加标注工作量。</p>
            
            <h4>文本长度限制</h4>
            <p>控制生成的问题和答案的最大长度，避免生成过长或过短的内容。</p>
          </Col>
          <Col span={12}>
            <h4>自动生成</h4>
            <p>启用后，系统会在OCR和切片完成后自动生成CoT问题和答案，提高处理效率。</p>
            
            <h4>质量阈值</h4>
            <p>用于过滤低质量生成内容的阈值。较高的阈值会产生更高质量的结果，但可能减少生成数量。</p>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default COTGenerationConfig;