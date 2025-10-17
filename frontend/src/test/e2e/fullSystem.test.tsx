/**
 * 前端全功能端到端测试
 * 测试知识图谱、导出功能、响应式布局等完整功能
 * 需求: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';

// 模拟组件
import KnowledgeGraphList from '../../pages/KnowledgeGraphList';
import KnowledgeGraph from '../../pages/KnowledgeGraph';
import Export from '../../pages/Export';
import { MainLayout } from '../../components/layout';

// 测试工具
const createTestWrapper = (children: React.ReactNode) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ConfigProvider>
          {children}
        </ConfigProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

// 模拟API响应
const mockApiResponses = {
  knowledgeGraphs: [
    {
      id: 'kg-1',
      name: '测试知识图谱1',
      description: '用于测试的知识图谱',
      nodeCount: 25,
      edgeCount: 40,
      lastUpdated: '2024-01-15T10:00:00Z'
    },
    {
      id: 'kg-2',
      name: '测试知识图谱2',
      description: '另一个测试知识图谱',
      nodeCount: 15,
      edgeCount: 20,
      lastUpdated: '2024-01-14T15:30:00Z'
    }
  ],
  knowledgeGraphData: {
    nodes: [
      { id: 'node1', label: '概念A', type: 'concept', size: 20, color: '#1677ff' },
      { id: 'node2', label: '概念B', type: 'concept', size: 15, color: '#52c41a' },
      { id: 'node3', label: '实体C', type: 'entity', size: 18, color: '#faad14' }
    ],
    edges: [
      { source: 'node1', target: 'node2', type: 'relates_to', color: '#d9d9d9' },
      { source: 'node2', target: 'node3', type: 'contains', color: '#d9d9d9' }
    ]
  },
  projects: [
    {
      id: 'project-1',
      name: '测试项目1',
      description: '用于测试的项目',
      status: 'active'
    }
  ],
  exportTasks: [
    {
      taskId: 'export-task-1',
      status: 'completed',
      progress: 100,
      downloadUrl: '/api/v1/export/download/export-task-1'
    }
  ]
};

// 模拟fetch
global.fetch = vi.fn();

describe('前端全功能端到端测试', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // 设置默认的fetch模拟
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/knowledge-graphs/accessible')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.knowledgeGraphs)
        });
      }
      
      if (url.includes('/knowledge-graphs/kg-1')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.knowledgeGraphData)
        });
      }
      
      if (url.includes('/projects')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.projects)
        });
      }
      
      if (url.includes('/export/tasks')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.exportTasks)
        });
      }
      
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      });
    });
  });

  describe('知识图谱模块直接访问测试', () => {
    it('应该显示可访问的知识图谱列表', async () => {
      render(createTestWrapper(<KnowledgeGraphList />));

      // 等待数据加载
      await waitFor(() => {
        expect(screen.getByText('测试知识图谱1')).toBeInTheDocument();
        expect(screen.getByText('测试知识图谱2')).toBeInTheDocument();
      });

      // 验证图谱信息显示
      expect(screen.getByText('25 个节点')).toBeInTheDocument();
      expect(screen.getByText('40 条边')).toBeInTheDocument();
    });

    it('应该支持搜索和过滤知识图谱', async () => {
      const user = userEvent.setup();
      render(createTestWrapper(<KnowledgeGraphList />));

      // 等待列表加载
      await waitFor(() => {
        expect(screen.getByText('测试知识图谱1')).toBeInTheDocument();
      });

      // 搜索功能测试
      const searchInput = screen.getByPlaceholderText('搜索知识图谱...');
      await user.type(searchInput, '测试知识图谱1');

      // 验证搜索结果
      await waitFor(() => {
        expect(screen.getByText('测试知识图谱1')).toBeInTheDocument();
        // 第二个图谱应该被过滤掉
        expect(screen.queryByText('测试知识图谱2')).not.toBeInTheDocument();
      });
    });

    it('应该支持直接访问特定知识图谱', async () => {
      const user = userEvent.setup();
      
      // 模拟路由参数
      const mockParams = { graphId: 'kg-1' };
      vi.mock('react-router-dom', async () => {
        const actual = await vi.importActual('react-router-dom');
        return {
          ...actual,
          useParams: () => mockParams,
        };
      });

      render(createTestWrapper(<KnowledgeGraph />));

      // 等待图谱数据加载
      await waitFor(() => {
        // 验证图谱可视化组件渲染
        expect(screen.getByTestId('knowledge-graph-container')).toBeInTheDocument();
      });

      // 验证节点和边的显示
      await waitFor(() => {
        expect(screen.getByText('概念A')).toBeInTheDocument();
        expect(screen.getByText('概念B')).toBeInTheDocument();
        expect(screen.getByText('实体C')).toBeInTheDocument();
      });
    });
  });

  describe('数据导出功能测试', () => {
    it('应该显示导出界面和选项', async () => {
      render(createTestWrapper(<Export />));

      // 验证导出界面元素
      await waitFor(() => {
        expect(screen.getByText('数据导出')).toBeInTheDocument();
        expect(screen.getByText('选择项目')).toBeInTheDocument();
        expect(screen.getByText('导出格式')).toBeInTheDocument();
        expect(screen.getByText('导出选项')).toBeInTheDocument();
      });

      // 验证格式选项
      expect(screen.getByText('JSON')).toBeInTheDocument();
      expect(screen.getByText('CSV')).toBeInTheDocument();
      expect(screen.getByText('Excel')).toBeInTheDocument();
    });

    it('应该支持创建导出任务', async () => {
      const user = userEvent.setup();
      render(createTestWrapper(<Export />));

      // 等待界面加载
      await waitFor(() => {
        expect(screen.getByText('数据导出')).toBeInTheDocument();
      });

      // 选择项目
      const projectSelect = screen.getByLabelText('选择项目');
      await user.click(projectSelect);
      await user.click(screen.getByText('测试项目1'));

      // 选择导出格式
      const formatSelect = screen.getByLabelText('导出格式');
      await user.click(formatSelect);
      await user.click(screen.getByText('JSON'));

      // 配置导出选项
      const includeMetadata = screen.getByLabelText('包含元数据');
      await user.click(includeMetadata);

      const includeKG = screen.getByLabelText('包含知识图谱');
      await user.click(includeKG);

      // 创建导出任务
      const exportButton = screen.getByText('开始导出');
      await user.click(exportButton);

      // 验证导出任务创建
      await waitFor(() => {
        expect(screen.getByText('导出任务已创建')).toBeInTheDocument();
      });
    });

    it('应该显示导出任务状态和进度', async () => {
      render(createTestWrapper(<Export />));

      // 等待任务列表加载
      await waitFor(() => {
        expect(screen.getByText('导出历史')).toBeInTheDocument();
      });

      // 验证任务状态显示
      await waitFor(() => {
        expect(screen.getByText('已完成')).toBeInTheDocument();
        expect(screen.getByText('100%')).toBeInTheDocument();
      });

      // 验证下载按钮
      expect(screen.getByText('下载')).toBeInTheDocument();
    });
  });

  describe('响应式布局测试', () => {
    it('应该在不同屏幕尺寸下正确调整布局', async () => {
      // 模拟不同的屏幕尺寸
      const screenSizes = [
        { width: 1920, height: 1080, name: '桌面大屏' },
        { width: 1366, height: 768, name: '桌面标准' },
        { width: 768, height: 1024, name: '平板' },
        { width: 375, height: 667, name: '手机' }
      ];

      for (const size of screenSizes) {
        // 设置窗口尺寸
        Object.defineProperty(window, 'innerWidth', {
          writable: true,
          configurable: true,
          value: size.width,
        });
        Object.defineProperty(window, 'innerHeight', {
          writable: true,
          configurable: true,
          value: size.height,
        });

        // 触发resize事件
        window.dispatchEvent(new Event('resize'));

        render(createTestWrapper(
          <MainLayout>
            <div data-testid="content">测试内容</div>
          </MainLayout>
        ));

        // 验证布局适配
        const layout = screen.getByTestId('main-layout');
        const computedStyle = window.getComputedStyle(layout);

        // 验证布局响应性
        if (size.width < 768) {
          // 移动端布局验证
          expect(computedStyle.flexDirection).toBe('column');
        } else {
          // 桌面端布局验证
          expect(computedStyle.display).toBe('flex');
        }

        console.log(`✅ ${size.name} (${size.width}x${size.height}) 布局验证通过`);
      }
    });

    it('应该支持侧边栏折叠和展开', async () => {
      const user = userEvent.setup();
      
      render(createTestWrapper(
        <MainLayout>
          <div>测试内容</div>
        </MainLayout>
      ));

      // 查找侧边栏切换按钮
      const toggleButton = screen.getByLabelText('切换侧边栏');
      
      // 初始状态验证
      const sidebar = screen.getByTestId('sidebar');
      expect(sidebar).toHaveClass('expanded');

      // 折叠侧边栏
      await user.click(toggleButton);
      
      await waitFor(() => {
        expect(sidebar).toHaveClass('collapsed');
      });

      // 展开侧边栏
      await user.click(toggleButton);
      
      await waitFor(() => {
        expect(sidebar).toHaveClass('expanded');
      });
    });
  });

  describe('跨功能集成测试', () => {
    it('应该支持从知识图谱页面导出数据', async () => {
      const user = userEvent.setup();
      
      // 模拟在知识图谱页面
      render(createTestWrapper(<KnowledgeGraph />));

      // 等待图谱加载
      await waitFor(() => {
        expect(screen.getByTestId('knowledge-graph-container')).toBeInTheDocument();
      });

      // 点击导出按钮
      const exportButton = screen.getByText('导出图谱');
      await user.click(exportButton);

      // 验证导出选项弹窗
      await waitFor(() => {
        expect(screen.getByText('导出知识图谱')).toBeInTheDocument();
        expect(screen.getByText('选择格式')).toBeInTheDocument();
      });

      // 选择导出格式并确认
      await user.click(screen.getByText('GraphML'));
      await user.click(screen.getByText('确认导出'));

      // 验证导出任务创建
      await waitFor(() => {
        expect(screen.getByText('导出任务已创建')).toBeInTheDocument();
      });
    });

    it('应该支持搜索结果的可视化展示', async () => {
      const user = userEvent.setup();
      
      render(createTestWrapper(<KnowledgeGraph />));

      // 等待图谱加载
      await waitFor(() => {
        expect(screen.getByTestId('knowledge-graph-container')).toBeInTheDocument();
      });

      // 使用搜索功能
      const searchInput = screen.getByPlaceholderText('搜索节点...');
      await user.type(searchInput, '概念A');

      // 验证搜索结果高亮
      await waitFor(() => {
        const highlightedNode = screen.getByTestId('node-node1');
        expect(highlightedNode).toHaveClass('highlighted');
      });

      // 验证搜索结果面板
      expect(screen.getByText('搜索结果: 1 个节点')).toBeInTheDocument();
    });
  });

  describe('性能和用户体验测试', () => {
    it('应该在数据加载时显示加载状态', async () => {
      // 模拟慢速网络
      (global.fetch as any).mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            json: () => Promise.resolve(mockApiResponses.knowledgeGraphs)
          }), 1000)
        )
      );

      render(createTestWrapper(<KnowledgeGraphList />));

      // 验证加载状态显示
      expect(screen.getByText('加载中...')).toBeInTheDocument();

      // 等待数据加载完成
      await waitFor(() => {
        expect(screen.getByText('测试知识图谱1')).toBeInTheDocument();
      }, { timeout: 2000 });

      // 验证加载状态消失
      expect(screen.queryByText('加载中...')).not.toBeInTheDocument();
    });

    it('应该正确处理错误状态', async () => {
      // 模拟API错误
      (global.fetch as any).mockImplementation(() => 
        Promise.resolve({
          ok: false,
          status: 500,
          json: () => Promise.resolve({ error: '服务器错误' })
        })
      );

      render(createTestWrapper(<KnowledgeGraphList />));

      // 验证错误状态显示
      await waitFor(() => {
        expect(screen.getByText('加载失败')).toBeInTheDocument();
        expect(screen.getByText('重试')).toBeInTheDocument();
      });
    });
  });
});

export default {};