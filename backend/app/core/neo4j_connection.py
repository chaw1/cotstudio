"""
Neo4j数据库连接管理
"""
from typing import Optional, Dict, Any, List
import logging
from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, AuthError

from .config import settings

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Neo4j数据库连接管理器"""
    
    def __init__(self):
        self._driver: Optional[Driver] = None
        self._uri = settings.NEO4J_URI
        self._user = settings.NEO4J_USER
        self._password = settings.NEO4J_PASSWORD
    
    def connect(self) -> bool:
        """建立Neo4j连接"""
        try:
            self._driver = GraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password)
            )
            # 测试连接
            with self._driver.session() as session:
                session.run("RETURN 1")
            logger.info("Neo4j连接建立成功")
            return True
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Neo4j连接失败: {e}")
            return False
        except Exception as e:
            logger.error(f"Neo4j连接异常: {e}")
            return False
    
    def close(self):
        """关闭Neo4j连接"""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j连接已关闭")
    
    def get_session(self) -> Optional[Session]:
        """获取Neo4j会话"""
        if not self._driver:
            if not self.connect():
                return None
        return self._driver.session()
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行Cypher查询"""
        if not parameters:
            parameters = {}
        
        try:
            with self.get_session() as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Neo4j查询执行失败: {e}")
            raise
    
    def execute_write_transaction(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行写事务"""
        if not parameters:
            parameters = {}
        
        try:
            with self.get_session() as session:
                result = session.write_transaction(self._run_query, query, parameters)
                return result
        except Exception as e:
            logger.error(f"Neo4j写事务执行失败: {e}")
            raise
    
    def execute_read_transaction(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行读事务"""
        if not parameters:
            parameters = {}
        
        try:
            with self.get_session() as session:
                result = session.read_transaction(self._run_query, query, parameters)
                return result
        except Exception as e:
            logger.error(f"Neo4j读事务执行失败: {e}")
            raise
    
    @staticmethod
    def _run_query(tx, query: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """事务中执行查询的辅助方法"""
        result = tx.run(query, parameters)
        return [record.data() for record in result]
    
    def create_constraints_and_indexes(self):
        """创建约束和索引"""
        constraints_and_indexes = [
            # 实体节点约束
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS NOT NULL",
            
            # 文档节点约束
            "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            
            # 概念节点约束
            "CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
            
            # CoT项目节点约束
            "CREATE CONSTRAINT cot_item_id IF NOT EXISTS FOR (cot:COTItem) REQUIRE cot.id IS UNIQUE",
            
            # 索引
            "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX document_project_idx IF NOT EXISTS FOR (d:Document) ON (d.project_id)",
            "CREATE INDEX cot_project_idx IF NOT EXISTS FOR (cot:COTItem) ON (cot.project_id)",
        ]
        
        for constraint_or_index in constraints_and_indexes:
            try:
                self.execute_query(constraint_or_index)
                logger.info(f"成功创建约束/索引: {constraint_or_index}")
            except Exception as e:
                logger.warning(f"创建约束/索引失败 (可能已存在): {constraint_or_index}, 错误: {e}")


# 全局Neo4j连接实例
neo4j_connection = Neo4jConnection()


def get_neo4j_connection() -> Neo4jConnection:
    """获取Neo4j连接实例"""
    return neo4j_connection


def init_neo4j():
    """初始化Neo4j连接和约束"""
    if neo4j_connection.connect():
        neo4j_connection.create_constraints_and_indexes()
        return True
    return False


def close_neo4j():
    """关闭Neo4j连接"""
    neo4j_connection.close()