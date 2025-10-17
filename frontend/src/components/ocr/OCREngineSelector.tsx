import React, { useState, useEffect } from 'react';
import {
  Card,
  Select,
  Form,
  Button,
  Space,
  Typography,
  Alert,
  Divider,
  Collapse,
  InputNumber,
  Switch,
  message,
} from 'antd';
import {
  SettingOutlined,
  PlayCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;
const { Panel } = Collapse;

export interface OCREngine {
  id: string;
  name: string;
  description: string;
  supported: boolean;
  config?: Record<string, any>;
}

export interface OCREngineConfig {
  engine: string;
  confidence: number;
  enableTableDetection: boolean;
  enableImageDetection: boolean;
  language: string;
  customParams?: Record<string, any>;
}

interface OCREngineSelectorProps {
  fileId: string;
  onStartOCR: (config: OCREngineConfig) => Promise<void>;
  loading?: boolean;
}

const OCREngineSelector: React.FC<OCREngineSelectorProps> = ({
  fileId,
  onStartOCR,
  loading = false,
}) => {
  const [form] = Form.useForm();
  const [selectedEngine, setSelectedEngine] = useState<string>('fallback');
  const [showAdvanced, setShowAdvanced] = useState(false);

  // 可用的OCR引擎
  const availableEngines: OCREngine[] = [
    {
      id: 'fallback',
      name: 'Text Extractor',
      description: '文本提取器，支持TXT、MD、JSON等纯文本文件',
      supported: true,
      config: {
        languages: ['auto'],
        defaultLanguage: 'auto',
      },
    },
    // 以下引擎暂未实现，待后续版本支持
    // {
    //   id: 'alibaba_alm',
    //   name: 'Alibaba AdvancedLiterateMachinery',
    //   description: '阿里巴巴高级文档理解引擎，专业处理学术文档',
    //   supported: false,
    //   config: {
    //     languages: ['zh-cn', 'en'],
    //     defaultLanguage: 'zh-cn',
    //   },
    // },
    // {
    //   id: 'mineru',
    //   name: 'MinerU',
    //   description: '专业的PDF文档解析工具，保持原始格式',
    //   supported: false,
    //   config: {
    //     languages: ['zh-cn', 'en', 'auto'],
    //     defaultLanguage: 'auto',
    //     preserveLayout: true,
    //     extractImages: true,
    //   },
    // },
  ];

  const selectedEngineInfo = availableEngines.find(e => e.id === selectedEngine);

  // 处理表单提交
  const handleSubmit = async (values: any) => {
    try {
      const config: OCREngineConfig = {
        engine: selectedEngine,
        confidence: values.confidence || 0.8,
        enableTableDetection: values.enableTableDetection ?? true,
        enableImageDetection: values.enableImageDetection ?? true,
        language: values.language || selectedEngineInfo?.config?.defaultLanguage || 'auto',
        customParams: values.customParams || {},
      };

      await onStartOCR(config);
      message.success('OCR处理已开始');
    } catch (error) {
      message.error('启动OCR处理失败');
    }
  };

  // 重置表单
  const handleReset = () => {
    form.resetFields();
    setSelectedEngine('fallback');
  };

  useEffect(() => {
    // 当选择的引擎改变时，更新表单默认值
    if (selectedEngineInfo) {
      form.setFieldsValue({
        language: selectedEngineInfo.config?.defaultLanguage,
      });
    }
  }, [selectedEngine, selectedEngineInfo, form]);

  return (
    <Card
      title={
        <Space>
          <SettingOutlined />
          <span>OCR引擎配置</span>
        </Space>
      }
      extra={
        <Button
          type="link"
          icon={<InfoCircleOutlined />}
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          {showAdvanced ? '隐藏高级选项' : '显示高级选项'}
        </Button>
      }
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          confidence: 0.8,
          enableTableDetection: true,
          enableImageDetection: true,
          language: selectedEngineInfo?.config?.defaultLanguage || 'auto',
        }}
      >
        {/* 引擎选择 */}
        <Form.Item
          label="OCR引擎"
          name="engine"
          rules={[{ required: true, message: '请选择OCR引擎' }]}
        >
          <Select
            value={selectedEngine}
            onChange={setSelectedEngine}
            placeholder="选择OCR引擎"
          >
            {availableEngines.map((engine) => (
              <Option
                key={engine.id}
                value={engine.id}
                disabled={!engine.supported}
              >
                <div>
                  <Text strong>{engine.name}</Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    {engine.description}
                  </Text>
                </div>
              </Option>
            ))}
          </Select>
        </Form.Item>

        {/* 引擎信息 */}
        {selectedEngineInfo && (
          <Alert
            message={selectedEngineInfo.name}
            description={selectedEngineInfo.description}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {/* 基础配置 */}
        <Form.Item
          label="识别语言"
          name="language"
          rules={[{ required: true, message: '请选择识别语言' }]}
        >
          <Select placeholder="选择识别语言">
            {selectedEngineInfo?.config?.languages?.map((lang: string) => (
              <Option key={lang} value={lang}>
                {getLanguageName(lang)}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item label="检测选项">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Form.Item
              name="enableTableDetection"
              valuePropName="checked"
              style={{ marginBottom: 8 }}
            >
              <Switch checkedChildren="开启" unCheckedChildren="关闭" />
              <Text style={{ marginLeft: 8 }}>表格检测</Text>
            </Form.Item>
            <Form.Item
              name="enableImageDetection"
              valuePropName="checked"
              style={{ marginBottom: 0 }}
            >
              <Switch checkedChildren="开启" unCheckedChildren="关闭" />
              <Text style={{ marginLeft: 8 }}>图像检测</Text>
            </Form.Item>
          </Space>
        </Form.Item>

        {/* 高级选项 */}
        {showAdvanced && (
          <Collapse ghost>
            <Panel header="高级选项" key="advanced">
              <Form.Item
                label="置信度阈值"
                name="confidence"
                help="设置OCR识别的最低置信度，范围0.1-1.0"
              >
                <InputNumber
                  min={0.1}
                  max={1.0}
                  step={0.1}
                  style={{ width: '100%' }}
                  placeholder="0.8"
                />
              </Form.Item>

              {selectedEngine === 'paddleocr' && (
                <Form.Item
                  label="检测模型"
                  name="detModel"
                  help="选择文本检测模型"
                >
                  <Select placeholder="使用默认模型">
                    <Option value="ch_PP-OCRv4_det">PP-OCRv4检测模型</Option>
                    <Option value="ch_PP-OCRv3_det">PP-OCRv3检测模型</Option>
                  </Select>
                </Form.Item>
              )}

              {selectedEngine === 'alibaba_alm' && (
                <Form.Item
                  label="文档类型"
                  name="documentType"
                  help="指定文档类型以优化识别效果"
                >
                  <Select placeholder="自动检测">
                    <Option value="academic">学术论文</Option>
                    <Option value="book">书籍</Option>
                    <Option value="magazine">杂志</Option>
                    <Option value="general">通用文档</Option>
                  </Select>
                </Form.Item>
              )}
            </Panel>
          </Collapse>
        )}

        <Divider />

        {/* 操作按钮 */}
        <Form.Item>
          <Space>
            <Button
              type="primary"
              htmlType="submit"
              icon={<PlayCircleOutlined />}
              loading={loading}
              size="large"
            >
              开始OCR处理
            </Button>
            <Button onClick={handleReset} disabled={loading}>
              重置配置
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};

// 获取语言显示名称
function getLanguageName(code: string): string {
  const languageMap: Record<string, string> = {
    ch: '中文',
    en: '英文',
    'zh-cn': '简体中文',
    fr: '法语',
    german: '德语',
    korean: '韩语',
    japan: '日语',
    auto: '自动检测', // 添加自动检测选项
  };
  return languageMap[code] || code;
}

export default OCREngineSelector;