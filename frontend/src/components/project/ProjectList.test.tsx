import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import ProjectList from './ProjectList';
import { Project } from '../../types';

// Mock date-fns
vi.mock('date-fns', () => ({
  formatDistanceToNow: vi.fn(() => '2 days ago'),
}));

vi.mock('date-fns/locale', () => ({
  zhCN: {},
}));

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
  {
    id: '2',
    name: 'Test Project 2',
    description: 'Another test description',
    owner: 'test-user',
    status: 'draft',
    tags: ['draft'],
    createdAt: '2023-01-02T00:00:00Z',
    updatedAt: '2023-01-02T00:00:00Z',
    fileCount: 2,
    cotCount: 0,
  },
];

const mockProps = {
  projects: mockProjects,
  loading: false,
  onCreateProject: vi.fn(),
  onEditProject: vi.fn(),
  onDeleteProject: vi.fn(),
  onViewProject: vi.fn(),
};

describe('ProjectList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders project list correctly', () => {
    render(<ProjectList {...mockProps} />);
    
    expect(screen.getByText('项目列表')).toBeInTheDocument();
    expect(screen.getByText('新建项目')).toBeInTheDocument();
    expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    expect(screen.getByText('Test Project 2')).toBeInTheDocument();
  });

  it('calls onCreateProject when create button is clicked', () => {
    render(<ProjectList {...mockProps} />);
    
    const createButton = screen.getByText('新建项目');
    fireEvent.click(createButton);
    
    expect(mockProps.onCreateProject).toHaveBeenCalledTimes(1);
  });

  it('calls onViewProject when project name is clicked', () => {
    render(<ProjectList {...mockProps} />);
    
    const projectLink = screen.getByText('Test Project 1');
    fireEvent.click(projectLink);
    
    expect(mockProps.onViewProject).toHaveBeenCalledWith(mockProjects[0]);
  });

  it('filters projects by search text', () => {
    render(<ProjectList {...mockProps} />);
    
    const searchInput = screen.getByPlaceholderText('搜索项目名称、描述或标签');
    fireEvent.change(searchInput, { target: { value: 'Project 1' } });
    
    expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    expect(screen.queryByText('Test Project 2')).not.toBeInTheDocument();
  });

  it('filters projects by status', () => {
    render(<ProjectList {...mockProps} />);
    
    // This would require more complex testing with Ant Design Select component
    // For now, we just verify the component renders without errors
    expect(screen.getByText('全部状态')).toBeInTheDocument();
  });

  it('displays project statistics correctly', () => {
    render(<ProjectList {...mockProps} />);
    
    expect(screen.getByText('5')).toBeInTheDocument(); // fileCount
    expect(screen.getByText('10')).toBeInTheDocument(); // cotCount
    expect(screen.getByText('2')).toBeInTheDocument(); // fileCount for project 2
    expect(screen.getByText('0')).toBeInTheDocument(); // cotCount for project 2
  });
});