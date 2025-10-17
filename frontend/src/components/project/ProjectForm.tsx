import React, { useEffect } from 'react';
import {
  Form,
  Input,
  Select,
  Button,
  Space,
  Tag,
} from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { Project } from '../../types';
import ModalContainer from '../common/ModalContainer';

const { TextArea } = Input;
const { Option } = Select;

interface ProjectFormProps {
  visible: boolean;
  project?: Project | null;
  loading: boolean;
  onSubmit: (values: any) => Promise<void>;
  onCancel: () => void;
}

const ProjectForm: React.FC<ProjectFormProps> = ({
  visible,
  project,
  loading,
  onSubmit,
  onCancel,
}) => {
  const [form] = Form.useForm();

  useEffect(() => {
    if (visible) {
      if (project) {
        // 编辑模式
        form.setFieldsValue({
          name: project.name,
          description: project.description,
          status: project.status,
          tags: project.tags,
        });
      } else {
        // 新建模式
        form.resetFields();
        form.setFieldsValue({
          status: 'draft',
          tags: [],
        });
      }
    }
  }, [visible, project, form]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      await onSubmit(values);
      form.resetFields();
    } catch (error) {
      console.error('Form validation failed:', error);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  // 预定义标签
  const predefinedTags = [
    '学术研究',
    '数据标注',
    '知识图谱',
    '机器学习',
    '自然语言处理',
    '文档处理',
    '实验项目',
    '生产环境',
  ];

  return (
    <ModalContainer
      visible={visible}
      onClose={handleCancel}
      title={project ? '编辑项目' : '新建项目'}
      width={600}
      footer={[
        <Button key="cancel" onClick={handleCancel}>
          取消
        </Button>,
        <Button
          key="submit"
          type="primary"
          loading={loading}
          onClick={handleSubmit}
        >
          {project ? '更新' : '创建'}
        </Button>,
      ]}
    >
      <Form
        form={form}
        layout="vertical"
        requiredMark={false}
      >
        <Form.Item
          name="name"
          label="项目名称"
          rules={[
            { required: true, message: '请输入项目名称' },
            { min: 2, message: '项目名称至少2个字符' },
            { max: 50, message: '项目名称不能超过50个字符' },
          ]}
        >
          <Input placeholder="请输入项目名称" />
        </Form.Item>

        <Form.Item
          name="description"
          label="项目描述"
          rules={[
            { max: 500, message: '项目描述不能超过500个字符' },
          ]}
        >
          <TextArea
            rows={4}
            placeholder="请输入项目描述（可选）"
            showCount
            maxLength={500}
          />
        </Form.Item>

        <Form.Item
          name="status"
          label="项目状态"
          rules={[{ required: true, message: '请选择项目状态' }]}
        >
          <Select placeholder="请选择项目状态">
            <Option value="draft">草稿</Option>
            <Option value="active">活跃</Option>
            <Option value="archived">已归档</Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="tags"
          label="项目标签"
        >
          <Select
            mode="tags"
            placeholder="选择或输入标签"
            style={{ width: '100%' }}
            tokenSeparators={[',']}
            maxTagCount={10}
            popupRender={(menu) => (
              <div>
                {menu}
                <div style={{ padding: '8px 12px', borderTop: '1px solid #f0f0f0' }}>
                  <div style={{ marginBottom: 8, fontSize: '12px', color: '#666' }}>
                    常用标签：
                  </div>
                  <Space wrap>
                    {predefinedTags.map((tag) => (
                      <Tag
                        key={tag}
                        style={{ cursor: 'pointer' }}
                        onClick={() => {
                          const currentTags = form.getFieldValue('tags') || [];
                          if (!currentTags.includes(tag)) {
                            form.setFieldsValue({
                              tags: [...currentTags, tag],
                            });
                          }
                        }}
                      >
                        <PlusOutlined style={{ fontSize: '10px' }} /> {tag}
                      </Tag>
                    ))}
                  </Space>
                </div>
              </div>
            )}
          >
            {predefinedTags.map((tag) => (
              <Option key={tag} value={tag}>
                {tag}
              </Option>
            ))}
          </Select>
        </Form.Item>
      </Form>
    </ModalContainer>
  );
};

export default ProjectForm;