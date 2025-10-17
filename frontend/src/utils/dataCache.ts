/**
 * 数据缓存工具
 * 实现数据缓存和优化查询性能
 * 需求: 4.1, 4.2, 4.3
 */
import { QueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';

// 缓存配置
export const CACHE_CONFIG = {
  // 默认缓存时间配置
  staleTime: {
    short: 30 * 1000,      // 30秒 - 用于频繁变化的数据
    medium: 5 * 60 * 1000,  // 5分钟 - 用于一般数据
    long: 30 * 60 * 1000,   // 30分钟 - 用于相对稳定的数据
    veryLong: 60 * 60 * 1000 // 1小时 - 用于很少变化的数据
  },
  
  // 缓存保留时间
  cacheTime: {
    short: 5 * 60 * 1000,   // 5分钟
    medium: 10 * 60 * 1000, // 10分钟
    long: 30 * 60 * 1000,   // 30分钟
    veryLong: 60 * 60 * 1000 // 1小时
  },
  
  // 重试配置
  retry: {
    default: 3,
    critical: 5,
    none: false
  }
};

// 查询键工厂
export const queryKeys = {
  // 用户相关
  users: {
    all: ['users'] as const,
    lists: () => [...queryKeys.users.all, 'list'] as const,
    list: (filters: Record<string, any>) => [...queryKeys.users.lists(), filters] as const,
    details: () => [...queryKeys.users.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.users.details(), id] as const,
    stats: () => [...queryKeys.users.all, 'stats'] as const,
  },
  
  // 项目相关
  projects: {
    all: ['projects'] as const,
    lists: () => [...queryKeys.projects.all, 'list'] as const,
    list: (filters: Record<string, any>) => [...queryKeys.projects.lists(), filters] as const,
    details: () => [...queryKeys.projects.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.projects.details(), id] as const,
    stats: (id: string) => [...queryKeys.projects.detail(id), 'stats'] as const,
  },
  
  // 权限相关
  permissions: {
    all: ['permissions'] as const,
    user: (userId: string) => [...queryKeys.permissions.all, 'user', userId] as const,
    project: (projectId: string) => [...queryKeys.permissions.all, 'project', projectId] as const,
    list: (filters: Record<string, any>) => [...queryKeys.permissions.all, 'list', filters] as const,
  },
  
  // 知识图谱相关
  knowledgeGraph: {
    all: ['knowledgeGraph'] as const,
    project: (projectId: string) => [...queryKeys.knowledgeGraph.all, 'project', projectId] as const,
    visualization: (projectId: string) => [...queryKeys.knowledgeGraph.project(projectId), 'visualization'] as const,
    search: (projectId: string, query: string) => [...queryKeys.knowledgeGraph.project(projectId), 'search', query] as const,
  },
  
  // 系统监控相关
  system: {
    all: ['system'] as const,
    resources: () => [...queryKeys.system.all, 'resources'] as const,
    contributions: () => [...queryKeys.system.all, 'contributions'] as const,
    activities: () => [...queryKeys.system.all, 'activities'] as const,
  },
  
  // 导出相关
  exports: {
    all: ['exports'] as const,
    tasks: () => [...queryKeys.exports.all, 'tasks'] as const,
    task: (taskId: string) => [...queryKeys.exports.tasks(), taskId] as const,
  }
};

// 创建优化的查询客户端
export const createOptimizedQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // 默认配置
        staleTime: CACHE_CONFIG.staleTime.medium,
        cacheTime: CACHE_CONFIG.cacheTime.medium,
        retry: CACHE_CONFIG.retry.default,
        refetchOnWindowFocus: false,
        refetchOnReconnect: true,
        
        // 错误处理
        onError: (error) => {
          console.error('Query error:', error);
        },
      },
      mutations: {
        // 默认重试配置
        retry: CACHE_CONFIG.retry.default,
        
        // 错误处理
        onError: (error) => {
          console.error('Mutation error:', error);
        },
      },
    },
  });
};

// 预定义的查询选项
export const queryOptions = {
  // 用户列表查询选项
  userList: (filters: Record<string, any> = {}): UseQueryOptions => ({
    queryKey: queryKeys.users.list(filters),
    staleTime: CACHE_CONFIG.staleTime.medium,
    cacheTime: CACHE_CONFIG.cacheTime.medium,
  }),
  
  // 用户详情查询选项
  userDetail: (userId: string): UseQueryOptions => ({
    queryKey: queryKeys.users.detail(userId),
    staleTime: CACHE_CONFIG.staleTime.long,
    cacheTime: CACHE_CONFIG.cacheTime.long,
    enabled: !!userId,
  }),
  
  // 项目列表查询选项
  projectList: (filters: Record<string, any> = {}): UseQueryOptions => ({
    queryKey: queryKeys.projects.list(filters),
    staleTime: CACHE_CONFIG.staleTime.medium,
    cacheTime: CACHE_CONFIG.cacheTime.medium,
  }),
  
  // 项目详情查询选项
  projectDetail: (projectId: string): UseQueryOptions => ({
    queryKey: queryKeys.projects.detail(projectId),
    staleTime: CACHE_CONFIG.staleTime.long,
    cacheTime: CACHE_CONFIG.cacheTime.long,
    enabled: !!projectId,
  }),
  
  // 权限查询选项
  userPermissions: (userId: string): UseQueryOptions => ({
    queryKey: queryKeys.permissions.user(userId),
    staleTime: CACHE_CONFIG.staleTime.short, // 权限变化较频繁
    cacheTime: CACHE_CONFIG.cacheTime.short,
    enabled: !!userId,
  }),
  
  // 系统资源监控查询选项
  systemResources: (): UseQueryOptions => ({
    queryKey: queryKeys.system.resources(),
    staleTime: 10 * 1000, // 10秒，实时性要求高
    cacheTime: 30 * 1000, // 30秒
    refetchInterval: 30 * 1000, // 每30秒自动刷新
  }),
  
  // 知识图谱可视化查询选项
  knowledgeGraphVisualization: (projectId: string): UseQueryOptions => ({
    queryKey: queryKeys.knowledgeGraph.visualization(projectId),
    staleTime: CACHE_CONFIG.staleTime.long,
    cacheTime: CACHE_CONFIG.cacheTime.long,
    enabled: !!projectId,
  }),
};

