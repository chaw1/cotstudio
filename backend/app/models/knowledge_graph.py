"""
知识图谱数据模型
"""
from sqlalchemy import Column, String, Text, Float, Integer, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import BaseModel


class EntityType(PyEnum):
    """实体类型枚举"""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    CONCEPT = "concept"
    EVENT = "event"
    OBJECT = "object"
    OTHER = "other"


class RelationType(PyEnum):
    """关系类型枚举"""
    IS_A = "is_a"
    PART_OF = "part_of"
    RELATED_TO = "related_to"
    CAUSES = "causes"
    LOCATED_IN = "located_in"
    WORKS_FOR = "works_for"
    MENTIONS = "mentions"
    DERIVED_FROM = "derived_from"
    OTHER = "other"


class KGEntity(BaseModel):
    """
    知识图谱实体模型
    """
    __tablename__ = "kg_entities"
    
    name = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)  # EntityType enum value
    description = Column(Text)
    properties = Column(JSON)  # 存储实体的属性信息
    confidence_score = Column(Float, default=0.0)
    
    # Neo4j节点ID，用于关联图数据库
    neo4j_node_id = Column(String(255), unique=True, index=True)
    
    # 向量嵌入相关
    embedding_vector = Column(JSON)  # 存储向量嵌入
    embedding_model = Column(String(100))  # 使用的嵌入模型
    
    # 关系
    extractions = relationship("KGExtraction", back_populates="entity")
    
    # 索引
    __table_args__ = (
        Index('idx_kg_entity_name_type', 'name', 'entity_type'),
        Index('idx_kg_entity_neo4j_id', 'neo4j_node_id'),
    )
    
    def __repr__(self):
        return f"<KGEntity(name='{self.name}', type='{self.entity_type}')>"


class KGRelation(BaseModel):
    """
    知识图谱关系模型
    """
    __tablename__ = "kg_relations"
    
    source_entity_id = Column(String(36), ForeignKey("kg_entities.id"), nullable=False)
    target_entity_id = Column(String(36), ForeignKey("kg_entities.id"), nullable=False)
    relation_type = Column(String(50), nullable=False)  # RelationType enum value
    description = Column(Text)
    properties = Column(JSON)  # 存储关系的属性信息
    confidence_score = Column(Float, default=0.0)
    
    # Neo4j关系ID，用于关联图数据库
    neo4j_relation_id = Column(String(255), unique=True, index=True)
    
    # 关系
    source_entity = relationship("KGEntity", foreign_keys=[source_entity_id])
    target_entity = relationship("KGEntity", foreign_keys=[target_entity_id])
    extractions = relationship("KGExtraction", back_populates="relation")
    
    # 索引
    __table_args__ = (
        Index('idx_kg_relation_entities', 'source_entity_id', 'target_entity_id'),
        Index('idx_kg_relation_type', 'relation_type'),
        Index('idx_kg_relation_neo4j_id', 'neo4j_relation_id'),
    )
    
    def __repr__(self):
        return f"<KGRelation(type='{self.relation_type}', source='{self.source_entity_id}', target='{self.target_entity_id}')>"


class KGExtraction(BaseModel):
    """
    知识图谱抽取记录模型 - 关联CoT数据和KG数据
    """
    __tablename__ = "kg_extractions"
    
    # 关联的CoT数据
    cot_item_id = Column(String(36), ForeignKey("cot_items.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    
    # 抽取的实体或关系
    entity_id = Column(String(36), ForeignKey("kg_entities.id"), nullable=True)
    relation_id = Column(String(36), ForeignKey("kg_relations.id"), nullable=True)
    
    # 抽取信息
    extraction_method = Column(String(100), nullable=False)  # 抽取方法：llm, rule_based, hybrid
    source_text = Column(Text, nullable=False)  # 原始文本片段
    context = Column(Text)  # 上下文信息
    confidence_score = Column(Float, default=0.0)
    
    # 元数据
    extraction_metadata = Column(JSON)  # 抽取过程的元数据
    
    # 关系
    cot_item = relationship("COTItem")
    project = relationship("Project")
    entity = relationship("KGEntity", back_populates="extractions")
    relation = relationship("KGRelation", back_populates="extractions")
    
    # 索引
    __table_args__ = (
        Index('idx_kg_extraction_cot', 'cot_item_id'),
        Index('idx_kg_extraction_project', 'project_id'),
        Index('idx_kg_extraction_entity', 'entity_id'),
        Index('idx_kg_extraction_relation', 'relation_id'),
    )
    
    def __repr__(self):
        return f"<KGExtraction(cot_item_id='{self.cot_item_id}', method='{self.extraction_method}')>"


class KGEmbedding(BaseModel):
    """
    向量嵌入模型
    """
    __tablename__ = "kg_embeddings"
    
    # 关联的实体或关系
    entity_id = Column(String(36), ForeignKey("kg_entities.id"), nullable=True)
    relation_id = Column(String(36), ForeignKey("kg_relations.id"), nullable=True)
    
    # 嵌入信息
    embedding_model = Column(String(100), nullable=False)  # 使用的嵌入模型
    embedding_vector = Column(JSON, nullable=False)  # 向量数据
    vector_dimension = Column(Integer, nullable=False)  # 向量维度
    
    # 文本信息
    source_text = Column(Text, nullable=False)  # 用于生成嵌入的文本
    
    # 元数据
    embedding_metadata = Column(JSON)  # 嵌入生成的元数据
    
    # 关系
    entity = relationship("KGEntity")
    relation = relationship("KGRelation")
    
    # 索引
    __table_args__ = (
        Index('idx_kg_embedding_entity', 'entity_id'),
        Index('idx_kg_embedding_relation', 'relation_id'),
        Index('idx_kg_embedding_model', 'embedding_model'),
    )
    
    def __repr__(self):
        return f"<KGEmbedding(model='{self.embedding_model}', dimension={self.vector_dimension})>"