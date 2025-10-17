"""
文件管理API端点
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.file import FileUploadResponse, FileResponse
from app.services.file_service import file_service
from app.services.project_service import project_service
from app.core.exceptions import FileProcessingError
from io import BytesIO

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/projects/{project_id}/upload", response_model=FileUploadResponse)
async def upload_file(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传文件到指定项目
    
    Args:
        project_id: 项目ID
        file: 上传的文件
        db: 数据库会话
        
    Returns:
        FileUploadResponse: 文件上传响应
        
    Raises:
        HTTPException: 项目不存在或文件处理错误
    """
    # 验证项目是否存在
    project = project_service.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    try:
        # 上传文件
        file_record = await file_service.upload_file(db, project_id, file)
        
        return FileUploadResponse(
            id=file_record.id,
            project_id=file_record.project_id,
            filename=file_record.filename,
            original_filename=file_record.original_filename,
            size=file_record.size,
            mime_type=file_record.mime_type,
            file_hash=file_record.file_hash,
            ocr_status=file_record.ocr_status,
            created_at=file_record.created_at,
            updated_at=file_record.updated_at
        )
        
    except FileProcessingError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in file upload: {e}")
        raise HTTPException(status_code=500, detail="文件上传失败")


@router.get("/projects/{project_id}/files", response_model=List[FileResponse])
def get_project_files(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    获取项目的所有文件
    
    Args:
        project_id: 项目ID
        db: 数据库会话
        
    Returns:
        List[FileResponse]: 文件列表
        
    Raises:
        HTTPException: 项目不存在
    """
    # 验证项目是否存在
    project = project_service.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    files = file_service.get_by_project(db, project_id)
    
    return [
        FileResponse(
            id=file.id,
            project_id=file.project_id,
            filename=file.filename,
            original_filename=file.original_filename,
            file_path=file.file_path,
            size=file.size,
            mime_type=file.mime_type,
            file_hash=file.file_hash,
            ocr_status=file.ocr_status,
            ocr_engine=file.ocr_engine,
            slice_count=len(file.slices) if file.slices else 0,
            created_at=file.created_at,
            updated_at=file.updated_at
        )
        for file in files
    ]


@router.get("/files/{file_id}", response_model=FileResponse)
def get_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    获取文件详情
    
    Args:
        file_id: 文件ID
        db: 数据库会话
        
    Returns:
        FileResponse: 文件详情
        
    Raises:
        HTTPException: 文件不存在
    """
    file_record = file_service.get(db, id=file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        id=file_record.id,
        project_id=file_record.project_id,
        filename=file_record.filename,
        original_filename=file_record.original_filename,
        file_path=file_record.file_path,
        size=file_record.size,
        mime_type=file_record.mime_type,
        file_hash=file_record.file_hash,
        ocr_status=file_record.ocr_status,
        ocr_engine=file_record.ocr_engine,
        slice_count=len(file_record.slices) if file_record.slices else 0,
        created_at=file_record.created_at,
        updated_at=file_record.updated_at
    )


@router.get("/files/{file_id}/download")
def download_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    下载文件
    
    Args:
        file_id: 文件ID
        db: 数据库会话
        
    Returns:
        StreamingResponse: 文件流响应
        
    Raises:
        HTTPException: 文件不存在或下载失败
    """
    file_record = file_service.get(db, id=file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    file_content = file_service.download_file(db, file_id)
    if file_content is None:
        raise HTTPException(status_code=500, detail="文件下载失败")
    
    return StreamingResponse(
        BytesIO(file_content),
        media_type=file_record.mime_type,
        headers={
            "Content-Disposition": f"attachment; filename={file_record.original_filename}"
        }
    )


@router.get("/files/{file_id}/url")
def get_file_url(
    file_id: str,
    expires: int = 3600,
    db: Session = Depends(get_db)
):
    """
    获取文件的预签名下载URL
    
    Args:
        file_id: 文件ID
        expires: URL过期时间（秒）
        db: 数据库会话
        
    Returns:
        dict: 包含预签名URL的响应
        
    Raises:
        HTTPException: 文件不存在或URL生成失败
    """
    file_record = file_service.get(db, id=file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    url = file_service.get_file_url(db, file_id, expires)
    if url is None:
        raise HTTPException(status_code=500, detail="URL生成失败")
    
    return {
        "url": url,
        "expires_in": expires,
        "filename": file_record.original_filename
    }


@router.delete("/files/{file_id}")
def delete_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    删除文件
    
    Args:
        file_id: 文件ID
        db: 数据库会话
        
    Returns:
        dict: 删除结果
        
    Raises:
        HTTPException: 文件不存在或删除失败
    """
    file_record = file_service.get(db, id=file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    success = file_service.delete_file(db, file_id)
    if not success:
        raise HTTPException(status_code=500, detail="文件删除失败")
    
    return {"message": "文件删除成功"}


@router.get("/projects/{project_id}/files/stats")
def get_project_file_stats(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    获取项目文件统计信息
    
    Args:
        project_id: 项目ID
        db: 数据库会话
        
    Returns:
        dict: 文件统计信息
        
    Raises:
        HTTPException: 项目不存在
    """
    # 验证项目是否存在
    project = project_service.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    stats = file_service.get_project_file_stats(db, project_id)
    
    return {
        "project_id": project_id,
        "statistics": stats
    }


@router.post("/files/validate")
async def validate_file_upload(
    file: UploadFile = File(...),
    project_id: str = Form(...)
):
    """
    验证文件是否可以上传（不实际上传）
    
    Args:
        file: 要验证的文件
        project_id: 项目ID
        
    Returns:
        dict: 验证结果
    """
    try:
        from app.utils.file_utils import (
            validate_file_type,
            validate_file_size,
            validate_file_content,
            scan_for_malicious_content,
            calculate_file_hash
        )
        
        validation_results = {
            "filename": file.filename,
            "content_type": file.content_type,
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 验证文件类型
        if not validate_file_type(file.filename, file.content_type):
            validation_results["valid"] = False
            validation_results["errors"].append({
                "code": "UNSUPPORTED_FILE_TYPE",
                "message": f"不支持的文件类型: {file.content_type}"
            })
        
        # 读取文件内容进行进一步验证
        file_content = await file.read()
        file_size = len(file_content)
        
        # 验证文件大小
        if not validate_file_size(file_size):
            validation_results["valid"] = False
            validation_results["errors"].append({
                "code": "FILE_SIZE_EXCEEDED",
                "message": f"文件大小超出限制: {file_size} bytes"
            })
        
        # 验证文件内容
        if not validate_file_content(file_content, file.filename):
            validation_results["valid"] = False
            validation_results["errors"].append({
                "code": "INVALID_FILE_CONTENT",
                "message": "文件内容格式无效或损坏"
            })
        
        # 安全扫描
        if not scan_for_malicious_content(file_content, file.filename):
            validation_results["valid"] = False
            validation_results["errors"].append({
                "code": "MALICIOUS_CONTENT_DETECTED",
                "message": "检测到可疑文件内容"
            })
        
        # 计算文件哈希
        if validation_results["valid"]:
            from io import BytesIO
            file_stream = BytesIO(file_content)
            file_hash = calculate_file_hash(file_stream)
            validation_results["file_hash"] = file_hash
            validation_results["file_size"] = file_size
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Error validating file {file.filename}: {e}")
        return {
            "filename": file.filename,
            "valid": False,
            "errors": [{
                "code": "VALIDATION_ERROR",
                "message": "文件验证过程中发生错误"
            }]
        }


@router.post("/files/batch-upload/{project_id}")
async def batch_upload_files(
    project_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    批量上传文件
    
    Args:
        project_id: 项目ID
        files: 上传的文件列表
        db: 数据库会话
        
    Returns:
        dict: 批量上传结果
        
    Raises:
        HTTPException: 项目不存在
    """
    # 验证项目是否存在
    project = project_service.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    results = []
    errors = []
    
    for file in files:
        try:
            file_record = await file_service.upload_file(db, project_id, file)
            results.append({
                "filename": file.filename,
                "file_id": str(file_record.id),
                "status": "success"
            })
        except FileProcessingError as e:
            errors.append({
                "filename": file.filename,
                "error": e.message,
                "error_code": e.error_code
            })
        except Exception as e:
            logger.error(f"Unexpected error uploading {file.filename}: {e}")
            errors.append({
                "filename": file.filename,
                "error": "上传失败",
                "error_code": "UPLOAD_FAILED"
            })
    
    return {
        "successful_uploads": len(results),
        "failed_uploads": len(errors),
        "results": results,
        "errors": errors
    }