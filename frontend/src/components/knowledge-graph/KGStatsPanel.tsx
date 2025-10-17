import React, { useEffect, useState } from 'react';
import { Card, Statistic, Row, Col, Progress, List, Typography, Space, Spin } from 'antd';
import { 
  NodeIndexOutlined, 
  LinkOutlined, 
  BarChartOutlined,
  PieChartOutlined
} from '@ant-design/icons';
import knowledgeGraphService, { KGStats } from '../../services/knowledgeGraphService';

const { Title, Text } = Typography;

interface KGStatsPanelProps {
  projectId: string;
}

const KGStatsPanel: React.FC<KGStatsPanelProps> = ({ projectId }) => {
  const [stats, setStats] = useState<KGStats | null>(null);
  const [loading, setLoading] = useState(true);

  // 加载统计数据
  useEffect(() => {
    const loadStats = async () => {
      try {
        setLoading(true);
        const data = await knowledgeGraphService.getKGStats(projectId);
        setStats(data);
      } catch (error) {
        console.error('Failed to load KG stats:', error);
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, [projectId]);

  if (loading) {
    return (
      <Card title="图谱统计" size="small">
        <Spin />
      </Card>
    );
  }

  if (!stats) {
    return (
      <Card title="图谱统计" size="small">
        <Text type="secondary">暂无统计数据</Text>
      </Card>
    );
  }

  // 计算图谱密度
  const density = stats.totalEntities > 0 
    ? (stats.totalRelations / (stats.totalEntities * (stats.totalEntities - 1))) * 100 
    : 0;

  // 获取颜色
  const getProgressColor = (percentage: number) => {
    if (percentage < 30) return '#52c41a';
    if (percentage < 70) return '#faad14';
    return '#f5222d';
  };

  return (
    <Card 
      title={
        <Space>
          <BarChartOutlined />
          图谱统计
        </Space>
      } 
      size="small"
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        {/* 基础统计 */}
        <Row gutter={16}>
          <Col span={12}>
            <Statistic
              title="节点数量"
              value={stats.totalEntities}
              prefix={<NodeIndexOutlined />}
              valueStyle={{ fontSize: '16px' }}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="边数量"
              value={stats.totalRelations}
              prefix={<LinkOutlined />}
              valueStyle={{ fontSize: '16px' }}
            />
          </Col>
        </Row>

        {/* 图谱密度 */}
        <div>
          <Text strong style={{ fontSize: '12px' }}>图谱密度</Text>
          <Progress
            percent={Math.min(density, 100)}
            size="small"
            strokeColor={getProgressColor(density)}
            format={(percent) => `${percent?.toFixed(1)}%`}
          />
          <Text type="secondary" style={{ fontSize: '11px' }}>
            {density < 10 ? '稀疏' : density < 30 ? '适中' : density < 60 ? '密集' : '非常密集'}
          </Text>
        </div>

        {/* 实体类型分布 */}
        <div>
          <Title level={5} style={{ margin: '12px 0 8px 0' }}>
            <PieChartOutlined style={{ marginRight: 4 }} />
            实体类型分布
          </Title>
          <List
            size="small"
            dataSource={stats.entityTypes.slice(0, 5)}
            renderItem={(item) => {
              const percentage = (item.count / stats.totalEntities) * 100;
              return (
                <List.Item style={{ padding: '4px 0' }}>
                  <div style={{ width: '100%' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                      <Text style={{ fontSize: '12px' }}>{item.type}</Text>
                      <Text style={{ fontSize: '12px' }}>{item.count}</Text>
                    </div>
                    <Progress
                      percent={percentage}
                      size="small"
                      showInfo={false}
                      strokeColor="#1890ff"
                    />
                  </div>
                </List.Item>
              );
            }}
          />
          {stats.entityTypes.length > 5 && (
            <Text type="secondary" style={{ fontSize: '11px' }}>
              还有 {stats.entityTypes.length - 5} 种类型...
            </Text>
          )}
        </div>

        {/* 关系类型分布 */}
        <div>
          <Title level={5} style={{ margin: '12px 0 8px 0' }}>
            <LinkOutlined style={{ marginRight: 4 }} />
            关系类型分布
          </Title>
          <List
            size="small"
            dataSource={stats.relationTypes.slice(0, 5)}
            renderItem={(item) => {
              const percentage = (item.count / stats.totalRelations) * 100;
              return (
                <List.Item style={{ padding: '4px 0' }}>
                  <div style={{ width: '100%' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                      <Text style={{ fontSize: '12px' }}>{item.type}</Text>
                      <Text style={{ fontSize: '12px' }}>{item.count}</Text>
                    </div>
                    <Progress
                      percent={percentage}
                      size="small"
                      showInfo={false}
                      strokeColor="#52c41a"
                    />
                  </div>
                </List.Item>
              );
            }}
          />
          {stats.relationTypes.length > 5 && (
            <Text type="secondary" style={{ fontSize: '11px' }}>
              还有 {stats.relationTypes.length - 5} 种关系...
            </Text>
          )}
        </div>

        {/* 图谱质量指标 */}
        <div>
          <Title level={5} style={{ margin: '12px 0 8px 0' }}>质量指标</Title>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>平均连接度:</Text>
              <Text style={{ fontSize: '12px' }}>
                {stats.totalEntities > 0 
                  ? (stats.totalRelations * 2 / stats.totalEntities).toFixed(1)
                  : '0'
                }
              </Text>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>连通性:</Text>
              <Text style={{ fontSize: '12px' }}>
                {density > 5 ? '良好' : density > 1 ? '一般' : '较差'}
              </Text>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>复杂度:</Text>
              <Text style={{ fontSize: '12px' }}>
                {stats.totalEntities > 100 ? '高' : stats.totalEntities > 50 ? '中' : '低'}
              </Text>
            </div>
          </Space>
        </div>

        {/* 建议 */}
        {stats.totalEntities > 0 && (
          <div style={{ 
            background: '#f6ffed', 
            border: '1px solid #b7eb8f', 
            borderRadius: '4px', 
            padding: '8px',
            marginTop: '8px'
          }}>
            <Text style={{ fontSize: '11px', color: '#389e0d' }}>
              💡 建议: {
                density < 1 
                  ? '图谱较为稀疏，可以考虑增加更多关系抽取'
                  : density > 50
                  ? '图谱过于密集，建议使用过滤器简化显示'
                  : '图谱结构良好，适合进行分析和可视化'
              }
            </Text>
          </div>
        )}
      </Space>
    </Card>
  );
};

export default KGStatsPanel;