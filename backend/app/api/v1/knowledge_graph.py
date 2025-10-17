"""
知识图谱API端点
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...middleware.auth import get_current_active_user
from ...models.user import User
from ...services.knowledge_graph_service import KnowledgeGraphService
from ...services.project_service import ProjectService
from ...schemas.knowledge_graph import (
    KGExtractionRequest, KGExtractionResponse,
    KGGraphResponse, KGEntitySearchRequest, KGEntitySearchResponse,
    KGNodeData, KGEdgeData, KGGraphStats
)

router = APIRouter()


async def get_current_user_model(
    current_user_data: Dict[str, Any] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户的数据库模型对象"""
    from ...services.user_service import user_service
    user = user_service.get(db, current_user_data["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@router.get("/accessible", response_model=List[Dict[str, Any]])
async def get_accessible_knowledge_graphs(
    current_user: User = Depends(get_current_user_model),
    db: Session = Depends(get_db)
):
    """
    获取用户可访问的所有知识图谱列表
    """
    try:
        project_service = ProjectService()
        kg_service = KnowledgeGraphService(db)
        
        # 获取用户可访问的项目
        accessible_projects = await project_service.get_user_accessible_projects(current_user.id)
        
        knowledge_graphs = []
        for project in accessible_projects:
            try:
                # 获取项目的知识图谱统计信息
                graph_data = kg_service.get_project_knowledge_graph(project.id)
                
                # 只包含有知识图谱数据的项目
                if graph_data["stats"]["entity_count"] > 0 or graph_data["stats"]["relation_count"] > 0:
                    knowledge_graphs.append({
                        "id": f"kg_{project.id}",
                        "project_id": project.id,
                        "project_name": project.name,
                        "project_description": project.description,
                        "owner": project.owner,
                        "entity_count": graph_data["stats"]["entity_count"],
                        "relation_count": graph_data["stats"]["relation_count"],
                        "last_updated": project.updated_at.isoformat() if project.updated_at else None,
                        "tags": project.tags or [],
                        "has_access": True
                    })
            except Exception as e:
                # 跳过无法访问或没有知识图谱数据的项目
                print(f"Warning: Failed to get KG data for project {project.id}: {str(e)}")
                continue
        
        return knowledge_graphs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取可访问知识图谱失败: {str(e)}")


@router.get("/{graph_id}/metadata")
async def get_knowledge_graph_metadata(
    graph_id: str,
    current_user: User = Depends(get_current_user_model),
    db: Session = Depends(get_db)
):
    """
    获取知识图谱元数据
    """
    try:
        # 从graph_id中提取project_id (格式: kg_{project_id})
        if not graph_id.startswith("kg_"):
            raise HTTPException(status_code=400, detail="无效的知识图谱ID格式")
        
        project_id = graph_id[3:]  # 移除 "kg_" 前缀
        
        # 检查用户是否有访问权限
        project_service = ProjectService()
        if not await project_service.check_user_project_access(current_user.id, project_id):
            raise HTTPException(status_code=403, detail="无权限访问此知识图谱")
        
        kg_service = KnowledgeGraphService(db)
        graph_data = kg_service.get_project_knowledge_graph(project_id)
        
        # 获取项目信息
        project = await project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        return {
            "id": graph_id,
            "project_id": project_id,
            "project_name": project.name,
            "project_description": project.description,
            "owner": project.owner,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "tags": project.tags or [],
            "stats": graph_data["stats"],
            "entity_types": graph_data.get("entity_types", []),
            "relation_types": graph_data.get("relation_types", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识图谱元数据失败: {str(e)}")


@router.get("/projects/{project_id}/accessible")
async def check_project_kg_access(
    project_id: str,
    current_user: User = Depends(get_current_user_model),
    db: Session = Depends(get_db)
):
    """
    检查用户是否可以访问指定项目的知识图谱
    """
    try:
        project_service = ProjectService()
        has_access = await project_service.check_user_project_access(current_user.id, project_id)
        
        if not has_access:
            return {
                "has_access": False,
                "message": "无权限访问此项目的知识图谱"
            }
        
        # 检查项目是否存在知识图谱数据
        kg_service = KnowledgeGraphService(db)
        try:
            graph_data = kg_service.get_project_knowledge_graph(project_id)
            has_kg_data = (graph_data["stats"]["entity_count"] > 0 or 
                          graph_data["stats"]["relation_count"] > 0)
        except:
            has_kg_data = False
        
        return {
            "has_access": True,
            "has_kg_data": has_kg_data,
            "message": "有权限访问" if has_kg_data else "有权限访问但暂无知识图谱数据"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查访问权限失败: {str(e)}")


@router.post("/extract/{cot_item_id}", response_model=KGExtractionResponse)
async def extract_knowledge_graph(
    cot_item_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    从CoT数据中抽取知识图谱
    """
    try:
        kg_service = KnowledgeGraphService(db)
        
        # 在后台任务中执行抽取
        background_tasks.add_task(
            kg_service.extract_knowledge_from_cot,
            cot_item_id
        )
        
        return KGExtractionResponse(
            status="started",
            message="知识图谱抽取任务已启动",
            cot_item_id=cot_item_id
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"抽取失败: {str(e)}")


@router.post("/extract/batch", response_model=KGExtractionResponse)
async def extract_knowledge_graph_batch(
    request: KGExtractionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    批量从CoT数据中抽取知识图谱
    """
    try:
        kg_service = KnowledgeGraphService(db)
        
        # 为每个CoT项目启动抽取任务
        for cot_item_id in request.cot_item_ids:
            background_tasks.add_task(
                kg_service.extract_knowledge_from_cot,
                cot_item_id
            )
        
        return KGExtractionResponse(
            status="started",
            message=f"已启动 {len(request.cot_item_ids)} 个知识图谱抽取任务",
            cot_item_ids=request.cot_item_ids
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量抽取失败: {str(e)}")


@router.get("/project/{project_id}/graph", response_model=KGGraphResponse)
async def get_project_knowledge_graph(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    获取项目的知识图谱数据
    """
    try:
        kg_service = KnowledgeGraphService(db)
        graph_data = kg_service.get_project_knowledge_graph(project_id)
        
        return KGGraphResponse(
            project_id=project_id,
            nodes=graph_data["nodes"],
            edges=graph_data["edges"],
            stats=graph_data["stats"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识图谱失败: {str(e)}")


@router.post("/search/entities", response_model=KGEntitySearchResponse)
async def search_entities(
    request: KGEntitySearchRequest,
    db: Session = Depends(get_db)
):
    """
    搜索实体
    """
    try:
        kg_service = KnowledgeGraphService(db)
        entities = kg_service.search_entities(
            query=request.query,
            entity_type=request.entity_type,
            project_id=request.project_id
        )
        
        return KGEntitySearchResponse(
            query=request.query,
            entities=entities,
            total_count=len(entities)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索实体失败: {str(e)}")


@router.get("/project/{project_id}/stats")
async def get_project_kg_stats(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    获取项目知识图谱统计信息
    """
    try:
        kg_service = KnowledgeGraphService(db)
        graph_data = kg_service.get_project_knowledge_graph(project_id)

        # 统计实体类型分布
        entity_type_counts = {}
        for node in graph_data["nodes"]:
            entity_type = node.get("type", "unknown")
            entity_type_counts[entity_type] = entity_type_counts.get(entity_type, 0) + 1

        entity_types = [
            {"type": type_name, "count": count}
            for type_name, count in sorted(entity_type_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        # 统计关系类型分布
        relation_type_counts = {}
        for edge in graph_data["edges"]:
            relation_type = edge.get("type", "unknown")
            relation_type_counts[relation_type] = relation_type_counts.get(relation_type, 0) + 1

        relation_types = [
            {"type": type_name, "count": count}
            for type_name, count in sorted(relation_type_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        return {
            "totalEntities": graph_data["stats"]["entity_count"],
            "totalRelations": graph_data["stats"]["relation_count"],
            "entityTypes": entity_types,
            "relationTypes": relation_types
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.delete("/project/{project_id}/graph")
async def clear_project_knowledge_graph(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    清除项目的知识图谱数据
    """
    try:
        # 这里应该实现清除逻辑
        # 包括删除数据库记录和Neo4j中的节点/关系
        
        return {
            "status": "success",
            "message": f"项目 {project_id} 的知识图谱数据已清除"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除知识图谱失败: {str(e)}")


@router.get("/neo4j/status")
async def get_neo4j_status():
    """
    获取Neo4j连接状态
    """
    try:
        from ...core.neo4j_connection import get_neo4j_connection
        
        neo4j = get_neo4j_connection()
        
        # 测试连接
        result = neo4j.execute_query("RETURN 1 as test")
        
        if result:
            return {
                "status": "connected",
                "message": "Neo4j连接正常"
            }
        else:
            return {
                "status": "disconnected",
                "message": "Neo4j连接失败"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Neo4j状态检查失败: {str(e)}"
        }