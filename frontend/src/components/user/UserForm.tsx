import React, { useEffect } from 'react';
import {
  Form,
  Input,
  Select,
  Switch,
  Button,
  Space,
  message,
  Row,
  Col
} from 'antd';
import {
  UserOutlined,
  MailOutlined,
  LockOutlined,
  TeamOutlined,
  IdcardOutlined
} from '@ant-design/icons';
import { User, UserCreateRequest, UserUpdateRequest } from '../../services/userManagementService';
import ModalContainer from '../common/ModalContainer';

const { Option } = Select;

interface UserFormProps {
  visible: boolean;
  mode: 'create' | 'edit';
  user?: User;
  loading?: boolean;
  onSubmit: (data: UserCreateRequest | UserUpdateRequest) => Promise<void>;
  onCancel: () => void;
}

const UserForm: React.FC<UserFormProps> = ({
  visible,
  mode,
  user,
  loading = false,
  onSubmit,
  onCancel
}) => {
  const [form] = Form.useForm();

  // Reset form when modal opens/closes or user changes
  useEffect(() => {
    if (visible) {
      if (mode === 'edit' && user) {
        form.setFieldsValue({
          username: user.username,
          email: user.email,
          full_name: user.full_name || '',
          role: user.role,
          department: user.department || '',
          is_active: user.is_active
        });
      } else {
        form.resetFields();
        // Set default values for create mode
        form.setFieldsValue({
          role: 'user',
          is_active: true
        });
      }
    }
  }, [visible, mode, user, form]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (mode === 'create') {
        const createData: UserCreateRequest = {
          username: values.username,
          email: values.email,
          password: values.password,
          full_name: values.full_name || undefined,
          role: values.role,
          department: values.department || undefined,
          is_active: values.is_active
        };
        await onSubmit(createData);
      } else {
        const updateData: UserUpdateRequest = {
          email: values.email,
          full_name: values.full_name || undefined,
          role: values.role,
          department: values.department || undefined,
          is_active: values.is_active
        };
        await onSubmit(updateData);
      }
      
      form.resetFields();
      message.success(mode === 'create' ? '用户创建成功' : '用户更新成功');
    } catch (error: any) {
      console.error('Form submission error:', error);
      message.error(error.message || `用户${mode === 'create' ? '创建' : '更新'}失败`);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  const validatePassword = (_: any, value: string) => {
    if (mode === 'create' && (!value || value.length < 8)) {
      return Promise.reject(new Error('密码长度至少8位'));
    }
    if (value && value.length > 0 && value.length < 8) {
      return Promise.reject(new Error('密码长度至少8位'));
    }
    return Promise.resolve();
  };

  const validateConfirmPassword = (_: any, value: string) => {
    const password = form.getFieldValue('password');
    if (mode === 'create' && value !== password) {
      return Promise.reject(new Error('两次输入的密码不一致'));
    }
    return Promise.resolve();
  };

  return (
    <ModalContainer
      visible={visible}
      onClose={handleCancel}
      title={
        <Space>
          <UserOutlined />
          {mode === 'create' ? '创建用户' : '编辑用户'}
        </Space>
      }
      width={600}
      footer={[
        <Button key="cancel" onClick={handleCancel}>
          取消
        </Button>,
        <Button
          key="submit"
          type="primary"
          loading={loading}
          onClick={handleSubmit}
        >
          {mode === 'create' ? '创建' : '更新'}
        </Button>
      ]}
    >
      <Form
        form={form}
        layout="vertical"
        requiredMark={false}
        style={{ marginTop: '20px' }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="username"
              label="用户名"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少3个字符' },
                { max: 50, message: '用户名最多50个字符' },
                { pattern: /^[a-zA-Z0-9_-]+$/, message: '用户名只能包含字母、数字、下划线和连字符' }
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="请输入用户名"
                disabled={mode === 'edit'} // 编辑模式下用户名不可修改
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="email"
              label="邮箱地址"
              rules={[
                { required: true, message: '请输入邮箱地址' },
                { type: 'email', message: '请输入有效的邮箱地址' }
              ]}
            >
              <Input
                prefix={<MailOutlined />}
                placeholder="请输入邮箱地址"
              />
            </Form.Item>
          </Col>
        </Row>

        {mode === 'create' && (
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="password"
                label="密码"
                rules={[
                  { required: true, message: '请输入密码' },
                  { validator: validatePassword }
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="请输入密码（至少8位）"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="confirmPassword"
                label="确认密码"
                dependencies={['password']}
                rules={[
                  { required: true, message: '请确认密码' },
                  { validator: validateConfirmPassword }
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="请再次输入密码"
                />
              </Form.Item>
            </Col>
          </Row>
        )}

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="full_name"
              label="姓名"
            >
              <Input
                prefix={<IdcardOutlined />}
                placeholder="请输入姓名（可选）"
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="department"
              label="部门"
            >
              <Input
                prefix={<TeamOutlined />}
                placeholder="请输入部门（可选）"
              />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="role"
              label="用户角色"
              rules={[{ required: true, message: '请选择用户角色' }]}
            >
              <Select placeholder="请选择用户角色">
                <Option value="viewer">只读用户</Option>
                <Option value="user">普通用户</Option>
                <Option value="admin">管理员</Option>
                <Option value="super_admin">超级管理员</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="is_active"
              label="账号状态"
              valuePropName="checked"
            >
              <Switch
                checkedChildren="激活"
                unCheckedChildren="禁用"
              />
            </Form.Item>
          </Col>
        </Row>
      </Form>
    </ModalContainer>
  );
};

export default UserForm;