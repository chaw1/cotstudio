import React, { useState } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  Popconfirm,
  Typography,
  Card,
  Input,
  Select,
  message,
  Row,
  Col,
  Popover,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  FolderOpenOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { Project } from '../../types';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { useResponsiveBreakpoint } from '../../hooks/useResponsiveBreakpoint';

const { Title } = Typography;
const { Search } = Input;
const { Option } = Select;

interface ProjectListProps {
  projects: Project[];
  loading: boolean;
  onCreateProject: () => void;
  onEditProject: (project: Project) => void;
  onDeleteProject: (projectId: string) => void;
  onViewProject: (project: Project) => void;
}

const ProjectList: React.FC<ProjectListProps> = ({
  projects,
  loading,
  onCreateProject,
  onEditProject,
  onDeleteProject,
  onViewProject,
}) => {
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const { isMobile, isTablet } = useResponsiveBreakpoint();

  // 标签展开组件
  const TagsRenderer: React.FC<{ tags: string[] }> = ({ tags }) => {
    const maxVisible = isMobile ? 1 : 2;
    const visibleTags = tags.slice(0, maxVisible);
    const hiddenTags = tags.slice(maxVisible);

    // 展开的标签内容
    const expandedContent = (
      <div style={{ maxWidth: 300 }}>
        <div style={{ marginBottom: 8, fontWeight: 'bold', fontSize: '12px' }}>
          全部标签 ({tags.length})
        </div>
        <Space wrap size="small" style={{ display: 'flex', flexWrap: 'wrap' }}>
          {tags.map((tag, index) => (
            <Tag 
              key={`${tag}-${index}`} 
              color="blue"
              style={{ 
                fontSize: '11px',
                marginBottom: '4px'
              }}
            >
              {tag}
            </Tag>
          ))}
        </Space>
      </div>
    );

    return (
      <Space wrap size="small">
        {visibleTags.map((tag, index) => (
          <Tag 
            key={`${tag}-${index}`} 
            color="blue"
            style={{ fontSize: isMobile ? '10px' : '11px' }}
          >
            {tag}
          </Tag>
        ))}
        {hiddenTags.length > 0 && (
          <Popover
            content={expandedContent}
            title={null}
            trigger="click"
            placement="bottomLeft"
            overlayStyle={{ maxWidth: 320 }}
          >
            <Tag 
              style={{ 
                fontSize: isMobile ? '10px' : '11px',
                cursor: 'pointer',
                background: '#f0f0f0',
                border: '1px dashed #d9d9d9'
              }}
            >
              +{hiddenTags.length}
            </Tag>
          </Popover>
        )}
      </Space>
    );
  };

  // 过滤项目
  const filteredProjects = projects.filter((project) => {
    const matchesSearch = project.name.toLowerCase().includes(searchText.toLowerCase()) ||
      project.description?.toLowerCase().includes(searchText.toLowerCase()) ||
      project.tags.some(tag => tag.toLowerCase().includes(searchText.toLowerCase()));
    
    const matchesStatus = statusFilter === 'all' || project.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  const handleDelete = async (projectId: string) => {
    try {
      await onDeleteProject(projectId);
      message.success('项目删除成功');
    } catch (error) {
      message.error('删除项目失败');
    }
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

  const columns = [
    {
      title: '项目名称',
      dataIndex: 'name',
      key: 'name',
      fixed: 'left' as const,
      width: isMobile ? 120 : 200,
      render: (text: string, record: Project) => (
        <Button
          type="link"
          icon={<FolderOpenOutlined />}
          onClick={() => onViewProject(record)}
          style={{ 
            padding: 0, 
            height: 'auto',
            fontSize: isMobile ? '12px' : '14px'
          }}
        >
          {text}
        </Button>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      width: isMobile ? 100 : 200,
      responsive: ['md' as const],
      render: (text: string) => text || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: isMobile ? 60 : 80,
      render: (status: string) => (
        <Tag 
          color={getStatusColor(status)}
          style={{ fontSize: isMobile ? '10px' : '12px' }}
        >
          {getStatusText(status)}
        </Tag>
      ),
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      width: isMobile ? 80 : 120,
      responsive: ['lg' as const],
      render: (tags: string[]) => <TagsRenderer tags={tags} />,
    },
    {
      title: '文件数',
      dataIndex: 'file_count',
      key: 'file_count',
      width: isMobile ? 50 : 80,
      align: 'center' as const,
      responsive: ['sm' as const],
      render: (count: number) => {
        if (!count || count === 0) {
          return <span style={{ color: '#ff4d4f', fontSize: '12px' }}>未上传</span>;
        }
        return <span style={{ fontWeight: 'bold' }}>{count}</span>;
      },
    },
    {
      title: 'CoT数',
      dataIndex: 'cot_count',
      key: 'cot_count',
      width: isMobile ? 50 : 80,
      align: 'center' as const,
      responsive: ['sm' as const],
      render: (count: number) => {
        if (!count || count === 0) {
          return <span style={{ color: '#ff4d4f', fontSize: '12px' }}>未创建</span>;
        }
        return <span style={{ fontWeight: 'bold' }}>{count}</span>;
      },
    },
    {
      title: '知识图谱',
      dataIndex: 'kg_count',
      key: 'kg_count', 
      width: isMobile ? 60 : 90,
      align: 'center' as const,
      responsive: ['lg' as const],
      render: (count: number) => {
        if (!count || count === 0) {
          return <span style={{ color: '#ff4d4f', fontSize: '12px' }}>未创建</span>;
        }
        return <span style={{ fontWeight: 'bold' }}>{count}</span>;
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: isMobile ? 80 : 120,
      responsive: ['md' as const],
      render: (date: string) => {
        try {
          if (!date) return '-';
          return formatDistanceToNow(new Date(date), { 
            addSuffix: true, 
            locale: zhCN 
          });
        } catch {
          return date || '-';
        }
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: isMobile ? 80 : 120,
      fixed: 'right' as const,
      render: (_: any, record: Project) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => onEditProject(record)}
            size={isMobile ? 'small' : 'middle'}
            style={{ fontSize: isMobile ? '12px' : '14px' }}
          />
          <Popconfirm
            title="确认删除"
            description="删除项目将同时删除所有相关数据，此操作不可恢复。"
            onConfirm={() => handleDelete(record.id)}
            okText="确认"
            cancelText="取消"
            okType="danger"
          >
            <Button
              type="text"
              icon={<DeleteOutlined />}
              danger
              size={isMobile ? 'small' : 'middle'}
              style={{ fontSize: isMobile ? '12px' : '14px' }}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="fade-in work-area-adaptive">
      <Card className="modern-card responsive-card">
        <div style={{ marginBottom: 16 }}>
          <Row 
            justify="space-between" 
            align="middle" 
            style={{ marginBottom: 16 }}
            gutter={[16, 16]}
          >
            <Col xs={24} sm={12} md={16}>
              <Title level={isMobile ? 4 : 3} style={{ margin: 0 }}>
                项目列表
              </Title>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={onCreateProject}
                className="modern-button"
                size={isMobile ? 'middle' : 'large'}
                style={{ width: isMobile ? '100%' : 'auto' }}
              >
                新建项目
              </Button>
            </Col>
          </Row>
          
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col xs={24} sm={16} md={18}>
              <Search
                placeholder="搜索项目名称、描述或标签"
                allowClear
                prefix={<SearchOutlined />}
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                size={isMobile ? 'middle' : 'large'}
              />
            </Col>
            <Col xs={24} sm={8} md={6}>
              <Select
                style={{ width: '100%' }}
                value={statusFilter}
                onChange={setStatusFilter}
                size={isMobile ? 'middle' : 'large'}
              >
                <Option value="all">全部状态</Option>
                <Option value="active">活跃</Option>
                <Option value="draft">草稿</Option>
                <Option value="archived">已归档</Option>
              </Select>
            </Col>
          </Row>
        </div>

        <div className="responsive-table">
          <Table
            columns={columns}
            dataSource={filteredProjects}
            rowKey="id"
            loading={loading}
            scroll={{ x: 1200 }}
            size={isMobile ? 'small' : 'middle'}
            pagination={{
              showSizeChanger: !isMobile,
              showQuickJumper: !isMobile,
              showTotal: (total, range) =>
                `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
              pageSize: isMobile ? 5 : 10,
              responsive: true,
            }}
          />
        </div>
      </Card>
    </div>
  );
};

export default ProjectList;