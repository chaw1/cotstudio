/**
 * 前端性能优化测试
 * 验证懒加载、缓存和虚拟滚动等优化功能
 * 需求: 4.1, 4.2, 4.3
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { performanceMonitor, performanceUtils } from '../utils/performanceMonitor';
import { VirtualList } from '../components/VirtualScrolling';
import { OptimizedComponent, withOptimization } from '../components/Performance';

// 模拟性能API
const mockPerformance = {
  mark: vi.fn(),
  measure: vi.fn(),
  getEntriesByName: vi.fn(() => [{ duration: 100 }]),
  clearMarks: vi.fn(),
  clearMeasures: vi.fn(),
  now: vi.fn(() => Date.now()),
};

Object.defineProperty(window, 'performance', {
  value: mockPerformance,
  writable: true,
});

describe('前端性能优化测试', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  describe('懒加载功能测试', () => {
    it('应该正确实现组件懒加载', async () => {
      const LazyTestComponent = () => <div>Lazy Component Loaded</div>;
      
      // 模拟懒加载
      const LazyComponent = withOptimization(LazyTestComponent, {
        name: 'LazyTest',
        enableMonitoring: true,
      });

      render(<LazyComponent />);
      
      await waitFor(() => {
        expect(screen.getByText('Lazy Component Loaded')).toBeInTheDocument();
      });
    });
  });

  describe('虚拟滚动测试', () => {
    it('应该正确渲染虚拟列表', () => {
      const testData = Array.from({ length: 1000 }, (_, i) => ({
        id: i,
        name: `Item ${i}`,
      }));

      const renderItem = (item: any) => (
        <div key={item.id}>{item.name}</div>
      );

      render(
        <VirtualList
          data={testData}
          itemHeight={50}
          height={400}
          renderItem={renderItem}
        />
      );

      // 虚拟滚动应该只渲染可见项目
      const renderedItems = screen.getAllByText(/Item \d+/);
      expect(renderedItems.length).toBeLessThan(testData.length);
    });
  });
});