"""
文件服务
"""
import logging
from typing import List, Optional, BinaryIO
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile

from app.models.file import File, OCRStatus
from app.services.base_service import BaseService
from app.core.minio_client import minio_client
from app.utils.file_utils import (
    calculate_file_hash,
    validate_file_type,
    validate_file_size,
    validate_file_content,
    scan_for_malicious_content,
    generate_file_path,
    sanitize_filename
)
from app.utils.security_scanner import scan_uploaded_file, is_file_safe, get_threat_summary, security_scanner
from app.core.exceptions import FileProcessingError

logger = logging.getLogger(__name__)


class FileService(BaseService[File]):
    """
    文件服务类
    """
    
    def __init__(self):
        super().__init__(File)
    
    def get_by_project(self, db: Session, project_id: str) -> List[File]:
        """
        根据项目ID获取文件列表,按创建时间倒序排序
        """
        return db.query(File).filter(File.project_id == project_id).order_by(File.created_at.desc()).all()
    
    def get_by_hash(self, db: Session, file_hash: str) -> Optional[File]:
        """
        根据文件哈希获取文件
        """
        return db.query(File).filter(File.file_hash == file_hash).first()
    
    def get_project_file_hashes(self, db: Session, project_id: str) -> List[str]:
        """
        获取项目中所有文件的哈希值列表
        """
        files = db.query(File.file_hash).filter(File.project_id == project_id).all()
        return [file.file_hash for file in files]
    
    def check_duplicate_in_project(self, db: Session, project_id: str, file_hash: str) -> Optional[File]:
        """
        检查项目中是否存在相同哈希的文件
        
        Args:
            db: 数据库会话
            project_id: 项目ID
            file_hash: 文件哈希值
            
        Returns:
            Optional[File]: 如果存在重复文件则返回文件记录，否则返回None
        """
        return db.query(File).filter(
            File.project_id == project_id,
            File.file_hash == file_hash
        ).first()
    
    def check_project_file_limit(self, db: Session, project_id: str) -> bool:
        """
        检查项目文件数量是否超出限制
        
        Args:
            db: 数据库会话
            project_id: 项目ID
            
        Returns:
            bool: 如果未超出限制返回True，否则返回False
        """
        from app.core.config import settings
        file_count = db.query(File).filter(File.project_id == project_id).count()
        return file_count < settings.MAX_FILES_PER_PROJECT
    
    def get_project_file_stats(self, db: Session, project_id: str) -> dict:
        """
        获取项目文件统计信息
        
        Args:
            db: 数据库会话
            project_id: 项目ID
            
        Returns:
            dict: 包含文件统计信息的字典
        """
        from sqlalchemy import func
        
        stats = db.query(
            func.count(File.id).label('total_files'),
            func.sum(File.size).label('total_size'),
            func.count(File.id).filter(File.ocr_status == OCRStatus.COMPLETED).label('processed_files'),
            func.count(File.id).filter(File.ocr_status == OCRStatus.PENDING).label('pending_files'),
            func.count(File.id).filter(File.ocr_status == OCRStatus.FAILED).label('failed_files')
        ).filter(File.project_id == project_id).first()
        
        return {
            'total_files': stats.total_files or 0,
            'total_size': stats.total_size or 0,
            'processed_files': stats.processed_files or 0,
            'pending_files': stats.pending_files or 0,
            'failed_files': stats.failed_files or 0
        }
    
    async def upload_file(self, db: Session, project_id: str, upload_file: UploadFile) -> File:
        """
        上传文件到项目
        
        Args:
            db: 数据库会话
            project_id: 项目ID
            upload_file: 上传的文件
            
        Returns:
            File: 创建的文件记录
            
        Raises:
            FileProcessingError: 文件处理错误
        """
        try:
            # 检查项目文件数量限制
            if not self.check_project_file_limit(db, project_id):
                raise FileProcessingError(
                    "项目文件数量已达到上限",
                    "PROJECT_FILE_LIMIT_EXCEEDED"
                )
            
            # 验证文件类型
            if not validate_file_type(upload_file.filename, upload_file.content_type):
                raise FileProcessingError(
                    f"不支持的文件类型: {upload_file.content_type}",
                    "UNSUPPORTED_FILE_TYPE"
                )
            
            # 读取文件内容
            file_content = await upload_file.read()
            file_size = len(file_content)
            
            # 验证文件大小
            if not validate_file_size(file_size):
                raise FileProcessingError(
                    f"文件大小超出限制: {file_size} bytes",
                    "FILE_SIZE_EXCEEDED"
                )
            
            # 验证文件内容
            if not validate_file_content(file_content, upload_file.filename):
                raise FileProcessingError(
                    "文件内容格式无效或损坏",
                    "INVALID_FILE_CONTENT"
                )
            
            # 增强安全扫描
            scan_result = scan_uploaded_file(file_content, upload_file.filename)
            
            if not is_file_safe(scan_result):
                threat_summary = get_threat_summary(scan_result)
                
                # 如果启用了隔离功能，将可疑文件隔离
                if settings.QUARANTINE_SUSPICIOUS_FILES:
                    quarantine_path = security_scanner.quarantine_file(
                        file_content, 
                        upload_file.filename, 
                        scan_result
                    )
                    logger.warning(f"Suspicious file quarantined: {quarantine_path}")
                
                raise FileProcessingError(
                    f"文件安全扫描失败: {threat_summary}",
                    "SECURITY_SCAN_FAILED"
                )
            
            # 记录扫描警告
            warnings = scan_result.get('warnings', [])
            if warnings:
                warning_summary = "; ".join([w.get('description', '') for w in warnings])
                logger.warning(f"File upload warnings for {upload_file.filename}: {warning_summary}")
            
            # 计算文件哈希
            from io import BytesIO
            file_stream = BytesIO(file_content)
            file_hash = calculate_file_hash(file_stream)
            
            # 检查项目内重复文件
            existing_file = self.check_duplicate_in_project(db, project_id, file_hash)
            if existing_file:
                logger.info(f"Duplicate file detected in project {project_id}: {file_hash}")
                return existing_file
            
            # 生成文件存储路径
            sanitized_filename = sanitize_filename(upload_file.filename)
            file_path = generate_file_path(project_id, sanitized_filename, file_hash)
            
            # 上传到MinIO
            file_stream.seek(0)
            upload_success = minio_client.upload_file(
                object_name=file_path,
                file_data=file_stream,
                file_size=file_size,
                content_type=upload_file.content_type
            )
            
            if not upload_success:
                raise FileProcessingError(
                    "文件上传到对象存储失败",
                    "STORAGE_UPLOAD_FAILED"
                )
            
            # 创建文件记录
            file_data = {
                "project_id": project_id,
                "filename": sanitized_filename,
                "original_filename": upload_file.filename,
                "file_path": file_path,
                "file_hash": file_hash,
                "size": file_size,
                "mime_type": upload_file.content_type,
                "ocr_status": OCRStatus.PENDING
            }
            
            file_record = self.create(db, obj_in=file_data)
            logger.info(f"File uploaded successfully: {file_record.id}")
            
            return file_record
            
        except FileProcessingError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during file upload: {e}")
            raise FileProcessingError(
                "文件上传过程中发生未知错误",
                "UPLOAD_UNKNOWN_ERROR"
            )
    
    def download_file(self, db: Session, file_id: str) -> Optional[bytes]:
        """
        下载文件内容
        
        Args:
            db: 数据库会话
            file_id: 文件ID
            
        Returns:
            Optional[bytes]: 文件内容，失败时返回None
        """
        file_record = self.get(db, id=file_id)
        if not file_record:
            return None
        
        return minio_client.download_file(file_record.file_path)
    
    def delete_file(self, db: Session, file_id: str) -> bool:
        """
        删除文件
        
        Args:
            db: 数据库会话
            file_id: 文件ID
            
        Returns:
            bool: 删除是否成功
        """
        file_record = self.get(db, id=file_id)
        if not file_record:
            return False
        
        # 从对象存储删除文件
        storage_deleted = minio_client.delete_file(file_record.file_path)
        
        # 从数据库删除记录
        db_deleted = self.remove(db, id=file_id)
        
        return storage_deleted and db_deleted is not None
    
    def get_file_url(self, db: Session, file_id: str, expires: int = 3600) -> Optional[str]:
        """
        获取文件的预签名下载URL
        
        Args:
            db: 数据库会话
            file_id: 文件ID
            expires: URL过期时间（秒）
            
        Returns:
            Optional[str]: 预签名URL，失败时返回None
        """
        file_record = self.get(db, id=file_id)
        if not file_record:
            return None
        
        return minio_client.get_file_url(file_record.file_path, expires)


# 创建全局文件服务实例
file_service = FileService()