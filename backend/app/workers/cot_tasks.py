"""
CoT生成相关的Celery任务
"""
import asyncio
import logging
from typing import Optional
from uuid import UUID
from celery import current_app as celery_app

from ..core.database import SessionLocal
from ..services.cot_generation_service import create_cot_generation_service
from ..services.cot_service import COTService
from ..models.slice import Slice
from ..models.project import Project


logger = logging.getLogger(__name__)


def run_async(coro):
    """运行异步函数的同步包装器"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


@celery_app.task(bind=True, name="generate_cot_async")
def generate_cot_async(
    self,
    project_id: str,
    slice_id: str,
    created_by: str,
    candidate_count: Optional[int] = None,
    context: Optional[str] = None
):
    """
    异步生成CoT数据项
    
    Args:
        project_id: 项目ID
        slice_id: 切片ID
        created_by: 创建者
        candidate_count: 候选答案数量
        context: 可选的上下文信息
    """
    try:
        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting CoT generation...'}
        )
        
        # 创建数据库会话
        db = SessionLocal()
        
        try:
            # 获取文本片段
            slice_obj = db.query(Slice).filter(Slice.id == slice_id).first()
            if not slice_obj:
                raise ValueError(f"Slice {slice_id} not found")
            
            # 验证项目存在
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            self.update_state(
                state='PROGRESS',
                meta={'current': 20, 'total': 100, 'status': 'Generating question...'}
            )
            
            # 创建CoT生成服务
            cot_generation_service = create_cot_generation_service()
            
            # 生成问题
            question = run_async(cot_generation_service.generate_question(
                slice_content=slice_obj.content,
                context=context
            ))
            
            self.update_state(
                state='PROGRESS',
                meta={'current': 50, 'total': 100, 'status': 'Generating candidates...'}
            )
            
            # 生成候选答案
            candidates = run_async(cot_generation_service.generate_candidates(
                question=question,
                slice_content=slice_obj.content,
                candidate_count=candidate_count,
                context=context
            ))
            
            self.update_state(
                state='PROGRESS',
                meta={'current': 80, 'total': 100, 'status': 'Saving to database...'}
            )
            
            # 创建完整的CoT数据
            cot_create = run_async(cot_generation_service.generate_cot_item(
                project_id=UUID(project_id),
                slice_id=UUID(slice_id),
                slice_content=slice_obj.content,
                created_by=created_by,
                candidate_count=candidate_count,
                context=context
            ))
            
            # 保存到数据库
            cot_service = COTService(db)
            cot_item = run_async(cot_service.create_cot_item(cot_create))
            
            self.update_state(
                state='PROGRESS',
                meta={'current': 100, 'total': 100, 'status': 'CoT generation completed'}
            )
            
            return {
                'status': 'SUCCESS',
                'cot_id': str(cot_item.id),
                'question': cot_item.question,
                'candidate_count': len(cot_item.candidates),
                'message': 'CoT generation completed successfully'
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in CoT generation task: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': 'CoT generation failed'}
        )
        raise


@celery_app.task(bind=True, name="regenerate_question_async")
def regenerate_question_async(
    self,
    cot_id: str,
    slice_content: str,
    context: Optional[str] = None
):
    """
    异步重新生成问题
    
    Args:
        cot_id: CoT项目ID
        slice_content: 文本片段内容
        context: 可选的上下文信息
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting question regeneration...'}
        )
        
        # 创建CoT生成服务
        cot_generation_service = create_cot_generation_service()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Generating new question...'}
        )
        
        # 重新生成问题
        new_question = run_async(cot_generation_service.regenerate_question(
            cot_item_id=UUID(cot_id),
            slice_content=slice_content,
            context=context
        ))
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': 'Updating database...'}
        )
        
        # 更新数据库
        db = SessionLocal()
        try:
            cot_service = COTService(db)
            updated_cot = cot_service.update_cot_question(UUID(cot_id), new_question)
            
            self.update_state(
                state='PROGRESS',
                meta={'current': 100, 'total': 100, 'status': 'Question regeneration completed'}
            )
            
            return {
                'status': 'SUCCESS',
                'cot_id': cot_id,
                'new_question': new_question,
                'message': 'Question regeneration completed successfully'
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in question regeneration task: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': 'Question regeneration failed'}
        )
        raise


