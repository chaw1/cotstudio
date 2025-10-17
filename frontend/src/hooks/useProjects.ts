import { useEffect } from 'react';
import { useProjectStore } from '../stores/projectStore';
import { projectService } from '../services/projectService';
import useApi from './useApi';

export default function useProjects() {
  const {
    projects,
    currentProject,
    loading,
    setProjects,
    setCurrentProject,
    addProject,
    updateProject,
    deleteProject,
    setLoading,
  } = useProjectStore();

  // API hooks
  const {
    execute: fetchProjects,
    loading: fetchLoading,
  } = useApi(projectService.getProjects);

  const {
    execute: createProject,
    loading: createLoading,
  } = useApi(projectService.createProject, {
    showSuccessMessage: true,
    successMessage: '项目创建成功',
  });

  const {
    execute: updateProjectApi,
    loading: updateLoading,
  } = useApi(projectService.updateProject, {
    showSuccessMessage: true,
    successMessage: '项目更新成功',
  });

  const {
    execute: deleteProjectApi,
    loading: deleteLoading,
  } = useApi(projectService.deleteProject, {
    showSuccessMessage: true,
    successMessage: '项目删除成功',
  });

  // 加载项目列表
  const loadProjects = async () => {
    setLoading(true);
    const result = await fetchProjects();
    if (result) {
      setProjects(result);
    }
    setLoading(false);
  };

  // 创建新项目
  const handleCreateProject = async (data: any) => {
    const result = await createProject(data);
    if (result) {
      addProject(result);
      return result;
    }
    return null;
  };

  // 更新项目
  const handleUpdateProject = async (id: string, data: any) => {
    const result = await updateProjectApi(id, data);
    if (result) {
      updateProject(id, result);
      return result;
    }
    return null;
  };

  // 删除项目
  const handleDeleteProject = async (id: string) => {
    const result = await deleteProjectApi(id);
    if (result !== null) {
      deleteProject(id);
      return true;
    }
    return false;
  };

  // 设置当前项目
  const selectProject = (project: any) => {
    setCurrentProject(project);
  };

  // 初始化加载
  useEffect(() => {
    loadProjects();
  }, []);

  return {
    // 状态
    projects,
    currentProject,
    loading: loading || fetchLoading || createLoading || updateLoading || deleteLoading,
    
    // 操作
    loadProjects,
    createProject: handleCreateProject,
    updateProject: handleUpdateProject,
    deleteProject: handleDeleteProject,
    selectProject,
  };
}