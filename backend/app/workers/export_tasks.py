"""
导出相关的Celery任务
"""
import os
import asyncio
import traceback
from typing import Dict, Any
from celery import current_task
from sqlalchemy.orm import Session

from ..worker import celery_app
from ..core.database import get_db
from ..services.export_service import ExportService
from ..services.export_task_service import ExportTaskService
from ..schemas.export import ExportRequest, ExportFormat


def run_async(coro):
    """运行异步函数的同步包装器"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


@celery_app.task(bind=True)
def export_project_task(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    异步导出项目任务
    
    Args:
        request_data: 导出请求数据
        
    Returns:
        任务结果
    """
    try:
        # 更新任务状态
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'message': '开始导出项目数据...'}
        )
        
        # 创建导出请求对象
        export_request = ExportRequest(**request_data)
        
        # 获取数据库会话
        db = next(get_db())
        export_service = ExportService(db)
        task_service = ExportTaskService(db)
        
        try:
            # 更新数据库任务状态
            run_async(task_service.update_task_status(
                task_id=self.request.id,
                status='processing',
                progress=10.0,
                message='开始处理导出任务...'
            ))
            
            # 更新进度
            current_task.update_state(
                state='PROGRESS',
                meta={'progress': 20, 'message': '收集项目数据...'}
            )
            
            # 执行导出
            if export_request.format in [ExportFormat.JSON, ExportFormat.MARKDOWN, 
                                       ExportFormat.LATEX, ExportFormat.TXT]:
                file_path = run_async(export_service.export_project(export_request))
            else:
                # 创建项目包
                file_path = run_async(export_service.create_project_package(export_request))
            
            # 更新进度
            current_task.update_state(
                state='PROGRESS',
                meta={'progress': 80, 'message': '验证导出数据...'}
            )
            
            # 验证导出数据
            validation_result = run_async(export_service.validate_export_data(file_path))
            
            # 更新进度
            current_task.update_state(
                state='PROGRESS',
                meta={'progress': 100, 'message': '导出完成'}
            )
            
            # 生成下载URL
            filename = os.path.basename(file_path)
            download_url = f"/api/v1/export/download/{filename}"
            
            # 获取文件大小
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            
            # 更新数据库任务状态
            run_async(task_service.update_task_status(
                task_id=self.request.id,
                status='completed',
                progress=100.0,
                message='导出成功完成',
                file_path=file_path,
                file_size=file_size,
                download_url=download_url,
                checksum=validation_result.checksum,
                validation_result=validation_result.model_dump(),
                total_items=validation_result.total_items
            ))
            
            return {
                'status': 'SUCCESS',
                'file_path': file_path,
                'download_url': download_url,
                'validation': validation_result.model_dump(),
                'message': '导出成功完成'
            }
            
        finally:
            db.close()
            
    except Exception as e:
        # 记录错误
        error_msg = f"导出失败: {str(e)}"
        traceback.print_exc()
        
        # 更新数据库任务状态
        try:
            db = next(get_db())
            task_service = ExportTaskService(db)
            run_async(task_service.update_task_status(
                task_id=self.request.id,
                status='failed',
                progress=0.0,
                error_message=error_msg
            ))
            db.close()
        except Exception:
            pass  # 忽略数据库更新错误
        
        current_task.update_state(
            state='FAILURE',
            meta={'error': error_msg, 'traceback': traceback.format_exc()}
        )
        
        return {
            'status': 'FAILURE',
            'error': error_msg
        }


@celery_app.task(bind=True)
def create_project_package_task(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    异步创建项目包任务
    
    Args:
        request_data: 导出请求数据
        
    Returns:
        任务结果
    """
    try:
        # 更新任务状态
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'message': '开始创建项目包...'}
        )
        
        # 创建导出请求对象
        export_request = ExportRequest(**request_data)
        
        # 获取数据库会话
        db = next(get_db())
        export_service = ExportService(db)
        task_service = ExportTaskService(db)
        
        try:
            # 更新数据库任务状态
            run_async(task_service.update_task_status(
                task_id=self.request.id,
                status='processing',
                progress=5.0,
                message='开始创建项目包...'
            ))
            
            # 更新进度
            current_task.update_state(
                state='PROGRESS',
                meta={'progress': 10, 'message': '收集项目数据...'}
            )
            
            # 创建项目包
            package_path = run_async(export_service.create_project_package(export_request))
            
            # 更新进度
            current_task.update_state(
                state='PROGRESS',
                meta={'progress': 90, 'message': '验证项目包...'}
            )
            
            # 验证项目包
            validation_result = run_async(export_service.validate_export_data(package_path))
            
            # 更新进度
            current_task.update_state(
                state='PROGRESS',
                meta={'progress': 100, 'message': '项目包创建完成'}
            )
            
            # 生成下载URL
            filename = os.path.basename(package_path)
            download_url = f"/api/v1/export/download/{filename}"
            
            # 获取文件大小
            file_size = os.path.getsize(package_path) if os.path.exists(package_path) else 0
            
            # 更新数据库任务状态
            run_async(task_service.update_task_status(
                task_id=self.request.id,
                status='completed',
                progress=100.0,
                message='项目包创建成功',
                file_path=package_path,
                file_size=file_size,
                download_url=download_url,
                checksum=validation_result.checksum,
                validation_result=validation_result.model_dump(),
                total_items=validation_result.total_items
            ))
            
            return {
                'status': 'SUCCESS',
                'file_path': package_path,
                'download_url': download_url,
                'validation': validation_result.model_dump(),
                'message': '项目包创建成功'
            }
            
        finally:
            db.close()
            
    except Exception as e:
        # 记录错误
        error_msg = f"项目包创建失败: {str(e)}"
        traceback.print_exc()
        
        # 更新数据库任务状态
        try:
            db = next(get_db())
            task_service = ExportTaskService(db)
            run_async(task_service.update_task_status(
                task_id=self.request.id,
                status='failed',
                progress=0.0,
                error_message=error_msg
            ))
            db.close()
        except Exception:
            pass  # 忽略数据库更新错误
        
        current_task.update_state(
            state='FAILURE',
            meta={'error': error_msg, 'traceback': traceback.format_exc()}
        )
        
        return {
            'status': 'FAILURE',
            'error': error_msg
        }


@celery_app.task
def cleanup_export_files(max_age_hours: int = 24) -> Dict[str, Any]:
    """
    清理过期的导出文件
    
    Args:
        max_age_hours: 文件最大保留时间（小时）
        
    Returns:
        清理结果
    """
    try:
        import time
        from pathlib import Path
        from ..core.config import settings
        
        export_dir = Path(settings.EXPORT_DIR or "exports")
        if not export_dir.exists():
            return {'status': 'SUCCESS', 'message': '导出目录不存在', 'deleted_count': 0}
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        deleted_count = 0
        
        for file_path in export_dir.iterdir():
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        print(f"Failed to delete {file_path}: {e}")
        
        return {
            'status': 'SUCCESS',
            'message': f'清理完成，删除了 {deleted_count} 个过期文件',
            'deleted_count': deleted_count
        }
        
    except Exception as e:
        return {
            'status': 'FAILURE',
            'error': f'清理失败: {str(e)}'
        }