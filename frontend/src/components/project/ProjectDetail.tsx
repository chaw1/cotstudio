import React, { useState, useEffect } from 'react';
import {
  Card,
  Descriptions,
  Space,
  Tag,
  Button,
  Tabs,
  Statistic,
  Row,
  Col,
  Typography,
  Breadcrumb,
  message,
} from 'antd';
import {
  EditOutlined,
  ArrowLeftOutlined,
  FileTextOutlined,
  BulbOutlined,
  ShareAltOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { Project, FileInfo } from '../../types';
import FileUpload from './FileUpload';
import ProjectSelector from './ProjectSelector';
import { fileService } from '../../services/fileService';
import OCRProcessingTab from './OCRProcessingTab';
import { KnowledgeGraphViewer } from '../knowledge-graph';
import { AnnotationWorkspace } from '../annotation';

const { Title, Text } = Typography;

interface ProjectDetailProps {
  project: Project;
  onEdit: (project: Project) => void;
  onBack: () => void;
  onProjectChange?: (project: Project) => void;
}

const ProjectDetail: React.FC<ProjectDetailProps> = ({
  project,
  onEdit,
  onBack,
  onProjectChange,
}) => {
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [filesLoading, setFilesLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // 加载文件列表
  const loadFiles = async () => {
    setFilesLoading(true);
    try {
      const fileList = await fileService.getProjectFiles(project.id);
      setFiles(fileList);
    } catch (error) {
      message.error('加载文件列表失败');
    } finally {
      setFilesLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, [project.id]);

  // 处理文件上传
  const handleFileUpload = async (uploadFiles: File[]) => {
    const uploadPromises = uploadFiles.map(async (file) => {
      try {
        await fileService.uploadFile(project.id, file);
      } catch (error) {
        throw new Error(`上传文件 ${file.name} 失败`);
      }
    });

    await Promise.all(uploadPromises);
    // 上传成功后刷新文件列表
    await loadFiles();
  };

  // 处理文件删除
  const handleFileDelete = async (fileId: string) => {
    await fileService.deleteFile(fileId);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'green';
      case 'archived':
        return 'orange';
      case 'draft':
        return 'blue';
      default:
        return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return '活跃';
      case 'archived':
        return '已归档';
      case 'draft':
        return '草稿';
      default:
        return status;
    }
  };

  // 格式化所有者显示
  const formatOwner = (project: Project) => {
    // 如果有owner_name，优先使用用户名
    if (project.owner_name) {
      return project.owner_name;
    }
    
    // 如果没有owner_name但有owner_id，说明是系统创建的项目或者数据问题
    // 只有当没有找到对应用户名时才显示SYSTEM
    return <span style={{ color: '#1677ff', fontWeight: 'bold' }}>SYSTEM</span>;
  };

  // 格式化时间显示
  const formatDateTime = (dateString: string) => {
    try {
      if (!dateString) return 'Invalid Date';
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return 'Invalid Date';
      }
      return date.toLocaleString('zh-CN');
    } catch {
      return 'Invalid Date';
    }
  };

  // 计算时间距离
  const getDaysAgo = (dateString: string) => {
    try {
      if (!dateString) return null;
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return null;
      }
      const now = new Date();
      const diffTime = Math.abs(now.getTime() - date.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      return diffDays;
    } catch {
      return null;
    }
  };

  // 获取时间距离的颜色
  const getDaysAgoColor = (days: number) => {
    if (days <= 7) return '#52c41a'; // 绿色
    if (days <= 14) return '#1677ff'; // 蓝色
    if (days <= 30) return '#faad14'; // 黄色
    return '#ff4d4f'; // 红色
  };

  // 获取时间距离的显示文本
  const getDaysAgoText = (days: number) => {
    if (days > 30) return '+30';
    return `+${days}`;
  };

  // 定义标签页配置
  const tabItems = [
    {
      key: 'overview',
      label: '项目概览',
      children: (
        <Card title="项目信息">
          <Descriptions column={2} bordered>
            <Descriptions.Item label="项目ID">
              {project.id}
            </Descriptions.Item>
            <Descriptions.Item label="所有者">
              {formatOwner(project)}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {formatDateTime((project as any).created_at || project.createdAt)}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              <Space>
                {formatDateTime((project as any).updated_at || project.updatedAt)}
                {(() => {
                  const dateField = (project as any).updated_at || project.updatedAt;
                  const days = getDaysAgo(dateField);
                  if (days && days > 0) {
                    return (
                      <span style={{ 
                        color: getDaysAgoColor(days),
                        fontSize: '12px',
                        fontWeight: 'bold',
                        marginLeft: '8px',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        backgroundColor: 'rgba(255, 255, 255, 0.8)'
                      }}>
                        {getDaysAgoText(days)}
                      </span>
                    );
                  }
                  return null;
                })()}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="项目状态">
              <Tag color={getStatusColor(project.status)}>
                {getStatusText(project.status)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="标签">
              <Space wrap>
                {project.tags.map((tag) => (
                  <Tag key={tag} color="blue">
                    {tag}
                  </Tag>
                ))}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="描述" span={2}>
              {project.description || '无描述'}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )
    },
    {
      key: 'files',
      label: '文件管理',
      children: (
        <FileUpload
          projectId={project.id}
          files={files}
          loading={filesLoading}
          onUpload={handleFileUpload}
          onDelete={handleFileDelete}
          onRefresh={loadFiles}
        />
      )
    },
    {
      key: 'ocr',
      label: 'OCR处理',
      children: (
        <OCRProcessingTab
          projectId={project.id}
          files={files}
          onRefresh={loadFiles}
        />
      )
    },
    {
      key: 'annotation',
      label: 'CoT标注',
      children: (
        <div style={{ height: '600px' }}>
          <AnnotationWorkspace projectId={project.id} />
        </div>
      )
    },
    {
      key: 'knowledge-graph',
      label: '知识图谱',
      children: (
        <div style={{ height: '600px' }}>
          <KnowledgeGraphViewer 
            projectId={project.id}
            height={600}
          />
        </div>
      )
    }
  ];

  return (
    <div>
      {/* 面包屑导航 */}
      <div style={{ 
        marginBottom: 16,
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        flexWrap: 'nowrap',
        gap: '12px'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'flex-start',
          minWidth: 0,
          flex: 1
        }}>
          <div style={{ 
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <Button
              type="link"
              icon={<ArrowLeftOutlined />}
              onClick={onBack}
              style={{ 
                padding: 0,
                fontSize: '14px',
                height: '32px',
                lineHeight: '32px'
              }}
            >
              项目列表
            </Button>
            <span style={{ 
              fontSize: '14px', 
              color: '#999',
              lineHeight: '32px'
            }}>
              &gt;
            </span>
            {onProjectChange ? (
              <ProjectSelector
                currentProject={project}
                onProjectSelect={onProjectChange}
                style={{ 
                  border: 'none',
                  boxShadow: 'none',
                  background: 'transparent',
                  height: '32px'
                }}
              />
            ) : (
              <span style={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                maxWidth: '200px',
                display: 'inline-block',
                fontSize: '14px',
                lineHeight: '32px'
              }}>
                {project.name}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 项目头部信息 */}
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ flex: 1 }}>
            <Space direction="vertical" size="small">
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <Title level={2} style={{ margin: 0 }}>
                  {project.name}
                </Title>
                <Tag color={getStatusColor(project.status)}>
                  {getStatusText(project.status)}
                </Tag>
              </div>
              
              {project.description && (
                <Text type="secondary">{project.description}</Text>
              )}
              
              {project.tags.length > 0 && (
                <Space wrap>
                  {project.tags.map((tag) => (
                    <Tag key={tag} color="blue">
                      {tag}
                    </Tag>
                  ))}
                </Space>
              )}
            </Space>
          </div>
          
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={() => onEdit(project)}
          >
            编辑项目
          </Button>
        </div>
      </Card>

      {/* 统计信息 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="文件数量"
              value={files.length}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="CoT数据"
              value={project.cotCount}
              prefix={<BulbOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="知识图谱节点"
              value={0}
              prefix={<ShareAltOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="处理进度"
              value={files.length > 0 ? Math.round((files.filter(f => f.ocrStatus === 'completed').length / files.length) * 100) : 0}
              suffix="%"
              prefix={<SettingOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 详细信息标签页 */}
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
    </div>
  );
};

export default ProjectDetail;