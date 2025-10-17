import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Select,
  Space,
  Tag,
  Typography,
  message,
  Popconfirm,
  Row,
  Col,
  Card,
  Checkbox,
  Divider,
  Alert,
  Spin
} from 'antd';
import {
  SafetyOutlined,
  ProjectOutlined,
  UserOutlined,
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { 
  userManagementService, 
  User, 
  Permission, 
  UserPermissionResponse,
  PermissionGrantRequest,
  PermissionRevokeRequest
} from '../../services/userManagementService';
import { projectService } from '../../services/projectService';
import { Project } from '../../types';
import ModalContainer from '../common/ModalContainer';

const { Title, Text } = Typography;
const { Option } = Select;
// CheckboxGroup is available as Checkbox.Group

interface PermissionManagerProps {
  visible: boolean;
  user?: User;
  onCancel: () => void;
  onPermissionChange?: () => void;
}

const PERMISSION_OPTIONS = [
  { label: '查看', value: 'view', color: 'blue' },
  { label: '创建', value: 'create', color: 'green' },
  { label: '编辑', value: 'edit', color: 'orange' },
  { label: '删除', value: 'delete', color: 'red' },
  { label: '管理', value: 'admin', color: 'purple' }
];

const PermissionManager: React.FC<PermissionManagerProps> = ({
  visible,
  user,
  onCancel,
  onPermissionChange
}) => {
  const [loading, setLoading] = useState(false);
  const [userPermissions, setUserPermissions] = useState<UserPermissionResponse | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);
  const [grantLoading, setGrantLoading] = useState(false);

  // Load user permissions and available projects
  const loadData = async () => {
    if (!user) return;
    
    setLoading(true);
    try {
      const [permissionsData, projectsData] = await Promise.all([
        userManagementService.getUserPermissions(user.id),
        projectService.getProjects()
      ]);
      
      setUserPermissions(permissionsData);
      setProjects(projectsData);
    } catch (error: any) {
      message.error(error.message || '加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (visible && user) {
      loadData();
    }
  }, [visible, user]);

  // Handle grant permission
  const handleGrantPermission = async () => {
    if (!user || !selectedProject || selectedPermissions.length === 0) {
      message.warning('请选择项目和权限');
      return;
    }

    setGrantLoading(true);
    try {
      const grantRequest: PermissionGrantRequest = {
        user_id: user.id,
        project_id: selectedProject,
        permissions: selectedPermissions
      };
      
      await userManagementService.grantPermission(grantRequest);
      message.success('权限授予成功');
      
      // Reset form and reload data
      setSelectedProject('');
      setSelectedPermissions([]);
      await loadData();
      
      if (onPermissionChange) {
        onPermissionChange();
      }
    } catch (error: any) {
      message.error(error.message || '权限授予失败');
    } finally {
      setGrantLoading(false);
    }
  };

  // Handle revoke permission
  const handleRevokePermission = async (permission: Permission, permissionsToRevoke?: string[]) => {
    try {
      const revokeRequest: PermissionRevokeRequest = {
        user_id: permission.user_id,
        project_id: permission.project_id,
        permissions: permissionsToRevoke
      };
      
      await userManagementService.revokePermission(revokeRequest);
      message.success(permissionsToRevoke ? '部分权限撤销成功' : '权限撤销成功');
      
      await loadData();
      
      if (onPermissionChange) {
        onPermissionChange();
      }
    } catch (error: any) {
      message.error(error.message || '权限撤销失败');
    }
  };

  // Get permission display info
  const getPermissionInfo = (permission: string) => {
    const info = PERMISSION_OPTIONS.find(opt => opt.value === permission);
    return info || { label: permission, value: permission, color: 'default' };
  };

  // Get available projects (exclude projects user already has permissions for)
  const getAvailableProjects = () => {
    if (!userPermissions) return projects;
    
    const userProjectIds = userPermissions.project_permissions.map(p => p.project_id);
    return projects.filter(project => !userProjectIds.includes(project.id));
  };

  // Table columns for user permissions
  const columns: ColumnsType<Permission> = [
    {
      title: '项目',
      key: 'project',
      render: (_, record) => (
        <Space>
          <ProjectOutlined style={{ color: '#1677ff' }} />
          <div>
            <div style={{ fontWeight: 500 }}>{record.project_name}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              ID: {record.project_id}
            </Text>
          </div>
        </Space>
      )
    },
    {
      title: '权限',
      dataIndex: 'permissions',
      key: 'permissions',
      render: (permissions: string[]) => (
        <Space wrap>
          {permissions.map(permission => {
            const info = getPermissionInfo(permission);
            return (
              <Tag key={permission} color={info.color}>
                {info.label}
              </Tag>
            );
          })}
        </Space>
      )
    },
    {
      title: '授权人',
      key: 'granter',
      render: (_, record) => (
        <div>
          <div>{record.granter_username || '系统'}</div>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {new Date(record.granted_at).toLocaleString()}
          </Text>
        </div>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Popconfirm
            title="撤销权限"
            description="确定要撤销该项目的所有权限吗？"
            onConfirm={() => handleRevokePermission(record)}
            okText="确认"
            cancelText="取消"
            okType="danger"
          >
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
            />
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <ModalContainer
      visible={visible}
      onClose={onCancel}
      title={
        <Space>
          <SafetyOutlined />
          权限管理
          {user && (
            <Text type="secondary">- {user.username}</Text>
          )}
        </Space>
      }
      width={800}
      footer={[
        <Button key="close" onClick={onCancel}>
          关闭
        </Button>
      ]}
    >
      {user && (
        <div>
          {/* User Info */}
          <Card size="small" style={{ marginBottom: '16px' }}>
            <Row gutter={16}>
              <Col span={8}>
                <Space>
                  <UserOutlined />
                  <div>
                    <div style={{ fontWeight: 500 }}>{user.username}</div>
                    <Text type="secondary">{user.email}</Text>
                  </div>
                </Space>
              </Col>
              <Col span={8}>
                <div>
                  <Text type="secondary">角色：</Text>
                  <Tag color="blue">{user.role}</Tag>
                </div>
              </Col>
              <Col span={8}>
                <div>
                  <Text type="secondary">部门：</Text>
                  <span>{user.department || '未设置'}</span>
                </div>
              </Col>
            </Row>
          </Card>

          {/* Grant New Permission */}
          <Card 
            title="授予新权限" 
            size="small" 
            style={{ marginBottom: '16px' }}
          >
            <Row gutter={[16, 16]} align="middle">
              <Col span={8}>
                <Select
                  placeholder="选择项目"
                  value={selectedProject}
                  onChange={setSelectedProject}
                  style={{ width: '100%' }}
                  showSearch
                  optionFilterProp="children"
                >
                  {getAvailableProjects().map(project => (
                    <Option key={project.id} value={project.id}>
                      {project.name}
                    </Option>
                  ))}
                </Select>
              </Col>
              <Col span={12}>
                <Checkbox.Group
                  options={PERMISSION_OPTIONS.map(opt => ({
                    label: opt.label,
                    value: opt.value
                  }))}
                  value={selectedPermissions}
                  onChange={setSelectedPermissions}
                />
              </Col>
              <Col span={4}>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  loading={grantLoading}
                  onClick={handleGrantPermission}
                  disabled={!selectedProject || selectedPermissions.length === 0}
                >
                  授予
                </Button>
              </Col>
            </Row>
            
            {getAvailableProjects().length === 0 && (
              <Alert
                message="该用户已拥有所有项目的权限"
                type="info"
                showIcon
                style={{ marginTop: '12px' }}
              />
            )}
          </Card>

          <Divider />

          {/* Current Permissions */}
          <div>
            <Title level={5}>
              <SafetyOutlined style={{ marginRight: '8px' }} />
              当前权限
            </Title>
            
            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Spin size="large" />
              </div>
            ) : (
              <Table
                columns={columns}
                dataSource={userPermissions?.project_permissions || []}
                rowKey="id"
                size="small"
                pagination={false}
                locale={{
                  emptyText: '暂无权限记录'
                }}
              />
            )}
          </div>
        </div>
      )}
    </ModalContainer>
  );
};

export default PermissionManager;