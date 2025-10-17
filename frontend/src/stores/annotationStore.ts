import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface COTCandidate {
  id: string;
  text: string;
  chainOfThought: string;
  score: number;
  chosen: boolean;
  rank: number;
}

export interface COTItem {
  id: string;
  projectId: string;
  sliceId: string;
  question: string;
  candidates: COTCandidate[];
  status: 'draft' | 'reviewed' | 'approved';
  createdAt: string;
  updatedAt: string;
}

interface AnnotationState {
  // 标注数据
  cotItems: COTItem[];
  currentCOTItem: COTItem | null;
  
  // UI状态
  loading: boolean;
  selectedSliceId: string | null;
  
  // Actions
  setCOTItems: (items: COTItem[]) => void;
  setCurrentCOTItem: (item: COTItem | null) => void;
  addCOTItem: (item: COTItem) => void;
  updateCOTItem: (id: string, updates: Partial<COTItem>) => void;
  deleteCOTItem: (id: string) => void;
  setSelectedSliceId: (sliceId: string | null) => void;
  setLoading: (loading: boolean) => void;
}

export const useAnnotationStore = create<AnnotationState>()(
  devtools(
    (set) => ({
      // Initial state
      cotItems: [],
      currentCOTItem: null,
      loading: false,
      selectedSliceId: null,
      
      // Actions
      setCOTItems: (items) => set({ cotItems: items }),
      setCurrentCOTItem: (item) => set({ currentCOTItem: item }),
      addCOTItem: (item) => set((state) => ({ 
        cotItems: [...state.cotItems, item] 
      })),
      updateCOTItem: (id, updates) => set((state) => ({
        cotItems: state.cotItems.map(item => 
          item.id === id ? { ...item, ...updates } : item
        ),
        currentCOTItem: state.currentCOTItem?.id === id 
          ? { ...state.currentCOTItem, ...updates }
          : state.currentCOTItem
      })),
      deleteCOTItem: (id) => set((state) => ({
        cotItems: state.cotItems.filter(item => item.id !== id),
        currentCOTItem: state.currentCOTItem?.id === id 
          ? null 
          : state.currentCOTItem
      })),
      setSelectedSliceId: (sliceId) => set({ selectedSliceId: sliceId }),
      setLoading: (loading) => set({ loading }),
    }),
    {
      name: 'annotation-store',
    }
  )
);