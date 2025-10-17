/**
 * 项目选择器组件
 */
import React, { useState, useEffect } from 'react';
import { Select, Card, Typography, Spin, Alert } from 'antd';
import { Project } from '../../types/export';
import exportService from '../../services/exportService';

const { Title, Text } = Typography;
const { Option } = Select;

interface ProjectSelectorProps {
  selectedProject?: string;
  onProjectChange: (projectId: string, project: Project) => void;
}

const ProjectSelector: React.FC<ProjectSelectorProps> = ({
  selectedProject,
  onProjectChange
}) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const projectList = await exportService.getProjects();
      setProjects(projectList);
    } catch (err: any) {
      setError(err.message || '加载项目列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleProjectChange = (projectId: string) => {
    const project = projects.find(p => p.id === projectId);
    if (project) {
      onProjectChange(projectId, project);
    }
  };

  const selectedProjectInfo = projects.find(p => p.id === selectedProject);

  return (
    <Card title="选择项目" size="small">
      {loading ? (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Spin size="large" />
          <div style={{ marginTop: '10px' }}>加载项目列表...</div>
        </div>
      ) : error ? (
        <Alert
          message="加载失败"
          description={error}
          type="error"
          showIcon
          action={
            <button onClick={loadProjects} style={{ border: 'none', background: 'none', color: '#1890ff', cursor: 'pointer' }}>
              重试
            </button>
          }
        />
      ) : (
        <>
          <Select
            style={{ width: '100%' }}
            placeholder="请选择要导出的项目"
            value={selectedProject}
            onChange={handleProjectChange}
            showSearch
            filterOption={(input, option) =>
              option?.children?.toString().toLowerCase().includes(input.toLowerCase()) ?? false
            }
          >
            {projects.map(project => (
              <Option key={project.id} value={project.id}>
                {project.name}
              </Option>
            ))}
          </Select>

          {selectedProjectInfo && (
            <div style={{ marginTop: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
              <Title level={5} style={{ margin: '0 0 8px 0' }}>
                {selectedProjectInfo.name}
              </Title>
              {selectedProjectInfo.description && (
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {selectedProjectInfo.description}
                </Text>
              )}
              <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
                <div>创建时间: {new Date(selectedProjectInfo.created_at).toLocaleString()}</div>
                <div>项目类型: {selectedProjectInfo.project_type}</div>
                {selectedProjectInfo.tags && selectedProjectInfo.tags.length > 0 && (
                  <div>标签: {selectedProjectInfo.tags.join(', ')}</div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </Card>
  );
};

export default ProjectSelector;