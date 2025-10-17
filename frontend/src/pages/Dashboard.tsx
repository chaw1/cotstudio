import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Typography, Space, Button } from 'antd';
import { 
  ProjectOutlined, 
  FileTextOutlined, 
  BranchesOutlined,
  PlusOutlined,
  ClockCircleOutlined,
  ArrowUpOutlined,
  TeamOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useResponsiveBreakpoint } from '../hooks/useResponsiveBreakpoint';
import { apiClient } from '../utils/apiClient';
import SystemResourceMonitor from '../components/dashboard/SystemResourceMonitor';
import UserContributionGraph from '../components/dashboard/UserContributionGraph';
import safeMessage from '../utils/message';
import './Dashboard.css';

const { Title, Text } = Typography;

interface DashboardStats {
  totals: {
    users: number;
    projects: number;
    files: number;
    cot_items: number;
  };
  recent_activity: {
    projects_30d: number;
    cot_items_30d: number;
  };
  top_contributors: Array<{
    username: string;
    project_count: number;
    cot_count: number;
  }>;
  project_status_distribution: Array<{
    status: string;
    count: number;
  }>;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { isMobile } = useResponsiveBreakpoint();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  const handleCreateProject = () => {
    try {
      // Navigate to projects page with create parameter
      navigate('/projects?create=true');
      safeMessage.success('正在跳转到项目创建页面...');
    } catch (error) {
      console.error('Navigation error:', error);
      safeMessage.error('跳转失败，请重试');
    }
  };

