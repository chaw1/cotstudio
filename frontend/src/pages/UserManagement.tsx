import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Input,
  Select,
  Space,
  Tag,
  Typography,
  Row,
  Col,
  Statistic,
  message,
  Popconfirm,
  Tooltip,
  Avatar
} from 'antd';
import {
  UserOutlined,
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  KeyOutlined,
  TeamOutlined,
  UserAddOutlined,
  CheckCircleOutlined,
  StopOutlined,
  SafetyOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useResponsiveBreakpoint } from '../hooks/useResponsiveBreakpoint';
import { userManagementService, User, UserSearchParams, UserStatsResponse, UserCreateRequest, UserUpdateRequest } from '../services/userManagementService';
import { UserForm, PasswordResetModal, PermissionManager } from '../components/user';

const { Title, Text } = Typography;
const { Option } = Select;

const UserManagement: React.FC = () => {
  const { isMobile, isTablet } = useResponsiveBreakpoint();
  
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<UserStatsResponse | null>(null);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total: number, range: [number, number]) => 
      `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`
  });
  
  // Search and filter states
  const [searchText, setSearchText] = useState('');
  const [selectedRole, setSelectedRole] = useState<string | undefined>(undefined);
  const [selectedDepartment, setSelectedDepartment] = useState<string | undefined>(undefined);
  const [selectedStatus, setSelectedStatus] = useState<boolean | undefined>(undefined);

  // Modal states
  const [userFormVisible, setUserFormVisible] = useState(false);
  const [userFormMode, setUserFormMode] = useState<'create' | 'edit'>('create');
  const [editingUser, setEditingUser] = useState<User | undefined>(undefined);
  const [userFormLoading, setUserFormLoading] = useState(false);
  
  const [passwordResetVisible, setPasswordResetVisible] = useState(false);
  const [resetPasswordUser, setResetPasswordUser] = useState<User | undefined>(undefined);
  const [passwordResetLoading, setPasswordResetLoading] = useState(false);

  const [permissionManagerVisible, setPermissionManagerVisible] = useState(false);
  const [permissionUser, setPermissionUser] = useState<User | undefined>(undefined);

  // Load users data
  const loadUsers = async (params: UserSearchParams = {}) => {
    setLoading(true);
    try {
      const searchParams = {
        page: pagination.current,
        size: pagination.pageSize,
        ...params
      };
      
      const response = await userManagementService.getUsers(searchParams);
      setUsers(response.users);
      setPagination(prev => ({
        ...prev,
        total: response.total,
        current: response.page
      }));
    } catch (error: any) {
      message.error(error.message || '加载用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  // Load statistics
  const loadStats = async () => {
    try {
      const statsData = await userManagementService.getUserStats();
      setStats(statsData);
    } catch (error: any) {
      console.error('Failed to load user stats:', error);
    }
  };

  // Initial load
  useEffect(() => {
    loadUsers();
    loadStats();
  }, []);

  // Handle search
  const handleSearch = () => {
    const searchParams: UserSearchParams = {};
    
    if (searchText.trim()) {
      searchParams.search = searchText.trim();
    }
    if (selectedRole) {
      searchParams.role = selectedRole;
    }
    if (selectedDepartment) {
      searchParams.department = selectedDepartment;
    }
    if (selectedStatus !== undefined) {
      searchParams.is_active = selectedStatus;
    }
    
    setPagination(prev => ({ ...prev, current: 1 }));
    loadUsers(searchParams);
  };

  // Handle reset filters
  const handleReset = () => {
    setSearchText('');
    setSelectedRole(undefined);
    setSelectedDepartment(undefined);
    setSelectedStatus(undefined);
    setPagination(prev => ({ ...prev, current: 1 }));
    loadUsers();
  };

  // Handle table pagination change
  const handleTableChange = (page: number, pageSize: number) => {
    setPagination(prev => ({
      ...prev,
      current: page,
      pageSize: pageSize
    }));
    
    const searchParams: UserSearchParams = {
      page,
      size: pageSize
    };
    
    if (searchText.trim()) searchParams.search = searchText.trim();
    if (selectedRole) searchParams.role = selectedRole;
    if (selectedDepartment) searchParams.department = selectedDepartment;
    if (selectedStatus !== undefined) searchParams.is_active = selectedStatus;
    
    loadUsers(searchParams);
  };

  // Handle delete user
  const handleDeleteUser = async (userId: string, username: string) => {
    try {
      await userManagementService.deleteUser(userId);
      message.success(`用户 ${username} 删除成功`);
      loadUsers();
      loadStats();
    } catch (error: any) {
      message.error(error.message || '删除用户失败');
    }
  };

  // Handle create user
  const handleCreateUser = () => {
    setUserFormMode('create');
    setEditingUser(undefined);
    setUserFormVisible(true);
  };

  // Handle edit user
  const handleEditUser = (user: User) => {
    setUserFormMode('edit');
    setEditingUser(user);
    setUserFormVisible(true);
  };

  // Handle user form submit
  const handleUserFormSubmit = async (data: UserCreateRequest | UserUpdateRequest) => {
    setUserFormLoading(true);
    try {
      if (userFormMode === 'create') {
        await userManagementService.createUser(data as UserCreateRequest);
      } else if (editingUser) {
        await userManagementService.updateUser(editingUser.id, data as UserUpdateRequest);
      }
      setUserFormVisible(false);
      loadUsers();
      loadStats();
    } catch (error: any) {
      throw error; // Re-throw to let UserForm handle the error display
    } finally {
      setUserFormLoading(false);
    }
  };

  // Handle password reset
  const handlePasswordReset = (user: User) => {
    setResetPasswordUser(user);
    setPasswordResetVisible(true);
  };

  // Handle password reset submit
  const handlePasswordResetSubmit = async (userId: string, newPassword: string) => {
    setPasswordResetLoading(true);
    try {
      await userManagementService.resetUserPassword(userId, newPassword);
      setPasswordResetVisible(false);
    } catch (error: any) {
      throw error; // Re-throw to let PasswordResetModal handle the error display
    } finally {
      setPasswordResetLoading(false);
    }
  };

  // Handle permission management
  const handleManagePermissions = (user: User) => {
    setPermissionUser(user);
    setPermissionManagerVisible(true);
  };

  // Handle permission change
  const handlePermissionChange = () => {
    // Optionally reload user list to reflect permission changes
    loadUsers();
  };

  // Get role display info
  const getRoleInfo = (role: string) => {
    const roleMap: Record<string, { label: string; color: string }> = {
      'super_admin': { label: '超级管理员', color: 'red' },
      'admin': { label: '管理员', color: 'orange' },
      'user': { label: '普通用户', color: 'blue' },
      'viewer': { label: '只读用户', color: 'default' }
    };
    return roleMap[role] || { label: role, color: 'default' };
  };

  // Table columns
  const columns: ColumnsType<User> = [
    {
      title: '用户',
      key: 'user',
      width: isMobile ? 120 : 200,
      fixed: 'left' as const,
      render: (_, record) => (
        <Space size="small">
          <Avatar 
            size={isMobile ? 'small' : 'default'} 
            icon={<UserOutlined />}
            style={{ backgroundColor: '#1677ff' }}
          >
            {record.username.charAt(0).toUpperCase()}
          </Avatar>
          <div>
            <div style={{ 
              fontWeight: 500,
              fontSize: isMobile ? '12px' : '14px'
            }}>
              {record.username}
            </div>
            {!isMobile && (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {record.full_name || '未设置姓名'}
              </Text>
            )}
          </div>
        </Space>
      )
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      width: isMobile ? 120 : 200,
      ellipsis: true,
      responsive: ['md'],
      render: (email: string) => (
        <span style={{ fontSize: isMobile ? '12px' : '14px' }}>
          {email}
        </span>
      )
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      width: isMobile ? 80 : 120,
      render: (role: string) => {
        const roleInfo = getRoleInfo(role);
        return (
          <Tag 
            color={roleInfo.color}
            style={{ fontSize: isMobile ? '10px' : '12px' }}
          >
            {isMobile ? roleInfo.label.slice(0, 2) : roleInfo.label}
          </Tag>
        );
      }
    },
    {
      title: '部门',
      dataIndex: 'department',
      key: 'department',
      width: isMobile ? 60 : 120,
      responsive: ['lg'],
      render: (department: string) => (
        <span style={{ fontSize: isMobile ? '12px' : '14px' }}>
          {department || '-'}
        </span>
      )
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: isMobile ? 60 : 100,
      render: (isActive: boolean) => (
        <Tag 
          icon={isActive ? <CheckCircleOutlined /> : <StopOutlined />}
          color={isActive ? 'success' : 'default'}
          style={{ fontSize: isMobile ? '10px' : '12px' }}
        >
          {isMobile ? (isActive ? '激活' : '禁用') : (isActive ? '激活' : '禁用')}
        </Tag>
      )
    },
    {
      title: '登录次数',
      dataIndex: 'login_count',
      key: 'login_count',
      width: isMobile ? 60 : 100,
      responsive: ['sm'],
      render: (count: number) => (
        <span style={{ fontSize: isMobile ? '12px' : '14px' }}>
          {count.toLocaleString()}
        </span>
      )
    },
    {
      title: '最后登录',
      dataIndex: 'last_login',
      key: 'last_login',
      width: isMobile ? 80 : 150,
      responsive: ['md'],
      render: (lastLogin: string) => (
        <span style={{ fontSize: isMobile ? '11px' : '13px' }}>
          {lastLogin ? new Date(lastLogin).toLocaleDateString() : '从未'}
        </span>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: isMobile ? 100 : 180,
      fixed: 'right' as const,
      render: (_, record) => (
        <Space size="small" wrap>
          <Tooltip title="编辑用户">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEditUser(record)}
              style={{ fontSize: isMobile ? '12px' : '14px' }}
            />
          </Tooltip>
          {!isMobile && (
            <Tooltip title="权限管理">
              <Button
                type="text"
                size="small"
                icon={<SafetyOutlined />}
                onClick={() => handleManagePermissions(record)}
              />
            </Tooltip>
          )}
          <Tooltip title="重置密码">
            <Button
              type="text"
              size="small"
              icon={<KeyOutlined />}
              onClick={() => handlePasswordReset(record)}
              style={{ fontSize: isMobile ? '12px' : '14px' }}
            />
          </Tooltip>
          <Tooltip title="删除用户">
            <Popconfirm
              title="确认删除"
              description={`确定要删除用户 "${record.username}" 吗？此操作不可撤销。`}
              onConfirm={() => handleDeleteUser(record.id, record.username)}
              okText="确认"
              cancelText="取消"
              okType="danger"
            >
              <Button
                type="text"
                size="small"
                danger
                icon={<DeleteOutlined />}
                style={{ fontSize: isMobile ? '12px' : '14px' }}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      )
    }
  ];

  return (
    <div className="fade-in work-area-adaptive" style={{ 
      padding: isMobile ? '16px' : '24px',
      maxWidth: '100%',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <Row 
        justify="space-between" 
        align="middle" 
        style={{ marginBottom: isMobile ? '16px' : '24px' }}
        gutter={[16, 16]}
      >
        <Col xs={24} sm={16} md={18}>
          <div>
            <Title level={isMobile ? 3 : 2} style={{ margin: 0, color: '#262626' }}>
              <TeamOutlined style={{ marginRight: '12px' }} />
              用户管理
            </Title>
            <Text type="secondary" style={{ 
              fontSize: isMobile ? '12px' : '14px',
              display: 'block',
              marginTop: '4px'
            }}>
              管理系统用户账号、角色权限和访问控制
            </Text>
          </div>
        </Col>
        <Col xs={24} sm={8} md={6}>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            size={isMobile ? 'middle' : 'large'}
            className="modern-button"
            style={{ 
              height: isMobile ? '36px' : '40px',
              width: isMobile ? '100%' : 'auto'
            }}
            onClick={handleCreateUser}
          >
            创建用户
          </Button>
        </Col>
      </Row>

      {/* Statistics Cards */}
      {stats && (
        <Row gutter={isMobile ? [12, 12] : [24, 24]} style={{ marginBottom: isMobile ? '16px' : '24px' }}>
          <Col xs={12} sm={12} lg={6}>
            <Card className="modern-card stats-card-responsive" style={{ height: isMobile ? '100px' : '120px' }}>
              <Statistic
                title={
                  <Space size="small">
                    <UserOutlined style={{ color: '#1677ff', fontSize: isMobile ? '12px' : '14px' }} />
                    <span style={{ 
                      color: '#8c8c8c', 
                      fontWeight: 500,
                      fontSize: isMobile ? '11px' : '13px'
                    }}>
                      总用户数
                    </span>
                  </Space>
                }
                value={stats.total_users}
                valueStyle={{ 
                  color: '#1677ff', 
                  fontSize: isMobile ? '20px' : '28px', 
                  fontWeight: 600 
                }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={12} lg={6}>
            <Card className="modern-card stats-card-responsive" style={{ height: isMobile ? '100px' : '120px' }}>
              <Statistic
                title={
                  <Space size="small">
                    <CheckCircleOutlined style={{ color: '#52c41a', fontSize: isMobile ? '12px' : '14px' }} />
                    <span style={{ 
                      color: '#8c8c8c', 
                      fontWeight: 500,
                      fontSize: isMobile ? '11px' : '13px'
                    }}>
                      活跃用户
                    </span>
                  </Space>
                }
                value={stats.active_users}
                valueStyle={{ 
                  color: '#52c41a', 
                  fontSize: isMobile ? '20px' : '28px', 
                  fontWeight: 600 
                }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={12} lg={6}>
            <Card className="modern-card stats-card-responsive" style={{ height: isMobile ? '100px' : '120px' }}>
              <Statistic
                title={
                  <Space size="small">
                    <StopOutlined style={{ color: '#ff4d4f', fontSize: isMobile ? '12px' : '14px' }} />
                    <span style={{ 
                      color: '#8c8c8c', 
                      fontWeight: 500,
                      fontSize: isMobile ? '11px' : '13px'
                    }}>
                      禁用用户
                    </span>
                  </Space>
                }
                value={stats.inactive_users}
                valueStyle={{ 
                  color: '#ff4d4f', 
                  fontSize: isMobile ? '20px' : '28px', 
                  fontWeight: 600 
                }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={12} lg={6}>
            <Card className="modern-card stats-card-responsive" style={{ height: isMobile ? '100px' : '120px' }}>
              <Statistic
                title={
                  <Space size="small">
                    <UserAddOutlined style={{ color: '#722ed1', fontSize: isMobile ? '12px' : '14px' }} />
                    <span style={{ 
                      color: '#8c8c8c', 
                      fontWeight: 500,
                      fontSize: isMobile ? '11px' : '13px'
                    }}>
                      近期登录
                    </span>
                  </Space>
                }
                value={stats.recent_logins}
                valueStyle={{ 
                  color: '#722ed1', 
                  fontSize: isMobile ? '20px' : '28px', 
                  fontWeight: 600 
                }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Search and Filter */}
      <Card className="modern-card responsive-card" style={{ marginBottom: isMobile ? '16px' : '24px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Input
              placeholder="搜索用户名、邮箱或姓名"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onPressEnter={handleSearch}
              size={isMobile ? 'middle' : 'large'}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              placeholder="选择角色"
              value={selectedRole}
              onChange={setSelectedRole}
              allowClear
              style={{ width: '100%' }}
              size={isMobile ? 'middle' : 'large'}
            >
              <Option value="super_admin">超级管理员</Option>
              <Option value="admin">管理员</Option>
              <Option value="user">普通用户</Option>
              <Option value="viewer">只读用户</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Input
              placeholder="部门"
              value={selectedDepartment}
              onChange={(e) => setSelectedDepartment(e.target.value)}
              size={isMobile ? 'middle' : 'large'}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              placeholder="状态"
              value={selectedStatus}
              onChange={setSelectedStatus}
              allowClear
              style={{ width: '100%' }}
              size={isMobile ? 'middle' : 'large'}
            >
              <Option value={true}>激活</Option>
              <Option value={false}>禁用</Option>
            </Select>
          </Col>
          <Col xs={24} md={6}>
            <Space 
              direction={isMobile ? 'vertical' : 'horizontal'}
              style={{ width: isMobile ? '100%' : 'auto' }}
            >
              <Button 
                type="primary" 
                icon={<SearchOutlined />} 
                onClick={handleSearch}
                size={isMobile ? 'middle' : 'large'}
                className="modern-button"
                style={{ width: isMobile ? '100%' : 'auto' }}
              >
                搜索
              </Button>
              <Button 
                onClick={handleReset}
                size={isMobile ? 'middle' : 'large'}
                style={{ width: isMobile ? '100%' : 'auto' }}
              >
                重置
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* User Table */}
      <Card className="modern-card responsive-card">
        <div className="responsive-table">
          <Table
            columns={columns}
            dataSource={users}
            rowKey="id"
            loading={loading}
            pagination={{
              ...pagination,
              onChange: handleTableChange,
              onShowSizeChange: handleTableChange,
              showSizeChanger: !isMobile,
              showQuickJumper: !isMobile,
              pageSize: isMobile ? 10 : pagination.pageSize,
              responsive: true,
            }}
            scroll={{ x: 800 }}
            size={isMobile ? 'small' : 'middle'}
          />
        </div>
      </Card>

      {/* User Form Modal */}
      <UserForm
        visible={userFormVisible}
        mode={userFormMode}
        user={editingUser}
        loading={userFormLoading}
        onSubmit={handleUserFormSubmit}
        onCancel={() => setUserFormVisible(false)}
      />

      {/* Password Reset Modal */}
      <PasswordResetModal
        visible={passwordResetVisible}
        user={resetPasswordUser}
        loading={passwordResetLoading}
        onSubmit={handlePasswordResetSubmit}
        onCancel={() => setPasswordResetVisible(false)}
      />

      {/* Permission Manager Modal */}
      <PermissionManager
        visible={permissionManagerVisible}
        user={permissionUser}
        onCancel={() => setPermissionManagerVisible(false)}
        onPermissionChange={handlePermissionChange}
      />
    </div>
  );
};

export default UserManagement;