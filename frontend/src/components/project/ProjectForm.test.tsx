import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import ProjectForm from './ProjectForm';
import { Project } from '../../types';

const mockProject: Project = {
  id: '1',
  name: 'Test Project',
  description: 'Test description',
  owner: 'test-user',
  status: 'active',
  tags: ['test', 'demo'],
  createdAt: '2023-01-01T00:00:00Z',
  updatedAt: '2023-01-01T00:00:00Z',
  fileCount: 5,
  cotCount: 10,
};

const mockProps = {
  visible: true,
  project: null,
  loading: false,
  onSubmit: vi.fn(),
  onCancel: vi.fn(),
};

describe('ProjectForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders create form correctly', () => {
    render(<ProjectForm {...mockProps} />);
    
    expect(screen.getByText('新建项目')).toBeInTheDocument();
    expect(screen.getByText('创建')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('请输入项目名称')).toBeInTheDocument();
  });

  it('renders edit form correctly', () => {
    render(<ProjectForm {...mockProps} project={mockProject} />);
    
    expect(screen.getByText('编辑项目')).toBeInTheDocument();
    expect(screen.getByText('更新')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Project')).toBeInTheDocument();
  });

  it('calls onCancel when cancel button is clicked', () => {
    render(<ProjectForm {...mockProps} />);
    
    const cancelButton = screen.getByText('取消');
    fireEvent.click(cancelButton);
    
    expect(mockProps.onCancel).toHaveBeenCalledTimes(1);
  });

  it('validates required fields', async () => {
    render(<ProjectForm {...mockProps} />);
    
    const submitButton = screen.getByText('创建');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('请输入项目名称')).toBeInTheDocument();
    });
  });

  it('submits form with correct data', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<ProjectForm {...mockProps} onSubmit={onSubmit} />);
    
    const nameInput = screen.getByPlaceholderText('请输入项目名称');
    const descriptionInput = screen.getByPlaceholderText('请输入项目描述（可选）');
    
    fireEvent.change(nameInput, { target: { value: 'New Project' } });
    fireEvent.change(descriptionInput, { target: { value: 'New description' } });
    
    const submitButton = screen.getByText('创建');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        name: 'New Project',
        description: 'New description',
        status: 'draft',
        tags: [],
      });
    });
  });

  it('does not render when not visible', () => {
    render(<ProjectForm {...mockProps} visible={false} />);
    
    expect(screen.queryByText('新建项目')).not.toBeInTheDocument();
  });
});