import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Switch,
  Button,
  InputNumber,
  Space,
  message,
  Tag,
  Alert,
  Collapse,
  Row,
  Col
} from 'antd';
import { CheckCircleOutlined, ExclamationCircleOutlined, SettingOutlined } from '@ant-design/icons';
import { OCREngineConfig as OCREngineConfigType } from '../../types';
import { useSettingsStore } from '../../stores/settingsStore';

const { Panel } = Collapse;
const { TextArea } = Input;

interface OCREngineConfigProps {
  onConfigChange?: (engines: OCREngineConfigType[]) => void;
}

const OCREngineConfig: React.FC<OCREngineConfigProps> = ({ onConfigChange }) => {
  const {
    ocrEngines,
    defaultOCREngine,
    loading,
    error,
    updateOCREngine,
    setDefaultOCREngine,
    validateOCREngine,
    clearError
  } = useSettingsStore();

  const [form] = Form.useForm();
  const [editingEngine, setEditingEngine] = useState<string | null>(null);
  const [validationResults, setValidationResults] = useState<Record<string, boolean>>({});
  const [validating, setValidating] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (error) {
      message.error(error);
      clearError();
    }
  }, [error, clearError]);

  useEffect(() => {
    onConfigChange?.(ocrEngines);
  }, [ocrEngines, onConfigChange]);

  const handleEngineUpdate = async (engine: string, values: any) => {
    try {
      const config: OCREngineConfigType = {
        engine,
        enabled: values.enabled,
        priority: values.priority,
        parameters: values.parameters || {}
      };

      await updateOCREngine(engine, config);
      setEditingEngine(null);
      message.success('OCR引擎配置已更新');
    } catch (error) {
      message.error('更新OCR引擎配置失败');
    }
  };

  const handleValidateEngine = async (engine: string, config: OCREngineConfigType) => {
    setValidating(prev => ({ ...prev, [engine]: true }));
    try {
      const isValid = await validateOCREngine(engine, config);
      setValidationResults(prev => ({ ...prev, [engine]: isValid }));
      message[isValid ? 'success' : 'error'](
        isValid ? '引擎配置验证成功' : '引擎配置验证失败'
      );
    } catch (error) {
      setValidationResults(prev => ({ ...prev, [engine]: false }));
    } finally {
      setValidating(prev => ({ ...prev, [engine]: false }));
    }
  };

  const handleSetDefault = async (engine: string) => {
    try {
      await setDefaultOCREngine(engine);
      message.success(`已设置 ${engine} 为默认OCR引擎`);
    } catch (error) {
      message.error('设置默认引擎失败');
    }
  };

  const getEngineDescription = (engine: string) => {
    const descriptions = {
      paddleocr: 'PaddleOCR是百度开源的OCR工具，支持多语言文字识别，适合通用文档处理',
      mineru: 'MinerU是专门针对学术文档的OCR工具，支持公式、表格等复杂结构识别',
      alibaba_advanced: '阿里云高级文字识别服务，提供高精度的商业级OCR能力'
    };
    return descriptions[engine as keyof typeof descriptions] || '未知OCR引擎';
  };

  const getDefaultParameters = (engine: string) => {
    const defaults = {
      paddleocr: {
        use_angle_cls: true,
        lang: 'ch',
        use_gpu: false,
        det_model_dir: '',
        rec_model_dir: '',
        cls_model_dir: ''
      },
      mineru: {
        layout_detection: true,
        formula_detection: true,
        table_detection: true,
        image_dpi: 200,
        output_format: 'markdown'
      },
      alibaba_advanced: {
        output_format: 'json',
        enable_table: true,
        enable_formula: true,
        enable_stamp: false,
        enable_qrcode: false
      }
    };
    return defaults[engine as keyof typeof defaults] || {};
  };

  const renderParameterForm = (engine: string, parameters: Record<string, any>) => {
    const defaultParams = getDefaultParameters(engine);
    
    return (
      <div>
        <h4>引擎参数配置</h4>
        {Object.entries(defaultParams).map(([key, defaultValue]) => (
          <Form.Item
            key={key}
            name={['parameters', key]}
            label={key.replace(/_/g, ' ').toUpperCase()}
            initialValue={parameters[key] ?? defaultValue}
          >
            {typeof defaultValue === 'boolean' ? (
              <Switch />
            ) : typeof defaultValue === 'number' ? (
              <InputNumber />
            ) : (
              <Input />
            )}
          </Form.Item>
        ))}
        
        <Form.Item
          name="custom_parameters"
          label="自定义参数 (JSON格式)"
        >
          <TextArea
            rows={4}
            placeholder='{"custom_param": "value"}'
          />
        </Form.Item>
      </div>
    );
  };

  const renderEngineCard = (engine: OCREngineConfigType) => {
    const isEditing = editingEngine === engine.engine;
    const isValidated = validationResults[engine.engine];
    const isValidating = validating[engine.engine];
    const isDefault = defaultOCREngine === engine.engine;

    return (
      <Card
        key={engine.engine}
        title={
          <Space>
            <span style={{ textTransform: 'uppercase' }}>{engine.engine}</span>
            {isDefault && <Tag color="blue">默认</Tag>}
            {engine.enabled && <Tag color="green">已启用</Tag>}
            {!engine.enabled && <Tag color="red">已禁用</Tag>}
            <Tag color="orange">优先级: {engine.priority}</Tag>
            {isValidated && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
            {isValidated === false && <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />}
          </Space>
        }
        extra={
          <Space>
            {!isDefault && engine.enabled && (
              <Button
                size="small"
                onClick={() => handleSetDefault(engine.engine)}
              >
                设为默认
              </Button>
            )}
            <Button
              size="small"
              type={isEditing ? 'default' : 'primary'}
              icon={<SettingOutlined />}
              onClick={() => {
                if (isEditing) {
                  setEditingEngine(null);
                } else {
                  setEditingEngine(engine.engine);
                  form.setFieldsValue({
                    ...engine,
                    custom_parameters: JSON.stringify(engine.parameters, null, 2)
                  });
                }
              }}
            >
              {isEditing ? '取消' : '配置'}
            </Button>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <p style={{ color: '#666', marginBottom: 16 }}>
          {getEngineDescription(engine.engine)}
        </p>

        {isEditing ? (
          <Form
            form={form}
            layout="vertical"
            onFinish={(values) => {
              // 合并自定义参数
              let finalParameters = { ...values.parameters };
              if (values.custom_parameters) {
                try {
                  const customParams = JSON.parse(values.custom_parameters);
                  finalParameters = { ...finalParameters, ...customParams };
                } catch (e) {
                  message.error('自定义参数JSON格式错误');
                  return;
                }
              }
              
              handleEngineUpdate(engine.engine, {
                ...values,
                parameters: finalParameters
              });
            }}
            initialValues={{
              ...engine,
              custom_parameters: JSON.stringify(engine.parameters, null, 2)
            }}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="enabled" label="启用引擎" valuePropName="checked">
                  <Switch />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="priority"
                  label="优先级"
                  rules={[{ required: true, message: '请输入优先级' }]}
                >
                  <InputNumber min={1} max={10} />
                </Form.Item>
              </Col>
            </Row>

            <Collapse>
              <Panel header="参数配置" key="parameters">
                {renderParameterForm(engine.engine, engine.parameters)}
              </Panel>
            </Collapse>

            <Form.Item style={{ marginTop: 16 }}>
              <Space>
                <Button type="primary" htmlType="submit" loading={loading}>
                  保存配置
                </Button>
                <Button
                  onClick={() => {
                    const currentValues = form.getFieldsValue();
                    let finalParameters = { ...currentValues.parameters };
                    if (currentValues.custom_parameters) {
                      try {
                        const customParams = JSON.parse(currentValues.custom_parameters);
                        finalParameters = { ...finalParameters, ...customParams };
                      } catch (e) {
                        message.error('自定义参数JSON格式错误');
                        return;
                      }
                    }
                    
                    handleValidateEngine(engine.engine, {
                      ...engine,
                      ...currentValues,
                      parameters: finalParameters
                    });
                  }}
                  loading={isValidating}
                >
                  验证配置
                </Button>
              </Space>
            </Form.Item>
          </Form>
        ) : (
          <div>
            <Row gutter={16}>
              <Col span={12}>
                <p><strong>优先级:</strong> {engine.priority}</p>
                <p><strong>状态:</strong> {engine.enabled ? '已启用' : '已禁用'}</p>
              </Col>
              <Col span={12}>
                <p><strong>参数数量:</strong> {Object.keys(engine.parameters).length}</p>
              </Col>
            </Row>
            
            {Object.keys(engine.parameters).length > 0 && (
              <Collapse size="small">
                <Panel header="查看参数" key="view-params">
                  <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 4 }}>
                    {JSON.stringify(engine.parameters, null, 2)}
                  </pre>
                </Panel>
              </Collapse>
            )}
          </div>
        )}
      </Card>
    );
  };

  if (loading) {
    return <div>加载中...</div>;
  }

  return (
    <div>
      <Alert
        message="OCR引擎配置"
        description="配置不同的OCR引擎用于文档文字识别。优先级数字越小，优先级越高。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      {ocrEngines
        .sort((a, b) => a.priority - b.priority)
        .map(renderEngineCard)}

      {ocrEngines.length === 0 && (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <p>暂无OCR引擎配置</p>
          </div>
        </Card>
      )}
    </div>
  );
};

export default OCREngineConfig;