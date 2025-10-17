"""
MinIO对象存储客户端
"""
import logging
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error
from io import BytesIO

from .config import settings

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO客户端封装类"""
    
    def __init__(self):
        self.client = None
        self.bucket_name = settings.MINIO_BUCKET
        self._initialized = False
    
    def _initialize(self):
        """延迟初始化MinIO客户端"""
        if not self._initialized:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=False  # 开发环境使用HTTP
            )
            self._ensure_bucket_exists()
            self._initialized = True
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error creating bucket: {e}")
            raise
    
    def upload_file(self, object_name: str, file_data: BinaryIO, 
                   file_size: int, content_type: str = "application/octet-stream") -> bool:
        """
        上传文件到MinIO
        
        Args:
            object_name: 对象名称（文件路径）
            file_data: 文件数据流
            file_size: 文件大小
            content_type: 文件MIME类型
            
        Returns:
            bool: 上传是否成功
        """
        try:
            self._initialize()
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_data,
                length=file_size,
                content_type=content_type
            )
            logger.info(f"Successfully uploaded {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Error uploading file {object_name}: {e}")
            return False
    
    def download_file(self, object_name: str) -> Optional[bytes]:
        """
        从MinIO下载文件
        
        Args:
            object_name: 对象名称（文件路径）
            
        Returns:
            Optional[bytes]: 文件内容，失败时返回None
        """
        try:
            self._initialize()
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Error downloading file {object_name}: {e}")
            return None
    
    def delete_file(self, object_name: str) -> bool:
        """
        从MinIO删除文件
        
        Args:
            object_name: 对象名称（文件路径）
            
        Returns:
            bool: 删除是否成功
        """
        try:
            self._initialize()
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Successfully deleted {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting file {object_name}: {e}")
            return False
    
    def file_exists(self, object_name: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            object_name: 对象名称（文件路径）
            
        Returns:
            bool: 文件是否存在
        """
        try:
            self._initialize()
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    def get_file_url(self, object_name: str, expires: int = 3600) -> Optional[str]:
        """
        获取文件的预签名URL
        
        Args:
            object_name: 对象名称（文件路径）
            expires: URL过期时间（秒）
            
        Returns:
            Optional[str]: 预签名URL，失败时返回None
        """
        try:
            from datetime import timedelta
            self._initialize()
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL for {object_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL for {object_name}: {e}")
            return None


# 创建全局MinIO客户端实例
minio_client = MinIOClient()