import React from 'react';
import {
  Form,
  Input,
  Button,
  Space,
  message,
  Typography,
  Alert
} from 'antd';
import {
  KeyOutlined,
  LockOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { User } from '../../services/userManagementService';
import ModalContainer from '../common/ModalContainer';

const { Text } = Typography;

interface PasswordResetModalProps {
  visible: boolean;
  user?: User;
  loading?: boolean;
  onSubmit: (userId: string, newPassword: string) => Promise<void>;
  onCancel: () => void;
}

const PasswordResetModal: React.FC<PasswordResetModalProps> = ({
  visible,
  user,
  loading = false,
  onSubmit,
  onCancel
}) => {
  const [form] = Form.useForm();

  const handleSubmit = async () => {
    if (!user) return;
    
    try {
      const values = await form.validateFields();
      await onSubmit(user.id, values.newPassword);
      form.resetFields();
      message.success('密码重置成功');
    } catch (error: any) {
      console.error('Password reset error:', error);
      message.error(error.message || '密码重置失败');
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  const validatePassword = (_: any, value: string) => {
    if (!value || value.length < 8) {
      return Promise.reject(new Error('密码长度至少8位'));
    }
    return Promise.resolve();
  };

  const validateConfirmPassword = (_: any, value: string) => {
    const newPassword = form.getFieldValue('newPassword');
    if (value !== newPassword) {
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
          <KeyOutlined />
          重置用户密码
        </Space>
      }
      width={500}
      footer={[
        <Button key="cancel" onClick={handleCancel}>
          取消
        </Button>,
        <Button
          key="submit"
          type="primary"
          danger
          loading={loading}
          onClick={handleSubmit}
        >
          重置密码
        </Button>
      ]}
    >
      {user && (
        <>
          <Alert
            message="重置密码操作"
            description={
              <div>
                <p>您正在为用户 <Text strong>{user.username}</Text> 重置密码。</p>
                <p>重置后，用户需要使用新密码登录系统。</p>
              </div>
            }
            type="warning"
            icon={<ExclamationCircleOutlined />}
            showIcon
            style={{ marginBottom: '20px' }}
          />

          <Form
            form={form}
            layout="vertical"
            requiredMark={false}
          >
            <Form.Item
              name="newPassword"
              label="新密码"
              rules={[
                { required: true, message: '请输入新密码' },
                { validator: validatePassword }
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="请输入新密码（至少8位）"
              />
            </Form.Item>

            <Form.Item
              name="confirmPassword"
              label="确认新密码"
              dependencies={['newPassword']}
              rules={[
                { required: true, message: '请确认新密码' },
                { validator: validateConfirmPassword }
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="请再次输入新密码"
              />
            </Form.Item>
          </Form>
        </>
      )}
    </ModalContainer>
  );
};

export default PasswordResetModal;