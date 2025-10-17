"""
知识图谱抽取服务
"""
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4
import re
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.knowledge_graph import (
    KGEntity, KGRelation, KGExtraction, KGEmbedding,
    EntityType, RelationType
)
from ..models.cot import COTItem, COTCandidate
from ..core.neo4j_connection import get_neo4j_connection
from ..services.llm_service import LLMService

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """知识图谱抽取服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.neo4j = get_neo4j_connection()
        self.llm_service = LLMService()
    
    async def extract_knowledge_from_cot(self, cot_item_id: str) -> Dict[str, Any]:
        """
        从CoT数据中抽取知识图谱
        
        Args:
            cot_item_id: CoT项目ID
            
        Returns:
            抽取结果统计
        """
        # 获取CoT数据
        cot_item = self.db.query(COTItem).filter(COTItem.id == cot_item_id).first()
        if not cot_item:
            raise ValueError(f"CoT项目不存在: {cot_item_id}")
        
        # 获取最佳候选答案
        chosen_candidate = self.db.query(COTCandidate).filter(
            and_(
                COTCandidate.cot_item_id == cot_item_id,
                COTCandidate.chosen == True
            )
        ).first()
        
        if not chosen_candidate:
            logger.warning(f"CoT项目 {cot_item_id} 没有选中的候选答案，跳过KG抽取")
            return {"status": "skipped", "reason": "no_chosen_candidate"}
        
        # 准备抽取文本
        extraction_text = f"问题: {cot_item.question}\n\n答案: {chosen_candidate.text}\n\n推理过程: {chosen_candidate.chain_of_thought}"
        
        try:
            # 抽取实体
            entities = await self._extract_entities(extraction_text)
            
            # 抽取关系
            relations = await self._extract_relations(extraction_text, entities)
            
            # 存储到数据库和Neo4j
            stored_entities = await self._store_entities(entities, cot_item, extraction_text)
            stored_relations = await self._store_relations(relations, stored_entities, cot_item, extraction_text)
            
            # 生成向量嵌入
            await self._generate_embeddings(stored_entities, stored_relations)
            
            return {
                "status": "success",
                "entities_count": len(stored_entities),
                "relations_count": len(stored_relations),
                "cot_item_id": cot_item_id
            }
            
        except Exception as e:
            logger.error(f"KG抽取失败: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """使用LLM抽取实体"""
        prompt = f"""
请从以下文本中抽取实体，包括人物、组织、地点、概念、事件、对象等。
对每个实体，请提供：
1. 实体名称
2. 实体类型 (person/organization/location/concept/event/object/other)
3. 简短描述
4. 置信度分数 (0-1)

文本：
{text}

请以JSON格式返回，格式如下：
[
  {{
    "name": "实体名称",
    "type": "实体类型",
    "description": "实体描述",
    "confidence": 0.9
  }}
]
"""
        
        try:
            response = await self.llm_service.generate_response(prompt)
            # 尝试解析JSON响应
            entities_data = self._parse_json_response(response)
            
            # 验证和清理数据
            validated_entities = []
            for entity in entities_data:
                if self._validate_entity(entity):
                    validated_entities.append(entity)
            
            return validated_entities
            
        except Exception as e:
            logger.error(f"实体抽取失败: {e}")
            return []
    
    async def _extract_relations(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """使用LLM抽取关系"""
        if len(entities) < 2:
            return []
        
        entity_names = [entity["name"] for entity in entities]
        
        prompt = f"""
请从以下文本中抽取实体之间的关系。
已识别的实体：{', '.join(entity_names)}

对每个关系，请提供：
1. 源实体名称
2. 目标实体名称  
3. 关系类型 (is_a/part_of/related_to/causes/located_in/works_for/mentions/derived_from/other)
4. 关系描述
5. 置信度分数 (0-1)

文本：
{text}

