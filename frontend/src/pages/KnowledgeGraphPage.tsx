import React from 'react';
import { useParams } from 'react-router-dom';
import { Card, Typography, Space } from 'antd';
import { NodeIndexOutlined } from '@ant-design/icons';
import { KnowledgeGraphViewer } from '../components/knowledge-graph';

const { Title } = Typography;

const KnowledgeGraphPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();

  if (!projectId) {
    return (
      <Card>
        <Typography.Text type="danger">项目ID不能为空</Typography.Text>
      </Card>
    );
  }

  return (
    <div style={{ height: '100vh', padding: '16px' }}>
      <div style={{ marginBottom: '16px' }}>
        <Title level={2}>
          <Space>
            <NodeIndexOutlined />
            知识图谱
          </Space>
        </Title>
      </div>
      
      <div style={{ height: 'calc(100vh - 120px)' }}>
        <KnowledgeGraphViewer
          projectId={projectId}
          height={600}
          showControls={true}
          showStats={true}
          onNodeSelect={(node) => {
            console.log('Selected node:', node);
          }}
          onEdgeSelect={(edge) => {
            console.log('Selected edge:', edge);
          }}
        />
      </div>
    </div>
  );
};

export default KnowledgeGraphPage;