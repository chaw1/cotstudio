import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { ProjectList, ProjectForm, FileUpload } from '../../components/project';
import { Project, FileInfo } from '../../types';

// Mock date-fns
vi.mock('date-fns', () => ({
  formatDistanceToNow: vi.fn(() => '2 days ago'),
}));

vi.mock('date-fns/locale', () => ({
  zhCN: {},
}));

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ConfigProvider locale={zhCN}>
    <DndProvider backend={HTML5Backend}>
      {children}
    </DndProvider>
  </ConfigProvider>
);

const mockProjects: Project[] = [
  {
    id: '1',
    name: 'Test Project 1',
    description: 'Test description',
    owner: 'test-user',
    status: 'active',
    tags: ['test', 'demo'],
    createdAt: '2023-01-01T00:00:00Z',
    updatedAt: '2023-01-01T00:00:00Z',
    fileCount: 5,
    cotCount: 10,
  },
];

const mockFiles: FileInfo[] = [
  {
    id: 'file-1',
    projectId: '1',
    filename: 'test.pdf',
    filePath: '/files/test.pdf',
    fileHash: 'abc123',
    size: 1024000,
    mimeType: 'application/pdf',
    ocrStatus: 'completed',
    createdAt: '2023-01-01T00:00:00Z',
    updatedAt: '2023-01-01T00:00:00Z',
  },
];

describe('Project Management Integration', () => {
  it('renders project list with all components', () => {
    const mockProps = {
      projects: mockProjects,
      loading: false,
      onCreateProject: vi.fn(),
      onEditProject: vi.fn(),
      onDeleteProject: vi.fn(),
      onViewProject: vi.fn(),
    };

    render(
      <TestWrapper>
        <ProjectList {...mockProps} />
      </TestWrapper>
    );

    expect(screen.getByText('项目列表')).toBeInTheDocument();
    expect(screen.getByText('新建项目')).toBeInTheDocument();
    expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    expect(screen.getByText('活跃')).toBeInTheDocument();
  });

  it('renders project form correctly', () => {
    const mockProps = {
      visible: true,
      project: null,
      loading: false,
      onSubmit: vi.fn(),
      onCancel: vi.fn(),
    };

    render(
      <TestWrapper>
        <ProjectForm {...mockProps} />
      </TestWrapper>
    );

    expect(screen.getByText('新建项目')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('请输入项目名称')).toBeInTheDocument();
    expect(screen.getByText('创建')).toBeInTheDocument();
  });

  it('renders file upload component correctly', () => {
    const mockProps = {
      projectId: '1',
      files: mockFiles,
      loading: false,
      onUpload: vi.fn(),
      onDelete: vi.fn(),
      onRefresh: vi.fn(),
    };

    render(
      <TestWrapper>
        <FileUpload {...mockProps} />
      </TestWrapper>
    );

    expect(screen.getByText('文件管理')).toBeInTheDocument();
    expect(screen.getByText('点击或拖拽文件到此区域上传')).toBeInTheDocument();
    expect(screen.getByText('test.pdf')).toBeInTheDocument();
    expect(screen.getByText('已完成')).toBeInTheDocument();
  });

  it('handles project creation flow', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const mockProps = {
      visible: true,
      project: null,
      loading: false,
      onSubmit,
      onCancel: vi.fn(),
    };

    render(
      <TestWrapper>
        <ProjectForm {...mockProps} />
      </TestWrapper>
    );

    const nameInput = screen.getByPlaceholderText('请输入项目名称');
    const descriptionInput = screen.getByPlaceholderText('请输入项目描述（可选）');
    
    fireEvent.change(nameInput, { target: { value: 'New Test Project' } });
    fireEvent.change(descriptionInput, { target: { value: 'New test description' } });

    const submitButton = screen.getByText('创建');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        name: 'New Test Project',
        description: 'New test description',
        status: 'draft',
        tags: [],
      });
    });
  });

  it('displays file information correctly', () => {
    const mockProps = {
      projectId: '1',
      files: mockFiles,
      loading: false,
      onUpload: vi.fn(),
      onDelete: vi.fn(),
      onRefresh: vi.fn(),
    };

    render(
      <TestWrapper>
        <FileUpload {...mockProps} />
      </TestWrapper>
    );

    expect(screen.getByText('test.pdf')).toBeInTheDocument();
    expect(screen.getByText('已完成')).toBeInTheDocument();
    expect(screen.getByText('1000.00 KB')).toBeInTheDocument();
    expect(screen.getByText('application/pdf')).toBeInTheDocument();
  });
});