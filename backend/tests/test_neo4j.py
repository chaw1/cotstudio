"""
Neo4j连接和知识图谱测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.core.neo4j_db import Neo4jConnection, KnowledgeGraphQueries, init_neo4j_schema


class TestNeo4jConnection:
    """Neo4j连接测试"""
    
    @patch('app.core.neo4j_db.GraphDatabase.driver')
    def test_neo4j_connection_success(self, mock_driver):
        """测试成功连接Neo4j"""
        # 模拟成功的连接
        mock_session = Mock()
        mock_driver_instance = Mock()
        mock_driver_instance.session.return_value.__enter__.return_value = mock_session
        mock_driver_instance.session.return_value.__exit__.return_value = None
        mock_driver.return_value = mock_driver_instance
        
        # 创建连接
        connection = Neo4jConnection()
        
        # 验证连接已建立
        assert connection._driver is not None
        mock_driver.assert_called_once()
    
    @patch('app.core.neo4j_db.GraphDatabase.driver')
    def test_neo4j_connection_failure(self, mock_driver):
        """测试Neo4j连接失败"""
        # 模拟连接失败
        mock_driver.side_effect = Exception("Connection failed")
        
        # 创建连接
        connection = Neo4jConnection()
        
        # 验证连接失败时的处理
        assert connection._driver is None
    
    @patch('app.core.neo4j_db.GraphDatabase.driver')
    def test_execute_query(self, mock_driver):
        """测试执行查询"""
        # 模拟查询结果
        mock_record = Mock()
        mock_record.data.return_value = {"name": "Test Entity", "type": "Person"}
        
        mock_result = Mock()
        mock_result.__iter__.return_value = iter([mock_record])
        
        mock_session = Mock()
        mock_session.run.return_value = mock_result
        
        mock_driver_instance = Mock()
        mock_driver_instance.session.return_value.__enter__.return_value = mock_session
        mock_driver_instance.session.return_value.__exit__.return_value = None
        mock_driver.return_value = mock_driver_instance
        
        # 创建连接并执行查询
        connection = Neo4jConnection()
        result = connection.execute_query("MATCH (n) RETURN n LIMIT 1")
        
        # 验证结果
        assert len(result) == 1
        assert result[0]["name"] == "Test Entity"
        assert result[0]["type"] == "Person"
    
    @patch('app.core.neo4j_db.GraphDatabase.driver')
    def test_execute_write_transaction(self, mock_driver):
        """测试执行写事务"""
        mock_record = Mock()
        mock_record.data.return_value = {"id": "entity-123", "created": True}
        
        mock_tx = Mock()
        mock_tx.run.return_value = [mock_record]
        
        mock_session = Mock()
        mock_session.execute_write.return_value = [{"id": "entity-123", "created": True}]
        
        mock_driver_instance = Mock()
        mock_driver_instance.session.return_value.__enter__.return_value = mock_session
        mock_driver_instance.session.return_value.__exit__.return_value = None
        mock_driver.return_value = mock_driver_instance
        
        # 创建连接并执行写事务
        connection = Neo4jConnection()
        result = connection.execute_write_transaction(
            "CREATE (e:Entity {id: $id, name: $name}) RETURN e",
            {"id": "entity-123", "name": "Test Entity"}
        )
        
        # 验证结果
        assert len(result) == 1
        assert result[0]["id"] == "entity-123"
    
    @patch('app.core.neo4j_db.GraphDatabase.driver')
    def test_close_connection(self, mock_driver):
        """测试关闭连接"""
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        # 创建连接并关闭
        connection = Neo4jConnection()
        connection.close()
        
        # 验证连接已关闭
        mock_driver_instance.close.assert_called_once()
        assert connection._driver is None


class TestKnowledgeGraphQueries:
    """知识图谱查询测试"""
    
    def test_query_templates_exist(self):
        """测试查询模板是否存在"""
        # 验证所有必需的查询模板都存在
        assert hasattr(KnowledgeGraphQueries, 'CREATE_ENTITY')
        assert hasattr(KnowledgeGraphQueries, 'CREATE_DOCUMENT')
        assert hasattr(KnowledgeGraphQueries, 'CREATE_CONCEPT')
        assert hasattr(KnowledgeGraphQueries, 'CREATE_COT_ITEM')
        assert hasattr(KnowledgeGraphQueries, 'CREATE_ENTITY_RELATIONSHIP')
        assert hasattr(KnowledgeGraphQueries, 'LINK_ENTITY_TO_DOCUMENT')
        assert hasattr(KnowledgeGraphQueries, 'LINK_COT_TO_ENTITY')
        assert hasattr(KnowledgeGraphQueries, 'FIND_ENTITY_RELATIONSHIPS')
        assert hasattr(KnowledgeGraphQueries, 'FIND_ENTITIES_IN_DOCUMENT')
        assert hasattr(KnowledgeGraphQueries, 'FIND_ENTITIES_FOR_COT')
        assert hasattr(KnowledgeGraphQueries, 'SEARCH_ENTITIES')
    
    def test_query_template_format(self):
        """测试查询模板格式"""
        # 验证查询模板包含正确的参数占位符
        assert "$entity_id" in KnowledgeGraphQueries.CREATE_ENTITY
        assert "$name" in KnowledgeGraphQueries.CREATE_ENTITY
        assert "$entity_type" in KnowledgeGraphQueries.CREATE_ENTITY
        
        assert "$document_id" in KnowledgeGraphQueries.CREATE_DOCUMENT
        assert "$title" in KnowledgeGraphQueries.CREATE_DOCUMENT
        
        assert "$cot_item_id" in KnowledgeGraphQueries.CREATE_COT_ITEM
        assert "$question" in KnowledgeGraphQueries.CREATE_COT_ITEM


@patch('app.core.neo4j_db.neo4j_connection')
def test_init_neo4j_schema(mock_connection):
    """测试Neo4j模式初始化"""
    # 模拟会话
    mock_session = Mock()
    mock_connection.get_session.return_value.__enter__.return_value = mock_session
    mock_connection.get_session.return_value.__exit__.return_value = None
    
    # 执行模式初始化
    init_neo4j_schema()
    
    # 验证约束和索引创建命令被执行
    assert mock_session.run.call_count > 0
    
    # 验证特定的约束创建命令
    calls = [call[0][0] for call in mock_session.run.call_args_list]
    constraint_calls = [call for call in calls if "CREATE CONSTRAINT" in call]
    index_calls = [call for call in calls if "CREATE INDEX" in call]
    
    assert len(constraint_calls) > 0
    assert len(index_calls) > 0
    
    # 验证特定约束
    entity_constraint = any("entity_id" in call for call in constraint_calls)
    document_constraint = any("document_id" in call for call in constraint_calls)
    concept_constraint = any("concept_id" in call for call in constraint_calls)
    
    assert entity_constraint
    assert document_constraint
    assert concept_constraint


class TestKnowledgeGraphIntegration:
    """知识图谱集成测试"""
    
    @patch('app.core.neo4j_db.GraphDatabase.driver')
    def test_create_entity_workflow(self, mock_driver):
        """测试创建实体的完整工作流"""
        # 模拟成功的实体创建
        mock_record = Mock()
        mock_record.data.return_value = {
            "e": {
                "id": "entity-123",
                "name": "Albert Einstein",
                "type": "Person",
                "properties": {"birth_year": 1879}
            }
        }
        
        mock_session = Mock()
        mock_session.run.return_value = [mock_record]
        
        mock_driver_instance = Mock()
        mock_driver_instance.session.return_value.__enter__.return_value = mock_session
        mock_driver_instance.session.return_value.__exit__.return_value = None
        mock_driver.return_value = mock_driver_instance
        
        # 创建连接并执行实体创建
        connection = Neo4jConnection()
        result = connection.execute_query(
            KnowledgeGraphQueries.CREATE_ENTITY,
            {
                "entity_id": "entity-123",
                "name": "Albert Einstein",
                "entity_type": "Person",
                "properties": {"birth_year": 1879}
            }
        )
        
        # 验证结果
        assert len(result) == 1
        entity = result[0]["e"]
        assert entity["id"] == "entity-123"
        assert entity["name"] == "Albert Einstein"
        assert entity["type"] == "Person"
    
    @patch('app.core.neo4j_db.GraphDatabase.driver')
    def test_link_entity_to_document_workflow(self, mock_driver):
        """测试将实体链接到文档的工作流"""
        mock_record = Mock()
        mock_record.data.return_value = {
            "r": {
                "start_offset": 100,
                "end_offset": 115,
                "context": "Albert Einstein was a theoretical physicist"
            }
        }
        
        mock_session = Mock()
        mock_session.run.return_value = [mock_record]
        
        mock_driver_instance = Mock()
        mock_driver_instance.session.return_value.__enter__.return_value = mock_session
        mock_driver_instance.session.return_value.__exit__.return_value = None
        mock_driver.return_value = mock_driver_instance
        
        # 创建连接并执行链接操作
        connection = Neo4jConnection()
        result = connection.execute_query(
            KnowledgeGraphQueries.LINK_ENTITY_TO_DOCUMENT,
            {
                "entity_id": "entity-123",
                "document_id": "doc-456",
                "start_offset": 100,
                "end_offset": 115,
                "context": "Albert Einstein was a theoretical physicist"
            }
        )
        
        # 验证结果
        assert len(result) == 1
        relationship = result[0]["r"]
        assert relationship["start_offset"] == 100
        assert relationship["end_offset"] == 115
        assert "Albert Einstein" in relationship["context"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])