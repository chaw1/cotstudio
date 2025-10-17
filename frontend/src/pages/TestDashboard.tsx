import React, { useState } from 'react';
import { Card, Button, Space, Typography, Alert, Divider } from 'antd';
import { 
  BugOutlined, 
  CheckCircleOutlined, 
  ExclamationCircleOutlined,
  ReloadOutlined 
} from '@ant-design/icons';
import { useResponsiveBreakpoint } from '../hooks/useResponsiveBreakpoint';
import { apiTester, testAllApis } from '../utils/apiTest';
import SystemResourceMonitor from '../components/dashboard/SystemResourceMonitor';
import UserContributionGraph from '../components/dashboard/UserContributionGraph';
import { ResponsiveContainer, ResponsiveGrid, ResponsiveText } from '../components/common/ResponsiveContainer';

const { Title, Text } = Typography;

interface TestResult {
  endpoint: string;
  success: boolean;
  status?: number;
  error?: string;
  responseTime?: number;
}

/**
 * 测试页面 - 用于验证仪表板错误修复
 */
const TestDashboard: React.FC = () => {
  const { isMobile, breakpoint, screenWidth, screenHeight } = useResponsiveBreakpoint();
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [testing, setTesting] = useState(false);

  const runTests = async () => {
    setTesting(true);
    try {
      const results = await testAllApis();
      setTestResults(results);
    } catch (error) {
      console.error('Test execution failed:', error);
    } finally {
      setTesting(false);
    }
  };

  const successCount = testResults.filter(r => r.success).length;
  const totalCount = testResults.length;
  const successRate = totalCount > 0 ? (successCount / totalCount) * 100 : 0;

  return (
    <ResponsiveContainer>
      <div style={{ padding: isMobile ? '16px' : '24px' }}>
        {/* 页面标题 */}
        <div style={{ marginBottom: isMobile ? '16px' : '24px' }}>
          <Title level={isMobile ? 3 : 2} style={{ margin: 0, color: '#262626' }}>
            <BugOutlined style={{ marginRight: '8px', color: '#1677ff' }} />
            仪表板错误修复测试
          </Title>
          <Text type="secondary" style={{ 
            fontSize: isMobile ? '12px' : '14px',
            display: 'block',
            marginTop: '4px'
          }}>
            验证前端仪表板错误修复的完整性和功能性
          </Text>
        </div>

        {/* 响应式信息卡片 */}
        <Card 
          title="响应式信息" 
          className="modern-card"
          style={{ marginBottom: isMobile ? '16px' : '24px' }}
          size="small"
        >
          <ResponsiveGrid gap={16} minItemWidth={200}>
            <div>
              <Text strong>当前断点:</Text>
              <div style={{ fontSize: '18px', color: '#1677ff', fontWeight: 'bold' }}>
                {breakpoint.toUpperCase()}
              </div>
            </div>
            <div>
              <Text strong>屏幕尺寸:</Text>
              <div style={{ fontSize: '14px', color: '#52c41a' }}>
                {screenWidth} × {screenHeight}
              </div>
            </div>
            <div>
              <Text strong>设备类型:</Text>
              <div style={{ fontSize: '14px', color: '#722ed1' }}>
                {isMobile ? '移动设备' : '桌面设备'}
              </div>
            </div>
          </ResponsiveGrid>
        </Card>

        {/* API测试区域 */}
        <Card 
          title="API端点测试" 
          className="modern-card"
          style={{ marginBottom: isMobile ? '16px' : '24px' }}
          extra={
            <Button 
              type="primary" 
              icon={<ReloadOutlined spin={testing} />}
              onClick={runTests}
              loading={testing}
              size={isMobile ? 'small' : 'middle'}
            >
              运行测试
            </Button>
          }
        >
          {testResults.length > 0 && (
            <>
              <div style={{ marginBottom: '16px' }}>
                <Alert
                  message={`测试完成: ${successCount}/${totalCount} 通过 (${successRate.toFixed(1)}%)`}
                  type={successRate === 100 ? 'success' : successRate >= 50 ? 'warning' : 'error'}
                  showIcon
                />
              </div>
              
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {testResults.map((result, index) => (
                  <div 
                    key={index}
                    style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      padding: '8px 0',
                      borderBottom: index < testResults.length - 1 ? '1px solid #f0f0f0' : 'none'
                    }}
                  >
                    <Space>
                      {result.success ? (
                        <CheckCircleOutlined style={{ color: '#52c41a' }} />
                      ) : (
                        <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
                      )}
                      <Text style={{ fontSize: isMobile ? '12px' : '14px' }}>
                        {result.endpoint}
                      </Text>
                    </Space>
                    <Space>
                      {result.responseTime && (
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {result.responseTime}ms
                        </Text>
                      )}
                      {!result.success && result.error && (
                        <Text type="danger" style={{ fontSize: '12px' }}>
                          {result.error}
                        </Text>
                      )}
                    </Space>
                  </div>
                ))}
              </div>
            </>
          )}
          
          {testResults.length === 0 && (
            <div style={{ 
              textAlign: 'center', 
              padding: '40px 0',
              color: '#8c8c8c'
            }}>
              <BugOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
              <div>点击"运行测试"按钮开始API端点测试</div>
            </div>
          )}
        </Card>

        {/* 组件测试区域 */}
        <ResponsiveGrid gap={isMobile ? 16 : 24} minItemWidth={400}>
          {/* 系统监控组件测试 */}
          <Card 
            title="系统监控组件" 
            className="modern-card"
            size="small"
          >
            <SystemResourceMonitor />
          </Card>

          {/* 用户贡献组件测试 */}
          <Card 
            title="用户贡献组件" 
            className="modern-card"
            size="small"
          >
            <UserContributionGraph />
          </Card>
        </ResponsiveGrid>

        {/* 修复说明 */}
        <Card 
          title="修复内容说明" 
          className="modern-card"
          style={{ marginTop: isMobile ? '16px' : '24px' }}
        >
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <div>
              <ResponsiveText variant="title">已修复的问题:</ResponsiveText>
              <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
                <li>✅ 认证Token自动刷新机制</li>
                <li>✅ API请求错误处理和重试逻辑</li>
                <li>✅ 系统监控组件的数据获取和显示</li>
                <li>✅ 用户贡献图表的数据转换和可视化</li>
                <li>✅ 响应式设计和移动端适配</li>
                <li>✅ 页面可见性检测和智能刷新</li>
                <li>✅ 内存泄漏防护和组件清理</li>
                <li>✅ 友好的错误提示和用户体验</li>
              </ul>
            </div>
            
            <Divider />
            
            <div>
              <ResponsiveText variant="title">技术改进:</ResponsiveText>
              <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
                <li>🔧 增强的AuthService类，支持token过期检测</li>
                <li>🔧 新的ApiClient工具类，统一API调用</li>
                <li>🔧 完善的错误分类和处理机制</li>
                <li>🔧 响应式设计工具和组件</li>
                <li>🔧 API端点测试和验证工具</li>
                <li>🔧 性能优化和内存管理</li>
              </ul>
            </div>
          </Space>
        </Card>
      </div>
    </ResponsiveContainer>
  );
};

export default TestDashboard;