"""
Celery异步任务定义
"""
import asyncio
from datetime import datetime
from typing import Any, Dict

from app.core.celery_app import celery_app
from app.core.app_logging import logger


def run_async(coro):
    """运行异步函数的同步包装器"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


async def send_websocket_update(task_id: str, user_id: str, status: str, progress: int = None, message: str = None, data: dict = None):
    """发送WebSocket任务更新"""
    try:
        from app.api.v1.websocket import manager
        await manager.send_task_update(task_id, user_id, status, progress, message, data)
    except Exception as e:
        logger.error("Failed to send WebSocket update", task_id=task_id, error=str(e))


def send_websocket_update_sync(task_id: str, user_id: str, status: str, progress: int = None, message: str = None, data: dict = None):
    """发送WebSocket任务更新的同步版本"""
    try:
        run_async(send_websocket_update(task_id, user_id, status, progress, message, data))
    except Exception as e:
        logger.error("Failed to send WebSocket update", task_id=task_id, error=str(e))


def update_task_monitor(task_id: str, **kwargs):
    """更新任务监控记录"""
    try:
        from app.core.database import SessionLocal
        from app.services.task_monitor_service import task_monitor_service
        from app.schemas.task import TaskMonitorUpdate
        
        db = SessionLocal()
        try:
            update_data = TaskMonitorUpdate(**kwargs)
            task_monitor_service.update_task_monitor(db, task_id, update_data)
        finally:
            db.close()
    except Exception as e:
        logger.error("Failed to update task monitor", task_id=task_id, error=str(e))


@celery_app.task(bind=True, name="app.workers.tasks.ocr_processing")
def ocr_processing(self, file_id: str, engine: str = "paddleocr", user_id: str = None) -> Dict[str, Any]:
    """
    OCR处理任务 - 集成OCR和切片功能
    """
    task_id = self.request.id
    
    try:
        from app.core.database import SessionLocal
        from app.services.file_service import file_service
        from app.services.ocr_service import ocr_service
        from app.services.slice_service import slice_service
        from app.core.minio_client import minio_client
        from app.models.file import OCRStatus
        
        logger.info("Starting OCR processing", file_id=file_id, engine=engine, task_id=task_id)
        
        # 更新任务监控状态
        update_task_monitor(task_id, status="PROGRESS", progress=0, message="Initializing OCR engine", started_at=datetime.utcnow())
        
        # 发送开始通知
        if user_id:
            send_websocket_update_sync(task_id, user_id, "PROGRESS", 0, "Initializing OCR engine")
        
        # 更新任务状态
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Initializing OCR engine"}
        )
        
        # 获取数据库会话
        db = SessionLocal()
        
        try:
            # 获取文件记录
            file_record = file_service.get(db, id=file_id)
            if not file_record:
                raise Exception(f"File not found: {file_id}")
            
            # 更新文件状态为处理中
            file_service.update(db, db_obj=file_record, obj_in={"ocr_status": OCRStatus.PROCESSING})
            
            # 从MinIO下载文件内容
            self.update_state(
                state="PROGRESS",
                meta={"current": 10, "total": 100, "status": "Downloading file content"}
            )
            
            file_content = minio_client.download_file(file_record.file_path)
            if not file_content:
                raise Exception("Failed to download file content")
            
            # 执行OCR处理
            self.update_state(
                state="PROGRESS",
                meta={"current": 30, "total": 100, "status": f"Processing with {engine} engine"}
            )
            
            # 更新任务监控进度
            update_task_monitor(task_id, progress=30, message=f"Processing with {engine} engine")
            
            if user_id:
                send_websocket_update_sync(task_id, user_id, "PROGRESS", 30, f"Processing with {engine} engine")
            
            # 使用OCR服务提取文本
            document_structure = ocr_service.extract_text(
                file_content=file_content,
                filename=file_record.filename,
                engine_name=engine
            )
            
            # 更新OCR结果到文件记录
            self.update_state(
                state="PROGRESS",
                meta={"current": 60, "total": 100, "status": "Saving OCR results"}
            )
            
            ocr_result_data = {
                "ocr_status": OCRStatus.COMPLETED,
                "ocr_engine": engine,
                "ocr_result": document_structure.full_text
            }
            file_service.update(db, db_obj=file_record, obj_in=ocr_result_data)
            
            # 创建文档切片
            self.update_state(
                state="PROGRESS",
                meta={"current": 80, "total": 100, "status": "Creating document slices"}
            )
            
            # 更新任务监控进度
            update_task_monitor(task_id, progress=80, message="Creating document slices")
            
            if user_id:
                send_websocket_update_sync(task_id, user_id, "PROGRESS", 80, "Creating document slices")
            
            slices = slice_service.create_slices_from_document(db, file_record, document_structure)
            
            # 准备返回结果
            result = {
                "file_id": file_id,
                "engine": engine,
                "status": "completed",
                "text_content": document_structure.full_text,
                "total_pages": document_structure.total_pages,
                "slices_count": len(slices),
                "slices": [
                    {
                        "id": str(slice_obj.id),
                        "content": slice_obj.content[:200] + "..." if len(slice_obj.content) > 200 else slice_obj.content,
                        "type": slice_obj.slice_type.value,
                        "page_number": slice_obj.page_number,
                        "sequence_number": slice_obj.sequence_number
                    }
                    for slice_obj in slices[:10]  # 只返回前10个切片的摘要
                ]
            }
            
            # 发送完成通知
            self.update_state(
                state="SUCCESS",
                meta={"current": 100, "total": 100, "status": "OCR processing completed"}
            )
            
            # 更新任务监控为成功状态
            result_data = {
                "file_id": file_id,
                "engine": engine,
                "slices_count": len(slices),
                "pages": document_structure.total_pages
            }
            update_task_monitor(
                task_id, 
                status="SUCCESS", 
                progress=100, 
                message="OCR processing completed",
                result=result_data,
                completed_at=datetime.utcnow()
            )
            
            if user_id:
                send_websocket_update_sync(task_id, user_id, "SUCCESS", 100, "OCR processing completed", result_data)
            
            logger.info("OCR processing completed", 
                       file_id=file_id, 
                       engine=engine, 
                       task_id=task_id,
                       slices_count=len(slices),
                       pages=document_structure.total_pages)
            
            return result
            
        finally:
            db.close()
        
    except Exception as exc:
        logger.error("OCR processing failed", file_id=file_id, error=str(exc), task_id=task_id)
        
        # 更新文件状态为失败
        try:
            db = SessionLocal()
            file_record = file_service.get(db, id=file_id)
            if file_record:
                file_service.update(db, db_obj=file_record, obj_in={"ocr_status": OCRStatus.FAILED})
            db.close()
        except Exception as db_exc:
            logger.error("Failed to update file status", error=str(db_exc))
        
        # 更新任务监控为失败状态
        error_info = {
            "error": str(exc),
            "file_id": file_id,
            "engine": engine,
            "error_type": type(exc).__name__
        }
        update_task_monitor(
            task_id,
            status="FAILURE",
            message=f"OCR processing failed: {str(exc)}",
            error_info=error_info,
            completed_at=datetime.utcnow()
        )
        
        # 发送失败通知
        if user_id:
            send_websocket_update_sync(task_id, user_id, "FAILURE", None, f"OCR processing failed: {str(exc)}", error_info)
        
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc), "file_id": file_id}
        )
        raise


@celery_app.task(bind=True, name="app.workers.tasks.llm_processing")
def llm_processing(self, slice_id: str, provider: str = "openai") -> Dict[str, Any]:
    """
    LLM处理任务 - 生成CoT问题和答案
    """
    try:
        logger.info("Starting LLM processing", slice_id=slice_id, provider=provider)
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Generating questions"}
        )
        
        # 这里将实现实际的LLM调用逻辑
        result = {
            "slice_id": slice_id,
            "provider": provider,
            "status": "completed",
            "question": "Generated question will be here",
            "candidates": []
        }
        
        logger.info("LLM processing completed", slice_id=slice_id, provider=provider)
        return result
        
    except Exception as exc:
        logger.error("LLM processing failed", slice_id=slice_id, error=str(exc))
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc), "slice_id": slice_id}
        )
        raise


@celery_app.task(bind=True, name="app.workers.tasks.kg_extraction")
def kg_extraction(self, cot_item_id: str) -> Dict[str, Any]:
    """
    知识图谱抽取任务
    """
    try:
        logger.info("Starting KG extraction", cot_item_id=cot_item_id)
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Extracting entities"}
        )
        
        # 这里将实现实际的知识图谱抽取逻辑
        result = {
            "cot_item_id": cot_item_id,
            "status": "completed",
            "entities": [],
            "relationships": [],
            "properties": []
        }
        
        logger.info("KG extraction completed", cot_item_id=cot_item_id)
        return result
        
    except Exception as exc:
        logger.error("KG extraction failed", cot_item_id=cot_item_id, error=str(exc))
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc), "cot_item_id": cot_item_id}
        )
        raise


@celery_app.task(bind=True, name="app.workers.tasks.file_processing")
def file_processing(self, file_id: str, operation: str) -> Dict[str, Any]:
    """
    文件处理任务
    """
    try:
        logger.info("Starting file processing", file_id=file_id, operation=operation)
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": f"Processing file: {operation}"}
        )
        
        # 这里将实现实际的文件处理逻辑
        result = {
            "file_id": file_id,
            "operation": operation,
            "status": "completed"
        }
        
        logger.info("File processing completed", file_id=file_id, operation=operation)
        return result
        
    except Exception as exc:
        logger.error("File processing failed", file_id=file_id, error=str(exc))
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc), "file_id": file_id}
        )
        raise


@celery_app.task(name="app.workers.tasks.health_check")
def health_check() -> Dict[str, Any]:
    """
    健康检查任务
    """
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "worker": "celery"
    }