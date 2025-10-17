import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface AppState {
  // UI状态
  loading: boolean;
  sidebarCollapsed: boolean;
  
  // 用户信息
  user: {
    id?: string;
    name?: string;
    email?: string;
  } | null;
  
  // 系统配置
  config: {
    theme: 'light' | 'dark';
    language: 'zh' | 'en';
  };
  
  // Actions
  setLoading: (loading: boolean) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setUser: (user: AppState['user']) => void;
  setConfig: (config: Partial<AppState['config']>) => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    (set) => ({
      // Initial state
      loading: false,
      sidebarCollapsed: false,
      user: null,
      config: {
        theme: 'light',
        language: 'zh',
      },
      
      // Actions
      setLoading: (loading) => set({ loading }),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      setUser: (user) => set({ user }),
      setConfig: (config) => set((state) => ({ 
        config: { ...state.config, ...config } 
      })),
    }),
    {
      name: 'app-store',
    }
  )
);