"""
MinIO客户端测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from minio.error import S3Error

from app.core.minio_client import MinIOClient


class TestMinIOClient:
    """MinIO客户端测试类"""
    
    @pytest.fixture
    def mock_minio_client(self):
        """模拟MinIO客户端"""
        with patch('app.core.minio_client.Minio') as mock_minio:
            mock_client_instance = Mock()
            mock_minio.return_value = mock_client_instance
            
            # 模拟bucket存在检查
            mock_client_instance.bucket_exists.return_value = True
            
            client = MinIOClient()
            client.client = mock_client_instance
            return client
    
    def test_init_creates_bucket_if_not_exists(self):
        """测试初始化时创建不存在的bucket"""
        with patch('app.core.minio_client.Minio') as mock_minio:
            mock_client_instance = Mock()
            mock_minio.return_value = mock_client_instance
            
            # 模拟bucket不存在
            mock_client_instance.bucket_exists.return_value = False
            
            client = MinIOClient()
            
            mock_client_instance.bucket_exists.assert_called_once()
            mock_client_instance.make_bucket.assert_called_once()
    
    def test_upload_file_success(self, mock_minio_client):
        """测试文件上传成功"""
        file_data = BytesIO(b"test content")
        
        result = mock_minio_client.upload_file(
            object_name="test/file.txt",
            file_data=file_data,
            file_size=12,
            content_type="text/plain"
        )
        
        assert result == True
        mock_minio_client.client.put_object.assert_called_once_with(
            bucket_name=mock_minio_client.bucket_name,
            object_name="test/file.txt",
            data=file_data,
            length=12,
            content_type="text/plain"
        )
    
    def test_upload_file_failure(self, mock_minio_client):
        """测试文件上传失败"""
        mock_minio_client.client.put_object.side_effect = S3Error(
            "Upload failed", "test", "test", "test", "test", "test"
        )
        
        file_data = BytesIO(b"test content")
        
        result = mock_minio_client.upload_file(
            object_name="test/file.txt",
            file_data=file_data,
            file_size=12
        )
        
        assert result == False
    
    def test_download_file_success(self, mock_minio_client):
        """测试文件下载成功"""
        mock_response = Mock()
        mock_response.read.return_value = b"file content"
        mock_minio_client.client.get_object.return_value = mock_response
        
        result = mock_minio_client.download_file("test/file.txt")
        
        assert result == b"file content"
        mock_minio_client.client.get_object.assert_called_once_with(
            mock_minio_client.bucket_name, "test/file.txt"
        )
        mock_response.close.assert_called_once()
        mock_response.release_conn.assert_called_once()
    
    def test_download_file_failure(self, mock_minio_client):
        """测试文件下载失败"""
        mock_minio_client.client.get_object.side_effect = S3Error(
            "Download failed", "test", "test", "test", "test", "test"
        )
        
        result = mock_minio_client.download_file("test/file.txt")
        
        assert result is None
    
    def test_delete_file_success(self, mock_minio_client):
        """测试文件删除成功"""
        result = mock_minio_client.delete_file("test/file.txt")
        
        assert result == True
        mock_minio_client.client.remove_object.assert_called_once_with(
            mock_minio_client.bucket_name, "test/file.txt"
        )
    
    def test_delete_file_failure(self, mock_minio_client):
        """测试文件删除失败"""
        mock_minio_client.client.remove_object.side_effect = S3Error(
            "Delete failed", "test", "test", "test", "test", "test"
        )
        
        result = mock_minio_client.delete_file("test/file.txt")
        
        assert result == False
    
    def test_file_exists_true(self, mock_minio_client):
        """测试文件存在检查 - 文件存在"""
        result = mock_minio_client.file_exists("test/file.txt")
        
        assert result == True
        mock_minio_client.client.stat_object.assert_called_once_with(
            mock_minio_client.bucket_name, "test/file.txt"
        )
    
    def test_file_exists_false(self, mock_minio_client):
        """测试文件存在检查 - 文件不存在"""
        mock_minio_client.client.stat_object.side_effect = S3Error(
            "Not found", "test", "test", "test", "test", "test"
        )
        
        result = mock_minio_client.file_exists("test/file.txt")
        
        assert result == False
    
    def test_get_file_url_success(self, mock_minio_client):
        """测试获取预签名URL成功"""
        mock_minio_client.client.presigned_get_object.return_value = "https://example.com/presigned-url"
        
        result = mock_minio_client.get_file_url("test/file.txt", 3600)
        
        assert result == "https://example.com/presigned-url"
        mock_minio_client.client.presigned_get_object.assert_called_once_with(
            bucket_name=mock_minio_client.bucket_name,
            object_name="test/file.txt",
            expires=3600
        )
    
    def test_get_file_url_failure(self, mock_minio_client):
        """测试获取预签名URL失败"""
        mock_minio_client.client.presigned_get_object.side_effect = S3Error(
            "URL generation failed", "test", "test", "test", "test", "test"
        )
        
        result = mock_minio_client.get_file_url("test/file.txt")
        
        assert result is None