@celery_app.task(bind=True, name="regenerate_candidates_async")
def regenerate_candidates_async(
    self,
    cot_id: str,
    question: str,
    slice_content: str,
    candidate_count: Optional[int] = None,
    context: Optional[str] = None
):
    """
    异步重新生成候选答案
    
    Args:
        cot_id: CoT项目ID
        question: 问题文本
        slice_content: 文本片段内容
        candidate_count: 候选答案数量
        context: 可选的上下文信息
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting candidates regeneration...'}
        )
        
        # 创建CoT生成服务
        cot_generation_service = create_cot_generation_service()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Generating new candidates...'}
        )
        
        # 重新生成候选答案
        new_candidates = run_async(cot_generation_service.regenerate_candidates(
            question=question,
            slice_content=slice_content,
            candidate_count=candidate_count,
            context=context
        ))
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': 'Updating database...'}
        )
        
        # 更新数据库
        db = SessionLocal()
        try:
            cot_service = COTService(db)
            updated_candidates = cot_service.update_candidates(UUID(cot_id), new_candidates)
            
            self.update_state(
                state='PROGRESS',
                meta={'current': 100, 'total': 100, 'status': 'Candidates regeneration completed'}
            )
            
            return {
                'status': 'SUCCESS',
                'cot_id': cot_id,
                'candidate_count': len(updated_candidates),
                'message': 'Candidates regeneration completed successfully'
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in candidates regeneration task: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': 'Candidates regeneration failed'}
        )
        raise


@celery_app.task(bind=True, name="batch_generate_cot")
def batch_generate_cot(
    self,
    project_id: str,
    slice_ids: list,
    created_by: str,
    candidate_count: Optional[int] = None
):
    """
    批量生成CoT数据项
    
    Args:
        project_id: 项目ID
        slice_ids: 切片ID列表
        created_by: 创建者
        candidate_count: 候选答案数量
    """
    try:
        total_slices = len(slice_ids)
        completed = 0
        failed = 0
        results = []
        
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 0,
                'total': total_slices,
                'status': f'Starting batch CoT generation for {total_slices} slices...'
            }
        )
        
        for i, slice_id in enumerate(slice_ids):
            try:
                # 调用单个CoT生成任务
                result = generate_cot_async.apply_async(
                    args=[project_id, slice_id, created_by, candidate_count],
                    countdown=i * 2  # 错开执行时间避免API限制
                )
                
                # 等待结果
                task_result = result.get(timeout=300)  # 5分钟超时
                
                results.append({
                    'slice_id': slice_id,
                    'status': 'SUCCESS',
                    'cot_id': task_result.get('cot_id'),
                    'message': task_result.get('message')
                })
                completed += 1
                
            except Exception as e:
                logger.error(f"Failed to generate CoT for slice {slice_id}: {str(e)}")
                results.append({
                    'slice_id': slice_id,
                    'status': 'FAILED',
                    'error': str(e)
                })
                failed += 1
            
            # 更新进度
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': i + 1,
                    'total': total_slices,
                    'completed': completed,
                    'failed': failed,
                    'status': f'Processed {i + 1}/{total_slices} slices'
                }
            )
        
        return {
            'status': 'SUCCESS',
            'total_slices': total_slices,
            'completed': completed,
            'failed': failed,
            'results': results,
            'message': f'Batch CoT generation completed: {completed} succeeded, {failed} failed'
        }
        
    except Exception as e:
        logger.error(f"Error in batch CoT generation task: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': 'Batch CoT generation failed'}
        )
        raise