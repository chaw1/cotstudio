"""
导入相关的Celery任务
"""
import os
import traceback
from typing import Dict, Any, List
from celery import current_task
from sqlalchemy.orm import Session

from ..core.celery_app import celery_app
from ..core.database import get_db
from ..services.import_service import ImportService
from ..schemas.import_schemas import (
    ImportRequest, ImportAnalysisResult, ImportResult, 
    ConflictResolution, ImportStatus
)
from ..models.user import User


@celery_app.task(bind=True)
def validate_import_file_task(self, file_path: str) -> Dict[str, Any]:
    """
    验证导入文件任务
    
    Args:
        file_path: 文件路径
        
    Returns:
        验证结果
    """
    try:
        # 更新任务状态
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'message': '开始验证文件...'}
        )
        
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 创建导入服务
            import_service = ImportService(db)
            
            # 更新进度
            current_task.update_state(
                state='PROGRESS',
                meta={'progress': 50, 'message': '正在验证文件格式和内容...'}
            )
            
            # 执行验证 (需要在异步上下文中运行)
            import asyncio
            validation_result = asyncio.run(import_service.validate_import_file(file_path))
            
            # 更新进度
            current_task.update_state(
                state='PROGRESS',
                meta={'progress': 100, 'message': '验证完成'}
            )
            
            return {
                'status': 'completed',
                'result': validation_result.dict(),
                'message': '文件验证完成'
            }
        
        finally:
            db.close()
    
    except Exception as e:
        error_msg = f"文件验证失败: {str(e)}"
        traceback.print_exc()
        
        return {
            'status': 'failed',
            'error': error_msg,
            'message': error_msg
        }


@celery_app.task(bind=True)
def analyze_import_differences_task(
    self, 
    file_path: str, 
    target_project_id: str = None
) -> Dict[str, Any]:
    """
    分析导入差异任务
    
    Args:
        file_path: 导入文件路径
        target_project_id: 目标项目ID
        
    Returns:
        分析结果
    """
    try:
        # 更新任务状态
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'message': '开始分析差异...'}
        )
        
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 创建导入服务
            import_service = ImportService(db)
            
            # 更新进度
            current_task.update_state(
                state='PROGRESS',
                meta={'progress': 30, 'message': '加载导入数据...'}
            )
            
            # 执行差异分析 (需要在异步上下文中运行)
            import asyncio
            analysis_result = asyncio.run(import_service.analyze_import_differences(
                file_path, target_project_id
            ))
            
            # 更新进度
            current_task.update_state(
                state='PROGRESS',
                meta={'progress': 80, 'message': '生成差异报告...'}
            )
            
            # 计算差异摘要
            differences_summary = {
                'total_differences': analysis_result.statistics.get('total_differences', 0),
                'total_conflicts': analysis_result.statistics.get('total_conflicts', 0),
                'new_items': analysis_result.statistics.get('new_items', 0),
                'modified_items': analysis_result.statistics.get('modified_items', 0),
                'deleted_items': analysis_result.statistics.get('deleted_items', 0)
            }
            
            # 更新进度
            current_task.update_state(
                state='PROGRESS',
                meta={'progress': 100, 'message': '差异分析完成'}
            )
            
            return {
                'status': 'completed',
                'result': analysis_result.dict(),
                'differences_summary': differences_summary,
                'message': '差异分析完成'
            }
        
        finally:
            db.close()
    
    except Exception as e:
        error_msg = f"差异分析失败: {str(e)}"
        traceback.print_exc()
        
        return {
            'status': 'failed',
            'error': error_msg,
            'message': error_msg
        }


@celery_app.task(bind=True)
def execute_import_task(
    self,
    import_request_dict: Dict[str, Any],
    confirmed_differences: List[str],
    conflict_resolutions_dict: Dict[str, Dict[str, Any]],
    user_id: str
) -> Dict[str, Any]:
    """
    执行导入任务
    
    Args:
        import_request_dict: 导入请求字典
        confirmed_differences: 确认的差异ID列表
        conflict_resolutions_dict: 冲突解决方案字典
        user_id: 用户ID
        
    Returns:
        导入结果
    """
    try:
        # 更新任务状态
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 5, 'message': '初始化导入任务...'}
        )
        
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 创建导入服务
            import_service = ImportService(db)
            
            # 转换请求对象
            import_request = ImportRequest(**import_request_dict)
            
            # 转换冲突解决方案
            conflict_resolutions = {}
            for key, value in conflict_resolutions_dict.items():
                conflict_resolutions[key] = ConflictResolution(**value)
            
            # 获取用户信息
            current_user = db.query(User).filter(User.id == user_id).first()
            if not current_user:
                raise ValueError(f"用户不存在: {user_id}")
            
            # 更新进度
            current_task.update_state(
                state='PROGRESS',
                meta={'progress': 10, 'message': '准备导入数据...'}
            )
            
            # 执行导入 (需要在异步上下文中运行)
            import asyncio
            import_result = asyncio.run(import_service.execute_import(
                import_request,
                confirmed_differences,
                conflict_resolutions,
                current_user
            ))
            
            # 更新进度
            if import_result.success:
                current_task.update_state(
                    state='PROGRESS',
                    meta={'progress': 100, 'message': '导入完成'}
                )
                
                return {
                    'status': 'completed',
                    'result': import_result.dict(),
                    'message': '数据导入完成'
                }
            else:
                return {
                    'status': 'failed',
                    'result': import_result.dict(),
                    'error': '; '.join(import_result.errors),
                    'message': '导入过程中出现错误'
                }
        
        finally:
            db.close()
    
    except Exception as e:
        error_msg = f"导入执行失败: {str(e)}"
        traceback.print_exc()
        
        return {
            'status': 'failed',
            'error': error_msg,
            'message': error_msg
        }


def update_import_progress(task_id: str, step: str, progress: float, message: str):
    """
    更新导入进度
    
    Args:
        task_id: 任务ID
        step: 当前步骤
        progress: 进度百分比
        message: 进度消息
    """
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={
                'progress': progress,
                'message': message,
                'current_step': step
            }
        )
    except Exception as e:
        print(f"更新进度失败: {str(e)}")


@celery_app.task(bind=True)
def cleanup_import_files_task(self, file_paths: List[str]) -> Dict[str, Any]:
    """
    清理导入文件任务
    
    Args:
        file_paths: 要清理的文件路径列表
        
    Returns:
        清理结果
    """
    try:
        cleaned_files = []
        failed_files = []
        
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    cleaned_files.append(file_path)
            except Exception as e:
                failed_files.append(f"{file_path}: {str(e)}")
        
        return {
            'status': 'completed',
            'cleaned_files': cleaned_files,
            'failed_files': failed_files,
            'message': f'清理完成，成功: {len(cleaned_files)}, 失败: {len(failed_files)}'
        }
    
    except Exception as e:
        return {
            'status': 'failed',
            'error': str(e),
            'message': f'清理任务失败: {str(e)}'
        }