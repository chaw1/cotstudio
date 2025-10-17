import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, App } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { authService } from '../../services/authService';

const { Title } = Typography;

interface LoginForm {
  username: string;
  password: string;
}

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { message } = App.useApp();

  const onFinish = async (values: LoginForm) => {
    setLoading(true);
    console.log('🔥 LOGIN COMPONENT: Starting login process');
    console.log('🔥 LOGIN COMPONENT: AuthService instance:', authService);
    try {
      console.log('🔥 LOGIN COMPONENT: Calling authService.login');
      const result = await authService.login(values.username, values.password);
      console.log('🔥 LOGIN COMPONENT: Login result:', result);
      
      // 登录成功后获取用户信息并存储角色
      try {
        const userInfo = await authService.getCurrentUser();
        
        // 存储用户角色信息
        localStorage.setItem('userRole', userInfo.roles[0] || 'user');
        localStorage.setItem('userPermissions', JSON.stringify(userInfo.roles || []));
        localStorage.setItem('userId', userInfo.user_id);
        localStorage.setItem('username', userInfo.username);
        
        console.log('用户信息:', userInfo);
        console.log('用户角色:', userInfo.roles);
      } catch (userError) {
        console.error('获取用户信息失败:', userError);
        // 即使获取用户信息失败，也不阻止登录流程
      }
      
      message.success('登录成功');
      navigate('/dashboard');
    } catch (error: any) {
      console.error('Login error:', error);
      message.error(error.message || '登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    }}>
      <Card
        style={{
          width: 400,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={2} style={{ color: '#1677ff', marginBottom: 8 }}>
            COT Studio
          </Title>
          <Typography.Text type="secondary">
            请登录您的账户
          </Typography.Text>
        </div>

        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名!' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码!' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            默认账户: admin / 971028
          </Typography.Text>
        </div>
      </Card>
    </div>
  );
};

export default Login;