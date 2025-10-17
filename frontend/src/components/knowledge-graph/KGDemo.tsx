import React, { useState } from 'react';
import { Card, Button, Space, Typography, Alert } from 'antd';
import { PlayCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { KnowledgeGraphViewer } from './index';

const { Title, Paragraph } = Typography;

// Mock data for demonstration
const mockKGData = {
  entities: [
    {
      id: 'person-1',
      label: 'Alice Johnson',
      type: 'Person',
      properties: { 
        connections: 5, 
        importance: 0.8,
        confidence: 0.9,
        role: 'Researcher'
      }
    },
    {
      id: 'org-1',
      label: 'Tech Corp',
      type: 'Organization',
      properties: { 
        connections: 8, 
        importance: 0.9,
        confidence: 0.8,
        industry: 'Technology'
      }
    },
    {
      id: 'concept-1',
      label: 'Machine Learning',
      type: 'Concept',
      properties: { 
        connections: 12, 
        importance: 0.95,
        confidence: 0.9,
        domain: 'AI'
      }
    },
    {
      id: 'doc-1',
      label: 'Research Paper',
      type: 'Document',
      properties: { 
        connections: 3, 
        importance: 0.7,
        confidence: 0.8,
        type: 'Academic'
      }
    },
    {
      id: 'tech-1',
      label: 'Neural Networks',
      type: 'Technology',
      properties: { 
        connections: 6, 
        importance: 0.85,
        confidence: 0.9,
        category: 'Deep Learning'
      }
    }
  ],
  relations: [
    {
      id: 'rel-1',
      source: 'person-1',
      target: 'org-1',
      type: 'works_for',
      properties: { weight: 0.9, confidence: 0.8, duration: '3 years' }
    },
    {
      id: 'rel-2',
      source: 'person-1',
      target: 'concept-1',
      type: 'researches',
      properties: { weight: 0.8, confidence: 0.9, expertise: 'high' }
    },
    {
      id: 'rel-3',
      source: 'person-1',
      target: 'doc-1',
      type: 'authored',
      properties: { weight: 0.7, confidence: 0.95, role: 'first_author' }
    },
    {
      id: 'rel-4',
      source: 'concept-1',
      target: 'tech-1',
      type: 'implements',
      properties: { weight: 0.9, confidence: 0.8, relationship: 'uses' }
    },
    {
      id: 'rel-5',
      source: 'org-1',
      target: 'tech-1',
      type: 'develops',
      properties: { weight: 0.8, confidence: 0.7, investment: 'high' }
    }
  ]
};

const KGDemo: React.FC = () => {
  const [demoMode, setDemoMode] = useState(false);

  // Mock the service for demo
  React.useEffect(() => {
    if (demoMode) {
      // Override the service temporarily for demo
      const originalService = require('../../services/knowledgeGraphService').default;
      
      const mockService = {
        ...originalService,
        getKnowledgeGraph: () => Promise.resolve(mockKGData),
        getKGStats: () => Promise.resolve({
          totalEntities: mockKGData.entities.length,
          totalRelations: mockKGData.relations.length,
          entityTypes: [
            { type: 'Person', count: 1 },
            { type: 'Organization', count: 1 },
            { type: 'Concept', count: 1 },
            { type: 'Document', count: 1 },
            { type: 'Technology', count: 1 }
          ],
          relationTypes: [
            { type: 'works_for', count: 1 },
            { type: 'researches', count: 1 },
            { type: 'authored', count: 1 },
            { type: 'implements', count: 1 },
            { type: 'develops', count: 1 }
          ]
        })
      };

      // This is just for demo purposes - in real app, data comes from API
    }
  }, [demoMode]);

  return (
    <div style={{ padding: '24px' }}>
      <Card style={{ marginBottom: '24px' }}>
        <Title level={3}>知识图谱可视化演示</Title>
        <Paragraph>
          这是知识图谱可视化组件的演示。该组件支持：
        </Paragraph>
        <ul>
          <li>多种布局算法（层次布局、力导向布局、约束布局等）</li>
          <li>实体和关系的交互式过滤</li>
          <li>节点和边的详细信息查看</li>
          <li>搜索和高亮功能</li>
          <li>图谱统计和质量指标</li>
          <li>图片导出功能</li>
        </ul>
        
        <Space style={{ marginTop: '16px' }}>
          <Button 
            type="primary" 
            icon={<PlayCircleOutlined />}
            onClick={() => setDemoMode(true)}
          >
            启动演示
          </Button>
          <Button 
            icon={<ReloadOutlined />}
            onClick={() => setDemoMode(false)}
          >
            重置
          </Button>
        </Space>
      </Card>

      {demoMode ? (
        <div style={{ height: '700px' }}>
          <Alert
            message="演示模式"
            description="当前显示的是模拟数据，实际使用时会从后端API获取真实的知识图谱数据。"
            type="info"
            showIcon
            style={{ marginBottom: '16px' }}
          />
          <KnowledgeGraphViewer
            projectId="demo-project"
            height={650}
            showControls={true}
            showStats={true}
            onNodeSelect={(node) => {
              console.log('Demo: Selected node:', node);
            }}
            onEdgeSelect={(edge) => {
              console.log('Demo: Selected edge:', edge);
            }}
          />
        </div>
      ) : (
        <Card style={{ textAlign: 'center', padding: '60px' }}>
          <Typography.Text type="secondary">
            点击"启动演示"按钮查看知识图谱可视化效果
          </Typography.Text>
        </Card>
      )}
    </div>
  );
};

export default KGDemo;