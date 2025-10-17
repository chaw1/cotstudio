import React, { useState } from 'react';
import { Card, Tabs, Typography, Space, Alert } from 'antd';
import { SafetyOutlined, HistoryOutlined, SettingOutlined } from '@ant-design/icons';
import AuditLogViewer from '../components/audit/AuditLogViewer';
import RolePermissionManager from '../components/audit/RolePermissionManager';

const { Title } = Typography;

const AuditPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('logs');

  const tabItems = [
    {
      key: 'logs',
      label: (
        <span>
          <HistoryOutlined />
          审计日志
        </span>
      ),
      children: (
        <AuditLogViewer />
      )
    },
    {
      key: 'permissions',
      label: (
        <span>
          <SettingOutlined />
          角色权限
        </span>
      ),
      children: (
        <RolePermissionManager />
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={2}>
            <SafetyOutlined /> 审计与权限管理
          </Title>
          <Alert
            message="审计系统"
            description="查看系统操作日志、管理用户角色和权限。所有敏感操作都会被记录在审计日志中。"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        </div>

        <Card>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={tabItems}
          />
        </Card>
      </Space>
    </div>
  );
};

export default AuditPage;