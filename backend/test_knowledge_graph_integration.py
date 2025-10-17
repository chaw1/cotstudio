"""
知识图谱抽取服务集成测试
"""
import pytest
import asyncio
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.models.project import Project
from app.models.cot import COTItem, COTCandidate, COTSource, COTStatus
from app.models.knowledge_graph import KGEntity, KGRelation, KGExtraction, EntityType, RelationType
from app.services.knowledge_graph_service import KnowledgeGraphService


class TestKnowledgeGraphService:
    """知识图谱服务测试"""
    
    @classmethod
    def setup_class(cls):
        """设置测试类"""
        # 创建测试数据库表
        Base.metadata.create_all(bind=engine)
    
    @classmethod
    def teardown_class(cls):
        """清理测试类"""
        # 删除测试数据库表
        Base.metadata.drop_all(bind=engine)
    
    def setup_method(self):
        """设置测试方法"""
        self.db = SessionLocal()
        
        # 创建测试项目
        self.test_project = Project(
            id="test-project-1",
            name="测试项目",
            owner="test_user",
            description="知识图谱测试项目"
        )
        self.db.add(self.test_project)
        
        # 创建测试CoT数据
        self.test_cot_item = COTItem(
            id="test-cot-1",
            project_id=self.test_project.id,
            slice_id="test-slice-1",
            question="什么是人工智能？",
            chain_of_thought="人工智能是计算机科学的一个分支...",
            source=COTSource.MANUAL,
            status=COTStatus.APPROVED,
            created_by="test_user"
        )
        self.db.add(self.test_cot_item)
        
        # 创建测试候选答案
        self.test_candidate = COTCandidate(
            id="test-candidate-1",
            cot_item_id=self.test_cot_item.id,
            text="人工智能（AI）是指由机器展现的智能，特别是计算机系统。它包括学习、推理和自我纠正的能力。",
            chain_of_thought="首先，人工智能是一个技术领域。其次，它涉及机器学习算法。最后，它可以应用于各种实际问题。",
            score=0.9,
            chosen=True,
            rank=1
        )
        self.db.add(self.test_candidate)
        
        self.db.commit()
        
        # 创建服务实例
        self.kg_service = KnowledgeGraphService(self.db)
    
    def teardown_method(self):
        """清理测试方法"""
        # 清理测试数据
        self.db.query(KGExtraction).delete()
        self.db.query(KGRelation).delete()
        self.db.query(KGEntity).delete()
        self.db.query(COTCandidate).delete()
        self.db.query(COTItem).delete()
        self.db.query(Project).delete()
        self.db.commit()
        self.db.close()
    
    @patch('app.services.knowledge_graph_service.KnowledgeGraphService._generate_text_embedding')
    @patch('app.services.knowledge_graph_service.KnowledgeGraphService._create_neo4j_relation')
    @patch('app.services.knowledge_graph_service.KnowledgeGraphService._create_neo4j_entity')
    @patch('app.services.llm_service.LLMService.generate_response')
    async def test_extract_knowledge_from_cot_success(
        self, 
        mock_llm_response,
        mock_neo4j_entity,
        mock_neo4j_relation,
        mock_embedding
    ):
        """测试成功从CoT数据抽取知识图谱"""
        
        # 模拟LLM响应 - 实体抽取
        mock_llm_response.side_effect = [
            '''[
                {
                    "name": "人工智能",
                    "type": "concept",
                    "description": "计算机科学的一个分支",
                    "confidence": 0.9
                },
                {
                    "name": "机器学习",
                    "type": "concept", 
                    "description": "AI的一个子领域",
                    "confidence": 0.8
                }
            ]''',
            '''[
                {
                    "source": "人工智能",
                    "target": "机器学习",
                    "type": "part_of",
                    "description": "机器学习是人工智能的一部分",
                    "confidence": 0.8
                }
            ]'''
        ]
        
        # 模拟Neo4j响应
        mock_neo4j_entity.return_value = "neo4j-entity-id"
        mock_neo4j_relation.return_value = "neo4j-relation-id"
        
        # 模拟嵌入生成
        mock_embedding.return_value = [0.1] * 128
        
        # 执行抽取
        result = await self.kg_service.extract_knowledge_from_cot(self.test_cot_item.id)
        
        # 验证结果
        assert result["status"] == "success"
        assert result["entities_count"] == 2
        assert result["relations_count"] == 1
        assert result["cot_item_id"] == self.test_cot_item.id
        
        # 验证数据库中的数据
        entities = self.db.query(KGEntity).all()
        assert len(entities) == 2
        
        relations = self.db.query(KGRelation).all()
        assert len(relations) == 1
        
        extractions = self.db.query(KGExtraction).all()
        assert len(extractions) == 3  # 2个实体 + 1个关系
        
        # 验证实体数据
        ai_entity = next((e for e in entities if e.name == "人工智能"), None)
        assert ai_entity is not None
        assert ai_entity.entity_type == "concept"
        assert ai_entity.confidence_score == 0.9
        
        ml_entity = next((e for e in entities if e.name == "机器学习"), None)
        assert ml_entity is not None
        assert ml_entity.entity_type == "concept"
        assert ml_entity.confidence_score == 0.8
        
        # 验证关系数据
        relation = relations[0]
        assert relation.relation_type == "part_of"
        assert relation.confidence_score == 0.8
    
    async def test_extract_knowledge_no_chosen_candidate(self):
        """测试没有选中候选答案的情况"""
        
        # 取消选中候选答案
        self.test_candidate.chosen = False
        self.db.commit()
        
        # 执行抽取
        result = await self.kg_service.extract_knowledge_from_cot(self.test_cot_item.id)
        
        # 验证结果
        assert result["status"] == "skipped"
        assert result["reason"] == "no_chosen_candidate"
    
    async def test_extract_knowledge_nonexistent_cot(self):
        """测试不存在的CoT项目"""
        
        with pytest.raises(ValueError, match="CoT项目不存在"):
            await self.kg_service.extract_knowledge_from_cot("nonexistent-id")
    
    def test_get_project_knowledge_graph(self):
        """测试获取项目知识图谱"""
        
        # 创建测试实体
        entity1 = KGEntity(
            id="entity-1",
            name="测试实体1",
            entity_type="concept",
            description="测试描述1",
            confidence_score=0.9
        )
        entity2 = KGEntity(
            id="entity-2", 
            name="测试实体2",
            entity_type="person",
            description="测试描述2",
            confidence_score=0.8
        )
        self.db.add_all([entity1, entity2])
        
        # 创建测试关系
        relation = KGRelation(
            id="relation-1",
            source_entity_id=entity1.id,
            target_entity_id=entity2.id,
            relation_type="related_to",
            description="测试关系",
            confidence_score=0.7
        )
        self.db.add(relation)
        
        # 创建抽取记录
        extraction1 = KGExtraction(
            id="extraction-1",
            cot_item_id=self.test_cot_item.id,
            project_id=self.test_project.id,
            entity_id=entity1.id,
            extraction_method="llm",
            source_text="测试文本",
            confidence_score=0.9
        )
        extraction2 = KGExtraction(
            id="extraction-2",
            cot_item_id=self.test_cot_item.id,
            project_id=self.test_project.id,
            entity_id=entity2.id,
            extraction_method="llm",
            source_text="测试文本",
            confidence_score=0.8
        )
        extraction3 = KGExtraction(
            id="extraction-3",
            cot_item_id=self.test_cot_item.id,
            project_id=self.test_project.id,
            relation_id=relation.id,
            extraction_method="llm",
            source_text="测试文本",
            confidence_score=0.7
        )
        self.db.add_all([extraction1, extraction2, extraction3])
        self.db.commit()
        
        # 获取知识图谱
        graph_data = self.kg_service.get_project_knowledge_graph(self.test_project.id)
        
        # 验证结果
        assert len(graph_data["nodes"]) == 2
        assert len(graph_data["edges"]) == 1
        assert graph_data["stats"]["entity_count"] == 2
        assert graph_data["stats"]["relation_count"] == 1
        
        # 验证节点数据
        node1 = next((n for n in graph_data["nodes"] if n["label"] == "测试实体1"), None)
        assert node1 is not None
        assert node1["type"] == "concept"
        assert node1["confidence"] == 0.9
        
        # 验证边数据
        edge = graph_data["edges"][0]
        assert edge["type"] == "related_to"
        assert edge["confidence"] == 0.7
    
    def test_search_entities(self):
        """测试实体搜索"""
        
        # 创建测试实体
        entity1 = KGEntity(
            id="entity-1",
            name="人工智能",
            entity_type="concept",
            description="AI技术",
            confidence_score=0.9
        )
        entity2 = KGEntity(
            id="entity-2",
            name="机器学习",
            entity_type="concept", 
            description="ML算法",
            confidence_score=0.8
        )
        entity3 = KGEntity(
            id="entity-3",
            name="张三",
            entity_type="person",
            description="研究员",
            confidence_score=0.7
        )
        self.db.add_all([entity1, entity2, entity3])
        
        # 创建抽取记录
        extraction1 = KGExtraction(
            id="extraction-1",
            cot_item_id=self.test_cot_item.id,
            project_id=self.test_project.id,
            entity_id=entity1.id,
            extraction_method="llm",
            source_text="测试文本",
            confidence_score=0.9
        )
        self.db.add(extraction1)
        self.db.commit()
        
        # 测试基本搜索
        results = self.kg_service.search_entities("智能")
        assert len(results) == 2  # 人工智能 和 机器学习（都包含"智能"相关）
        
        # 测试类型过滤
        results = self.kg_service.search_entities("", entity_type="person")
        assert len(results) == 1
        assert results[0]["name"] == "张三"
        
        # 测试项目过滤
        results = self.kg_service.search_entities("", project_id=self.test_project.id)
        assert len(results) == 1  # 只有entity1有抽取记录关联到项目
        assert results[0]["name"] == "人工智能"
    
    def test_validate_entity(self):
        """测试实体验证"""
        
        # 测试有效实体
        valid_entity = {
            "name": "测试实体",
            "type": "concept",
            "description": "测试描述",
            "confidence": 0.8
        }
        assert self.kg_service._validate_entity(valid_entity) == True
        
        # 测试无效实体类型
        invalid_type_entity = {
            "name": "测试实体",
            "type": "invalid_type",
            "description": "测试描述", 
            "confidence": 0.8
        }
        assert self.kg_service._validate_entity(invalid_type_entity) == True
        assert invalid_type_entity["type"] == "other"  # 应该被修正为other
        
        # 测试无效置信度
        invalid_confidence_entity = {
            "name": "测试实体",
            "type": "concept",
            "description": "测试描述",
            "confidence": 1.5  # 超出范围
        }
        assert self.kg_service._validate_entity(invalid_confidence_entity) == True
        assert invalid_confidence_entity["confidence"] == 0.5  # 应该被修正为0.5
        
        # 测试缺少字段
        incomplete_entity = {
            "name": "测试实体",
            "type": "concept"
            # 缺少description和confidence
        }
        assert self.kg_service._validate_entity(incomplete_entity) == False
    
    def test_validate_relation(self):
        """测试关系验证"""
        
        entity_names = ["实体1", "实体2", "实体3"]
        
        # 测试有效关系
        valid_relation = {
            "source": "实体1",
            "target": "实体2",
            "type": "related_to",
            "description": "测试关系",
            "confidence": 0.7
        }
        assert self.kg_service._validate_relation(valid_relation, entity_names) == True
        
        # 测试不存在的实体
        invalid_entity_relation = {
            "source": "不存在的实体",
            "target": "实体2",
            "type": "related_to",
            "description": "测试关系",
            "confidence": 0.7
        }
        assert self.kg_service._validate_relation(invalid_entity_relation, entity_names) == False
        
        # 测试无效关系类型
        invalid_type_relation = {
            "source": "实体1",
            "target": "实体2", 
            "type": "invalid_relation",
            "description": "测试关系",
            "confidence": 0.7
        }
        assert self.kg_service._validate_relation(invalid_type_relation, entity_names) == True
        assert invalid_type_relation["type"] == "other"  # 应该被修正为other


