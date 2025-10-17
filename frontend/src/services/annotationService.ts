import api from './api';
import { COTItem, COTCandidate } from '../stores/annotationStore';

export interface CreateCOTRequest {
  projectId: string;
  sliceId: string;
  question: string;
  candidates: Omit<COTCandidate, 'id'>[];
}

export interface UpdateCOTRequest {
  question?: string;
  candidates?: COTCandidate[];
  status?: 'draft' | 'reviewed' | 'approved';
}

export const annotationService = {
  // 获取CoT数据列表
  async getCOTItems(projectId: string): Promise<COTItem[]> {
    return api.get(`/cot-annotation/project/${projectId}`);
  },

  // 获取CoT数据详情
  async getCOTItem(id: string): Promise<COTItem> {
    return api.get(`/cot-annotation/${id}`);
  },

  // 创建CoT数据
  async createCOTItem(data: CreateCOTRequest): Promise<COTItem> {
    return api.post('/cot-annotation', data);
  },

  // 更新CoT数据
  async updateCOTItem(id: string, data: UpdateCOTRequest): Promise<COTItem> {
    return api.put(`/cot-annotation/${id}`, data);
  },

  // 删除CoT数据
  async deleteCOTItem(id: string): Promise<void> {
    return api.delete(`/cot-annotation/${id}`);
  },

  // 生成问题
  async generateQuestion(sliceId: string): Promise<string> {
    return api.post(`/cot/generate-question`, { slice_id: sliceId });
  },

  // 生成候选答案
  async generateCandidates(question: string, sliceId: string): Promise<COTCandidate[]> {
    return api.post(`/cot/generate-candidates`, { question, slice_id: sliceId });
  },
};