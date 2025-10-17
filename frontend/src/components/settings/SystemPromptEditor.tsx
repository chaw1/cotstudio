import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Select,
  Space,
  message,
  Table,
  Tag,
  Popconfirm,
  Alert,
  Tabs,
  Row,
  Col
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { Breakpoint } from 'antd/es/_util/responsiveObserver';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  StarOutlined,
  StarFilled
} from '@ant-design/icons';
import { SystemPromptTemplate } from '../../types';
import { useSettingsStore } from '../../stores/settingsStore';
import ModalContainer from '../common/ModalContainer';
import { useResponsiveBreakpoint } from '../../hooks/useResponsiveBreakpoint';

const { Option } = Select;
const { TextArea } = Input;

interface SystemPromptEditorProps {
  onPromptChange?: (prompts: SystemPromptTemplate[]) => void;
}

const SystemPromptEditor: React.FC<SystemPromptEditorProps> = ({ onPromptChange }) => {
  const {
    systemPrompts,
    promptCategories,
    loading,
    error,
    updateSystemPrompt,
    addSystemPrompt,
    deleteSystemPrompt,
    clearError
  } = useSettingsStore();
  
  const { isMobile, isTablet } = useResponsiveBreakpoint();

  const [form] = Form.useForm();
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<SystemPromptTemplate | null>(null);
  const [viewingPrompt, setViewingPrompt] = useState<SystemPromptTemplate | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  useEffect(() => {
    if (error) {
      message.error(error);
      clearError();
    }
  }, [error, clearError]);

  useEffect(() => {
    onPromptChange?.(systemPrompts);
  }, [systemPrompts, onPromptChange]);

  const handleAddPrompt = () => {
    setEditingPrompt(null);
    form.resetFields();
    setEditModalVisible(true);
  };

  const handleEditPrompt = (prompt: SystemPromptTemplate) => {
    setEditingPrompt(prompt);
    form.setFieldsValue(prompt);
    setEditModalVisible(true);
  };

  const handleViewPrompt = (prompt: SystemPromptTemplate) => {
    setViewingPrompt(prompt);
    setViewModalVisible(true);
  };

  const handleSavePrompt = async (values: any) => {
    try {
      const prompt: SystemPromptTemplate = {
        name: values.name,
        description: values.description,
        template: values.template,
        variables: values.variables ? values.variables.split(',').map((v: string) => v.trim()) : [],
        category: values.category,
        is_default: values.is_default || false
      };

      if (editingPrompt) {
        await updateSystemPrompt(editingPrompt.name, prompt);
        message.success('提示词模板已更新');
      } else {
        await addSystemPrompt(prompt);
        message.success('提示词模板已添加');
      }

      setEditModalVisible(false);
      form.resetFields();
    } catch (error) {
      message.error('保存提示词模板失败');
    }
  };

  const handleDeletePrompt = async (name: string) => {
    try {
      await deleteSystemPrompt(name);
      message.success('提示词模板已删除');
    } catch (error) {
      message.error('删除提示词模板失败');
    }
  };

  const handleSetDefault = async (prompt: SystemPromptTemplate) => {
    try {
      // 先取消同类别的其他默认模板
      const updatedPrompts = systemPrompts.map(p => ({
        ...p,
        is_default: p.category === prompt.category ? p.name === prompt.name : p.is_default
      }));

      // 更新当前模板为默认
      const updatedPrompt = { ...prompt, is_default: true };
      await updateSystemPrompt(prompt.name, updatedPrompt);
      message.success('已设置为默认模板');
    } catch (error) {
      message.error('设置默认模板失败');
    }
  };

  const getFilteredPrompts = () => {
    if (selectedCategory === 'all') {
      return systemPrompts;
    }
    return systemPrompts.filter(p => p.category === selectedCategory);
  };

  const columns: ColumnsType<SystemPromptTemplate> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: isMobile ? 100 : 150,
      fixed: 'left' as const,
      render: (text: string, record: SystemPromptTemplate) => (
        <Space size="small">
          <span style={{ fontSize: isMobile ? '12px' : '14px' }}>{text}</span>
          {record.is_default && <StarFilled style={{ color: '#faad14', fontSize: '12px' }} />}
        </Space>
      )
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: isMobile ? 80 : 100,
      responsive: ['sm' as Breakpoint],
      render: (category: string) => (
        <Tag 
          color="blue" 
          style={{ fontSize: isMobile ? '10px' : '12px' }}
        >
          {category}
        </Tag>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: isMobile ? 120 : 200,
      ellipsis: true,
      responsive: ['md' as Breakpoint],
      render: (text: string) => (
        <span style={{ fontSize: isMobile ? '12px' : '14px' }}>
          {text || '-'}
        </span>
      )
    },
    {
      title: '变量',
      dataIndex: 'variables',
      key: 'variables',
      width: isMobile ? 100 : 150,
      responsive: ['lg' as Breakpoint],
      render: (variables: string[]) => (
        <Space wrap size="small">
          {variables.slice(0, isMobile ? 1 : 3).map(variable => (
            <Tag 
              key={variable} 
              color="green"
              style={{ fontSize: isMobile ? '10px' : '11px' }}
            >
              {variable}
            </Tag>
          ))}
          {variables.length > (isMobile ? 1 : 3) && (
            <Tag style={{ fontSize: isMobile ? '10px' : '11px' }}>
              +{variables.length - (isMobile ? 1 : 3)}
            </Tag>
          )}
        </Space>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: isMobile ? 120 : 200,
      fixed: 'right' as const,
      render: (_, record: SystemPromptTemplate) => (
        <Space size="small" wrap>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewPrompt(record)}
            style={{ fontSize: isMobile ? '11px' : '12px' }}
          >
            {isMobile ? '' : '查看'}
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditPrompt(record)}
            style={{ fontSize: isMobile ? '11px' : '12px' }}
          >
            {isMobile ? '' : '编辑'}
          </Button>
          {!record.is_default && (
            <Button
              size="small"
              icon={<StarOutlined />}
              onClick={() => handleSetDefault(record)}
              style={{ fontSize: isMobile ? '11px' : '12px' }}
            >
              {isMobile ? '' : '默认'}
            </Button>
          )}
          <Popconfirm
            title="确定要删除这个提示词模板吗？"
            onConfirm={() => handleDeletePrompt(record.name)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              size="small"
              danger
              icon={<DeleteOutlined />}
              style={{ fontSize: isMobile ? '11px' : '12px' }}
            >
              {isMobile ? '' : '删除'}
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  const renderPromptPreview = (template: string, variables: string[]) => {
    let preview = template;
    variables.forEach(variable => {
      preview = preview.replace(
        new RegExp(`{${variable}}`, 'g'),
        `<span style="background: #e6f7ff; padding: 2px 4px; border-radius: 2px;">{${variable}}</span>`
      );
    });
    return <div dangerouslySetInnerHTML={{ __html: preview }} />;
  };

  return (
    <div>
      <Alert
        message="系统提示词管理"
        description="管理用于LLM生成的系统提示词模板。支持变量替换，使用 {变量名} 格式。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Card
        className="modern-card responsive-card"
        title={
          <span style={{ fontSize: isMobile ? '14px' : '16px' }}>
            提示词模板
          </span>
        }
        extra={
          <Space 
            direction={isMobile ? 'vertical' : 'horizontal'}
            size="small"
            style={{ width: isMobile ? '100%' : 'auto' }}
          >
            <Select
              value={selectedCategory}
              onChange={setSelectedCategory}
              style={{ width: isMobile ? '100%' : 150 }}
              size={isMobile ? 'small' : 'middle'}
            >
              <Option value="all">全部分类</Option>
              {promptCategories.map(category => (
                <Option key={category} value={category}>{category}</Option>
              ))}
            </Select>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAddPrompt}
              size={isMobile ? 'small' : 'middle'}
              className="modern-button"
              style={{ width: isMobile ? '100%' : 'auto' }}
            >
              添加模板
            </Button>
          </Space>
        }
      >
        <div className="responsive-table">
          <Table
            columns={columns}
            dataSource={getFilteredPrompts()}
            rowKey="name"
            loading={loading}
            scroll={{ x: 800 }}
            size={isMobile ? 'small' : 'middle'}
            pagination={{
              pageSize: isMobile ? 5 : 10,
              showSizeChanger: !isMobile,
              showQuickJumper: !isMobile,
              responsive: true,
              showTotal: (total, range) =>
                `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            }}
          />
        </div>
      </Card>

      {/* 编辑/添加模态框 */}
      <ModalContainer
        visible={editModalVisible}
        onClose={() => setEditModalVisible(false)}
        title={editingPrompt ? '编辑提示词模板' : '添加提示词模板'}
        width={800}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSavePrompt}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="模板名称"
                rules={[{ required: true, message: '请输入模板名称' }]}
              >
                <Input placeholder="输入模板名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="category"
                label="分类"
                rules={[{ required: true, message: '请选择分类' }]}
              >
                <Select placeholder="选择分类">
                  <Option value="question_generation">问题生成</Option>
                  <Option value="answer_generation">答案生成</Option>
                  <Option value="knowledge_extraction">知识抽取</Option>
                  <Option value="general">通用</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="描述"
          >
            <Input placeholder="输入模板描述" />
          </Form.Item>

          <Form.Item
            name="variables"
            label="变量列表"
            help="用逗号分隔多个变量，如: text_content, question, answer"
          >
            <Input placeholder="text_content, question" />
          </Form.Item>

          <Form.Item
            name="template"
            label="模板内容"
            rules={[{ required: true, message: '请输入模板内容' }]}
          >
            <TextArea
              rows={10}
              placeholder="输入提示词模板，使用 {变量名} 格式插入变量"
            />
          </Form.Item>

          <Form.Item name="is_default" valuePropName="checked">
            <input type="checkbox" /> 设为该分类的默认模板
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                保存
              </Button>
              <Button onClick={() => setEditModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </ModalContainer>

      {/* 查看模态框 */}
      <ModalContainer
        visible={viewModalVisible}
        onClose={() => setViewModalVisible(false)}
        title="查看提示词模板"
        width={800}
        footer={[
          <Button key="close" onClick={() => setViewModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {viewingPrompt && (
          <div>
            <Tabs 
              defaultActiveKey="template"
              items={[
                {
                  key: 'template',
                  label: '模板内容',
                  children: (
                    <div>
                      <div style={{ marginBottom: 16 }}>
                        <h4>基本信息</h4>
                        <p><strong>名称:</strong> {viewingPrompt.name}</p>
                        <p><strong>分类:</strong> <Tag color="blue">{viewingPrompt.category}</Tag></p>
                        <p><strong>描述:</strong> {viewingPrompt.description}</p>
                        <p><strong>是否默认:</strong> {viewingPrompt.is_default ? '是' : '否'}</p>
                      </div>

                      <div style={{ marginBottom: 16 }}>
                        <h4>变量列表</h4>
                        <Space wrap>
                          {viewingPrompt.variables.map(variable => (
                            <Tag key={variable} color="green">{variable}</Tag>
                          ))}
                        </Space>
                      </div>

                      <div>
                        <h4>模板内容</h4>
                        <div style={{
                          background: '#f5f5f5',
                          padding: 16,
                          borderRadius: 4,
                          whiteSpace: 'pre-wrap'
                        }}>
                          {viewingPrompt.template}
                        </div>
                      </div>
                    </div>
                  )
                },
                {
                  key: 'preview',
                  label: '预览效果',
                  children: (
                    <div>
                      <h4>变量替换预览</h4>
                      <div style={{
                        background: '#f5f5f5',
                        padding: 16,
                        borderRadius: 4,
                        lineHeight: 1.6
                      }}>
                        {renderPromptPreview(viewingPrompt.template, viewingPrompt.variables)}
                      </div>
                    </div>
                  )
                }
              ]}
            />
          </div>
        )}
      </ModalContainer>
    </div>
  );
};

export default SystemPromptEditor;