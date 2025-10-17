"""
知识图谱相关的Pydantic模式
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class KGEntityBase(BaseModel):
    """实体基础模式"""
    name: str = Field(..., description="实体名称")
    entity_type: str = Field(..., description="实体类型")
    description: Optional[str] = Field(None, description="实体描述")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="置信度分数")


class KGEntityCreate(KGEntityBase):
    """创建实体模式"""
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="实体属性")


class KGEntityResponse(KGEntityBase):
    """实体响应模式"""
    id: str = Field(..., description="实体ID")
    neo4j_node_id: Optional[str] = Field(None, description="Neo4j节点ID")
    created_at: str = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class KGRelationBase(BaseModel):
    """关系基础模式"""
    relation_type: str = Field(..., description="关系类型")
    description: Optional[str] = Field(None, description="关系描述")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="置信度分数")


class KGRelationCreate(KGRelationBase):
    """创建关系模式"""
    source_entity_id: str = Field(..., description="源实体ID")
    target_entity_id: str = Field(..., description="目标实体ID")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="关系属性")


class KGRelationResponse(KGRelationBase):
    """关系响应模式"""
    id: str = Field(..., description="关系ID")
    source_entity_id: str = Field(..., description="源实体ID")
    target_entity_id: str = Field(..., description="目标实体ID")
    neo4j_relation_id: Optional[str] = Field(None, description="Neo4j关系ID")
    created_at: str = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class KGExtractionRequest(BaseModel):
    """知识图谱抽取请求"""
    cot_item_ids: List[str] = Field(..., description="CoT项目ID列表")
    extraction_method: Optional[str] = Field("llm", description="抽取方法")
    force_reextract: bool = Field(False, description="是否强制重新抽取")


class KGExtractionResponse(BaseModel):
    """知识图谱抽取响应"""
    status: str = Field(..., description="抽取状态")
    message: str = Field(..., description="状态消息")
    cot_item_id: Optional[str] = Field(None, description="单个CoT项目ID")
    cot_item_ids: Optional[List[str]] = Field(None, description="批量CoT项目ID")
    entities_count: Optional[int] = Field(None, description="抽取的实体数量")
    relations_count: Optional[int] = Field(None, description="抽取的关系数量")


class KGNodeData(BaseModel):
    """图节点数据"""
    id: str = Field(..., description="节点ID")
    label: str = Field(..., description="节点标签")
    type: str = Field(..., description="节点类型")
    description: Optional[str] = Field(None, description="节点描述")
    confidence: float = Field(..., description="置信度")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="节点属性")


class KGEdgeData(BaseModel):
    """图边数据"""
    id: str = Field(..., description="边ID")
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    type: str = Field(..., description="关系类型")
    description: Optional[str] = Field(None, description="关系描述")
    confidence: float = Field(..., description="置信度")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="关系属性")


class KGGraphStats(BaseModel):
    """图统计信息"""
    entity_count: int = Field(..., description="实体数量")
    relation_count: int = Field(..., description="关系数量")
    avg_confidence: Optional[float] = Field(None, description="平均置信度")
    extraction_coverage: Optional[str] = Field(None, description="抽取覆盖率")


class KGGraphResponse(BaseModel):
    """知识图谱响应"""
    project_id: str = Field(..., description="项目ID")
    nodes: List[KGNodeData] = Field(..., description="图节点列表")
    edges: List[KGEdgeData] = Field(..., description="图边列表")
    stats: KGGraphStats = Field(..., description="图统计信息")


class KGEntitySearchRequest(BaseModel):
    """实体搜索请求"""
    query: str = Field(..., min_length=1, description="搜索查询")
    entity_type: Optional[str] = Field(None, description="实体类型过滤")
    project_id: Optional[str] = Field(None, description="项目ID过滤")
    limit: int = Field(50, ge=1, le=100, description="结果数量限制")


class KGEntitySearchResponse(BaseModel):
    """实体搜索响应"""
    query: str = Field(..., description="搜索查询")
    entities: List[Dict[str, Any]] = Field(..., description="搜索结果")
    total_count: int = Field(..., description="结果总数")


class KGEmbeddingRequest(BaseModel):
    """向量嵌入请求"""
    text: str = Field(..., description="要嵌入的文本")
    model: Optional[str] = Field("text-embedding-ada-002", description="嵌入模型")


class KGEmbeddingResponse(BaseModel):
    """向量嵌入响应"""
    embedding: List[float] = Field(..., description="嵌入向量")
    dimension: int = Field(..., description="向量维度")
    model: str = Field(..., description="使用的模型")


class KGVisualizationConfig(BaseModel):
    """知识图谱可视化配置"""
    layout: str = Field("force", description="布局算法")
    node_size_field: str = Field("confidence", description="节点大小字段")
    edge_width_field: str = Field("confidence", description="边宽度字段")
    color_scheme: str = Field("category", description="颜色方案")
    show_labels: bool = Field(True, description="是否显示标签")
    max_nodes: int = Field(500, description="最大节点数")


class KGExportRequest(BaseModel):
    """知识图谱导出请求"""
    project_id: str = Field(..., description="项目ID")
    format: str = Field("json", description="导出格式")
    include_embeddings: bool = Field(False, description="是否包含嵌入向量")
    include_metadata: bool = Field(True, description="是否包含元数据")


class KGImportRequest(BaseModel):
    """知识图谱导入请求"""
    project_id: str = Field(..., description="项目ID")
    data: Dict[str, Any] = Field(..., description="导入数据")
    merge_strategy: str = Field("update", description="合并策略")
    validate_data: bool = Field(True, description="是否验证数据")