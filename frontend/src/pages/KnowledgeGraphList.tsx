import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Card, 
  Row, 
  Col, 
  Input, 
  Select, 
  Button, 
  Typography, 
  Space, 
  Spin, 
  Empty,
  Tag,
  Tooltip
} from 'antd';
import { 
  NodeIndexOutlined, 
  SearchOutlined, 
  EyeOutlined,
  ProjectOutlined,
  UserOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import knowledgeGraphService from '../services/knowledgeGraphService';
import { Project } from '../types';
import safeMessage from '../utils/message';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;

interface KnowledgeGraphInfo {
  id: string;
  projectId: string;
  projectName: string;
  projectDescription?: string;
  owner: string;
  entityCount: number;
  relationCount: number;
  lastUpdated: string;
  tags: string[];
  hasAccess: boolean;
}

const KnowledgeGraphList: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [graphs, setGraphs] = useState<KnowledgeGraphInfo[]>([]);
  const [filteredGraphs, setFilteredGraphs] = useState<KnowledgeGraphInfo[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'updated' | 'entities'>('updated');

  useEffect(() => {
    fetchAccessibleGraphs();
  }, []);

  useEffect(() => {
    filterAndSortGraphs();
  }, [graphs, searchQuery, sortBy]);

  const fetchAccessibleGraphs = async () => {
    try {
      setLoading(true);
      // Use the new API endpoint to get accessible knowledge graphs
      const graphsData = await knowledgeGraphService.getAccessibleKnowledgeGraphs();
      setGraphs(graphsData);
    } catch (error) {
      console.error('Failed to fetch accessible knowledge graphs:', error);
      safeMessage.error('获取知识图谱列表失败');
      
      // Fallback to the old method if the new API is not available
      try {
        const response = await fetch('/api/v1/projects');
        const projects: Project[] = await response.json();
        
        const fallbackGraphsData: KnowledgeGraphInfo[] = [];
        
        // Get KG stats for each project
        for (const project of projects) {
          try {
            const stats = await knowledgeGraphService.getKGStats(project.id);
            if (stats.totalEntities > 0 || stats.totalRelations > 0) {
              fallbackGraphsData.push({
                id: `kg_${project.id}`,
                projectId: project.id,
                projectName: project.name,
                projectDescription: project.description,
                owner: project.owner,
                entityCount: stats.totalEntities,
                relationCount: stats.totalRelations,
                lastUpdated: project.updatedAt,
                tags: project.tags || [],
                hasAccess: true
              });
            }
          } catch (error) {
            // Skip projects without KG data or access issues
            console.warn(`Failed to get KG stats for project ${project.id}:`, error);
          }
        }
        
        setGraphs(fallbackGraphsData);
      } catch (fallbackError) {
        console.error('Fallback method also failed:', fallbackError);
      }
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortGraphs = () => {
    let filtered = graphs;

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(graph => 
        graph.projectName.toLowerCase().includes(query) ||
        graph.projectDescription?.toLowerCase().includes(query) ||
        graph.owner.toLowerCase().includes(query) ||
        graph.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.projectName.localeCompare(b.projectName);
        case 'updated':
          return new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime();
        case 'entities':
          return b.entityCount - a.entityCount;
        default:
          return 0;
      }
    });

    setFilteredGraphs(filtered);
  };

  const handleViewGraph = (graph: KnowledgeGraphInfo) => {
    navigate(`/knowledge-graph/${graph.projectId}`);
  };

  const handleViewProject = (graph: KnowledgeGraphInfo) => {
    navigate(`/projects/${graph.projectId}`);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const renderGraphCard = (graph: KnowledgeGraphInfo) => (
    <Col xs={24} sm={12} lg={8} xl={6} key={graph.id}>
      <Card
        hoverable
        className="knowledge-graph-card"
        style={{ height: '100%' }}
        actions={[
          <Tooltip title="查看知识图谱">
            <Button 
              type="text" 
              icon={<EyeOutlined />}
              onClick={() => handleViewGraph(graph)}
            >
              查看图谱
            </Button>
          </Tooltip>,
          <Tooltip title="查看项目">
            <Button 
              type="text" 
              icon={<ProjectOutlined />}
              onClick={() => handleViewProject(graph)}
            >
              查看项目
            </Button>
          </Tooltip>
        ]}
      >
        <div style={{ minHeight: '200px' }}>
          <div style={{ marginBottom: '12px' }}>
            <Title level={4} style={{ margin: 0, fontSize: '16px' }}>
              <NodeIndexOutlined style={{ marginRight: '8px', color: '#1677ff' }} />
              {graph.projectName}
            </Title>
          </div>

          {graph.projectDescription && (
            <Text type="secondary" style={{ display: 'block', marginBottom: '12px' }}>
              {graph.projectDescription.length > 80 
                ? `${graph.projectDescription.substring(0, 80)}...`
                : graph.projectDescription
              }
            </Text>
          )}

          <div style={{ marginBottom: '12px' }}>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <div>
                <Text strong>实体数量: </Text>
                <Tag color="blue">{graph.entityCount}</Tag>
              </div>
              <div>
                <Text strong>关系数量: </Text>
                <Tag color="green">{graph.relationCount}</Tag>
              </div>
              <div>
                <UserOutlined style={{ marginRight: '4px' }} />
                <Text type="secondary">{graph.owner}</Text>
              </div>
              <div>
                <CalendarOutlined style={{ marginRight: '4px' }} />
                <Text type="secondary">{formatDate(graph.lastUpdated)}</Text>
              </div>
            </Space>
          </div>

          {graph.tags.length > 0 && (
            <div>
              {graph.tags.slice(0, 3).map(tag => (
                <Tag key={tag} style={{ marginBottom: '4px' }}>
                  {tag}
                </Tag>
              ))}
              {graph.tags.length > 3 && (
                <Tag style={{ marginBottom: '4px' }}>
                  +{graph.tags.length - 3}
                </Tag>
              )}
            </div>
          )}
        </div>
      </Card>
    </Col>
  );

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>
          <Space>
            <NodeIndexOutlined />
            知识图谱
          </Space>
        </Title>
        <Text type="secondary">
          浏览和访问所有可用的知识图谱
        </Text>
      </div>

      <div style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="搜索知识图谱..."
              allowClear
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              prefix={<SearchOutlined />}
            />
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Select
              style={{ width: '100%' }}
              value={sortBy}
              onChange={setSortBy}
              placeholder="排序方式"
            >
              <Option value="updated">按更新时间</Option>
              <Option value="name">按名称</Option>
              <Option value="entities">按实体数量</Option>
            </Select>
          </Col>
          <Col xs={24} sm={24} md={8}>
            <Button 
              type="primary" 
              icon={<ProjectOutlined />}
              onClick={() => navigate('/projects')}
              style={{ width: '100%' }}
            >
              创建新项目
            </Button>
          </Col>
        </Row>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
          <div style={{ marginTop: '16px' }}>
            <Text>正在加载知识图谱...</Text>
          </div>
        </div>
      ) : filteredGraphs.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            searchQuery 
              ? `没有找到匹配"${searchQuery}"的知识图谱`
              : "暂无可用的知识图谱"
          }
        >
          {!searchQuery && (
            <Button 
              type="primary" 
              icon={<ProjectOutlined />}
              onClick={() => navigate('/projects')}
            >
              创建第一个项目
            </Button>
          )}
        </Empty>
      ) : (
        <Row gutter={[16, 16]}>
          {filteredGraphs.map(renderGraphCard)}
        </Row>
      )}
    </div>
  );
};

export default KnowledgeGraphList;