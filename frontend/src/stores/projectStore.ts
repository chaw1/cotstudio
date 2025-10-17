import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { Project } from '../types';

interface ProjectState {
  // 项目数据
  projects: Project[];
  currentProject: Project | null;
  
  // UI状态
  loading: boolean;
  
  // Actions
  setProjects: (projects: Project[]) => void;
  setCurrentProject: (project: Project | null) => void;
  addProject: (project: Project) => void;
  updateProject: (id: string, updates: Partial<Project>) => void;
  deleteProject: (id: string) => void;
  setLoading: (loading: boolean) => void;
}

export const useProjectStore = create<ProjectState>()(
  devtools(
    (set) => ({
      // Initial state
      projects: [],
      currentProject: null,
      loading: false,
      
      // Actions
      setProjects: (projects) => set({ projects }),
      setCurrentProject: (project) => set({ currentProject: project }),
      addProject: (project) => set((state) => ({ 
        projects: [...state.projects, project] 
      })),
      updateProject: (id, updates) => set((state) => ({
        projects: state.projects.map(p => 
          p.id === id ? { ...p, ...updates } : p
        ),
        currentProject: state.currentProject?.id === id 
          ? { ...state.currentProject, ...updates }
          : state.currentProject
      })),
      deleteProject: (id) => set((state) => ({
        projects: state.projects.filter(p => p.id !== id),
        currentProject: state.currentProject?.id === id 
          ? null 
          : state.currentProject
      })),
      setLoading: (loading) => set({ loading }),
    }),
    {
      name: 'project-store',
    }
  )
);