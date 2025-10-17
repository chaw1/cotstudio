"""
文件工具函数测试
"""
import pytest
from io import BytesIO
from pathlib import Path

from app.utils.file_utils import (
    calculate_file_hash,
    validate_file_type,
    validate_file_size,
    sanitize_filename,
    generate_file_path,
    get_file_extension_info,
    is_duplicate_file
)
from app.core.config import settings


class TestFileUtils:
    """文件工具函数测试类"""
    
    def test_calculate_file_hash(self):
        """测试文件哈希计算"""
        # 测试相同内容产生相同哈希
        content1 = b"Hello, World!"
        content2 = b"Hello, World!"
        
        stream1 = BytesIO(content1)
        stream2 = BytesIO(content2)
        
        hash1 = calculate_file_hash(stream1)
        hash2 = calculate_file_hash(stream2)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256哈希长度
        
        # 测试不同内容产生不同哈希
        content3 = b"Different content"
        stream3 = BytesIO(content3)
        hash3 = calculate_file_hash(stream3)
        
        assert hash1 != hash3
    
    def test_validate_file_type(self):
        """测试文件类型验证"""
        # 测试允许的MIME类型
        assert validate_file_type("test.pdf", "application/pdf") == True
        assert validate_file_type("test.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document") == True
        assert validate_file_type("test.txt", "text/plain") == True
        assert validate_file_type("test.json", "application/json") == True
        
        # 测试不允许的MIME类型
        assert validate_file_type("test.exe", "application/x-executable") == False
        assert validate_file_type("test.zip", "application/zip") == False
        
        # 测试根据文件扩展名推断
        assert validate_file_type("document.pdf", "application/octet-stream") == True
        assert validate_file_type("text.md", "text/plain") == True
        assert validate_file_type("latex.tex", "text/plain") == True
    
    def test_validate_file_size(self):
        """测试文件大小验证"""
        # 测试正常大小
        assert validate_file_size(1024) == True
        assert validate_file_size(50 * 1024 * 1024) == True  # 50MB
        
        # 测试超出限制
        assert validate_file_size(settings.MAX_FILE_SIZE + 1) == False
        
        # 测试零大小和负数
        assert validate_file_size(0) == False
        assert validate_file_size(-1) == False
    
    def test_sanitize_filename(self):
        """测试文件名清理"""
        # 测试正常文件名
        assert sanitize_filename("normal_file.txt") == "normal_file.txt"
        
        # 测试包含不安全字符的文件名
        assert sanitize_filename("../../../etc/passwd") == "_.._.._.._etc_passwd"
        assert sanitize_filename("file<>:\"|?*.txt") == "file________.txt"
        
        # 测试长文件名
        long_name = "a" * 300 + ".txt"
        sanitized = sanitize_filename(long_name)
        assert len(sanitized) <= 255
        assert sanitized.endswith(".txt")
    
    def test_generate_file_path(self):
        """测试文件路径生成"""
        project_id = "test-project-123"
        filename = "test_document.pdf"
        file_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        
        path = generate_file_path(project_id, filename, file_hash)
        
        # 验证路径格式
        assert path.startswith(f"projects/{project_id}/files/")
        assert filename in path
        assert file_hash in path
        
        # 验证哈希分层
        hash_prefix = file_hash[:2]
        hash_suffix = file_hash[2:4]
        assert f"/{hash_prefix}/{hash_suffix}/" in path
    
    def test_get_file_extension_info(self):
        """测试文件扩展名信息获取"""
        # 测试常见文件类型
        ext, mime = get_file_extension_info("document.pdf")
        assert ext == ".pdf"
        
        ext, mime = get_file_extension_info("text.TXT")
        assert ext == ".txt"
        
        ext, mime = get_file_extension_info("data.json")
        assert ext == ".json"
        
        # 测试无扩展名文件
        ext, mime = get_file_extension_info("README")
        assert ext == ""
    
    def test_is_duplicate_file(self):
        """测试重复文件检测"""
        file_hash = "abc123"
        existing_hashes = ["def456", "ghi789", "abc123"]
        
        # 测试重复文件
        assert is_duplicate_file(file_hash, existing_hashes) == True
        
        # 测试非重复文件
        assert is_duplicate_file("xyz999", existing_hashes) == False
        
        # 测试空列表
        assert is_duplicate_file(file_hash, []) == False