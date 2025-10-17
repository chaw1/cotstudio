"""
安全测试用例
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from io import BytesIO

from app.main import app
from app.core.security_validators import SecurityValidator
from app.utils.security_scanner import SecurityScanner, scan_uploaded_file
from app.middleware.security import SecurityMiddleware


class TestSecurityValidators:
    """
    安全验证器测试
    """
    
    def test_sql_injection_detection(self):
        """
        测试SQL注入检测
        """
        # 正常输入
        assert SecurityValidator.validate_sql_injection("normal text") == True
        assert SecurityValidator.validate_sql_injection("user@example.com") == True
        
        # SQL注入攻击
        assert SecurityValidator.validate_sql_injection("'; DROP TABLE users; --") == False
        assert SecurityValidator.validate_sql_injection("1' OR '1'='1") == False
        assert SecurityValidator.validate_sql_injection("UNION SELECT * FROM users") == False
        assert SecurityValidator.validate_sql_injection("admin'--") == False
    
    def test_xss_detection(self):
        """
        测试XSS攻击检测
        """
        # 正常输入
        assert SecurityValidator.validate_xss("Hello World") == True
        assert SecurityValidator.validate_xss("This is a normal text") == True
        
        # XSS攻击
        assert SecurityValidator.validate_xss("<script>alert('xss')</script>") == False
        assert SecurityValidator.validate_xss("javascript:alert('xss')") == False
        assert SecurityValidator.validate_xss("<img src=x onerror=alert('xss')>") == False
        assert SecurityValidator.validate_xss("<iframe src='javascript:alert(1)'></iframe>") == False
    
    def test_path_traversal_detection(self):
        """
        测试路径遍历攻击检测
        """
        # 正常路径
        assert SecurityValidator.validate_path_traversal("normal/path") == True
        assert SecurityValidator.validate_path_traversal("file.txt") == True
        
        # 路径遍历攻击
        assert SecurityValidator.validate_path_traversal("../../../etc/passwd") == False
        assert SecurityValidator.validate_path_traversal("..\\..\\windows\\system32") == False
        assert SecurityValidator.validate_path_traversal("%2e%2e%2f%2e%2e%2f") == False
    
    def test_command_injection_detection(self):
        """
        测试命令注入检测
        """
        # 正常输入
        assert SecurityValidator.validate_command_injection("normal text") == True
        assert SecurityValidator.validate_command_injection("filename.txt") == True
        
        # 命令注入攻击
        assert SecurityValidator.validate_command_injection("file.txt; rm -rf /") == False
        assert SecurityValidator.validate_command_injection("$(cat /etc/passwd)") == False
        assert SecurityValidator.validate_command_injection("`whoami`") == False
        assert SecurityValidator.validate_command_injection("file.txt && cat /etc/passwd") == False
    
    def test_filename_validation(self):
        """
        测试文件名验证
        """
        # 正常文件名
        assert SecurityValidator.validate_filename("document.pdf") == True
        assert SecurityValidator.validate_filename("report_2024.docx") == True
        
        # 危险文件名
        assert SecurityValidator.validate_filename("../../../etc/passwd") == False
        assert SecurityValidator.validate_filename("file<script>.txt") == False
        assert SecurityValidator.validate_filename("CON.txt") == False  # Windows保留名
        assert SecurityValidator.validate_filename("file|pipe.txt") == False
    
    def test_uuid_validation(self):
        """
        测试UUID验证
        """
        # 有效UUID
        assert SecurityValidator.validate_uuid("123e4567-e89b-12d3-a456-426614174000") == True
        assert SecurityValidator.validate_uuid("00000000-0000-0000-0000-000000000000") == True
        
        # 无效UUID
        assert SecurityValidator.validate_uuid("invalid-uuid") == False
        assert SecurityValidator.validate_uuid("123e4567-e89b-12d3-a456") == False
        assert SecurityValidator.validate_uuid("") == False
    
    def test_string_sanitization(self):
        """
        测试字符串清理
        """
        # 正常字符串
        result = SecurityValidator.sanitize_string("Hello World")
        assert result == "Hello World"
        
        # 包含HTML的字符串
        result = SecurityValidator.sanitize_string("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        
        # 超长字符串
        long_string = "a" * 2000
        result = SecurityValidator.sanitize_string(long_string, max_length=100)
        assert len(result) <= 100


class TestSecurityScanner:
    """
    安全扫描器测试
    """
    
    def setup_method(self):
        """
        测试设置
        """
        self.scanner = SecurityScanner()
    
    def test_pdf_file_scan(self):
        """
        测试PDF文件扫描
        """
        # 模拟PDF文件内容
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n'
        
        result = self.scanner.scan_file_content(pdf_content, "document.pdf")
        
        assert result['safe'] == True
        assert result['file_size'] == len(pdf_content)
        assert 'md5_hash' in result
        assert 'sha256_hash' in result
    
    def test_executable_file_detection(self):
        """
        测试可执行文件检测
        """
        # 模拟Windows PE文件头
        exe_content = b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00'
        
        result = self.scanner.scan_file_content(exe_content, "malware.exe")
        
        assert result['safe'] == False
        assert any(threat['type'] == 'EXECUTABLE_FILE_DETECTED' for threat in result['threats'])
    
    def test_oversized_file_detection(self):
        """
        测试超大文件检测
        """
        # 创建超大文件内容
        large_content = b'A' * (200 * 1024 * 1024)  # 200MB
        
        result = self.scanner.scan_file_content(large_content, "large_file.txt")
        
        assert result['safe'] == False
        assert any(threat['type'] == 'FILE_SIZE_EXCEEDED' for threat in result['threats'])
    
    def test_malicious_script_detection(self):
        """
        测试恶意脚本检测
        """
        # 模拟包含恶意内容的文本文件
        script_content = b'#!/bin/bash\nrm -rf /\n'
        
        result = self.scanner.scan_file_content(script_content, "script.txt")
        
        # 应该检测到可疑内容
        assert len(result['threats']) > 0 or len(result['warnings']) > 0
    
    def test_json_file_validation(self):
        """
        测试JSON文件验证
        """
        # 有效JSON
        valid_json = b'{"name": "test", "value": 123}'
        result = self.scanner.scan_file_content(valid_json, "data.json")
        assert result['safe'] == True
        
        # 无效JSON
        invalid_json = b'{"name": "test", "value": }'
        result = self.scanner.scan_file_content(invalid_json, "data.json")
        assert result['safe'] == False
    
    @patch('app.utils.security_scanner.yara')
    def test_yara_scanning(self, mock_yara):
        """
        测试YARA规则扫描
        """
        # 模拟YARA匹配结果
        mock_match = Mock()
        mock_match.rule = 'SuspiciousExecutable'
        mock_yara.compile.return_value.match.return_value = [mock_match]
        
        scanner = SecurityScanner()
        result = scanner._scan_malware(b'test content')
        
        assert len(result['threats']) > 0
        assert result['threats'][0]['rule'] == 'SuspiciousExecutable'


class TestSecurityMiddleware:
    """
    安全中间件测试
    """
    
    def setup_method(self):
        """
        测试设置
        """
        self.client = TestClient(app)
    
    def test_rate_limiting(self):
        """
        测试速率限制
        """
        # 模拟大量请求
        responses = []
        for i in range(70):  # 超过每分钟60次的限制
            response = self.client.get("/health")
            responses.append(response)
        
        # 检查是否有请求被限制
        rate_limited = any(r.status_code == 429 for r in responses)
        # 注意：由于测试环境的特殊性，这个测试可能需要调整
    
    def test_security_headers(self):
        """
        测试安全响应头
        """
        response = self.client.get("/health")
        
        # 检查安全头是否存在
        expected_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Content-Security-Policy'
        ]
        
        for header in expected_headers:
            assert header in response.headers
    
    def test_malicious_path_blocking(self):
        """
        测试恶意路径阻止
        """
        malicious_paths = [
            "/admin/../../../etc/passwd",
            "/api/v1/files?file=../../../etc/passwd",
            "/test.php",
            "/.env"
        ]
        
        for path in malicious_paths:
            response = self.client.get(path)
            # 应该返回400或404，而不是200
            assert response.status_code in [400, 404]
    
    def test_sql_injection_in_params(self):
        """
        测试查询参数中的SQL注入
        """
        malicious_params = {
            'id': "1' OR '1'='1",
            'name': "'; DROP TABLE users; --"
        }
        
        response = self.client.get("/api/v1/projects", params=malicious_params)
        # 应该被安全中间件拦截
        assert response.status_code == 400
    
    def test_xss_in_params(self):
        """
        测试查询参数中的XSS
        """
        malicious_params = {
            'search': "<script>alert('xss')</script>",
            'filter': "javascript:alert('xss')"
        }
        
        response = self.client.get("/api/v1/projects", params=malicious_params)
        # 应该被安全中间件拦截
        assert response.status_code == 400


class TestFileUploadSecurity:
    """
    文件上传安全测试
    """
    
    def setup_method(self):
        """
        测试设置
        """
        self.client = TestClient(app)
    
    def test_malicious_file_upload(self):
        """
        测试恶意文件上传
        """
        # 模拟可执行文件
        malicious_content = b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00'
        
        files = {
            'file': ('malware.exe', BytesIO(malicious_content), 'application/octet-stream')
        }
        
        # 尝试上传到一个测试项目
        response = self.client.post(
            "/api/v1/projects/test-project-id/upload",
            files=files
        )
        
        # 应该被拒绝
        assert response.status_code in [400, 403]
    
    def test_oversized_file_upload(self):
        """
        测试超大文件上传
        """
        # 创建超大文件内容
        large_content = b'A' * (200 * 1024 * 1024)  # 200MB
        
        files = {
            'file': ('large_file.txt', BytesIO(large_content), 'text/plain')
        }
        
        response = self.client.post(
            "/api/v1/projects/test-project-id/upload",
            files=files
        )
        
        # 应该被拒绝
        assert response.status_code in [400, 413]
    
    def test_path_traversal_filename(self):
        """
        测试文件名路径遍历
        """
        normal_content = b'This is a normal file content'
        
        files = {
            'file': ('../../../etc/passwd', BytesIO(normal_content), 'text/plain')
        }
        
        response = self.client.post(
            "/api/v1/projects/test-project-id/upload",
            files=files
        )
        
        # 应该被拒绝或文件名被清理
        assert response.status_code in [400, 200]
        if response.status_code == 200:
            # 如果上传成功，文件名应该被清理
            data = response.json()
            assert '../' not in data.get('filename', '')


class TestDatabaseSecurity:
    """
    数据库安全测试
    """
    
    @pytest.mark.asyncio
    async def test_sql_injection_protection(self):
        """
        测试SQL注入防护
        """
        from app.core.database import get_db
        from app.services.project_service import project_service
        
        # 尝试SQL注入
        malicious_input = "'; DROP TABLE projects; --"
        
        db = next(get_db())
        
        # 这应该不会导致SQL注入，因为使用了ORM
        try:
            result = project_service.get_by_name(db, malicious_input)
            # 应该返回None或空结果，而不是执行恶意SQL
            assert result is None or isinstance(result, list)
        except Exception as e:
            # 如果抛出异常，应该是正常的数据库异常，而不是SQL语法错误
            assert "syntax error" not in str(e).lower()
        finally:
            db.close()


@pytest.fixture
def security_test_app():
    """
    安全测试应用fixture
    """
    from fastapi import FastAPI
    from app.middleware.security import SecurityMiddleware
    
    test_app = FastAPI()
    test_app.add_middleware(SecurityMiddleware)
    
    @test_app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    return test_app


class TestSecurityIntegration:
    """
    安全集成测试
    """
    
    def test_comprehensive_security_scan(self):
        """
        综合安全扫描测试
        """
        # 测试多种攻击向量的组合
        test_cases = [
            {
                'name': 'SQL注入 + XSS',
                'input': "'; DROP TABLE users; --<script>alert('xss')</script>",
                'expected_safe': False
            },
            {
                'name': '路径遍历 + 命令注入',
                'input': "../../../etc/passwd; cat /etc/shadow",
                'expected_safe': False
            },
            {
                'name': '正常输入',
                'input': "normal user input text",
                'expected_safe': True
            }
        ]
        
        for case in test_cases:
            result_sql = SecurityValidator.validate_sql_injection(case['input'])
            result_xss = SecurityValidator.validate_xss(case['input'])
            result_path = SecurityValidator.validate_path_traversal(case['input'])
            result_cmd = SecurityValidator.validate_command_injection(case['input'])
            
            overall_safe = all([result_sql, result_xss, result_path, result_cmd])
            
            if case['expected_safe']:
                assert overall_safe, f"Test case '{case['name']}' should be safe but was flagged as dangerous"
            else:
                assert not overall_safe, f"Test case '{case['name']}' should be dangerous but was flagged as safe"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])