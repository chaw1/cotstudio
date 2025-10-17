import React, { useEffect } from 'react';
import { Typography, Tabs, Spin, Alert } from 'antd';
import {
  SettingOutlined,
  RobotOutlined,
  EyeOutlined,
  MessageOutlined,
  SlidersFilled,
  ImportOutlined
} from '@ant-design/icons';
import { useSettingsStore } from '../stores/settingsStore';
import { useResponsiveBreakpoint } from '../hooks/useResponsiveBreakpoint';
import {
  LLMProviderConfig,
  OCREngineConfig,
  SystemPromptEditor,
  COTGenerationConfig,
  SettingsImportExport
} from '../components/settings';
import './Settings.css';

const { Title } = Typography;

const Settings: React.FC = () => {
  const { loading, error, loadSettings, clearError } = useSettingsStore();
  const { isMobile, isTablet } = useResponsiveBreakpoint();

  const tabItems = [
    {
      key: 'llm',
      label: (
        <span style={{ fontSize: isMobile ? '12px' : '14px' }}>
          <RobotOutlined />
          {isMobile ? 'LLM' : 'LLM配置'}
        </span>
      ),
      children: (
        <div style={{ padding: isMobile ? '8px 0' : '16px 0' }}>
          <LLMProviderConfig />
        </div>
      )
    },
    {
      key: 'ocr',
      label: (
        <span style={{ fontSize: isMobile ? '12px' : '14px' }}>
          <EyeOutlined />
          {isMobile ? 'OCR' : 'OCR引擎'}
        </span>
      ),
      children: (
        <div style={{ padding: isMobile ? '8px 0' : '16px 0' }}>
          <OCREngineConfig />
        </div>
      )
    },
    {
      key: 'prompts',
      label: (
        <span style={{ fontSize: isMobile ? '12px' : '14px' }}>
          <MessageOutlined />
          {isMobile ? '提示词' : '系统提示词'}
        </span>
      ),
      children: (
        <div style={{ padding: isMobile ? '8px 0' : '16px 0' }}>
          <SystemPromptEditor />
        </div>
      )
    },
    {
      key: 'cot',
      label: (
        <span style={{ fontSize: isMobile ? '12px' : '14px' }}>
          <SlidersFilled />
          {isMobile ? 'CoT' : 'CoT生成'}
        </span>
      ),
      children: (
        <div style={{ padding: isMobile ? '8px 0' : '16px 0' }}>
          <COTGenerationConfig />
        </div>
      )
    },
    {
      key: 'import-export',
      label: (
        <span style={{ fontSize: isMobile ? '12px' : '14px' }}>
          <ImportOutlined />
          {isMobile ? '导入导出' : '导入导出'}
        </span>
      ),
      children: (
        <div style={{ padding: isMobile ? '8px 0' : '16px 0' }}>
          <SettingsImportExport />
        </div>
      )
    }
  ];

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  useEffect(() => {
    if (error) {
      clearError();
    }
  }, [error, clearError]);

  if (loading && !useSettingsStore.getState().settings) {
    return (
      <div style={{ textAlign: 'center', padding: '50px 0' }}>
        <Spin size="large" />
        <p style={{ marginTop: 16 }}>加载系统设置中...</p>
      </div>
    );
  }

  return (
    <div className="fade-in work-area-adaptive settings-page">
      <Title level={isMobile ? 3 : 2} style={{ marginBottom: isMobile ? '16px' : '24px' }}>
        <SettingOutlined /> 系统设置
      </Title>
      
      {error && (
        <Alert
          message="加载设置失败"
          description={error}
          type="error"
          closable
          onClose={clearError}
          style={{ marginBottom: 16 }}
        />
      )}

      <Tabs
        defaultActiveKey="llm"
        type="card"
        size={isMobile ? 'small' : 'large'}
        style={{ 
          marginTop: 16,
          width: '100%'
        }}
        tabPosition={isMobile ? 'top' : 'top'}
        tabBarStyle={{
          marginBottom: isMobile ? '12px' : '16px'
        }}
        items={tabItems}
      />
    </div>
  );
};

export default Settings;