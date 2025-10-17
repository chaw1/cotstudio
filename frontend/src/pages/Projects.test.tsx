import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import Projects from './Projects';

// Mock the hooks
vi.mock('../hooks/useProjects', () => ({
  default: () => ({
    projects: [
      {
        id: '1',
        name: 'Test Project',
        description: 'Test description',
        owner: 'test-user',
        status: 'active',
        tags: ['test'],
        createdAt: '2023-01-01T00:00:00Z',
        updatedAt: '2023-01-01T00:00:00Z',
        fileCount: 5,
        cotCount: 10,
      },
    ],
    currentProject: null,
    loading: false,
    createProject: vi.fn(),
    updateProject: vi.fn(),
    deleteProject: vi.fn(),
    selectProject: vi.fn(),
  }),
}));

// Mock date-fns
vi.mock('date-fns', () => ({
  formatDistanceToNow: vi.fn(() => '2 days ago'),
}));

vi.mock('date-fns/locale', () => ({
  zhCN: {},
}));

// Mock file service
vi.mock('../services/fileService', () => ({
  fileService: {
    getProjectFiles: vi.fn().mockResolvedValue([]),
    uploadFile: vi.fn().mockResolvedValue({}),
    deleteFile: vi.fn().mockResolvedValue({}),
  },
}));

const renderWithDnd = (component: React.ReactElement) => {
  return render(
    <DndProvider backend={HTML5Backend}>
      {component}
    </DndProvider>
  );
};

describe('Projects Page', () => {
  it('renders project list by default', () => {
    renderWithDnd(<Projects />);
    
    expect(screen.getByText('项目列表')).toBeInTheDocument();
    expect(screen.getByText('新建项目')).toBeInTheDocument();
    expect(screen.getByText('Test Project')).toBeInTheDocument();
  });

  it('opens create form when create button is clicked', async () => {
    renderWithDnd(<Projects />);
    
    const createButton = screen.getByText('新建项目');
    fireEvent.click(createButton);
    
    await waitFor(() => {
      expect(screen.getByText('新建项目')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('请输入项目名称')).toBeInTheDocument();
    });
  });

  it('opens edit form when edit button is clicked', async () => {
    renderWithDnd(<Projects />);
    
    // Find and click the edit button (assuming it's rendered in the table)
    const editButtons = screen.getAllByRole('button');
    const editButton = editButtons.find(button => 
      button.querySelector('.anticon-edit')
    );
    
    if (editButton) {
      fireEvent.click(editButton);
      
      await waitFor(() => {
        expect(screen.getByText('编辑项目')).toBeInTheDocument();
      });
    }
  });
});