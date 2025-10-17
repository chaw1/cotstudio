import React, { useState } from 'react';
import {
  Card,
  Button,
  Space,
  message,
  Upload,
  Alert,
  Descriptions,
  Popconfirm
} from 'antd';
import {
  DownloadOutlined,
  UploadOutlined,
  FileTextOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { SystemSettings } from '../../types';
import { useSettingsStore } from '../../stores/settingsStore';
import ModalContainer from '../common/ModalContainer';

const SettingsImportExport: React.FC = () => {
  const {
    settings,
    loading,
    exportSettings,
    importSettings,
    resetSettings
  } = useSettingsStore();

  const [importModalVisible, setImportModalVisible] = useState(false);
  const [importData, setImportData] = useState<SystemSettings | null>(null);
  const [importFile, setImportFile] = useState<File | null>(null);

  const handleExport = async () => {
    try {
      const exportData = await exportSettings();
      
      // 创建下载链接
      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: 'application/json'
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `cot-studio-settings-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      message.success('设置已导出');
    } catch (error) {
      message.error('导出设置失败');
    }
  };

  const handleImportFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const data = JSON.parse(content);
        
        // 验证数据结构
        if (data.settings && typeof data.settings === 'object') {
          setImportData(data.settings);
          setImportFile(file);
          setImportModalVisible(true);
        } else {
          message.error('无效的设置文件格式');
        }
      } catch (error) {
        message.error('解析设置文件失败');
      }
    };
    reader.readAsText(file);
    return false; // 阻止自动上传
  };

  const handleConfirmImport = async () => {
    if (!importData) return;
    
    try {
      await importSettings(importData);
      setImportModalVisible(false);
      setImportData(null);
      setImportFile(null);
      message.success('设置已导入');
    } catch (error) {
      message.error('导入设置失败');
    }
  };

  const handleResetSettings = async () => {
    try {
      await resetSettings();
      message.success('设置已重置为默认值');
    } catch (error) {
      message.error('重置设置失败');
    }
  };

  const renderImportPreview = () => {
    if (!importData) return null;

    return (
      <div>
        <Alert
          message="导入预览"
          description="请确认以下设置信息，导入后将覆盖当前设置。"
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Descriptions title="设置概览" bordered column={2}>
          <Descriptions.Item label="LLM提供商数量">
            {importData.llm_providers?.length || 0}
          </Descriptions.Item>
          <Descriptions.Item label="默认LLM提供商">
            {importData.default_llm_provider || '未设置'}
          </Descriptions.Item>
          <Descriptions.Item label="OCR引擎数量">
            {importData.ocr_engines?.length || 0}
          </Descriptions.Item>
          <Descriptions.Item label="默认OCR引擎">
            {importData.default_ocr_engine || '未设置'}
          </Descriptions.Item>
          <Descriptions.Item label="系统提示词数量">
            {importData.system_prompts?.length || 0}
          </Descriptions.Item>
          <Descriptions.Item label="候选答案数量">
            {importData.cot_generation?.candidate_count || '未设置'}
          </Descriptions.Item>
        </Descriptions>

        {importData.llm_providers && importData.llm_providers.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <h4>LLM提供商列表</h4>
            <ul>
              {importData.llm_providers.map(provider => (
                <li key={provider.provider}>
                  {provider.provider} - {provider.model} 
                  {provider.enabled ? ' (已启用)' : ' (已禁用)'}
                </li>
              ))}
            </ul>
          </div>
        )}

        {importData.ocr_engines && importData.ocr_engines.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <h4>OCR引擎列表</h4>
            <ul>
              {importData.ocr_engines.map(engine => (
                <li key={engine.engine}>
                  {engine.engine} - 优先级: {engine.priority}
                  {engine.enabled ? ' (已启用)' : ' (已禁用)'}
                </li>
              ))}
            </ul>
          </div>
        )}

        {importData.system_prompts && importData.system_prompts.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <h4>系统提示词分类</h4>
            <ul>
              {[...new Set(importData.system_prompts.map(p => p.category))].map(category => (
                <li key={category}>
                  {category} ({importData.system_prompts!.filter(p => p.category === category).length}个模板)
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  return (
    <div>
      <Alert
        message="设置备份与恢复"
        description="导出当前设置用于备份，或导入之前的设置文件进行恢复。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Card title="备份与恢复操作">
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <h4>导出设置</h4>
            <p>将当前所有系统设置导出为JSON文件，用于备份或迁移。</p>
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={handleExport}
              loading={loading}
            >
              导出设置
            </Button>
          </div>

          <div>
            <h4>导入设置</h4>
            <p>从之前导出的设置文件中恢复配置。导入后将覆盖当前所有设置。</p>
            <Upload
              accept=".json"
              beforeUpload={handleImportFile}
              showUploadList={false}
            >
              <Button icon={<UploadOutlined />}>
                选择设置文件
              </Button>
            </Upload>
          </div>

          <div>
            <h4>重置设置</h4>
            <p>将所有设置重置为系统默认值。此操作不可撤销。</p>
            <Popconfirm
              title="确定要重置所有设置吗？"
              description="此操作将清除所有自定义配置，恢复为系统默认设置。"
              onConfirm={handleResetSettings}
              okText="确定重置"
              cancelText="取消"
              icon={<ExclamationCircleOutlined style={{ color: 'red' }} />}
            >
              <Button danger>
                重置为默认设置
              </Button>
            </Popconfirm>
          </div>
        </Space>
      </Card>

      {settings && (
        <Card title="当前设置概览" style={{ marginTop: 16 }}>
          <Descriptions bordered column={2}>
            <Descriptions.Item label="LLM提供商">
              {settings.llm_providers.length}个 (默认: {settings.default_llm_provider})
            </Descriptions.Item>
            <Descriptions.Item label="OCR引擎">
              {settings.ocr_engines.length}个 (默认: {settings.default_ocr_engine})
            </Descriptions.Item>
            <Descriptions.Item label="系统提示词">
              {settings.system_prompts.length}个模板
            </Descriptions.Item>
            <Descriptions.Item label="候选答案数量">
              {settings.cot_generation.candidate_count}个
            </Descriptions.Item>
            <Descriptions.Item label="问题最大长度">
              {settings.cot_generation.question_max_length}字符
            </Descriptions.Item>
            <Descriptions.Item label="答案最大长度">
              {settings.cot_generation.answer_max_length}字符
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      {/* 导入确认模态框 */}
      <ModalContainer
        visible={importModalVisible}
        onClose={() => {
          setImportModalVisible(false);
          setImportData(null);
          setImportFile(null);
        }}
        title="确认导入设置"
        footer={[
          <Button
            key="cancel"
            onClick={() => {
              setImportModalVisible(false);
              setImportData(null);
              setImportFile(null);
            }}
          >
            取消
          </Button>,
          <Button
            key="import"
            type="primary"
            onClick={handleConfirmImport}
            loading={loading}
          >
            确认导入
          </Button>
        ]}
        width={800}
      >
        {renderImportPreview()}
      </ModalContainer>
    </div>
  );
};

export default SettingsImportExport;