"""
Neo4j数据库连接和会话管理
"""
from typing import Optional, Dict, Any, List
from neo4j import GraphDatabase, Driver, Session
from contextlib import contextmanager
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Neo4j数据库连接管理器"""
    
    def __init__(self):
        self._driver: Optional[Driver] = None
        self._connect()
    
    def _connect(self):
        """建立Neo4j连接"""
        try:
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            # 测试连接
            with self._driver.session() as session:
                session.run("RETURN 1")
            logger.info("Neo4j connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self._driver = None
    
    @contextmanager
    def get_session(self) -> Session:
        """获取Neo4j会话的上下文管理器"""
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized")
        
        session = self._driver.session()
        try:
            yield session
        finally:
            session.close()
    
    def close(self):
        """关闭Neo4j连接"""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行Cypher查询"""
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized")
        
        with self.get_session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def execute_write_transaction(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行写事务"""
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized")
        
        def _write_tx(tx, query, params):
            result = tx.run(query, params)
            return [record.data() for record in result]
        
        with self.get_session() as session:
            return session.execute_write(_write_tx, query, parameters or {})


# 全局Neo4j连接实例
neo4j_connection = Neo4jConnection()


def get_neo4j_connection() -> Neo4jConnection:
    """获取Neo4j连接实例"""
    return neo4j_connection


def init_neo4j_schema():
    """初始化Neo4j数据库模式"""
    try:
        with neo4j_connection.get_session() as session:
            # 创建约束和索引
            constraints_and_indexes = [
                # 实体节点约束
                "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
                
                # 文档节点约束
                "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
                
                # 概念节点约束
                "CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
                
                # CoT项目节点约束
                "CREATE CONSTRAINT cot_item_id IF NOT EXISTS FOR (cot:COTItem) REQUIRE cot.id IS UNIQUE",
                
                # 项目节点约束
                "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
                
                # 创建索引以提高查询性能
                "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.type)",
                "CREATE INDEX document_title_idx IF NOT EXISTS FOR (d:Document) ON (d.title)",
                "CREATE INDEX concept_name_idx IF NOT EXISTS FOR (c:Concept) ON (c.name)",
            ]
            
            for constraint_or_index in constraints_and_indexes:
                try:
                    session.run(constraint_or_index)
                    logger.info(f"Applied: {constraint_or_index}")
                except Exception as e:
                    # 约束或索引可能已存在，这是正常的
                    logger.debug(f"Constraint/Index already exists or failed: {e}")
        
        logger.info("Neo4j schema initialization completed")
        
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j schema: {e}")
        raise


# 知识图谱相关的Cypher查询模板
class KnowledgeGraphQueries:
    """知识图谱查询模板"""
    
    # 创建实体节点
    CREATE_ENTITY = """
    MERGE (e:Entity {id: $entity_id})
    SET e.name = $name,
        e.type = $entity_type,
        e.properties = $properties,
        e.created_at = datetime(),
        e.updated_at = datetime()
    RETURN e
    """
    
    # 创建文档节点
    CREATE_DOCUMENT = """
    MERGE (d:Document {id: $document_id})
    SET d.title = $title,
        d.file_path = $file_path,
        d.content_hash = $content_hash,
        d.created_at = datetime(),
        d.updated_at = datetime()
    RETURN d
    """
    
    # 创建概念节点
    CREATE_CONCEPT = """
    MERGE (c:Concept {id: $concept_id})
    SET c.name = $name,
        c.description = $description,
        c.category = $category,
        c.created_at = datetime(),
        c.updated_at = datetime()
    RETURN c
    """
    
    # 创建CoT项目节点
    CREATE_COT_ITEM = """
    MERGE (cot:COTItem {id: $cot_item_id})
    SET cot.question = $question,
        cot.answer = $answer,
        cot.chain_of_thought = $chain_of_thought,
        cot.score = $score,
        cot.created_at = datetime(),
        cot.updated_at = datetime()
    RETURN cot
    """
    
    # 创建实体关系
    CREATE_ENTITY_RELATIONSHIP = """
    MATCH (e1:Entity {id: $entity1_id})
    MATCH (e2:Entity {id: $entity2_id})
    MERGE (e1)-[r:RELATED_TO {type: $relationship_type}]->(e2)
    SET r.properties = $properties,
        r.confidence = $confidence,
        r.created_at = datetime()
    RETURN r
    """
    
    # 连接实体到文档
    LINK_ENTITY_TO_DOCUMENT = """
    MATCH (e:Entity {id: $entity_id})
    MATCH (d:Document {id: $document_id})
    MERGE (e)-[r:MENTIONED_IN]->(d)
    SET r.start_offset = $start_offset,
        r.end_offset = $end_offset,
        r.context = $context,
        r.created_at = datetime()
    RETURN r
    """
    
    # 连接CoT项目到实体
    LINK_COT_TO_ENTITY = """
    MATCH (cot:COTItem {id: $cot_item_id})
    MATCH (e:Entity {id: $entity_id})
    MERGE (cot)-[r:REFERENCES]->(e)
    SET r.relevance_score = $relevance_score,
        r.created_at = datetime()
    RETURN r
    """
    
    # 查询实体及其关系
    FIND_ENTITY_RELATIONSHIPS = """
    MATCH (e:Entity {id: $entity_id})-[r]-(related)
    RETURN e, r, related
    LIMIT $limit
    """
    
    # 查询文档中的实体
    FIND_ENTITIES_IN_DOCUMENT = """
    MATCH (e:Entity)-[:MENTIONED_IN]->(d:Document {id: $document_id})
    RETURN e
    ORDER BY e.name
    """
    
    # 查询与CoT项目相关的实体
    FIND_ENTITIES_FOR_COT = """
    MATCH (cot:COTItem {id: $cot_item_id})-[:REFERENCES]->(e:Entity)
    RETURN e
    ORDER BY e.name
    """
    
    # 全文搜索实体
    SEARCH_ENTITIES = """
    MATCH (e:Entity)
    WHERE e.name CONTAINS $search_term OR any(prop IN keys(e.properties) WHERE e.properties[prop] CONTAINS $search_term)
    RETURN e
    ORDER BY e.name
    LIMIT $limit
    """