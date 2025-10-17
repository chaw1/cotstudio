import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ProjectList, ProjectForm, ProjectDetail } from '../components/project';
import { Project } from '../types';
import useProjects from '../hooks/useProjects';
import safeMessage from '../utils/message';

const Projects: React.FC = () => {
  const {
    projects,
    currentProject,
    loading,
    createProject,
    updateProject,
    deleteProject,
    selectProject,
  } = useProjects();

  const [searchParams, setSearchParams] = useSearchParams();
  const [showForm, setShowForm] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [showDetail, setShowDetail] = useState(false);

  // Check for create parameter on component mount
  useEffect(() => {
    const shouldCreate = searchParams.get('create');
    if (shouldCreate === 'true') {
      setShowForm(true);
      // Remove the parameter from URL
      setSearchParams({});
    }
  }, [searchParams, setSearchParams]);

  // 处理创建项目
  const handleCreateProject = () => {
    setEditingProject(null);
    setShowForm(true);
  };

  // 处理编辑项目
  const handleEditProject = (project: Project) => {
    setEditingProject(project);
    setShowForm(true);
  };

  // 处理查看项目详情
  const handleViewProject = (project: Project) => {
    selectProject(project);
    setShowDetail(true);
  };

  // 处理表单提交
  const handleFormSubmit = async (values: any) => {
    try {
      if (editingProject) {
        await updateProject(editingProject.id, values);
        safeMessage.success('项目更新成功');
      } else {
        await createProject(values);
        safeMessage.success('项目创建成功');
      }
      setShowForm(false);
      setEditingProject(null);
    } catch (error) {
      safeMessage.error(editingProject ? '项目更新失败' : '项目创建失败');
    }
  };

  // 处理表单取消
  const handleFormCancel = () => {
    setShowForm(false);
    setEditingProject(null);
  };

  // 处理删除项目
  const handleDeleteProject = async (projectId: string) => {
    try {
      await deleteProject(projectId);
      safeMessage.success('项目删除成功');
    } catch (error) {
      safeMessage.error('项目删除失败');
    }
  };

  // 处理返回项目列表
  const handleBackToList = () => {
    setShowDetail(false);
    selectProject(null);
  };

  // 处理项目切换
  const handleProjectChange = (project: Project) => {
    selectProject(project);
    setShowDetail(true);
  };

  // 如果显示项目详情
  if (showDetail && currentProject) {
    return (
      <ProjectDetail
        project={currentProject}
        onEdit={handleEditProject}
        onBack={handleBackToList}
        onProjectChange={handleProjectChange}
      />
    );
  }

  // 显示项目列表
  return (
    <>
      <ProjectList
        projects={projects}
        loading={loading}
        onCreateProject={handleCreateProject}
        onEditProject={handleEditProject}
        onDeleteProject={handleDeleteProject}
        onViewProject={handleViewProject}
      />

      <ProjectForm
        visible={showForm}
        project={editingProject}
        loading={loading}
        onSubmit={handleFormSubmit}
        onCancel={handleFormCancel}
      />
    </>
  );
};

export default Projects;