请以JSON格式返回，格式如下：
[
  {{
    "source": "源实体名称",
    "target": "目标实体名称",
    "type": "关系类型",
    "description": "关系描述",
    "confidence": 0.8
  }}
]
"""
        
        try:
            response = await self.llm_service.generate_response(prompt)
            relations_data = self._parse_json_response(response)
            
            # 验证和清理数据
            validated_relations = []
            for relation in relations_data:
                if self._validate_relation(relation, entity_names):
                    validated_relations.append(relation)
            
            return validated_relations
            
        except Exception as e:
            logger.error(f"关系抽取失败: {e}")
            return []
    
    def _parse_json_response(self, response: str) -> List[Dict[str, Any]]:
        """解析LLM的JSON响应"""
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # 如果都失败了，返回空列表
            logger.warning(f"无法解析JSON响应: {response}")
            return []
    
    def _validate_entity(self, entity: Dict[str, Any]) -> bool:
        """验证实体数据"""
        required_fields = ["name", "type", "description", "confidence"]
        if not all(field in entity for field in required_fields):
            return False
        
        # 验证实体类型
        valid_types = [e.value for e in EntityType]
        if entity["type"] not in valid_types:
            entity["type"] = "other"
        
        # 验证置信度
        try:
            confidence = float(entity["confidence"])
            if not 0 <= confidence <= 1:
                entity["confidence"] = 0.5
        except (ValueError, TypeError):
            entity["confidence"] = 0.5
        
        return True
    
    def _validate_relation(self, relation: Dict[str, Any], entity_names: List[str]) -> bool:
        """验证关系数据"""
        required_fields = ["source", "target", "type", "description", "confidence"]
        if not all(field in relation for field in required_fields):
            return False
        
        # 验证实体存在
        if relation["source"] not in entity_names or relation["target"] not in entity_names:
            return False
        
        # 验证关系类型
        valid_types = [r.value for r in RelationType]
        if relation["type"] not in valid_types:
            relation["type"] = "other"
        
        # 验证置信度
        try:
            confidence = float(relation["confidence"])
            if not 0 <= confidence <= 1:
                relation["confidence"] = 0.5
        except (ValueError, TypeError):
            relation["confidence"] = 0.5
        
        return True
    
    async def _store_entities(self, entities: List[Dict[str, Any]], cot_item: COTItem, source_text: str) -> List[KGEntity]:
        """存储实体到数据库和Neo4j"""
        stored_entities = []
        
        for entity_data in entities:
            # 检查实体是否已存在
            existing_entity = self.db.query(KGEntity).filter(
                and_(
                    KGEntity.name == entity_data["name"],
                    KGEntity.entity_type == entity_data["type"]
                )
            ).first()
            
            if existing_entity:
                # 更新置信度（取最高值）
                if entity_data["confidence"] > existing_entity.confidence_score:
                    existing_entity.confidence_score = entity_data["confidence"]
                    self.db.commit()
                stored_entities.append(existing_entity)
            else:
                # 创建新实体
                entity = KGEntity(
                    id=str(uuid4()),
                    name=entity_data["name"],
                    entity_type=entity_data["type"],
                    description=entity_data["description"],
                    confidence_score=entity_data["confidence"],
                    properties={}
                )
                
                self.db.add(entity)
                self.db.commit()
                
                # 存储到Neo4j
                neo4j_node_id = await self._create_neo4j_entity(entity)
                entity.neo4j_node_id = neo4j_node_id
                self.db.commit()
                
                stored_entities.append(entity)
            
            # 创建抽取记录
            extraction = KGExtraction(
                id=str(uuid4()),
                cot_item_id=cot_item.id,
                project_id=cot_item.project_id,
                entity_id=stored_entities[-1].id,
                extraction_method="llm",
                source_text=source_text,
                confidence_score=entity_data["confidence"],
                extraction_metadata={"llm_provider": self.llm_service.current_provider}
            )
            
            self.db.add(extraction)
        
        self.db.commit()
        return stored_entities
    
    async def _store_relations(self, relations: List[Dict[str, Any]], entities: List[KGEntity], 
                             cot_item: COTItem, source_text: str) -> List[KGRelation]:
        """存储关系到数据库和Neo4j"""
        stored_relations = []
        entity_map = {entity.name: entity for entity in entities}
        
        for relation_data in relations:
            source_entity = entity_map.get(relation_data["source"])
            target_entity = entity_map.get(relation_data["target"])
            
            if not source_entity or not target_entity:
                continue
            
            # 检查关系是否已存在
            existing_relation = self.db.query(KGRelation).filter(
                and_(
                    KGRelation.source_entity_id == source_entity.id,
                    KGRelation.target_entity_id == target_entity.id,
                    KGRelation.relation_type == relation_data["type"]
                )
            ).first()
            
            if existing_relation:
                # 更新置信度
                if relation_data["confidence"] > existing_relation.confidence_score:
                    existing_relation.confidence_score = relation_data["confidence"]
                    self.db.commit()
                stored_relations.append(existing_relation)
            else:
                # 创建新关系
                relation = KGRelation(
                    id=str(uuid4()),
                    source_entity_id=source_entity.id,
                    target_entity_id=target_entity.id,
                    relation_type=relation_data["type"],
                    description=relation_data["description"],
                    confidence_score=relation_data["confidence"],
                    properties={}
                )
                
                self.db.add(relation)
                self.db.commit()
                
                # 存储到Neo4j
                neo4j_relation_id = await self._create_neo4j_relation(relation, source_entity, target_entity)
                relation.neo4j_relation_id = neo4j_relation_id
                self.db.commit()
                
                stored_relations.append(relation)
            
            # 创建抽取记录
            extraction = KGExtraction(
                id=str(uuid4()),
                cot_item_id=cot_item.id,
                project_id=cot_item.project_id,
                relation_id=stored_relations[-1].id,
                extraction_method="llm",
                source_text=source_text,
                confidence_score=relation_data["confidence"],
                extraction_metadata={"llm_provider": self.llm_service.current_provider}
            )
            
            self.db.add(extraction)
        
        self.db.commit()
        return stored_relations
    
    async def _create_neo4j_entity(self, entity: KGEntity) -> str:
        """在Neo4j中创建实体节点"""
        query = """
        CREATE (e:Entity {
            id: $entity_id,
            name: $name,
            type: $type,
            description: $description,
            confidence: $confidence,
            created_at: datetime()
        })
        RETURN e.id as node_id
        """
        
        parameters = {
            "entity_id": entity.id,
            "name": entity.name,
            "type": entity.entity_type,
            "description": entity.description,
            "confidence": entity.confidence_score
        }
        
        try:
            result = self.neo4j.execute_write_transaction(query, parameters)
            return result[0]["node_id"] if result else entity.id
        except Exception as e:
            logger.error(f"创建Neo4j实体节点失败: {e}")
            return entity.id
    
    async def _create_neo4j_relation(self, relation: KGRelation, source_entity: KGEntity, target_entity: KGEntity) -> str:
        """在Neo4j中创建关系"""
        query = """
        MATCH (source:Entity {id: $source_id})
        MATCH (target:Entity {id: $target_id})
        CREATE (source)-[r:RELATION {
            id: $relation_id,
            type: $relation_type,
            description: $description,
            confidence: $confidence,
            created_at: datetime()
        }]->(target)
        RETURN r.id as relation_id
        """
        
        parameters = {
            "source_id": source_entity.id,
            "target_id": target_entity.id,
            "relation_id": relation.id,
            "relation_type": relation.relation_type,
            "description": relation.description,
            "confidence": relation.confidence_score
        }
        
        try:
            result = self.neo4j.execute_write_transaction(query, parameters)
            return result[0]["relation_id"] if result else relation.id
        except Exception as e:
            logger.error(f"创建Neo4j关系失败: {e}")
            return relation.id
    
    async def _generate_embeddings(self, entities: List[KGEntity], relations: List[KGRelation]):
        """生成向量嵌入"""
        # 这里使用简单的文本嵌入，实际项目中可以使用更复杂的嵌入模型
        try:
            for entity in entities:
                embedding_text = f"{entity.name}: {entity.description}"
                # 这里应该调用实际的嵌入服务，暂时使用模拟数据
                embedding_vector = await self._generate_text_embedding(embedding_text)
                
                # 存储嵌入
                embedding = KGEmbedding(
                    id=str(uuid4()),
                    entity_id=entity.id,
                    embedding_model="text-embedding-ada-002",  # 示例模型
                    embedding_vector=embedding_vector,
                    vector_dimension=len(embedding_vector),
                    source_text=embedding_text,
                    embedding_metadata={}
                )
                
                self.db.add(embedding)
            
            for relation in relations:
                embedding_text = f"{relation.relation_type}: {relation.description}"
                embedding_vector = await self._generate_text_embedding(embedding_text)
                
                embedding = KGEmbedding(
                    id=str(uuid4()),
                    relation_id=relation.id,
                    embedding_model="text-embedding-ada-002",
                    embedding_vector=embedding_vector,
                    vector_dimension=len(embedding_vector),
                    source_text=embedding_text,
                    embedding_metadata={}
                )
                
                self.db.add(embedding)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"生成嵌入失败: {e}")
    
    async def _generate_text_embedding(self, text: str) -> List[float]:
        """生成文本嵌入向量（模拟实现）"""
        # 这里应该调用实际的嵌入API，比如OpenAI的embedding API
        # 暂时返回模拟的向量数据
        import hashlib
        import struct
        
        # 使用文本哈希生成确定性的模拟向量
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # 将哈希转换为浮点数向量
        vector = []
        for i in range(0, len(hash_bytes), 4):
            chunk = hash_bytes[i:i+4]
            if len(chunk) == 4:
                value = struct.unpack('f', chunk)[0]
                # 归一化到[-1, 1]范围
                normalized_value = (value % 2.0) - 1.0
                vector.append(normalized_value)
        
        # 确保向量长度为128维
        while len(vector) < 128:
            vector.append(0.0)
        
        return vector[:128]
    
    def get_project_knowledge_graph(self, project_id: str) -> Dict[str, Any]:
        """获取项目的知识图谱数据"""
        # 获取项目相关的实体 (修复: 使用distinct(KGEntity.id)避免JSON字段比较错误)
        entities = self.db.query(KGEntity).join(KGExtraction).filter(
            KGExtraction.project_id == project_id
        ).distinct(KGEntity.id).all()

        # 获取项目相关的关系 (修复: 使用distinct(KGRelation.id)避免JSON字段比较错误)
        relations = self.db.query(KGRelation).join(KGExtraction).filter(
            KGExtraction.project_id == project_id
        ).distinct(KGRelation.id).all()
        
        # 构建图数据
        nodes = []
        edges = []
        
        for entity in entities:
            nodes.append({
                "id": entity.id,
                "label": entity.name,
                "type": entity.entity_type,
                "description": entity.description,
                "confidence": entity.confidence_score
            })
        
        for relation in relations:
            edges.append({
                "id": relation.id,
                "source": relation.source_entity_id,
                "target": relation.target_entity_id,
                "type": relation.relation_type,
                "description": relation.description,
                "confidence": relation.confidence_score
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "entity_count": len(entities),
                "relation_count": len(relations)
            }
        }
    
    def search_entities(self, query: str, entity_type: Optional[str] = None, 
                       project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """搜索实体"""
        query_filter = KGEntity.name.ilike(f"%{query}%")
        
        if entity_type:
            query_filter = and_(query_filter, KGEntity.entity_type == entity_type)
        
        if project_id:
            query_filter = and_(
                query_filter,
                KGEntity.extractions.any(KGExtraction.project_id == project_id)
            )
        
        entities = self.db.query(KGEntity).filter(query_filter).limit(50).all()
        
        return [
            {
                "id": entity.id,
                "name": entity.name,
                "type": entity.entity_type,
                "description": entity.description,
                "confidence": entity.confidence_score
            }
            for entity in entities
        ]