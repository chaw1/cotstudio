import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Form,
  Input,
  Select,
  Space,
  Tag,
  Popconfirm,
  message,
  Tabs,
  Transfer,
  Typography,
  Descriptions,
  Alert,
  Row,
  Col,
  Checkbox
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UserOutlined,
  SafetyOutlined,
  SettingOutlined
} from '@ant-design/icons';
import ModalContainer from '../common/ModalContainer';
import type { ColumnsType } from 'antd/es/table';
import type { TransferDirection } from 'antd/es/transfer';

const { Option } = Select;
const { TextArea } = Input;
const { Text } = Typography;

interface Role {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  role_type: string;
  permissions: string[];
  is_system_role: boolean;
  created_at: string;
}

interface Permission {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  resource_type: string;
  action: string;
  is_system_permission: boolean;
}

interface UserRole {
  id: string;
  user_id: string;
  role_id: string;
  granted_by?: string;
  granted_at: string;
  expires_at?: string;
  role: Role;
}

const RolePermissionManager: React.FC = () => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [userRoles, setUserRoles] = useState<UserRole[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('roles');

  // 角色管理状态
  const [roleModalVisible, setRoleModalVisible] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [roleForm] = Form.useForm();

  // 用户角色管理状态
  const [userRoleModalVisible, setUserRoleModalVisible] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<string>('');
  const [availableRoles, setAvailableRoles] = useState<string[]>([]);
  const [assignedRoles, setAssignedRoles] = useState<string[]>([]);

  const roleTypeOptions = [
    { value: 'admin', label: '管理员', color: 'red' },
    { value: 'editor', label: '编辑者', color: 'blue' },
    { value: 'reviewer', label: '审核者', color: 'orange' },
    { value: 'viewer', label: '查看者', color: 'green' }
  ];

  const resourceTypeOptions = [
    { value: 'project', label: '项目' },
    { value: 'file', label: '文件' },
    { value: 'cot_item', label: 'CoT数据' },
    { value: 'user', label: '用户' },
    { value: 'role', label: '角色' },
    { value: 'permission', label: '权限' },
    { value: 'system_setting', label: '系统设置' },
    { value: 'knowledge_graph', label: '知识图谱' }
  ];

  // 获取角色列表
  const fetchRoles = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/audit/roles');
      const data = await response.json();
      if (response.ok) {
        setRoles(data);
      } else {
        message.error('获取角色列表失败');
      }
    } catch (error) {
      message.error('获取角色列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取权限列表
  const fetchPermissions = async () => {
    try {
      const response = await fetch('/api/v1/audit/permissions');
      const data = await response.json();
      if (response.ok) {
        setPermissions(data);
      }
    } catch (error) {
      console.error('Failed to fetch permissions:', error);
    }
  };

  // 获取用户角色列表
  const fetchUserRoles = async (userId?: string) => {
    try {
      const url = userId 
        ? `/api/v1/audit/users/${userId}/permissions`
        : '/api/v1/audit/user-roles'; // 假设有这个端点
      const response = await fetch(url);
      const data = await response.json();
      if (response.ok) {
        if (userId) {
          setAssignedRoles(data.roles.map((ur: UserRole) => ur.role_id));
        } else {
          setUserRoles(data);
        }
      }
    } catch (error) {
      console.error('Failed to fetch user roles:', error);
    }
  };

  useEffect(() => {
    fetchRoles();
    fetchPermissions();
  }, []);

  // 创建或更新角色
  const handleSaveRole = async (values: any) => {
    try {
      const url = editingRole 
        ? `/api/v1/audit/roles/${editingRole.id}`
        : '/api/v1/audit/roles';
      
      const method = editingRole ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(values),
      });

      if (response.ok) {
        message.success(editingRole ? '角色更新成功' : '角色创建成功');
        setRoleModalVisible(false);
        setEditingRole(null);
        roleForm.resetFields();
        fetchRoles();
      } else {
        const error = await response.json();
        message.error(error.detail || '操作失败');
      }
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 删除角色
  const handleDeleteRole = async (roleId: string) => {
    try {
      const response = await fetch(`/api/v1/audit/roles/${roleId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        message.success('角色删除成功');
        fetchRoles();
      } else {
        const error = await response.json();
        message.error(error.detail || '删除失败');
      }
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 分配角色给用户
  const handleAssignRole = async (userId: string, roleId: string) => {
    try {
      const response = await fetch(`/api/v1/audit/users/${userId}/roles`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          role_id: roleId,
        }),
      });

      if (response.ok) {
        message.success('角色分配成功');
        fetchUserRoles(userId);
      } else {
        const error = await response.json();
        message.error(error.detail || '分配失败');
      }
    } catch (error) {
      message.error('分配失败');
    }
  };

  // 撤销用户角色
  const handleRevokeRole = async (userId: string, roleId: string) => {
    try {
      const response = await fetch(`/api/v1/audit/users/${userId}/roles/${roleId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        message.success('角色撤销成功');
        fetchUserRoles(userId);
      } else {
        const error = await response.json();
        message.error(error.detail || '撤销失败');
      }
    } catch (error) {
      message.error('撤销失败');
    }
  };

  const openRoleModal = (role?: Role) => {
    setEditingRole(role || null);
    if (role) {
      roleForm.setFieldsValue(role);
    } else {
      roleForm.resetFields();
    }
    setRoleModalVisible(true);
  };

  const openUserRoleModal = (userId: string) => {
    setSelectedUserId(userId);
    setAvailableRoles(roles.map(role => role.id));
    fetchUserRoles(userId);
    setUserRoleModalVisible(true);
  };

  const getRoleTypeTag = (roleType: string) => {
    const option = roleTypeOptions.find(opt => opt.value === roleType);
    return (
      <Tag color={option?.color || 'default'}>
        {option?.label || roleType}
      </Tag>
    );
  };

  const roleColumns: ColumnsType<Role> = [
    {
      title: '角色名称',
      dataIndex: 'display_name',
      key: 'display_name',
    },
    {
      title: '标识符',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text code>{text}</Text>
    },
    {
      title: '类型',
      dataIndex: 'role_type',
      key: 'role_type',
      render: getRoleTypeTag
    },
    {
      title: '权限数量',
      dataIndex: 'permissions',
      key: 'permissions',
      render: (permissions: string[]) => permissions.length
    },
    {
      title: '系统角色',
      dataIndex: 'is_system_role',
      key: 'is_system_role',
      render: (isSystem: boolean) => (
        <Tag color={isSystem ? 'blue' : 'default'}>
          {isSystem ? '是' : '否'}
        </Tag>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => openRoleModal(record)}
            disabled={record.is_system_role}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个角色吗？"
            onConfirm={() => handleDeleteRole(record.id)}
            disabled={record.is_system_role}
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              disabled={record.is_system_role}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  const permissionColumns: ColumnsType<Permission> = [
    {
      title: '权限名称',
      dataIndex: 'display_name',
      key: 'display_name',
    },
    {
      title: '标识符',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text code>{text}</Text>
    },
    {
      title: '资源类型',
      dataIndex: 'resource_type',
      key: 'resource_type',
      render: (resourceType: string) => {
        const option = resourceTypeOptions.find(opt => opt.value === resourceType);
        return option?.label || resourceType;
      }
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
    },
    {
      title: '系统权限',
      dataIndex: 'is_system_permission',
      key: 'is_system_permission',
      render: (isSystem: boolean) => (
        <Tag color={isSystem ? 'blue' : 'default'}>
          {isSystem ? '是' : '否'}
        </Tag>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    }
  ];

  return (
    <div>
      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        items={[
          {
            key: 'roles',
            label: <span><SafetyOutlined />角色管理</span>,
            children: (
              <Card
                title="角色管理"
                extra={
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => openRoleModal()}
                  >
                    创建角色
                  </Button>
                }
              >
                <Table
                  columns={roleColumns}
                  dataSource={roles}
                  rowKey="id"
                  loading={loading}
                  pagination={{
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                  }}
                />
              </Card>
            )
          },
          {
            key: 'permissions',
            label: <span><SettingOutlined />权限列表</span>,
            children: (
              <Card title="系统权限">
                <Table
                  columns={permissionColumns}
                  dataSource={permissions}
                  rowKey="id"
                  pagination={{
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                  }}
                />
              </Card>
            )
          },
          {
            key: 'user-roles',
            label: <span><UserOutlined />用户角色</span>,
            children: (
              <Card
                title="用户角色管理"
                extra={
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => {
                      // 这里可以打开用户选择对话框
                      const userId = prompt('请输入用户ID:');
                      if (userId) {
                        openUserRoleModal(userId);
                      }
                    }}
                  >
                    分配角色
                  </Button>
                }
              >
                <Alert
                  message="用户角色管理"
                  description="在这里可以查看和管理用户的角色分配情况。点击分配角色按钮为用户分配新角色。"
                  type="info"
                  style={{ marginBottom: 16 }}
                />
                {/* 这里可以添加用户角色列表表格 */}
              </Card>
            )
          }
        ]}
      />

      {/* 角色创建/编辑模态框 */}
      <ModalContainer
        visible={roleModalVisible}
        onClose={() => {
          setRoleModalVisible(false);
          setEditingRole(null);
          roleForm.resetFields();
        }}
        title={editingRole ? '编辑角色' : '创建角色'}
        width={600}
        footer={null}
      >
        <Form
          form={roleForm}
          layout="vertical"
          onFinish={handleSaveRole}
        >
          <Form.Item
            name="name"
            label="角色标识符"
            rules={[
              { required: true, message: '请输入角色标识符' },
              { pattern: /^[a-z0-9_-]+$/, message: '只能包含小写字母、数字、下划线和连字符' }
            ]}
          >
            <Input placeholder="例如: custom_editor" disabled={!!editingRole} />
          </Form.Item>

          <Form.Item
            name="display_name"
            label="显示名称"
            rules={[{ required: true, message: '请输入显示名称' }]}
          >
            <Input placeholder="例如: 自定义编辑者" />
          </Form.Item>

          <Form.Item
            name="role_type"
            label="角色类型"
            rules={[{ required: true, message: '请选择角色类型' }]}
          >
            <Select placeholder="选择角色类型">
              {roleTypeOptions.map(option => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={3} placeholder="角色描述" />
          </Form.Item>

          <Form.Item
            name="permissions"
            label="权限"
            rules={[{ required: true, message: '请选择至少一个权限' }]}
          >
            <Checkbox.Group>
              <Row>
                {permissions.map(permission => (
                  <Col span={12} key={permission.id} style={{ marginBottom: 8 }}>
                    <Checkbox value={permission.name}>
                      {permission.display_name}
                    </Checkbox>
                  </Col>
                ))}
              </Row>
            </Checkbox.Group>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingRole ? '更新' : '创建'}
              </Button>
              <Button onClick={() => {
                setRoleModalVisible(false);
                setEditingRole(null);
                roleForm.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </ModalContainer>

      {/* 用户角色分配模态框 */}
      <ModalContainer
        visible={userRoleModalVisible}
        onClose={() => {
          setUserRoleModalVisible(false);
          setSelectedUserId('');
        }}
        title={`为用户 ${selectedUserId} 分配角色`}
        width={800}
        footer={null}
      >
        <div>
          <Text strong>可用角色：</Text>
          <div style={{ marginTop: 8 }}>
            {roles.map(role => (
              <Tag
                key={role.id}
                color={assignedRoles.includes(role.id) ? 'blue' : 'default'}
                style={{ marginBottom: 8, cursor: 'pointer' }}
                onClick={() => {
                  if (assignedRoles.includes(role.id)) {
                    handleRevokeRole(selectedUserId, role.id);
                  } else {
                    handleAssignRole(selectedUserId, role.id);
                  }
                }}
              >
                {role.display_name} {assignedRoles.includes(role.id) && '✓'}
              </Tag>
            ))}
          </div>
        </div>
      </ModalContainer>
    </div>
  );
};

export default RolePermissionManager;