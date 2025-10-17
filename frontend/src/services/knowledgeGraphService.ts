import api from './api';
import { KGEntity, KGRelation } from '../types';

export interface KnowledgeGraphData {
  entities: KGEntity[];
  relations: KGRelation[];
}

export interface KGQueryParams {
  projectId?: string;
  entityTypes?: string[];
  relationTypes?: string[];
  limit?: number;
  offset?: number;
  search?: string;
}

export interface KGStats {
  totalEntities: number;
  totalRelations: number;
  entityTypes: { type: string; count: number }[];
  relationTypes: { type: string; count: number }[];
}

class KnowledgeGraphService {
  // 获取用户可访问的知识图谱列表
  async getAccessibleKnowledgeGraphs(): Promise<any[]> {
    return api.get('/kg/accessible');
  }

  // 获取知识图谱元数据
  async getKnowledgeGraphMetadata(graphId: string): Promise<any> {
    return api.get(`/kg/${graphId}/metadata`);
  }

  // 检查项目知识图谱访问权限
  async checkProjectKGAccess(projectId: string): Promise<any> {
    return api.get(`/kg/projects/${projectId}/accessible`);
  }

  // 获取知识图谱数据
  async getKnowledgeGraph(projectId: string, params?: KGQueryParams): Promise<KnowledgeGraphData> {
    const response = await api.get(`/kg/project/${projectId}/graph`, { params });
    // 后端返回 nodes 和 edges,需要转换为 entities 和 relations
    const entities = (response.nodes || []).map((node: any) => ({
      id: node.id,
      label: node.label,
      type: node.type,
      properties: {
        ...node.properties,
        description: node.description,
        confidence: node.confidence
      }
    }));
    
    const relations = (response.edges || []).map((edge: any) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: edge.type,
      properties: {
        ...edge.properties,
        description: edge.description,
        confidence: edge.confidence
      }
    }));
    
    return { entities, relations };
  }

  // 获取知识图谱统计信息
  async getKGStats(projectId: string): Promise<KGStats> {
    return api.get(`/kg/project/${projectId}/stats`);
  }

  // 搜索实体
  async searchEntities(projectId: string, query: string, limit = 20): Promise<KGEntity[]> {
    return api.get(`/kg/project/${projectId}/entities/search`, {
      params: { q: query, limit }
    });
  }

  // 获取实体详情
  async getEntity(projectId: string, entityId: string): Promise<KGEntity> {
    return api.get(`/kg/project/${projectId}/entities/${entityId}`);
  }

  // 获取实体的邻居节点
  async getEntityNeighbors(projectId: string, entityId: string, depth = 1): Promise<KnowledgeGraphData> {
    return api.get(`/kg/project/${projectId}/entities/${entityId}/neighbors`, {
      params: { depth }
    });
  }

  // 获取两个实体之间的路径
  async getPath(projectId: string, sourceId: string, targetId: string): Promise<KnowledgeGraphData> {
    return api.get(`/kg/project/${projectId}/path`, {
      params: { source: sourceId, target: targetId }
    });
  }

  // 更新实体
  async updateEntity(projectId: string, entityId: string, data: Partial<KGEntity>): Promise<KGEntity> {
    return api.put(`/kg/project/${projectId}/entities/${entityId}`, data);
  }

  // 删除实体
  async deleteEntity(projectId: string, entityId: string): Promise<void> {
    return api.delete(`/kg/project/${projectId}/entities/${entityId}`);
  }

  // 创建关系
  async createRelation(projectId: string, relation: Omit<KGRelation, 'id'>): Promise<KGRelation> {
    return api.post(`/kg/project/${projectId}/relations`, relation);
  }

  // 删除关系
  async deleteRelation(projectId: string, relationId: string): Promise<void> {
    return api.delete(`/kg/project/${projectId}/relations/${relationId}`);
  }
}

const knowledgeGraphService = new KnowledgeGraphService();
export default knowledgeGraphService;