// 缓存失效工具
export const cacheInvalidation = {
  // 用户相关缓存失效
  invalidateUsers: (queryClient: QueryClient) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
  },
  
  invalidateUser: (queryClient: QueryClient, userId: string) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.users.detail(userId) });
    queryClient.invalidateQueries({ queryKey: queryKeys.users.lists() });
  },
  
  // 项目相关缓存失效
  invalidateProjects: (queryClient: QueryClient) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
  },
  
  invalidateProject: (queryClient: QueryClient, projectId: string) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.projects.detail(projectId) });
    queryClient.invalidateQueries({ queryKey: queryKeys.projects.lists() });
  },
  
  // 权限相关缓存失效
  invalidatePermissions: (queryClient: QueryClient) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.permissions.all });
  },
  
  invalidateUserPermissions: (queryClient: QueryClient, userId: string) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.permissions.user(userId) });
  },
  
  invalidateProjectPermissions: (queryClient: QueryClient, projectId: string) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.permissions.project(projectId) });
  },
  
  // 知识图谱相关缓存失效
  invalidateKnowledgeGraph: (queryClient: QueryClient, projectId: string) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.knowledgeGraph.project(projectId) });
  },
};

// 预取工具
export const prefetchUtils = {
  // 预取用户详情
  prefetchUserDetail: async (queryClient: QueryClient, userId: string, fetchFn: () => Promise<any>) => {
    await queryClient.prefetchQuery({
      queryKey: queryKeys.users.detail(userId),
      queryFn: fetchFn,
      staleTime: CACHE_CONFIG.staleTime.long,
    });
  },
  
  // 预取项目详情
  prefetchProjectDetail: async (queryClient: QueryClient, projectId: string, fetchFn: () => Promise<any>) => {
    await queryClient.prefetchQuery({
      queryKey: queryKeys.projects.detail(projectId),
      queryFn: fetchFn,
      staleTime: CACHE_CONFIG.staleTime.long,
    });
  },
  
  // 预取知识图谱数据
  prefetchKnowledgeGraph: async (queryClient: QueryClient, projectId: string, fetchFn: () => Promise<any>) => {
    await queryClient.prefetchQuery({
      queryKey: queryKeys.knowledgeGraph.visualization(projectId),
      queryFn: fetchFn,
      staleTime: CACHE_CONFIG.staleTime.long,
    });
  },
};

// 乐观更新工具
export const optimisticUpdates = {
  // 用户更新的乐观更新
  updateUser: (queryClient: QueryClient, userId: string, updatedData: any) => {
    queryClient.setQueryData(queryKeys.users.detail(userId), (oldData: any) => ({
      ...oldData,
      ...updatedData,
    }));
  },
  
  // 项目更新的乐观更新
  updateProject: (queryClient: QueryClient, projectId: string, updatedData: any) => {
    queryClient.setQueryData(queryKeys.projects.detail(projectId), (oldData: any) => ({
      ...oldData,
      ...updatedData,
    }));
  },
  
  // 权限更新的乐观更新
  updateUserPermissions: (queryClient: QueryClient, userId: string, updatedPermissions: any) => {
    queryClient.setQueryData(queryKeys.permissions.user(userId), (oldData: any) => ({
      ...oldData,
      project_permissions: updatedPermissions,
    }));
  },
};

// 批量操作工具
export const batchOperations = {
  // 批量预取
  batchPrefetch: async (
    queryClient: QueryClient,
    operations: Array<{
      queryKey: any[];
      queryFn: () => Promise<any>;
      staleTime?: number;
    }>
  ) => {
    const promises = operations.map(({ queryKey, queryFn, staleTime }) =>
      queryClient.prefetchQuery({
        queryKey,
        queryFn,
        staleTime: staleTime || CACHE_CONFIG.staleTime.medium,
      })
    );
    
    await Promise.allSettled(promises);
  },
  
  // 批量失效
  batchInvalidate: (queryClient: QueryClient, queryKeys: any[][]) => {
    queryKeys.forEach(queryKey => {
      queryClient.invalidateQueries({ queryKey });
    });
  },
};

export default {
  CACHE_CONFIG,
  queryKeys,
  createOptimizedQueryClient,
  queryOptions,
  cacheInvalidation,
  prefetchUtils,
  optimisticUpdates,
  batchOperations,
};