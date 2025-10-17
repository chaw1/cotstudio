import React, { useState } from 'react';
import { 
  Card, 
  Descriptions, 
  Button, 
  Space, 
  Typography, 
  Tag, 
  Divider,
  Collapse,
  List,
  Tooltip,
  Form,
  Input,
  Select
} from 'antd';
import { 
  CloseOutlined, 
  EditOutlined, 
  DeleteOutlined,
  NodeIndexOutlined,
  LinkOutlined,
  InfoCircleOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { KGEntity, KGRelation } from '../../types';
import ModalContainer from '../common/ModalContainer';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;
const { Option } = Select;

interface KGEntityPanelProps {
  entity: KGEntity | null;
  relation: KGRelation | null;
  onClose: () => void;
  onHighlightNeighbors: (entityId: string) => void;
  onEdit?: (entity: KGEntity) => void;
  onDelete?: (entityId: string) => void;
}

const KGEntityPanel: React.FC<KGEntityPanelProps> = ({
  entity,
  relation,
  onClose,
  onHighlightNeighbors,
  onEdit,
  onDelete
}) => {
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [deleteModalVisible, setDeleteModalVisible] = useState(false);
  const [form] = Form.useForm();

  // 处理编辑
  const handleEdit = () => {
    if (entity) {
      form.setFieldsValue({
        label: entity.label,
        type: entity.type,
        properties: JSON.stringify(entity.properties, null, 2)
      });
      setEditModalVisible(true);
    }
  };

  // 提交编辑
  const handleEditSubmit = async () => {
    try {
      const values = await form.validateFields();
      const updatedEntity: KGEntity = {
        ...entity!,
        label: values.label,
        type: values.type,
        properties: JSON.parse(values.properties)
      };
      onEdit?.(updatedEntity);
      setEditModalVisible(false);
    } catch (error) {
      console.error('Edit validation failed:', error);
    }
  };

  // 处理删除
  const handleDelete = () => {
    if (entity) {
      onDelete?.(entity.id);
      setDeleteModalVisible(false);
      onClose();
    }
  };

  // 渲染实体详情
  const renderEntityDetails = (entity: KGEntity) => (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          <NodeIndexOutlined style={{ marginRight: 8, color: '#1890ff' }} />
          实体详情
        </Title>
        <Space>
          <Tooltip title="高亮邻居节点">
            <Button 
              icon={<EyeOutlined />} 
              size="small"
              onClick={() => onHighlightNeighbors(entity.id)}
            />
          </Tooltip>
          {onEdit && (
            <Tooltip title="编辑实体">
              <Button 
                icon={<EditOutlined />} 
                size="small"
                onClick={handleEdit}
              />
            </Tooltip>
          )}
          {onDelete && (
            <Tooltip title="删除实体">
              <Button 
                icon={<DeleteOutlined />} 
                size="small"
                danger
                onClick={() => setDeleteModalVisible(true)}
              />
            </Tooltip>
          )}
          <Button 
            icon={<CloseOutlined />} 
            size="small"
            onClick={onClose}
          />
        </Space>
      </div>

      <Descriptions column={1} size="small" bordered>
        <Descriptions.Item label="ID">
          <Text code copyable={{ text: entity.id }}>
            {entity.id.substring(0, 8)}...
          </Text>
        </Descriptions.Item>
        <Descriptions.Item label="标签">
          <Text strong>{entity.label}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="类型">
          <Tag color="blue">{entity.type}</Tag>
        </Descriptions.Item>
      </Descriptions>

      {/* 属性信息 */}
      {Object.keys(entity.properties).length > 0 && (
        <>
          <Divider style={{ margin: '16px 0' }} />
          <Collapse size="small" ghost>
            <Panel 
              header={
                <Space>
                  <InfoCircleOutlined />
                  <Text strong>属性信息</Text>
                  <Tag>{Object.keys(entity.properties).length} 个属性</Tag>
                </Space>
              } 
              key="properties"
            >
              <List
                size="small"
                dataSource={Object.entries(entity.properties)}
                renderItem={([key, value]) => (
                  <List.Item>
                    <List.Item.Meta
                      title={<Text strong>{key}</Text>}
                      description={
                        <div>
                          {typeof value === 'object' ? (
                            <pre style={{ 
                              fontSize: '11px', 
                              margin: 0, 
                              whiteSpace: 'pre-wrap',
                              maxHeight: '100px',
                              overflow: 'auto'
                            }}>
                              {JSON.stringify(value, null, 2)}
                            </pre>
                          ) : (
                            <Text>{String(value)}</Text>
                          )}
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            </Panel>
          </Collapse>
        </>
      )}

      {/* 统计信息 */}
      <Divider style={{ margin: '16px 0' }} />
      <div>
        <Text strong>统计信息</Text>
        <div style={{ marginTop: '8px' }}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text type="secondary">连接数:</Text>
              <Text>{entity.properties.connections || 0}</Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text type="secondary">重要性:</Text>
              <Text>{entity.properties.importance || 'N/A'}</Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text type="secondary">置信度:</Text>
              <Text>{entity.properties.confidence || 'N/A'}</Text>
            </div>
          </Space>
        </div>
      </div>
    </div>
  );

  // 渲染关系详情
  const renderRelationDetails = (relation: KGRelation) => (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          <LinkOutlined style={{ marginRight: 8, color: '#52c41a' }} />
          关系详情
        </Title>
        <Button 
          icon={<CloseOutlined />} 
          size="small"
          onClick={onClose}
        />
      </div>

      <Descriptions column={1} size="small" bordered>
        <Descriptions.Item label="ID">
          <Text code copyable={{ text: relation.id }}>
            {relation.id.substring(0, 8)}...
          </Text>
        </Descriptions.Item>
        <Descriptions.Item label="类型">
          <Tag color="green">{relation.type}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="源节点">
          <Text code>{relation.source}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="目标节点">
          <Text code>{relation.target}</Text>
        </Descriptions.Item>
      </Descriptions>

      {/* 关系属性 */}
      {Object.keys(relation.properties).length > 0 && (
        <>
          <Divider style={{ margin: '16px 0' }} />
          <Collapse size="small" ghost>
            <Panel 
              header={
                <Space>
                  <InfoCircleOutlined />
                  <Text strong>关系属性</Text>
                  <Tag>{Object.keys(relation.properties).length} 个属性</Tag>
                </Space>
              } 
              key="properties"
            >
              <List
                size="small"
                dataSource={Object.entries(relation.properties)}
                renderItem={([key, value]) => (
                  <List.Item>
                    <List.Item.Meta
                      title={<Text strong>{key}</Text>}
                      description={
                        <div>
                          {typeof value === 'object' ? (
                            <pre style={{ 
                              fontSize: '11px', 
                              margin: 0, 
                              whiteSpace: 'pre-wrap',
                              maxHeight: '100px',
                              overflow: 'auto'
                            }}>
                              {JSON.stringify(value, null, 2)}
                            </pre>
                          ) : (
                            <Text>{String(value)}</Text>
                          )}
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            </Panel>
          </Collapse>
        </>
      )}
    </div>
  );

  return (
    <>
      <Card 
        style={{ height: '100%' }}
        bodyStyle={{ padding: '16px', height: 'calc(100% - 57px)', overflowY: 'auto' }}
      >
        {entity && renderEntityDetails(entity)}
        {relation && renderRelationDetails(relation)}
        {!entity && !relation && (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Text type="secondary">选择节点或边查看详情</Text>
          </div>
        )}
      </Card>

      {/* 编辑实体模态框 */}
      <ModalContainer
        visible={editModalVisible}
        onClose={() => setEditModalVisible(false)}
        title="编辑实体"
        width={600}
        footer={[
          <Button key="cancel" onClick={() => setEditModalVisible(false)}>
            取消
          </Button>,
          <Button key="ok" type="primary" onClick={handleEditSubmit}>
            确定
          </Button>
        ]}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="label"
            label="标签"
            rules={[{ required: true, message: '请输入实体标签' }]}
          >
            <Input placeholder="输入实体标签" />
          </Form.Item>
          
          <Form.Item
            name="type"
            label="类型"
            rules={[{ required: true, message: '请选择实体类型' }]}
          >
            <Select placeholder="选择实体类型">
              <Option value="Person">人物</Option>
              <Option value="Organization">组织</Option>
              <Option value="Location">地点</Option>
              <Option value="Concept">概念</Option>
              <Option value="Event">事件</Option>
              <Option value="Document">文档</Option>
              <Option value="Technology">技术</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="properties"
            label="属性 (JSON格式)"
            rules={[
              { required: true, message: '请输入属性信息' },
              {
                validator: (_, value) => {
                  try {
                    JSON.parse(value);
                    return Promise.resolve();
                  } catch {
                    return Promise.reject(new Error('请输入有效的JSON格式'));
                  }
                }
              }
            ]}
          >
            <Input.TextArea 
              rows={8} 
              placeholder='{"key": "value"}' 
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>
        </Form>
      </ModalContainer>

      {/* 删除确认模态框 */}
      <ModalContainer
        visible={deleteModalVisible}
        onClose={() => setDeleteModalVisible(false)}
        title="确认删除"
        footer={[
          <Button key="cancel" onClick={() => setDeleteModalVisible(false)}>
            取消
          </Button>,
          <Button key="ok" type="primary" danger onClick={handleDelete}>
            删除
          </Button>
        ]}
      >
        <p>确定要删除实体 <Text strong>"{entity?.label}"</Text> 吗？</p>
        <p><Text type="secondary">此操作不可撤销，相关的关系也会被删除。</Text></p>
      </ModalContainer>
    </>
  );
};

export default KGEntityPanel;