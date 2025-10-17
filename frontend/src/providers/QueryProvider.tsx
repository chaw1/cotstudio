/**
 * 优化的查询提供者
 * 集成数据缓存和性能优化
 * 需求: 4.1, 4.2, 4.3
 */
import React from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { createOptimizedQueryClient } from '../utils/dataCache';
import { performanceMonitor } from '../utils/performanceMonitor';

// 创建优化的查询客户端
const queryClient = createOptimizedQueryClient();

// 添加全局错误处理
queryClient.setDefaultOptions({
  queries: {
    onError: (error) => {
      console.error('Query error:', error);
      performanceMonitor.mark('query-error');
    },
    onSuccess: () => {
      performanceMonitor.mark('query-success');
    },
  },
  mutations: {
    onError: (error) => {
      console.error('Mutation error:', error);
      performanceMonitor.mark('mutation-error');
    },
    onSuccess: () => {
      performanceMonitor.mark('mutation-success');
    },
  },
});

interface QueryProviderProps {
  children: React.ReactNode;
}

export const QueryProvider: React.FC<QueryProviderProps> = ({ children }) => {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {/* React Query开发工具已关闭 */}
      {false && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
};

export { queryClient };
export default QueryProvider;