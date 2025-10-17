import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Typography, Space, Alert, Button, Breadcrumb, Spin, Drawer } from 'antd';
import { NodeIndexOutlined, ArrowLeftOutlined, ProjectOutlined, MenuOutlined } from '@ant-design/icons';
import { KnowledgeGraphViewer } from '../components/knowledge-graph';
import { Project } from '../types';
import { useResponsiveBreakpoint } from '../hooks/useResponsiveBreakpoint';
import safeMessage from '../utils/message';

const { Title, Text } = Typography;

const KnowledgeGraph: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [controlsVisible, setControlsVisible] = useState(false);
  
  const { isMobile, isTablet, breakpoint } = useResponsiveBreakpoint();

  useEffect(() => {
    if (projectId) {
      fetchProjectInfo();
    } else {
      setError('项目ID缺失');
      setLoading(false);
    }
  }, [projectId]);

  const fetchProjectInfo = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/projects/${projectId}`);
      if (!response.ok) {
        throw new Error('项目不存在或无访问权限');
      }
      const projectData: Project = await response.json();
      setProject(projectData);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch project info:', err);
      setError(err instanceof Error ? err.message : '获取项目信息失败');
      safeMessage.error('获取项目信息失败');
    } finally {
      setLoading(false);
    }
  };

  const handleGoBack = () => {
    navigate('/knowledge-graph');
  };

  const handleGoToProject = () => {
    if (projectId) {
      navigate(`/projects/${projectId}`);
    }
  };

  // 响应式样式计算
  const containerPadding = isMobile ? '12px' : '16px';
  const headerMargin = isMobile ? '12px' : '16px';
  const titleLevel = isMobile ? 3 : 2;
  const buttonSize = isMobile ? 'small' : 'middle';
  const graphHeight = isMobile ? 'calc(100vh - 140px)' : 'calc(100vh - 180px)';

  if (loading) {
    return (
      <div style={{ 
        padding: containerPadding, 
        textAlign: 'center',
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center'
      }}>
        <Spin size="large" />
        <div style={{ marginTop: '16px' }}>
          <Text style={{ fontSize: isMobile ? '12px' : '14px' }}>
            正在加载项目信息...
          </Text>
        </div>
      </div>
    );
  }

  if (error || !projectId) {
    return (
      <div style={{ padding: containerPadding }}>
        <Alert
          message="无法访问知识图谱"
          description={error || "项目ID缺失，请从知识图谱列表或项目页面访问"}
          type="warning"
          showIcon
          action={
            <Space direction={isMobile ? 'vertical' : 'horizontal'} style={{ width: isMobile ? '100%' : 'auto' }}>
              <Button size={buttonSize} onClick={handleGoBack} style={{ width: isMobile ? '100%' : 'auto' }}>
                返回知识图谱列表
              </Button>
              <Button 
                size={buttonSize} 
                type="primary" 
                onClick={() => navigate('/projects')}
                style={{ width: isMobile ? '100%' : 'auto' }}
              >
                查看项目
              </Button>
            </Space>
          }
        />
      </div>
    );
  }

  return (
    <div style={{ height: '100vh', padding: containerPadding }}>
      <div style={{ marginBottom: headerMargin }}>
        {/* 面包屑导航 - 在移动端可能隐藏或简化 */}
        {!isMobile && (
          <Breadcrumb style={{ marginBottom: headerMargin }}>
            <Breadcrumb.Item>
              <Button 
                type="link" 
                icon={<NodeIndexOutlined />}
                onClick={handleGoBack}
                style={{ padding: 0, fontSize: '12px' }}
              >
                知识图谱
              </Button>
            </Breadcrumb.Item>
            <Breadcrumb.Item>
              <Button 
                type="link" 
                icon={<ProjectOutlined />}
                onClick={handleGoToProject}
                style={{ padding: 0, fontSize: '12px' }}
              >
                {project?.name || '项目'}
              </Button>
            </Breadcrumb.Item>
            <Breadcrumb.Item>可视化</Breadcrumb.Item>
          </Breadcrumb>
        )}

        {/* 标题和操作按钮 */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: isMobile ? 'flex-start' : 'center',
          flexDirection: isMobile ? 'column' : 'row',
          gap: isMobile ? '12px' : '0'
        }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <Title level={titleLevel} style={{ 
              margin: 0,
              fontSize: isMobile ? '18px' : undefined,
              lineHeight: 1.2
            }}>
              <Space size={isMobile ? 'small' : 'middle'}>
                <NodeIndexOutlined style={{ fontSize: isMobile ? '16px' : '20px' }} />
                <span style={{ 
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: isMobile ? 'nowrap' : 'normal'
                }}>
                  {isMobile ? project?.name : `${project?.name} - 知识图谱可视化`}
                </span>
              </Space>
            </Title>
            
            {project?.description && (
              <Text type="secondary" style={{ 
                display: 'block', 
                marginTop: '8px',
                fontSize: isMobile ? '12px' : '14px',
                lineHeight: 1.4,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: isMobile ? 'nowrap' : 'normal'
              }}>
                {project.description}
              </Text>
            )}
          </div>
          
          {/* 操作按钮 */}
          {isMobile ? (
            <div style={{ display: 'flex', gap: '8px', width: '100%' }}>
              <Button 
                icon={<ArrowLeftOutlined />}
                onClick={handleGoBack}
                size={buttonSize}
                style={{ flex: 1 }}
              >
                返回
              </Button>
              <Button 
                type="primary"
                icon={<ProjectOutlined />}
                onClick={handleGoToProject}
                size={buttonSize}
                style={{ flex: 1 }}
              >
                项目
              </Button>
              <Button 
                icon={<MenuOutlined />}
                onClick={() => setControlsVisible(true)}
                size={buttonSize}
              >
                控制
              </Button>
            </div>
          ) : (
            <Space>
              <Button 
                icon={<ArrowLeftOutlined />}
                onClick={handleGoBack}
                size={buttonSize}
              >
                返回列表
              </Button>
              <Button 
                type="primary"
                icon={<ProjectOutlined />}
                onClick={handleGoToProject}
                size={buttonSize}
              >
                查看项目
              </Button>
            </Space>
          )}
        </div>
      </div>
      
      {/* 知识图谱可视化区域 */}
      <div style={{ height: graphHeight }}>
        <KnowledgeGraphViewer
          projectId={projectId}
          height={isMobile ? undefined : 600}
          showControls={!isMobile}
          showStats={!isMobile}

          onNodeSelect={(node) => {
            console.log('Selected node:', node);
          }}
          onEdgeSelect={(edge) => {
            console.log('Selected edge:', edge);
          }}
        />
      </div>

      {/* 移动端控制面板抽屉 */}
      {isMobile && (
        <Drawer
          title="图谱控制"
          placement="bottom"
          height="60%"
          open={controlsVisible}
          onClose={() => setControlsVisible(false)}
        >
          <div style={{ padding: '16px' }}>
            <Text>图谱控制选项将在这里显示</Text>
            {/* 这里可以放置图谱控制组件 */}
          </div>
        </Drawer>
      )}
    </div>
  );
};

export default KnowledgeGraph;