def test_kg_service_integration():
    """集成测试入口"""
    test_instance = TestKnowledgeGraphService()
    
    # 设置测试类
    test_instance.setup_class()
    
    try:
        # 运行测试方法
        test_instance.setup_method()
        
        # 测试获取项目知识图谱
        test_instance.test_get_project_knowledge_graph()
        print("✓ 测试获取项目知识图谱 - 通过")
        
        # 测试实体搜索
        test_instance.test_search_entities()
        print("✓ 测试实体搜索 - 通过")
        
        # 测试实体验证
        test_instance.test_validate_entity()
        print("✓ 测试实体验证 - 通过")
        
        # 测试关系验证
        test_instance.test_validate_relation()
        print("✓ 测试关系验证 - 通过")
        
        test_instance.teardown_method()
        
        # 测试异步方法
        async def run_async_tests():
            test_instance.setup_method()
            
            # 测试没有选中候选答案
            await test_instance.test_extract_knowledge_no_chosen_candidate()
            print("✓ 测试没有选中候选答案 - 通过")
            
            # 测试不存在的CoT项目
            try:
                await test_instance.test_extract_knowledge_nonexistent_cot()
            except ValueError:
                print("✓ 测试不存在的CoT项目 - 通过")
            
            test_instance.teardown_method()
        
        # 运行异步测试
        asyncio.run(run_async_tests())
        
        print("\n🎉 所有知识图谱服务测试通过！")
        
    finally:
        # 清理测试类
        test_instance.teardown_class()


if __name__ == "__main__":
    test_kg_service_integration()