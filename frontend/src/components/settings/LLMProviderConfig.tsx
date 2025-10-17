import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Switch,
  Button,
  Select,
  InputNumber,
  Space,
  message,
  Popconfirm,
  Tag,
  Tooltip,
  Alert
} from 'antd';
import { PlusOutlined, DeleteOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { LLMProviderConfig as LLMProviderConfigType } from '../../types';
import { useSettingsStore } from '../../stores/settingsStore';

const { Option } = Select;
const { Password } = Input;

interface LLMProviderConfigProps {
  onConfigChange?: (providers: LLMProviderConfigType[]) => void;
}

const LLMProviderConfig: React.FC<LLMProviderConfigProps> = ({ onConfigChange }) => {
  const {
    llmProviders,
    defaultLLMProvider,
    loading,
    error,
    updateLLMProvider,
    setDefaultLLMProvider,
    validateLLMProvider,
    clearError
  } = useSettingsStore();

  const [form] = Form.useForm();
  const [editingProvider, setEditingProvider] = useState<string | null>(null);
  const [validationResults, setValidationResults] = useState<Record<string, boolean>>({});
  const [validating, setValidating] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (error) {
      message.error(error);
      clearError();
    }
  }, [error, clearError]);

  useEffect(() => {
    onConfigChange?.(llmProviders);
  }, [llmProviders, onConfigChange]);

  const handleProviderUpdate = async (provider: string, values: any) => {
    try {
      const config: LLMProviderConfigType = {
        provider,
        api_key: values.api_key,
        base_url: values.base_url,
        model: values.model,
        enabled: values.enabled,
        timeout: values.timeout,
        max_retries: values.max_retries,
        retry_delay: values.retry_delay
      };

      await updateLLMProvider(provider, config);
      setEditingProvider(null);
      message.success('LLM提供商配置已更新');
    } catch (error) {
      message.error('更新LLM提供商配置失败');
    }
  };

  const handleValidateProvider = async (provider: string, config: LLMProviderConfigType) => {
    setValidating(prev => ({ ...prev, [provider]: true }));
    try {
      const isValid = await validateLLMProvider(provider, config);
      setValidationResults(prev => ({ ...prev, [provider]: isValid }));
      message[isValid ? 'success' : 'error'](
        isValid ? '配置验证成功' : '配置验证失败'
      );
    } catch (error) {
      setValidationResults(prev => ({ ...prev, [provider]: false }));
    } finally {
      setValidating(prev => ({ ...prev, [provider]: false }));
    }
  };

  const handleSetDefault = async (provider: string) => {
    try {
      await setDefaultLLMProvider(provider);
      message.success(`已设置 ${provider} 为默认LLM提供商`);
    } catch (error) {
      message.error('设置默认提供商失败');
    }
  };

  const renderProviderCard = (provider: LLMProviderConfigType) => {
    const isEditing = editingProvider === provider.provider;
    const isValidated = validationResults[provider.provider];
    const isValidating = validating[provider.provider];
    const isDefault = defaultLLMProvider === provider.provider;

    return (
      <Card
        key={provider.provider}
        title={
          <Space>
            <span style={{ textTransform: 'uppercase' }}>{provider.provider}</span>
            {isDefault && <Tag color="blue">默认</Tag>}
            {provider.enabled && <Tag color="green">已启用</Tag>}
            {!provider.enabled && <Tag color="red">已禁用</Tag>}
            {isValidated && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
            {isValidated === false && <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />}
          </Space>
        }
        extra={
          <Space>
            {!isDefault && provider.enabled && (
              <Button
                size="small"
                onClick={() => handleSetDefault(provider.provider)}
              >
                设为默认
              </Button>
            )}
            <Button
              size="small"
              type={isEditing ? 'default' : 'primary'}
              onClick={() => {
                if (isEditing) {
                  setEditingProvider(null);
                } else {
                  setEditingProvider(provider.provider);
                  form.setFieldsValue(provider);
                }
              }}
            >
              {isEditing ? '取消' : '编辑'}
            </Button>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        {isEditing ? (
          <Form
            form={form}
            layout="vertical"
            onFinish={(values) => handleProviderUpdate(provider.provider, values)}
            initialValues={provider}
          >
            <Form.Item
              name="api_key"
              label="API密钥"
              rules={[
                { required: provider.provider !== 'local', message: '请输入API密钥' }
              ]}
            >
              <Password placeholder="输入API密钥" />
            </Form.Item>

            <Form.Item
              name="base_url"
              label="API基础URL"
              rules={[{ required: true, message: '请输入API基础URL' }]}
            >
              <Input placeholder="https://api.example.com" />
            </Form.Item>

            <Form.Item
              name="model"
              label="模型名称"
              rules={[{ required: true, message: '请输入模型名称' }]}
            >
              <Input placeholder="模型名称" />
            </Form.Item>

            <Form.Item name="enabled" label="启用" valuePropName="checked">
              <Switch />
            </Form.Item>

            <Form.Item
              name="timeout"
              label="请求超时(秒)"
              rules={[{ required: true, message: '请输入超时时间' }]}
            >
              <InputNumber min={1} max={300} />
            </Form.Item>

            <Form.Item
              name="max_retries"
              label="最大重试次数"
              rules={[{ required: true, message: '请输入最大重试次数' }]}
            >
              <InputNumber min={0} max={10} />
            </Form.Item>

            <Form.Item
              name="retry_delay"
              label="重试延迟(秒)"
              rules={[{ required: true, message: '请输入重试延迟' }]}
            >
              <InputNumber min={0.1} max={10} step={0.1} />
            </Form.Item>

            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" loading={loading}>
                  保存
                </Button>
                <Button
                  onClick={() => {
                    const currentValues = form.getFieldsValue();
                    handleValidateProvider(provider.provider, {
                      ...provider,
                      ...currentValues
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
            <p><strong>模型:</strong> {provider.model}</p>
            <p><strong>API URL:</strong> {provider.base_url}</p>
            <p><strong>超时时间:</strong> {provider.timeout}秒</p>
            <p><strong>最大重试:</strong> {provider.max_retries}次</p>
            <p><strong>重试延迟:</strong> {provider.retry_delay}秒</p>
            {provider.api_key && (
              <p><strong>API密钥:</strong> {'*'.repeat(20)}</p>
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
        message="LLM提供商配置"
        description="配置不同的LLM提供商，用于生成CoT问题和答案。请确保API密钥的安全性。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      {llmProviders.map(renderProviderCard)}

      {llmProviders.length === 0 && (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <p>暂无LLM提供商配置</p>
          </div>
        </Card>
      )}
    </div>
  );
};

export default LLMProviderConfig;