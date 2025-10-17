"""
文件服务测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from fastapi import UploadFile

from app.services.file_service import file_service
from app.models.file import File, OCRStatus
from app.core.exceptions import FileProcessingError


class TestFileService:
    """文件服务测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock()
    
    @pytest.fixture
    def sample_file_data(self):
        """示例文件数据"""
        return {
            "id": "test-file-id",
            "project_id": "test-project-id",
            "filename": "test.pdf",
            "original_filename": "test document.pdf",
            "file_path": "projects/test-project-id/files/ab/cd/abcd1234_test.pdf",
            "file_hash": "abcd1234567890",
            "size": 1024,
            "mime_type": "application/pdf",
            "ocr_status": OCRStatus.PENDING
        }
    
    @pytest.fixture
    def mock_upload_file(self):
        """模拟上传文件"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = Mock(return_value=b"PDF content here")
        return mock_file
    
    def test_get_by_project(self, mock_db, sample_file_data):
        """测试根据项目获取文件列表"""
        # 模拟数据库查询结果
        mock_files = [File(**sample_file_data)]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_files
        
        result = file_service.get_by_project(mock_db, "test-project-id")
        
        assert len(result) == 1
        assert result[0].project_id == "test-project-id"
        mock_db.query.assert_called_once()
    
    def test_get_by_hash(self, mock_db, sample_file_data):
        """测试根据哈希获取文件"""
        mock_file = File(**sample_file_data)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_file
        
        result = file_service.get_by_hash(mock_db, "abcd1234567890")
        
        assert result is not None
        assert result.file_hash == "abcd1234567890"
        mock_db.query.assert_called_once()
    
    def test_get_project_file_hashes(self, mock_db):
        """测试获取项目文件哈希列表"""
        mock_results = [
            Mock(file_hash="hash1"),
            Mock(file_hash="hash2"),
            Mock(file_hash="hash3")
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_results
        
        result = file_service.get_project_file_hashes(mock_db, "test-project-id")
        
        assert result == ["hash1", "hash2", "hash3"]
        mock_db.query.assert_called_once()
    
    @patch('app.services.file_service.minio_client')
    @patch('app.utils.file_utils.calculate_file_hash')
    @patch('app.utils.file_utils.validate_file_type')
    @patch('app.utils.file_utils.validate_file_size')
    async def test_upload_file_success(self, mock_validate_size, mock_validate_type, 
                                     mock_calculate_hash, mock_minio, mock_db, 
                                     mock_upload_file, sample_file_data):
        """测试文件上传成功"""
        # 设置模拟返回值
        mock_validate_type.return_value = True
        mock_validate_size.return_value = True
        mock_calculate_hash.return_value = "abcd1234567890"
        mock_minio.upload_file.return_value = True
        
        # 模拟数据库操作
        mock_db.query.return_value.filter.return_value.first.return_value = None  # 无重复文件
        file_service.create = Mock(return_value=File(**sample_file_data))
        
        result = await file_service.upload_file(mock_db, "test-project-id", mock_upload_file)
        
        assert result is not None
        assert result.filename == "test.pdf"
        mock_minio.upload_file.assert_called_once()
        file_service.create.assert_called_once()
    
    @patch('app.utils.file_utils.validate_file_type')
    async def test_upload_file_invalid_type(self, mock_validate_type, mock_db, mock_upload_file):
        """测试上传不支持的文件类型"""
        mock_validate_type.return_value = False
        
        with pytest.raises(FileProcessingError) as exc_info:
            await file_service.upload_file(mock_db, "test-project-id", mock_upload_file)
        
        assert "不支持的文件类型" in str(exc_info.value.message)
        assert exc_info.value.error_code == "UNSUPPORTED_FILE_TYPE"
    
    @patch('app.utils.file_utils.validate_file_type')
    @patch('app.utils.file_utils.validate_file_size')
    async def test_upload_file_size_exceeded(self, mock_validate_size, mock_validate_type, 
                                           mock_db, mock_upload_file):
        """测试文件大小超出限制"""
        mock_validate_type.return_value = True
        mock_validate_size.return_value = False
        
        with pytest.raises(FileProcessingError) as exc_info:
            await file_service.upload_file(mock_db, "test-project-id", mock_upload_file)
        
        assert "文件大小超出限制" in str(exc_info.value.message)
        assert exc_info.value.error_code == "FILE_SIZE_EXCEEDED"
    
    @patch('app.services.file_service.minio_client')
    def test_download_file_success(self, mock_minio, mock_db, sample_file_data):
        """测试文件下载成功"""
        mock_file = File(**sample_file_data)
        file_service.get = Mock(return_value=mock_file)
        mock_minio.download_file.return_value = b"file content"
        
        result = file_service.download_file(mock_db, "test-file-id")
        
        assert result == b"file content"
        mock_minio.download_file.assert_called_once_with(mock_file.file_path)
    
    def test_download_file_not_found(self, mock_db):
        """测试下载不存在的文件"""
        file_service.get = Mock(return_value=None)
        
        result = file_service.download_file(mock_db, "nonexistent-file-id")
        
        assert result is None
    
    @patch('app.services.file_service.minio_client')
    def test_delete_file_success(self, mock_minio, mock_db, sample_file_data):
        """测试文件删除成功"""
        mock_file = File(**sample_file_data)
        file_service.get = Mock(return_value=mock_file)
        file_service.remove = Mock(return_value=mock_file)
        mock_minio.delete_file.return_value = True
        
        result = file_service.delete_file(mock_db, "test-file-id")
        
        assert result == True
        mock_minio.delete_file.assert_called_once_with(mock_file.file_path)
        file_service.remove.assert_called_once_with(mock_db, id="test-file-id")
    
    def test_delete_file_not_found(self, mock_db):
        """测试删除不存在的文件"""
        file_service.get = Mock(return_value=None)
        
        result = file_service.delete_file(mock_db, "nonexistent-file-id")
        
        assert result == False
    
    @patch('app.services.file_service.minio_client')
    def test_get_file_url_success(self, mock_minio, mock_db, sample_file_data):
        """测试获取文件URL成功"""
        mock_file = File(**sample_file_data)
        file_service.get = Mock(return_value=mock_file)
        mock_minio.get_file_url.return_value = "https://example.com/presigned-url"
        
        result = file_service.get_file_url(mock_db, "test-file-id", 3600)
        
        assert result == "https://example.com/presigned-url"
        mock_minio.get_file_url.assert_called_once_with(mock_file.file_path, 3600)
    
    def test_get_file_url_not_found(self, mock_db):
        """测试获取不存在文件的URL"""
        file_service.get = Mock(return_value=None)
        
        result = file_service.get_file_url(mock_db, "nonexistent-file-id")
        
        assert result is None