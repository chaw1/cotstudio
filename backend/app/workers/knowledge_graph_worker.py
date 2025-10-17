"""
知识图谱抽取异步任务
"""
import logging
from typing import Dict, Any
from celery import Celery
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..services.knowledge_graph_service import KnowledgeGraphService
from ..worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="extract_knowledge_graph")
def extract_knowledge_graph_task(self, cot_item_id: str) -> Dict[str, Any]:
    """
    异步抽取知识图谱任务
    
    Args:
        cot_item_id: CoT项目ID
        
    Returns:
        抽取结果
    """
    try:
        # 更新任务状态
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "开始抽取知识图谱..."}
        )
        
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 创建KG服务实例
            kg_service = KnowledgeGraphService(db)
            
            # 更新进度
            self.update_state(
                state="PROGRESS",
                meta={"current": 20, "total": 100, "status": "正在抽取实体..."}
            )
            
            # 执行抽取
            import asyncio
            result = asyncio.run(kg_service.extract_knowledge_from_cot(cot_item_id))
            
            # 更新进度
            self.update_state(
                state="PROGRESS",
                meta={"current": 80, "total": 100, "status": "正在生成向量嵌入..."}
            )
            
            # 完成
            self.update_state(
                state="SUCCESS",
                meta={"current": 100, "total": 100, "status": "知识图谱抽取完成"}
            )
            
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"知识图谱抽取任务失败: {e}")
        
        # 更新任务状态为失败
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "知识图谱抽取失败"}
        )
        
        raise


@celery_app.task(bind=True, name="batch_extract_knowledge_graph")
def batch_extract_knowledge_graph_task(self, cot_item_ids: list) -> Dict[str, Any]:
    """
    批量异步抽取知识图谱任务
    
    Args:
        cot_item_ids: CoT项目ID列表
        
    Returns:
        批量抽取结果
    """
    try:
        total_items = len(cot_item_ids)
        results = []
        
        # 更新任务状态
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": total_items, "status": f"开始批量抽取 {total_items} 个项目..."}
        )
        
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 创建KG服务实例
            kg_service = KnowledgeGraphService(db)
            
            for i, cot_item_id in enumerate(cot_item_ids):
                try:
                    # 更新进度
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "current": i,
                            "total": total_items,
                            "status": f"正在处理项目 {i+1}/{total_items}: {cot_item_id}"
                        }
                    )
                    
                    # 执行单个抽取
                    import asyncio
                    result = asyncio.run(kg_service.extract_knowledge_from_cot(cot_item_id))
                    results.append({
                        "cot_item_id": cot_item_id,
                        "status": "success",
                        "result": result
                    })
                    
                except Exception as e:
                    logger.error(f"处理CoT项目 {cot_item_id} 失败: {e}")
                    results.append({
                        "cot_item_id": cot_item_id,
                        "status": "error",
                        "error": str(e)
                    })
            
            # 完成
            success_count = sum(1 for r in results if r["status"] == "success")
            error_count = total_items - success_count
            
            self.update_state(
                state="SUCCESS",
                meta={
                    "current": total_items,
                    "total": total_items,
                    "status": f"批量抽取完成: 成功 {success_count}, 失败 {error_count}"
                }
            )
            
            return {
                "total_items": total_items,
                "success_count": success_count,
                "error_count": error_count,
                "results": results
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"批量知识图谱抽取任务失败: {e}")
        
        # 更新任务状态为失败
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "批量知识图谱抽取失败"}
        )
        
        raise


@celery_app.task(name="cleanup_kg_data")
def cleanup_kg_data_task(project_id: str) -> Dict[str, Any]:
    """
    清理项目知识图谱数据任务
    
    Args:
        project_id: 项目ID
        
    Returns:
        清理结果
    """
    try:
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 这里实现清理逻辑
            # 1. 删除数据库中的KG数据
            # 2. 删除Neo4j中的节点和关系
            # 3. 删除向量嵌入数据
            
            from ..models.knowledge_graph import KGEntity, KGRelation, KGExtraction, KGEmbedding
            from ..core.neo4j_connection import get_neo4j_connection
            
            # 删除抽取记录
            extractions = db.query(KGExtraction).filter(
                KGExtraction.project_id == project_id
            ).all()
            
            entity_ids = [e.entity_id for e in extractions if e.entity_id]
            relation_ids = [e.relation_id for e in extractions if e.relation_id]
            
            # 删除嵌入数据
            db.query(KGEmbedding).filter(
                KGEmbedding.entity_id.in_(entity_ids) if entity_ids else False
            ).delete(synchronize_session=False)
            
            db.query(KGEmbedding).filter(
                KGEmbedding.relation_id.in_(relation_ids) if relation_ids else False
            ).delete(synchronize_session=False)
            
            # 删除关系
            if relation_ids:
                db.query(KGRelation).filter(
                    KGRelation.id.in_(relation_ids)
                ).delete(synchronize_session=False)
            
            # 删除实体（如果没有其他项目引用）
            if entity_ids:
                for entity_id in entity_ids:
                    # 检查是否有其他项目引用此实体
                    other_extractions = db.query(KGExtraction).filter(
                        KGExtraction.entity_id == entity_id,
                        KGExtraction.project_id != project_id
                    ).count()
                    
                    if other_extractions == 0:
                        db.query(KGEntity).filter(KGEntity.id == entity_id).delete()
            
            # 删除抽取记录
            db.query(KGExtraction).filter(
                KGExtraction.project_id == project_id
            ).delete(synchronize_session=False)
            
            db.commit()
            
            # 删除Neo4j中的数据
            neo4j = get_neo4j_connection()
            neo4j.execute_query(
                "MATCH (n) WHERE n.project_id = $project_id DETACH DELETE n",
                {"project_id": project_id}
            )
            
            return {
                "status": "success",
                "message": f"项目 {project_id} 的知识图谱数据已清理",
                "deleted_entities": len(entity_ids),
                "deleted_relations": len(relation_ids),
                "deleted_extractions": len(extractions)
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"清理知识图谱数据失败: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(name="regenerate_embeddings")
def regenerate_embeddings_task(project_id: str, embedding_model: str = "text-embedding-ada-002") -> Dict[str, Any]:
    """
    重新生成项目的向量嵌入任务
    
    Args:
        project_id: 项目ID
        embedding_model: 嵌入模型名称
        
    Returns:
        重新生成结果
    """
    try:
        # 获取数据库会话
        db = next(get_db())
        
        try:
            kg_service = KnowledgeGraphService(db)
            
            # 获取项目相关的实体和关系
            from ..models.knowledge_graph import KGEntity, KGRelation, KGExtraction
            
            entities = db.query(KGEntity).join(KGExtraction).filter(
                KGExtraction.project_id == project_id
            ).distinct().all()
            
            relations = db.query(KGRelation).join(KGExtraction).filter(
                KGExtraction.project_id == project_id
            ).distinct().all()
            
            # 重新生成嵌入
            import asyncio
            asyncio.run(kg_service._generate_embeddings(entities, relations))
            
            return {
                "status": "success",
                "message": f"项目 {project_id} 的向量嵌入已重新生成",
                "entities_count": len(entities),
                "relations_count": len(relations),
                "embedding_model": embedding_model
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"重新生成向量嵌入失败: {e}")
        return {
            "status": "error",
            "error": str(e)
        }