  const fetchDashboardStats = async () => {
    try {
      const result = await apiClient.get<{
        success: boolean;
        data: DashboardStats;
      }>('/analytics/dashboard-stats');
      
      if (result.success) {
        setStats(result.data);
      }
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  // 响应式样式计算
  const headerMargin = isMobile ? '16px' : '24px';
  const titleLevel = isMobile ? 3 : 2;
  const buttonSize = isMobile ? 'middle' : 'large';
  const cardHeight = isMobile ? '120px' : '140px';
  const cardPadding = isMobile ? '16px' : '24px';
  const statisticFontSize = isMobile ? '24px' : '32px';

  return (
    <div className="fade-in work-area-adaptive" style={{ 
      background: 'transparent',
      minHeight: '100%'
    }}>
      {/* Header with Create Project Button */}
      <div style={{ 
        marginBottom: headerMargin, 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: isMobile ? 'flex-start' : 'center',
        flexDirection: isMobile ? 'column' : 'row',
        gap: isMobile ? '12px' : '0'
      }}>
        <div style={{ flex: 1 }}>
          <Title level={titleLevel} style={{ margin: 0, color: '#262626' }}>
            仪表板
          </Title>
          <Text type="secondary" style={{ 
            fontSize: isMobile ? '12px' : '14px',
            display: 'block',
            marginTop: '4px'
          }}>
            欢迎使用 COT Studio，开始构建您的 Chain-of-Thought 数据集
          </Text>
        </div>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          size={buttonSize}
          className="modern-button"
          onClick={handleCreateProject}
          style={{ 
            height: isMobile ? '36px' : '40px',
            width: isMobile ? '100%' : 'auto'
          }}
        >
          创建新项目
        </Button>
      </div>

      {/* First Row: Basic Statistics Cards */}
      <Row gutter={isMobile ? [16, 16] : [24, 24]}>
        <Col xs={24} sm={12} lg={6}>
          <Card 
            className="modern-card stats-card-responsive"
            style={{ height: cardHeight }}
          >
            <Statistic
              title={
                <Space size={isMobile ? 'small' : 'middle'}>
                  <TeamOutlined style={{ 
                    color: '#722ed1',
                    fontSize: isMobile ? '14px' : '16px'
                  }} />
                  <span style={{ 
                    color: '#8c8c8c', 
                    fontWeight: 500,
                    fontSize: isMobile ? '12px' : '14px'
                  }}>
                    用户总数
                  </span>
                </Space>
              }
              value={stats?.totals.users || 0}
              valueStyle={{ 
                color: '#722ed1', 
                fontSize: statisticFontSize, 
                fontWeight: 600,
                lineHeight: 1.2
              }}
              loading={loading}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card 
            className="modern-card stats-card-responsive"
            style={{ height: cardHeight }}
          >
            <Statistic
              title={
                <Space size={isMobile ? 'small' : 'middle'}>
                  <ProjectOutlined style={{ 
                    color: '#1677ff',
                    fontSize: isMobile ? '14px' : '16px'
                  }} />
                  <span style={{ 
                    color: '#8c8c8c', 
                    fontWeight: 500,
                    fontSize: isMobile ? '12px' : '14px'
                  }}>
                    项目总数
                  </span>
                </Space>
              }
              value={stats?.totals.projects || 0}
              valueStyle={{ 
                color: '#1677ff', 
                fontSize: statisticFontSize, 
                fontWeight: 600,
                lineHeight: 1.2
              }}
              suffix={
                stats?.recent_activity.projects_30d ? (
                  <div style={{ 
                    fontSize: isMobile ? '10px' : '12px', 
                    color: '#52c41a', 
                    marginTop: '4px' 
                  }}>
                    <ArrowUpOutlined /> +{stats.recent_activity.projects_30d} (30天)
                  </div>
                ) : undefined
              }
              loading={loading}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card 
            className="modern-card stats-card-responsive"
            style={{ height: cardHeight }}
          >
            <Statistic
              title={
                <Space size={isMobile ? 'small' : 'middle'}>
                  <FileTextOutlined style={{ 
                    color: '#52c41a',
                    fontSize: isMobile ? '14px' : '16px'
                  }} />
                  <span style={{ 
                    color: '#8c8c8c', 
                    fontWeight: 500,
                    fontSize: isMobile ? '12px' : '14px'
                  }}>
                    CoT数据条数
                  </span>
                </Space>
              }
              value={stats?.totals.cot_items || 0}
              valueStyle={{ 
                color: '#52c41a', 
                fontSize: statisticFontSize, 
                fontWeight: 600,
                lineHeight: 1.2
              }}
              suffix={
                stats?.recent_activity.cot_items_30d ? (
                  <div style={{ 
                    fontSize: isMobile ? '10px' : '12px', 
                    color: '#52c41a', 
                    marginTop: '4px' 
                  }}>
                    <ArrowUpOutlined /> +{stats.recent_activity.cot_items_30d} (30天)
                  </div>
                ) : undefined
              }
              loading={loading}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card 
            className="modern-card stats-card-responsive"
            style={{ height: cardHeight }}
          >
            <Statistic
              title={
                <Space size={isMobile ? 'small' : 'middle'}>
                  <BranchesOutlined style={{ 
                    color: '#fa8c16',
                    fontSize: isMobile ? '14px' : '16px'
                  }} />
                  <span style={{ 
                    color: '#8c8c8c', 
                    fontWeight: 500,
                    fontSize: isMobile ? '12px' : '14px'
                  }}>
                    文件总数
                  </span>
                </Space>
              }
              value={stats?.totals.files || 0}
              valueStyle={{ 
                color: '#fa8c16', 
                fontSize: statisticFontSize, 
                fontWeight: 600,
                lineHeight: 1.2
              }}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      {/* Second Row: System Status and User Contributions */}
      <Row 
        gutter={isMobile ? [16, 16] : [24, 24]} 
        style={{ marginTop: headerMargin }}
        className="dashboard-equal-height-row"
      >
        <Col xs={24} lg={12}>
          <Card 
            title="系统状态"
            className="modern-card responsive-card"
            style={{ 
              height: isMobile ? 'auto' : '650px', // 从500px增加到650px
              display: 'flex',
              flexDirection: 'column'
            }}
            styles={{ 
              body: {
                flex: 1,
                padding: isMobile ? '16px' : '24px',
                overflow: 'hidden'
              }
            }}
          >
            <div className="system-monitor-container">
              <SystemResourceMonitor />
            </div>
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card 
            title="用户贡献"
            className="modern-card responsive-card"
            style={{ 
              height: isMobile ? 'auto' : '650px', // 从500px增加到650px
              display: 'flex',
              flexDirection: 'column'
            }}
            styles={{ 
              body: {
                flex: 1,
                padding: isMobile ? '16px' : '24px',
                overflow: 'hidden'
              }
            }}
          >
            <div className="contribution-graph-container">
              <UserContributionGraph />
            </div>
          </Card>
        </Col>
      </Row>

      {/* Third Row: Recent Activity */}
      <Row gutter={isMobile ? [16, 16] : [24, 24]} style={{ marginTop: headerMargin }}>
        <Col xs={24}>
          <Card 
            title={
              <Space size={isMobile ? 'small' : 'middle'}>
                <ClockCircleOutlined style={{ fontSize: isMobile ? '14px' : '16px' }} />
                <span style={{ fontSize: isMobile ? '14px' : '16px' }}>最近活动</span>
              </Space>
            }
            className="modern-card responsive-card"
          >
            {stats?.top_contributors && stats.top_contributors.length > 0 ? (
              <div>
                <Title level={5} style={{ marginBottom: '16px' }}>
                  活跃贡献者
                </Title>
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  {stats.top_contributors.slice(0, 5).map((contributor, index) => (
                    <div 
                      key={contributor.username}
                      style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '8px 0',
                        borderBottom: index < stats.top_contributors.length - 1 ? '1px solid #f0f0f0' : 'none'
                      }}
                    >
                      <Space>
                        <TeamOutlined style={{ color: '#1677ff' }} />
                        <Text strong>{contributor.username}</Text>
                      </Space>
                      <Space>
                        <Text type="secondary">
                          {contributor.project_count} 项目
                        </Text>
                        <Text type="secondary">
                          {contributor.cot_count} CoT数据
                        </Text>
                      </Space>
                    </div>
                  ))}
                </Space>
              </div>
            ) : (
              <div style={{ 
                textAlign: 'center', 
                padding: isMobile ? '24px 0' : '40px 0',
                color: '#8c8c8c'
              }}>
                <FileTextOutlined style={{ 
                  fontSize: isMobile ? '36px' : '48px', 
                  marginBottom: isMobile ? '12px' : '16px' 
                }} />
                <div style={{ fontSize: isMobile ? '14px' : '16px' }}>
                  暂无活动记录
                </div>
                <div style={{ 
                  fontSize: isMobile ? '11px' : '12px', 
                  marginTop: '8px',
                  lineHeight: 1.4
                }}>
                  开始创建项目和标注数据后，这里将显示您的活动历史
                </div>
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;