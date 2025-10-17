import React, { useState, useEffect } from 'react';
import { Select, Button, Space, Avatar } from 'antd';
import { 
  FolderOpenOutlined, 
  DownOutlined,
  ProjectOutlined 
} from '@ant-design/icons';
import { Project } from '../../types';
import { projectService } from '../../services/projectService';
import safeMessage from '../../utils/message';

const { Option } = Select;

interface ProjectSelectorProps {
  currentProject?: Project;
  onProjectSelect: (project: Project) => void;
  style?: React.CSSProperties;
  className?: string;
  placeholder?: string;
}

/**
 * 项目选择器组件
 * 支持下拉选择项目并快速跳转
 */
const ProjectSelector: React.FC<ProjectSelectorProps> = ({
  currentProject,
  onProjectSelect,
  style = {},
  className = '',
  placeholder = '选择项目'
}) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  // 加载项目列表
  const loadProjects = async () => {
    try {
      setLoading(true);
      const projectList = await projectService.getProjects();
      setProjects(projectList);
    } catch (error) {
      safeMessage.error('加载项目列表失败');
      console.error('Error loading projects:', error);
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时加载项目列表
  useEffect(() => {
    loadProjects();
  }, []);

  // 处理项目选择
  const handleProjectSelect = (projectId: string) => {
    const selectedProject = projects.find(p => p.id === projectId);
    if (selectedProject) {
      onProjectSelect(selectedProject);
      setOpen(false);
    }
  };

  // 获取项目状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return '#52c41a';
      case 'archived':
        return '#faad14';
      case 'draft':
        return '#1677ff';
      default:
        return '#d9d9d9';
    }
  };

  // 自定义下拉渲染
  const popupRender = (menu: React.ReactElement) => (
    <div>
      {menu}
      {projects.length === 0 && !loading && (
        <div style={{ 
          padding: '8px 12px', 
          textAlign: 'center', 
          color: '#999',
          fontSize: '12px'
        }}>
          暂无可用项目
        </div>
      )}
    </div>
  );

  return (
    <Select
      value={currentProject?.id}
      placeholder={placeholder}
      style={{ 
        minWidth: '350px',
        width: 'auto',
        ...style 
      }}
      className={className}
      loading={loading}
      open={open}
      onOpenChange={setOpen}
      onSelect={handleProjectSelect}
      popupRender={popupRender}
      suffixIcon={<DownOutlined />}
      showSearch
      filterOption={(input, option) => {
        const project = projects.find(p => p.id === option?.value);
        return project?.name.toLowerCase().includes(input.toLowerCase()) || false;
      }}
      optionFilterProp="children"
    >
      {projects.map((project) => (
        <Option 
          key={project.id} 
          value={project.id}
          style={{ padding: '8px 12px' }}
        >
          <div style={{ 
            display: 'flex', 
            alignItems: 'center',
            width: '100%',
            gap: '8px'
          }}>
            <Avatar
              size="small"
              icon={<ProjectOutlined />}
              style={{ 
                backgroundColor: getStatusColor(project.status),
                fontSize: '12px',
                flexShrink: 0
              }}
            />
            <div style={{ 
              flex: 1,
              minWidth: 0,
              fontSize: '14px',
              lineHeight: '20px'
            }}>
              <span style={{ fontWeight: 500 }}>
                {project.name}
              </span>
              {project.description && (
                <>
                  <span style={{ color: '#999', margin: '0 6px' }}>/</span>
                  <span style={{ color: '#666' }}>
                    {project.description.length > 10 
                      ? project.description.substring(0, 10) + '...' 
                      : project.description}
                  </span>
                </>
              )}
              <span style={{ color: '#999', margin: '0 6px' }}>/</span>
              <span style={{ color: '#1677ff', fontSize: '12px' }}>
                {project.fileCount || 0} 文件
              </span>
            </div>
          </div>
        </Option>
      ))}
    </Select>
  );
};

export default ProjectSelector;