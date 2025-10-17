"""
安全验证器 - 输入验证和SQL注入防护
"""
import re
import html
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, validator
from fastapi import HTTPException, status


class SecurityValidator:
    """
    安全验证器类
    """
    
    # SQL注入检测模式
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(\b(UNION|OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+\w+\s*=\s*\w+)",
        r"(--|#|/\*|\*/)",
        r"(\bxp_cmdshell\b)",
        r"(\bsp_executesql\b)",
        r"(\bCAST\s*\()",
        r"(\bCONVERT\s*\()",
        r"(\bCHAR\s*\()",
        r"(\bASCII\s*\()",
        r"(\bSUBSTRING\s*\()",
        r"(\bLEN\s*\()",
        r"(\bWAITFOR\s+DELAY)",
        r"(\bBENCHMARK\s*\()",
        r"(\bSLEEP\s*\()",
        r"(\bLOAD_FILE\s*\()",
        r"(\bINTO\s+OUTFILE)",
        r"(\bINTO\s+DUMPFILE)",
    ]
    
    # XSS检测模式
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onmouseover\s*=",
        r"onfocus\s*=",
        r"onblur\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<form[^>]*>",
        r"<input[^>]*>",
        r"<img[^>]*onerror",
        r"<svg[^>]*onload",
    ]
    
    # 路径遍历检测模式
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e%5c",
        r"..%2f",
        r"..%5c",
        r"%252e%252e%252f",
        r"%252e%252e%255c",
    ]
    
    # 命令注入检测模式
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]<>]",
        r"\b(cat|ls|dir|type|echo|ping|wget|curl|nc|netcat|telnet|ssh|ftp)\b",
        r"\b(rm|del|rmdir|mkdir|touch|chmod|chown|sudo|su)\b",
        r"\b(python|perl|ruby|php|bash|sh|cmd|powershell)\b",
        r"\b(eval|exec|system|shell_exec|passthru|proc_open)\b",
    ]
    
    @classmethod
    def validate_sql_injection(cls, value: str) -> bool:
        """
        检测SQL注入攻击
        
        Args:
            value: 要检测的字符串
            
        Returns:
            bool: True表示安全，False表示检测到SQL注入
        """
        if not isinstance(value, str):
            return True
            
        # 转换为小写进行检测
        lower_value = value.lower()
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, lower_value, re.IGNORECASE):
                return False
                
        return True
    
    @classmethod
    def validate_xss(cls, value: str) -> bool:
        """
        检测XSS攻击
        
        Args:
            value: 要检测的字符串
            
        Returns:
            bool: True表示安全，False表示检测到XSS
        """
        if not isinstance(value, str):
            return True
            
        # 转换为小写进行检测
        lower_value = value.lower()
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, lower_value, re.IGNORECASE):
                return False
                
        return True
    
    @classmethod
    def validate_path_traversal(cls, value: str) -> bool:
        """
        检测路径遍历攻击
        
        Args:
            value: 要检测的字符串
            
        Returns:
            bool: True表示安全，False表示检测到路径遍历
        """
        if not isinstance(value, str):
            return True
            
        # URL解码后检测
        import urllib.parse
        decoded_value = urllib.parse.unquote(value).lower()
        
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, decoded_value, re.IGNORECASE):
                return False
                
        return True
    
    @classmethod
    def validate_command_injection(cls, value: str) -> bool:
        """
        检测命令注入攻击
        
        Args:
            value: 要检测的字符串
            
        Returns:
            bool: True表示安全，False表示检测到命令注入
        """
        if not isinstance(value, str):
            return True
            
        # 转换为小写进行检测
        lower_value = value.lower()
        
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, lower_value, re.IGNORECASE):
                return False
                
        return True
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """
        清理字符串，移除危险字符
        
        Args:
            value: 要清理的字符串
            max_length: 最大长度限制
            
        Returns:
            str: 清理后的字符串
        """
        if not isinstance(value, str):
            return str(value)
        
        # 限制长度
        if len(value) > max_length:
            value = value[:max_length]
        
        # HTML转义
        value = html.escape(value)
        
        # 移除控制字符
        value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
        
        return value.strip()
    
    @classmethod
    def validate_uuid(cls, value: str) -> bool:
        """
        验证UUID格式
        
        Args:
            value: 要验证的UUID字符串
            
        Returns:
            bool: True表示有效的UUID格式
        """
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, value.lower()))
    
    @classmethod
    def validate_filename(cls, filename: str) -> bool:
        """
        验证文件名安全性
        
        Args:
            filename: 文件名
            
        Returns:
            bool: True表示安全的文件名
        """
        if not filename or len(filename) > 255:
            return False
        
        # 检查危险字符
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\x00']
        for char in dangerous_chars:
            if char in filename:
                return False
        
        # 检查路径遍历
        if not cls.validate_path_traversal(filename):
            return False
        
        # 检查保留名称（Windows）
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        name_without_ext = filename.split('.')[0].upper()
        if name_without_ext in reserved_names:
            return False
        
        return True
    
    @classmethod
    def validate_comprehensive(cls, value: str, field_name: str = "input") -> str:
        """
        综合安全验证
        
        Args:
            value: 要验证的值
            field_name: 字段名称（用于错误消息）
            
        Returns:
            str: 验证通过的值
            
        Raises:
            HTTPException: 验证失败时抛出异常
        """
        if not isinstance(value, str):
            value = str(value)
        
        # SQL注入检测
        if not cls.validate_sql_injection(value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"检测到SQL注入攻击尝试: {field_name}"
            )
        
        # XSS检测
        if not cls.validate_xss(value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"检测到XSS攻击尝试: {field_name}"
            )
        
        # 路径遍历检测
        if not cls.validate_path_traversal(value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"检测到路径遍历攻击尝试: {field_name}"
            )
        
        # 命令注入检测
        if not cls.validate_command_injection(value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"检测到命令注入攻击尝试: {field_name}"
            )
        
        return cls.sanitize_string(value)


