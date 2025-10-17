import { useEffect } from 'react';
import { useAnnotationStore } from '../stores/annotationStore';
import { annotationService } from '../services/annotationService';
import useApi from './useApi';

export default function useAnnotation(projectId?: string) {
  const {
    cotItems,
    currentCOTItem,
    loading,
    selectedSliceId,
    setCOTItems,
    setCurrentCOTItem,
    addCOTItem,
    updateCOTItem,
    deleteCOTItem,
    setSelectedSliceId,
    setLoading,
  } = useAnnotationStore();

  // API hooks
  const {
    execute: fetchCOTItems,
    loading: fetchLoading,
  } = useApi(annotationService.getCOTItems);

  const {
    execute: createCOTItem,
    loading: createLoading,
  } = useApi(annotationService.createCOTItem, {
    showSuccessMessage: true,
    successMessage: 'CoT数据创建成功',
  });

  const {
    execute: updateCOTItemApi,
    loading: updateLoading,
  } = useApi(annotationService.updateCOTItem, {
    showSuccessMessage: true,
    successMessage: 'CoT数据更新成功',
  });

  const {
    execute: deleteCOTItemApi,
    loading: deleteLoading,
  } = useApi(annotationService.deleteCOTItem, {
    showSuccessMessage: true,
    successMessage: 'CoT数据删除成功',
  });

  const {
    execute: generateQuestion,
    loading: generateQuestionLoading,
  } = useApi(annotationService.generateQuestion);

  const {
    execute: generateCandidates,
    loading: generateCandidatesLoading,
  } = useApi(annotationService.generateCandidates);

  // 加载CoT数据列表
  const loadCOTItems = async () => {
    if (!projectId) return;
    
    setLoading(true);
    const result = await fetchCOTItems(projectId);
    if (result) {
      setCOTItems(result);
    }
    setLoading(false);
  };

  // 创建CoT数据
  const handleCreateCOTItem = async (data: any) => {
    const result = await createCOTItem(data);
    if (result) {
      addCOTItem(result);
      return result;
    }
    return null;
  };

  // 更新CoT数据
  const handleUpdateCOTItem = async (id: string, data: any) => {
    const result = await updateCOTItemApi(id, data);
    if (result) {
      updateCOTItem(id, result);
      return result;
    }
    return null;
  };

  // 删除CoT数据
  const handleDeleteCOTItem = async (id: string) => {
    const result = await deleteCOTItemApi(id);
    if (result !== null) {
      deleteCOTItem(id);
      return true;
    }
    return false;
  };

  // 生成问题
  const handleGenerateQuestion = async (sliceId: string) => {
    const result = await generateQuestion(sliceId);
    return result;
  };

  // 生成候选答案
  const handleGenerateCandidates = async (question: string, sliceId: string) => {
    const result = await generateCandidates(question, sliceId);
    return result;
  };

  // 选择切片
  const selectSlice = (sliceId: string) => {
    setSelectedSliceId(sliceId);
  };

  // 设置当前CoT项
  const selectCOTItem = (item: any) => {
    setCurrentCOTItem(item);
  };

  // 初始化加载
  useEffect(() => {
    if (projectId) {
      loadCOTItems();
    }
  }, [projectId]);

  return {
    // 状态
    cotItems,
    currentCOTItem,
    selectedSliceId,
    loading: loading || fetchLoading || createLoading || updateLoading || deleteLoading,
    generateQuestionLoading,
    generateCandidatesLoading,
    
    // 操作
    loadCOTItems,
    createCOTItem: handleCreateCOTItem,
    updateCOTItem: handleUpdateCOTItem,
    deleteCOTItem: handleDeleteCOTItem,
    generateQuestion: handleGenerateQuestion,
    generateCandidates: handleGenerateCandidates,
    selectSlice,
    selectCOTItem,
  };
}