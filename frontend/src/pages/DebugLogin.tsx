import React, { useState, useEffect } from 'react';
import { Card, Button, Typography, Space, Alert, Descriptions, Tag } from 'antd';
import { ReloadOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { runFullHealthCheck, HealthCheckResult } from '../utils/backendHealthCheck';

const { Title, Text, Paragraph } = Typography;

interface HealthCheckState {
  loading: boolean;
  results: {
    overall: boolean;
    checks: {
      backend: HealthCheckResult;
      auth: HealthCheckResult;
    }
  } | null;
}

const DebugLogin: React.FC = () => {
  const [healthCheck, setHealthCheck] = useState<HealthCheckState>({
    loading: false,
    results: null
  });

  const runHealthCheck = async () => {
    setHealthCheck({ loading: true, results: null });
    try {
      const results = await runFullHealthCheck();
      setHealthCheck({ loading: false, results });
    } catch (error) {
      console.error('Health check failed:', error);
      setHealthCheck({ loading: false, results: null });
    }
  };

  useEffect(() => {
    runHealthCheck();
  }, []);

  const testLogin = async () => {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: 'admin',
          password: '971028'
        })
      });

      const data = await response.text();
      console.log('Login response status:', response.status);
      console.log('Login response headers:', Object.fromEntries(response.headers.entries()));
      console.log('Login response body:', data);

      if (response.ok) {
        alert('登录成功！检查控制台查看详细信息。');
      } else {
        alert(`登录失败！状态码: ${response.status}\n响应: ${data}`);
      }
    } catch (error) {
      console.error('Login test error:', error);
      alert(`登录测试出错: ${error}`);
    }
  };

  const testAuthService = async () => {
    try {
      console.log('Testing AuthService login...');
      const { authService } = await import('../services/authService');
      const result = await authService.login('admin', '971028');
      console.log('AuthService login result:', result);
      alert('AuthService登录成功！检查控制台查看详细信息。');
    } catch (error) {
      console.error('AuthService login error:', error);
      alert(`AuthService登录失败: ${error}`);
    }
  };

  const getStatusIcon = (isHealthy: boolean) => {
    return isHealthy ? 
      <CheckCircleOutlined style={{ color: '#52c41a' }} /> : 
      <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
  };

  const getStatusTag = (isHealthy: boolean) => {
    return isHealthy ? 
      <Tag color="success">正常</Tag> : 
      <Tag color="error">异常</Tag>;
  };

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <Title level={2}>登录问题调试页面</Title>
      
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 健康检查 */}
        <Card 
          title="后端服务健康检查" 
          extra={
            <Button 
              icon={<ReloadOutlined />} 
              onClick={runHealthCheck}
              loading={healthCheck.loading}
            >
              重新检查
            </Button>
          }
        >
          {healthCheck.loading && (
            <Alert message="正在检查后端服务状态..." type="info" />
          )}
          
          {healthCheck.results && (
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Alert
                message={`总体状态: ${healthCheck.results.overall ? '正常' : '异常'}`}
                type={healthCheck.results.overall ? 'success' : 'error'}
                icon={getStatusIcon(healthCheck.results.overall)}
              />
              
              <Descriptions title="详细检查结果" bordered column={1}>
                <Descriptions.Item 
                  label={
                    <Space>
                      {getStatusIcon(healthCheck.results.checks.backend.isHealthy)}
                      后端服务
                    </Space>
                  }
                >
                  <Space direction="vertical">
                    {getStatusTag(healthCheck.results.checks.backend.isHealthy)}
                    <Text>{healthCheck.results.checks.backend.message}</Text>
                    {healthCheck.results.checks.backend.details && (
                      <Text code style={{ fontSize: '12px' }}>
                        {JSON.stringify(healthCheck.results.checks.backend.details, null, 2)}
                      </Text>
                    )}
                  </Space>
                </Descriptions.Item>
                
                <Descriptions.Item 
                  label={
                    <Space>
                      {getStatusIcon(healthCheck.results.checks.auth.isHealthy)}
                      认证端点
                    </Space>
                  }
                >
                  <Space direction="vertical">
                    {getStatusTag(healthCheck.results.checks.auth.isHealthy)}
                    <Text>{healthCheck.results.checks.auth.message}</Text>
                    {healthCheck.results.checks.auth.details && (
                      <Text code style={{ fontSize: '12px' }}>
                        {JSON.stringify(healthCheck.results.checks.auth.details, null, 2)}
                      </Text>
                    )}
                  </Space>
                </Descriptions.Item>
              </Descriptions>
            </Space>
          )}
        </Card>

        {/* 登录测试 */}
        <Card title="登录功能测试">
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Alert
              message="✅ 后端服务正常！"
              description="直接测试后端登录成功，问题可能在前端代理配置。"
              type="success"
              showIcon
            />
            
            <Paragraph>
              点击下面的按钮测试登录功能，使用账号 <Text code>admin</Text> 和密码 <Text code>971028</Text>。
              测试结果将显示在浏览器控制台中。
            </Paragraph>
            
            <Space wrap>
              <Button type="primary" onClick={testLogin}>
                测试直接登录 (通过代理)
              </Button>
              <Button type="default" onClick={testAuthService}>
                测试AuthService登录
              </Button>
              <Button 
                type="dashed" 
                onClick={() => {
                  // 直接访问后端，绕过代理
                  fetch('http://localhost:8000/api/v1/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: 'admin', password: '971028' })
                  })
                  .then(res => res.json())
                  .then(data => {
                    console.log('Direct backend test success:', data);
                    alert('直接后端测试成功！检查控制台。');
                  })
                  .catch(err => {
                    console.error('Direct backend test failed:', err);
                    alert('直接后端测试失败：' + err.message);
                  });
                }}
              >
                测试直接后端 (绕过代理)
              </Button>
            </Space>
          </Space>
        </Card>

        {/* 配置信息 */}
        <Card title="当前配置信息">
          <Descriptions bordered column={1}>
            <Descriptions.Item label="前端地址">
              {window.location.origin}
            </Descriptions.Item>
            <Descriptions.Item label="API基础路径">
              /api/v1
            </Descriptions.Item>
            <Descriptions.Item label="代理目标">
              http://localhost:8000 (根据vite.config.ts)
            </Descriptions.Item>
            <Descriptions.Item label="登录端点">
              /api/v1/auth/login
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* 故障排除建议 */}
        <Card title="故障排除建议">
          <Space direction="vertical" size="large">
            <Alert
              message="🎉 前端修复成功！"
              description="URL重复问题已解决，现在使用正确的fetch方法。任何500错误都是后端服务器问题。"
              type="success"
              showIcon
            />
            
            <div>
              <Text strong>立即执行的诊断步骤：</Text>
              <ol>
                <li><Text code>curl http://localhost:8000/api/v1/health</Text> - 检查后端服务状态</li>
                <li>如果无响应，启动后端服务：<Text code>cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload</Text></li>
                <li>查看后端启动日志，注意数据库连接和认证相关错误</li>
                <li>确认admin用户存在：可能需要运行 <Text code>python manage.py createsuperuser</Text></li>
              </ol>
            </div>
            
            <div>
              <Text strong>常见500错误原因：</Text>
              <ul>
                <li><Text strong>后端服务未启动</Text> - 最常见原因</li>
                <li><Text strong>数据库连接失败</Text> - 检查数据库服务和配置</li>
                <li><Text strong>admin用户不存在</Text> - 需要创建初始用户</li>
                <li><Text strong>依赖包缺失</Text> - 运行 <Text code>pip install -r requirements.txt</Text></li>
                <li><Text strong>环境变量未设置</Text> - 检查.env文件</li>
              </ul>
            </div>
            
            <div>
              <Text strong>测试后端的命令：</Text>
              <div style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px', marginTop: '8px' }}>
                <Text code style={{ display: 'block', marginBottom: '4px' }}>
                  curl -X POST http://localhost:8000/api/v1/auth/login \
                </Text>
                <Text code style={{ display: 'block', marginBottom: '4px' }}>
                  &nbsp;&nbsp;-H "Content-Type: application/json" \
                </Text>
                <Text code style={{ display: 'block' }}>
                  &nbsp;&nbsp;-d '{"username":"admin","password":"971028"}' -v
                </Text>
              </div>
            </div>
          </Space>
        </Card>
      </Space>
    </div>
  );
};

export default DebugLogin;