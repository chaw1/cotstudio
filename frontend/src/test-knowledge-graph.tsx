import React from 'react';
import { KnowledgeGraphViewer } from './components/knowledge-graph';

const TestKnowledgeGraph: React.FC = () => {
  const testData = {
    nodes: [
      { id: 'user-1', label: '用户中心', type: 'user', size: 40 },
      { id: 'project-1', label: '项目A', type: 'project', size: 30 },
      { id: 'project-2', label: '项目B', type: 'project', size: 25 },
      { id: 'cot-1', label: 'CoT数据', type: 'cot', size: 20 },
    ],
    edges: [
      { id: 'edge-1', source: 'user-1', target: 'project-1', type: 'contributes' },
      { id: 'edge-2', source: 'user-1', target: 'project-2', type: 'contributes' },
      { id: 'edge-3', source: 'project-1', target: 'cot-1', type: 'contains' },
    ]
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>知识图谱测试</h1>
      <div style={{ border: '1px solid #ccc', height: '400px' }}>
        <KnowledgeGraphViewer
          projectId={null}
          height={400}
          showControls={false}
          showStats={false}
          data={testData}
          disableDataFetch={true}
        />
      </div>
    </div>
  );
};

export default TestKnowledgeGraph;