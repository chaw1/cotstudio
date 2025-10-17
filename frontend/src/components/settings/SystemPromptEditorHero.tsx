import React, { useState, useEffect } from 'react';
import { message } from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  StarOutlined,
  StarFilled,
  MoreOutlined
} from '@ant-design/icons';
import { SystemPromptTemplate } from '../../types';
import { useSettingsStore } from '../../stores/settingsStore';
import { useResponsiveBreakpoint } from '../../hooks/useResponsiveBreakpoint';

// HeroUI imports
import { 
  Card,
  Table,
  Button,
  Modal,
  Input,
  Select,
  Textarea,
  Checkbox,
  Alert,
  Tabs,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  CardHeader,
  CardBody,
  SelectItem,
  Tab,
  Chip,
  Tooltip,
  useDisclosure,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Spinner
} from '@heroui/react';

interface SystemPromptEditorProps {
  onPromptChange?: (prompts: SystemPromptTemplate[]) => void;
}

const SystemPromptEditorHero: React.FC<SystemPromptEditorProps> = ({ onPromptChange }) => {
  const { 
    systemPrompts, 
    loading, 
    loadSystemPrompts, 
    addSystemPrompt, 
    updateSystemPrompt, 
    deleteSystemPrompt 
  } = useSettingsStore();
  
  const { isMobile } = useResponsiveBreakpoint();
  const { isOpen: isEditOpen, onOpen: onEditOpen, onClose: onEditClose } = useDisclosure();
  const { isOpen: isViewOpen, onOpen: onViewOpen, onClose: onViewClose } = useDisclosure();
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure();

  const [selectedPrompt, setSelectedPrompt] = useState<SystemPromptTemplate | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    description: '',
    template: '',
    variables: '',
    is_default: false
  });
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  useEffect(() => {
    loadSystemPrompts();
  }, [loadSystemPrompts]);

  const categories = ['all', ...Array.from(new Set(systemPrompts.map(p => p.category)))];
  const filteredPrompts = selectedCategory === 'all' 
    ? systemPrompts 
    : systemPrompts.filter(p => p.category === selectedCategory);

  const handleEdit = (prompt: SystemPromptTemplate) => {
    setSelectedPrompt(prompt);
    setFormData({
      name: prompt.name,
      category: prompt.category,
      description: prompt.description || '',
      template: prompt.template,
      variables: prompt.variables?.join(', ') || '',
      is_default: prompt.is_default || false
    });
    onEditOpen();
  };

  const handleView = (prompt: SystemPromptTemplate) => {
    setSelectedPrompt(prompt);
    onViewOpen();
  };

  const handleDelete = (prompt: SystemPromptTemplate) => {
    setSelectedPrompt(prompt);
    onDeleteOpen();
  };

  const handleSavePrompt = async () => {
    if (!formData.name.trim() || !formData.template.trim()) {
      message.error('请填写必填字段');
      return;
    }

    setIsLoading(true);
    try {
      const promptData = {
        ...formData,
        variables: formData.variables ? formData.variables.split(',').map(v => v.trim()) : []
      };

      if (selectedPrompt) {
        await updateSystemPrompt(selectedPrompt.name, promptData);
        message.success('模板更新成功');
      } else {
        await addSystemPrompt(promptData);
        message.success('模板创建成功');
      }
      
      onEditClose();
      setFormData({
        name: '',
        category: '',
        description: '',
        template: '',
        variables: '',
        is_default: false
      });
      setSelectedPrompt(null);
      
      if (onPromptChange) {
        onPromptChange(systemPrompts);
      }
    } catch (error) {
      message.error('操作失败');
    } finally {
      setIsLoading(false);
    }
  };

  const confirmDelete = async () => {
    if (!selectedPrompt) return;
    
    setIsLoading(true);
    try {
      await deleteSystemPrompt(selectedPrompt.name);
      message.success('模板删除成功');
      onDeleteClose();
      setSelectedPrompt(null);
      
      if (onPromptChange) {
        onPromptChange(systemPrompts);
      }
    } catch (error) {
      message.error('删除失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateNew = () => {
    setSelectedPrompt(null);
    setFormData({
      name: '',
      category: '',
      description: '',
      template: '',
      variables: '',
      is_default: false
    });
    onEditOpen();
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  const columns = [
    {
      key: 'name',
      label: '名称',
      render: (prompt: SystemPromptTemplate) => (
        <div className="flex items-center gap-2">
          <span className="font-medium">{prompt.name}</span>
          {prompt.is_default && <StarFilled className="text-yellow-500" />}
        </div>
      )
    },
    {
      key: 'category',
      label: '分类',
      render: (prompt: SystemPromptTemplate) => (
        <Chip size="sm" variant="flat" color="primary">
          {prompt.category}
        </Chip>
      )
    },
    {
      key: 'description',
      label: '描述',
      render: (prompt: SystemPromptTemplate) => (
        <Tooltip content={prompt.description || '-'}>
          <span className="truncate max-w-xs">
            {prompt.description || '-'}
          </span>
        </Tooltip>
      )
    },
    {
      key: 'actions',
      label: '操作',
      render: (prompt: SystemPromptTemplate) => (
        <div className="flex gap-1">
          <Button
            isIconOnly
            size="sm"
            variant="light"
            onPress={() => handleView(prompt)}
          >
            <EyeOutlined />
          </Button>
          <Button
            isIconOnly
            size="sm"
            variant="light"
            onPress={() => handleEdit(prompt)}
          >
            <EditOutlined />
          </Button>
          {!prompt.is_default && (
            <Button
              isIconOnly
              size="sm"
              variant="light"
              onPress={() => handleDelete(prompt)}
            >
              <DeleteOutlined />
            </Button>
          )}
        </div>
      )
    }
  ];

  return (
    <div className="system-prompt-editor">
      <Card>
        <CardHeader className="flex justify-between items-center">
          <h3 className="text-lg font-semibold">系统提示词模板</h3>
          <Button
            color="primary"
            startContent={<PlusOutlined />}
            onPress={handleCreateNew}
          >
            新建模板
          </Button>
        </CardHeader>
        <CardBody>
          {systemPrompts.length === 0 ? (
            <Alert
              color="primary"
              title="暂无系统提示词模板"
              description="点击上方按钮创建您的第一个模板"
            />
          ) : (
            <>
              <div className="mb-4">
                <Select
                  label="筛选分类"
                  placeholder="选择分类"
                  size="sm"
                  selectedKeys={[selectedCategory]}
                  onSelectionChange={(keys) => setSelectedCategory(Array.from(keys)[0] as string)}
                >
                  {categories.map((category) => (
                    <SelectItem key={category}>{category}</SelectItem>
                  ))}
                </Select>
              </div>
              <Button
                size="sm"
                onPress={handleCreateNew}
                className="mb-4"
              >
                <PlusOutlined /> 新建模板
              </Button>
              <Table
                aria-label="系统提示词模板表格"
                classNames={{
                  wrapper: "min-h-[200px]",
                  table: "min-h-[120px]",
                }}
              >
                <TableHeader>
                  {columns.map((column) => (
                    <TableColumn key={column.key}>{column.label}</TableColumn>
                  ))}
                </TableHeader>
                <TableBody>
                  {filteredPrompts.map((prompt) => (
                    <TableRow key={prompt.name}>
                      {columns.map((column) => (
                        <TableCell key={column.key}>
                          {column.render(prompt)}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </>
          )}
        </CardBody>
      </Card>

      {/* Edit/Create Modal */}
      <Modal 
        isOpen={isEditOpen} 
        onClose={onEditClose} 
        size="2xl"
        scrollBehavior="inside"
      >
        <ModalContent>
          <ModalHeader>
            {selectedPrompt ? '编辑模板' : '新建模板'}
          </ModalHeader>
          <ModalBody>
            <div className="space-y-4">
              <Input
                label="模板名称"
                placeholder="请输入模板名称"
                value={formData.name}
                onValueChange={(value) => setFormData({...formData, name: value})}
                isRequired
              />
              <Select
                label="分类"
                placeholder="选择或输入分类"
                selectedKeys={formData.category ? [formData.category] : []}
                onSelectionChange={(keys) => setFormData({...formData, category: Array.from(keys)[0] as string})}
                isRequired
              >
                {categories.filter(c => c !== 'all').map((category) => (
                  <SelectItem key={category}>{category}</SelectItem>
                ))}
              </Select>
              <Input
                label="描述"
                placeholder="请输入模板描述"
                value={formData.description}
                onValueChange={(value) => setFormData({...formData, description: value})}
              />
              <Textarea
                label="变量列表"
                placeholder="请输入变量名，用逗号分隔"
                description="例如：name, age, role"
                value={formData.variables}
                onValueChange={(value) => setFormData({...formData, variables: value})}
              />
              <Textarea
                label="模板内容"
                placeholder="请输入提示词模板内容"
                value={formData.template}
                onValueChange={(value) => setFormData({...formData, template: value})}
                minRows={6}
                isRequired
              />
              <Checkbox
                isSelected={formData.is_default}
                onValueChange={(checked) => setFormData({...formData, is_default: checked})}
              >
                设为默认模板
              </Checkbox>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onPress={onEditClose}>
              取消
            </Button>
            <Button 
              color="primary" 
              onPress={handleSavePrompt}
              isLoading={isLoading}
            >
              {selectedPrompt ? '更新' : '创建'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* View Modal */}
      <Modal 
        isOpen={isViewOpen} 
        onClose={onViewClose} 
        size="2xl"
        scrollBehavior="inside"
      >
        <ModalContent>
          <ModalHeader>查看模板详情</ModalHeader>
          <ModalBody>
            {selectedPrompt && (
              <Tabs defaultSelectedKey="template">
                <Tab key="template" title="模板内容">
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium mb-2">基本信息</h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <span className="text-sm text-gray-500">名称：</span>
                          <span>{selectedPrompt.name}</span>
                        </div>
                        <div>
                          <span className="text-sm text-gray-500">分类：</span>
                          <Chip size="sm" variant="flat" color="primary">
                            {selectedPrompt.category}
                          </Chip>
                        </div>
                      </div>
                      {selectedPrompt.description && (
                        <div className="mt-2">
                          <span className="text-sm text-gray-500">描述：</span>
                          <p>{selectedPrompt.description}</p>
                        </div>
                      )}
                    </div>
                    <div>
                      <h4 className="font-medium mb-2">模板内容</h4>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <pre className="whitespace-pre-wrap text-sm">
                          {selectedPrompt.template}
                        </pre>
                      </div>
                    </div>
                    {selectedPrompt.variables && selectedPrompt.variables.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2">变量列表</h4>
                        <div className="flex flex-wrap gap-2">
                          {selectedPrompt.variables.map((variable, index) => (
                            <Chip key={index} size="sm" variant="bordered">
                              {variable}
                            </Chip>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </Tab>
              </Tabs>
            )}
          </ModalBody>
          <ModalFooter>
            <Button onPress={onViewClose}>关闭</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={isDeleteOpen} onClose={onDeleteClose} size="sm">
        <ModalContent>
          <ModalHeader>确认删除</ModalHeader>
          <ModalBody>
            <p>确定要删除模板 "{selectedPrompt?.name}" 吗？此操作不可撤销。</p>
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onPress={onDeleteClose}>
              取消
            </Button>
            <Button 
              color="danger" 
              onPress={confirmDelete}
              isLoading={isLoading}
            >
              删除
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
};

export default SystemPromptEditorHero;