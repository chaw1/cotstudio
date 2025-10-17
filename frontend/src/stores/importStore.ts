/**
 * 导入状态管理
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { 
  ImportTaskResponse, 
  ImportAnalysisResult, 
  ImportResult, 
  DataDifference,
  ConflictResolution,
  importService 
} from '../services/importService';

export interface ImportState {
  // 当前导入流程状态
  currentStep: 'upload' | 'validate' | 'analyze' | 'confirm' | 'import' | 'complete';
  
  // 文件信息
  uploadedFile: File | null;
  filePath: string | null;
  
  // 任务状态
  currentTask: ImportTaskResponse | null;
  
  // 分析结果
  analysisResult: ImportAnalysisResult | null;
  
  // 差异和冲突
  differences: DataDifference[];
  conflicts: DataDifference[];
  
  // 用户选择
  selectedDifferences: Set<string>;
  conflictResolutions: Record<string, ConflictResolution>;
  
  // 导入结果
  importResult: ImportResult | null;
  
  // UI状态
  loading: boolean;
  error: string | null;
  
  // 目标项目
  targetProjectId: string | null;
  importMode: 'merge' | 'replace' | 'create_new';
  newProjectName: string | null;
}

export interface ImportActions {
  // 文件上传
  setUploadedFile: (file: File) => void;
  uploadFile: (file: File) => Promise<void>;
  
  // 验证文件
  validateFile: () => Promise<void>;
  
  // 分析差异
  analyzeDifferences: (targetProjectId?: string) => Promise<void>;
  
  // 差异选择
  toggleDifference: (differenceId: string) => void;
  selectAllDifferences: () => void;
  deselectAllDifferences: () => void;
  
  // 冲突解决
  setConflictResolution: (differenceId: string, resolution: ConflictResolution) => void;
  
  // 执行导入
  executeImport: () => Promise<void>;
  
  // 任务管理
  pollTaskStatus: (taskId: string) => Promise<void>;
  cancelTask: () => Promise<void>;
  
  // 状态管理
  setCurrentStep: (step: ImportState['currentStep']) => void;
  setTargetProject: (projectId: string | null) => void;
  setImportMode: (mode: ImportState['importMode']) => void;
  setNewProjectName: (name: string) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  reset: () => void;
}

const initialState: ImportState = {
  currentStep: 'upload',
  uploadedFile: null,
  filePath: null,
  currentTask: null,
  analysisResult: null,
  differences: [],
  conflicts: [],
  selectedDifferences: new Set(),
  conflictResolutions: {},
  importResult: null,
  loading: false,
  error: null,
  targetProjectId: null,
  importMode: 'create_new',
  newProjectName: null,
};

export const useImportStore = create<ImportState & ImportActions>()(
  devtools(
    (set, get) => ({
      ...initialState,

      setUploadedFile: (file) => {
        set({ uploadedFile: file });
      },

      uploadFile: async (file) => {
        set({ loading: true, error: null });
        
        try {
          const result = await importService.uploadImportFile(file);
          set({
            uploadedFile: file,
            filePath: result.file_path,
            currentStep: 'validate',
            loading: false,
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '文件上传失败',
            loading: false,
          });
        }
      },

      validateFile: async () => {
        const { filePath } = get();
        if (!filePath) {
          set({ error: '没有文件需要验证' });
          return;
        }

        set({ loading: true, error: null });

        try {
          const task = await importService.validateImportFile(filePath);
          set({ currentTask: task });

          // 轮询任务状态
          await get().pollTaskStatus(task.task_id);
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '文件验证失败',
            loading: false,
          });
        }
      },

      analyzeDifferences: async (targetProjectId) => {
        const { filePath } = get();
        if (!filePath) {
          set({ error: '没有文件需要分析' });
          return;
        }

        set({ 
          loading: true, 
          error: null,
          targetProjectId,
          currentStep: 'analyze'
        });

        try {
          const task = await importService.analyzeImportDifferences(filePath, targetProjectId);
          set({ currentTask: task });

          // 轮询任务状态
          await get().pollTaskStatus(task.task_id);
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '差异分析失败',
            loading: false,
          });
        }
      },

      toggleDifference: (differenceId) => {
        const { selectedDifferences } = get();
        const newSelected = new Set(selectedDifferences);
        
        if (newSelected.has(differenceId)) {
          newSelected.delete(differenceId);
        } else {
          newSelected.add(differenceId);
        }
        
        set({ selectedDifferences: newSelected });
      },

      selectAllDifferences: () => {
        const { differences } = get();
        const allIds = new Set(differences.map(d => d.id));
        set({ selectedDifferences: allIds });
      },

      deselectAllDifferences: () => {
        set({ selectedDifferences: new Set() });
      },

      setConflictResolution: (differenceId, resolution) => {
        const { conflictResolutions } = get();
        set({
          conflictResolutions: {
            ...conflictResolutions,
            [differenceId]: resolution,
          },
        });
      },

      executeImport: async () => {
        const { 
          currentTask, 
          selectedDifferences, 
          conflictResolutions,
          targetProjectId,
          importMode,
          newProjectName
        } = get();
        
        if (!currentTask) {
          set({ error: '没有有效的分析任务' });
          return;
        }

        set({ loading: true, error: null, currentStep: 'import' });

        try {
          const confirmation = {
            task_id: currentTask.task_id,
            confirmed_differences: Array.from(selectedDifferences),
            conflict_resolutions: Object.fromEntries(
              Object.entries(conflictResolutions).map(([key, value]) => [key, value.resolution])
            ),
            import_settings: {
              import_mode: importMode,
              target_project_id: targetProjectId,
              new_project_name: newProjectName,
            },
          };

          const task = await importService.executeImport(confirmation);
          set({ currentTask: task });

          // 轮询任务状态
          await get().pollTaskStatus(task.task_id);
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '导入执行失败',
            loading: false,
          });
        }
      },

      pollTaskStatus: async (taskId) => {
        try {
          const finalStatus = await importService.pollTaskStatus(
            taskId,
            (status) => {
              set({ currentTask: status });
            }
          );

          set({ currentTask: finalStatus, loading: false });

          if (finalStatus.status === 'completed') {
            // 获取任务结果
            const result = await importService.getImportTaskResult(taskId);
            
            if (result.result) {
              if (result.result.is_valid !== undefined) {
                // 这是验证结果
                set({ currentStep: 'analyze' });
              } else if (result.result.differences !== undefined) {
                // 这是分析结果
                set({
                  analysisResult: result.result,
                  differences: result.result.differences || [],
                  conflicts: result.result.conflicts || [],
                  currentStep: 'confirm',
                });
              } else if (result.result.success !== undefined) {
                // 这是导入结果
                set({
                  importResult: result.result,
                  currentStep: 'complete',
                });
              }
            }
          } else if (finalStatus.status === 'failed') {
            set({ error: finalStatus.message || '任务执行失败' });
          }
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '获取任务状态失败',
            loading: false,
          });
        }
      },

      cancelTask: async () => {
        const { currentTask } = get();
        if (!currentTask) return;

        try {
          await importService.cancelImportTask(currentTask.task_id);
          set({ currentTask: null, loading: false });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '取消任务失败',
          });
        }
      },

      setCurrentStep: (step) => {
        set({ currentStep: step });
      },

      setTargetProject: (projectId) => {
        set({ targetProjectId: projectId });
      },

      setImportMode: (mode) => {
        set({ importMode: mode });
      },

      setNewProjectName: (name) => {
        set({ newProjectName: name });
      },

      setError: (error) => {
        set({ error });
      },

      clearError: () => {
        set({ error: null });
      },

      reset: () => {
        set(initialState);
      },
    }),
    {
      name: 'import-store',
    }
  )
);