class SecureBaseModel(BaseModel):
    """
    安全的基础模型，自动进行输入验证
    """
    
    @validator('*', pre=True)
    def validate_security(cls, v, values, **kwargs):
        """
        对所有字符串字段进行安全验证
        """
        field_name = kwargs.get('field', {}).get('field_info', {}).get('alias', 'unknown')
        
        if isinstance(v, str):
            # 跳过某些不需要严格验证的字段
            skip_fields = ['password', 'token', 'content', 'description']
            if field_name not in skip_fields:
                return SecurityValidator.validate_comprehensive(v, field_name)
        return v


def secure_query_params(**params) -> Dict[str, Any]:
    """
    安全验证查询参数
    
    Args:
        **params: 查询参数
        
    Returns:
        Dict[str, Any]: 验证后的参数
    """
    validated_params = {}
    
    for key, value in params.items():
        if isinstance(value, str):
            validated_params[key] = SecurityValidator.validate_comprehensive(value, key)
        else:
            validated_params[key] = value
    
    return validated_params


def validate_request_size(content_length: Optional[int], max_size: int = 100 * 1024 * 1024) -> bool:
    """
    验证请求大小
    
    Args:
        content_length: 请求内容长度
        max_size: 最大允许大小（字节）
        
    Returns:
        bool: True表示大小合法
    """
    if content_length is None:
        return True
    
    return content_length <= max_size


def validate_rate_limit(request_count: int, time_window: int, max_requests: int = 100) -> bool:
    """
    验证请求频率限制
    
    Args:
        request_count: 时间窗口内的请求数量
        time_window: 时间窗口（秒）
        max_requests: 最大请求数量
        
    Returns:
        bool: True表示未超过限制
    """
    return request_count <= max_requests