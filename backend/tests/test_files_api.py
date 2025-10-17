"""
文件API端点测试
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from io import BytesIO

from app.main import app
from app.models.file import File, OCRStatus
from app.core.exceptions import FileProcessingError


class TestFilesAPI:
    """文件API测试类"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)
    
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
            "ocr_status": OCRStatus.PENDING,
            "ocr_engine": None,
            "slices": []
        }
    
    @patch('app.api.v1.files.project_service')
    @patch('app.api.v1.files.file_service')
    def test_upload_file_success(self, mock_file_service, mock_project_service, 
                               client, sample_file_data):
        """测试文件上传成功"""
        # 模拟项目存在
        mock_project_service.get.return_value = Mock(id="test-project-id")
        
        # 模拟文件上传成功
        mock_file = Mock(**sample_file_data)
        mock_file_service.upload_file.return_value = mock_file
        
        # 准备测试文件
        test_file = BytesIO(b"PDF content")
        
        response = client.post(
            "/api/v1/projects/test-project-id/upload",
            files={"file": ("test.pdf", test_file, "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["project_id"] == "test-project-id"
        assert data["file_hash"] == "abcd1234567890"
    
    @patch('app.api.v1.files.project_service')
    def test_upload_file_project_not_found(self, mock_project_service, client):
        """测试上传文件到不存在的项目"""
        mock_project_service.get.return_value = None
        
        test_file = BytesIO(b"PDF content")
        
        response = client.post(
            "/api/v1/projects/nonexistent-project/upload",
            files={"file": ("test.pdf", test_file, "application/pdf")}
        )
        
        assert response.status_code == 404
        assert "项目不存在" in response.json()["detail"]
    
    @patch('app.api.v1.files.project_service')
    @patch('app.api.v1.files.file_service')
    def test_upload_file_processing_error(self, mock_file_service, mock_project_service, client):
        """测试文件处理错误"""
        mock_project_service.get.return_value = Mock(id="test-project-id")
        mock_file_service.upload_file.side_effect = FileProcessingError(
            "不支持的文件类型", "UNSUPPORTED_FILE_TYPE"
        )
        
        test_file = BytesIO(b"Invalid content")
        
        response = client.post(
            "/api/v1/projects/test-project-id/upload",
            files={"file": ("test.exe", test_file, "application/x-executable")}
        )
        
        assert response.status_code == 400
        assert "不支持的文件类型" in response.json()["detail"]
    
    @patch('app.api.v1.files.project_service')
    @patch('app.api.v1.files.file_service')
    def test_get_project_files(self, mock_file_service, mock_project_service, 
                             client, sample_file_data):
        """测试获取项目文件列表"""
        mock_project_service.get.return_value = Mock(id="test-project-id")
        
        mock_file = Mock(**sample_file_data)
        mock_file_service.get_by_project.return_value = [mock_file]
        
        response = client.get("/api/v1/projects/test-project-id/files")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["filename"] == "test.pdf"
        assert data[0]["slice_count"] == 0
    
    @patch('app.api.v1.files.project_service')
    def test_get_project_files_project_not_found(self, mock_project_service, client):
        """测试获取不存在项目的文件列表"""
        mock_project_service.get.return_value = None
        
        response = client.get("/api/v1/projects/nonexistent-project/files")
        
        assert response.status_code == 404
        assert "项目不存在" in response.json()["detail"]
    
    @patch('app.api.v1.files.file_service')
    def test_get_file_success(self, mock_file_service, client, sample_file_data):
        """测试获取文件详情成功"""
        mock_file = Mock(**sample_file_data)
        mock_file_service.get.return_value = mock_file
        
        response = client.get("/api/v1/files/test-file-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-file-id"
        assert data["filename"] == "test.pdf"
    
    @patch('app.api.v1.files.file_service')
    def test_get_file_not_found(self, mock_file_service, client):
        """测试获取不存在的文件"""
        mock_file_service.get.return_value = None
        
        response = client.get("/api/v1/files/nonexistent-file-id")
        
        assert response.status_code == 404
        assert "文件不存在" in response.json()["detail"]
    
    @patch('app.api.v1.files.file_service')
    def test_download_file_success(self, mock_file_service, client, sample_file_data):
        """测试文件下载成功"""
        mock_file = Mock(**sample_file_data)
        mock_file_service.get.return_value = mock_file
        mock_file_service.download_file.return_value = b"PDF content"
        
        response = client.get("/api/v1/files/test-file-id/download")
        
        assert response.status_code == 200
        assert response.content == b"PDF content"
        assert response.headers["content-type"] == "application/pdf"
    
    @patch('app.api.v1.files.file_service')
    def test_download_file_not_found(self, mock_file_service, client):
        """测试下载不存在的文件"""
        mock_file_service.get.return_value = None
        
        response = client.get("/api/v1/files/nonexistent-file-id/download")
        
        assert response.status_code == 404
        assert "文件不存在" in response.json()["detail"]
    
    @patch('app.api.v1.files.file_service')
    def test_get_file_url_success(self, mock_file_service, client, sample_file_data):
        """测试获取文件URL成功"""
        mock_file = Mock(**sample_file_data)
        mock_file_service.get.return_value = mock_file
        mock_file_service.get_file_url.return_value = "https://example.com/presigned-url"
        
        response = client.get("/api/v1/files/test-file-id/url?expires=7200")
        
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://example.com/presigned-url"
        assert data["expires_in"] == 7200
        assert data["filename"] == "test document.pdf"
    
    @patch('app.api.v1.files.file_service')
    def test_delete_file_success(self, mock_file_service, client, sample_file_data):
        """测试文件删除成功"""
        mock_file = Mock(**sample_file_data)
        mock_file_service.get.return_value = mock_file
        mock_file_service.delete_file.return_value = True
        
        response = client.delete("/api/v1/files/test-file-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "文件删除成功"
    
    @patch('app.api.v1.files.file_service')
    def test_delete_file_not_found(self, mock_file_service, client):
        """测试删除不存在的文件"""
        mock_file_service.get.return_value = None
        
        response = client.delete("/api/v1/files/nonexistent-file-id")
        
        assert response.status_code == 404
        assert "文件不存在" in response.json()["detail"]
    
    @patch('app.api.v1.files.project_service')
    @patch('app.api.v1.files.file_service')
    def test_batch_upload_files_success(self, mock_file_service, mock_project_service, 
                                      client, sample_file_data):
        """测试批量文件上传成功"""
        mock_project_service.get.return_value = Mock(id="test-project-id")
        
        # 模拟第一个文件上传成功
        mock_file1 = Mock(**sample_file_data)
        mock_file1.id = "file-1"
        
        # 模拟第二个文件上传失败
        mock_file_service.upload_file.side_effect = [
            mock_file1,
            FileProcessingError("文件类型不支持", "UNSUPPORTED_FILE_TYPE")
        ]
        
        # 准备测试文件
        files = [
            ("files", ("test1.pdf", BytesIO(b"PDF content 1"), "application/pdf")),
            ("files", ("test2.exe", BytesIO(b"EXE content"), "application/x-executable"))
        ]
        
        response = client.post("/api/v1/files/batch-upload/test-project-id", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["successful_uploads"] == 1
        assert data["failed_uploads"] == 1
        assert len(data["results"]) == 1
        assert len(data["errors"]) == 1
        assert data["results"][0]["filename"] == "test1.pdf"
        assert data["errors"][0]["filename"] == "test2.exe"