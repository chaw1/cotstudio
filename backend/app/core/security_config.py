"""
安全配置管理
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.core.config import settings


class SecurityConfig(BaseModel):
    """
    安全配置类
    """
    
    # 输入验证配置
    max_input_length: int = Field(default=10000, description="最大输入长度")
    enable_sql_injection_detection: bool = Field(default=True, description="启用SQL注入检测")
    enable_xss_detection: bool = Field(default=True, description="启用XSS检测")
    enable_path_traversal_detection: bool = Field(default=True, description="启用路径遍历检测")
    enable_command_injection_detection: bool = Field(default=True, description="启用命令注入检测")
    
    # 文件上传安全配置
    max_file_size: int = Field(default=100*1024*1024, description="最大文件大小（字节）")
    allowed_mime_types: List[str] = Field(default_factory=lambda: [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/markdown",
        "application/x-latex",
        "application/json"
    ])
    enable_virus_scanning: bool = Field(default=True, description="启用病毒扫描")
    quarantine_suspicious_files: bool = Field(default=True, description="隔离可疑文件")
    max_compression_ratio: float = Field(default=1000.0, description="最大压缩比")
    
    # 速率限制配置
    enable_rate_limiting: bool = Field(default=True, description="启用速率限制")
    max_requests_per_minute: int = Field(default=60, description="每分钟最大请求数")
    max_requests_per_hour: int = Field(default=1000, description="每小时最大请求数")
    rate_limit_window_minutes: int = Field(default=1, description="速率限制窗口（分钟）")
    
    # 安全响应头配置
    enable_security_headers: bool = Field(default=True, description="启用安全响应头")
    hsts_max_age: int = Field(default=31536000, description="HSTS最大年龄（秒）")
    csp_policy: str = Field(
        default="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        description="内容安全策略"
    )
    
    # 错误处理配置
    enable_circuit_breaker: bool = Field(default=True, description="启用熔断器")
    circuit_breaker_failure_threshold: int = Field(default=5, description="熔断器失败阈值")
    circuit_breaker_recovery_timeout: int = Field(default=60, description="熔断器恢复超时（秒）")
    
    # 重试配置
    max_retry_attempts: int = Field(default=3, description="最大重试次数")
    retry_base_delay: float = Field(default=1.0, description="重试基础延迟（秒）")
    retry_max_delay: float = Field(default=60.0, description="重试最大延迟（秒）")
    
    # 日志和监控配置
    log_security_events: bool = Field(default=True, description="记录安全事件")
    log_failed_requests: bool = Field(default=True, description="记录失败请求")
    enable_request_tracing: bool = Field(default=True, description="启用请求追踪")
    
    # IP阻止配置
    enable_ip_blocking: bool = Field(default=True, description="启用IP阻止")
    auto_block_threshold: int = Field(default=10, description="自动阻止阈值")
    block_duration_minutes: int = Field(default=60, description="阻止持续时间（分钟）")
    
    # CSRF保护配置
    enable_csrf_protection: bool = Field(default=False, description="启用CSRF保护")
    csrf_token_expiry_hours: int = Field(default=24, description="CSRF令牌过期时间（小时）")
    
    # 健康检查配置
    health_check_interval_seconds: int = Field(default=30, description="健康检查间隔（秒）")
    health_check_timeout_seconds: int = Field(default=10, description="健康检查超时（秒）")


class ThreatDetectionConfig(BaseModel):
    """
    威胁检测配置
    """
    
    # SQL注入检测模式
    sql_injection_patterns: List[str] = Field(default_factory=lambda: [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(\b(UNION|OR|AND)\s+\d+\s*=\s*\d+)",
        r"(--|#|/\*|\*/)",
        r"(\bxp_cmdshell\b)",
        r"(\bsp_executesql\b)"
    ])
    
    # XSS检测模式
    xss_patterns: List[str] = Field(default_factory=lambda: [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*="
    ])
    
    # 可疑User-Agent模式
    suspicious_user_agents: List[str] = Field(default_factory=lambda: [
        "sqlmap", "nikto", "nmap", "masscan", "zap",
        "burp", "w3af", "acunetix", "nessus"
    ])
    
    # 可疑文件扩展名
    dangerous_extensions: List[str] = Field(default_factory=lambda: [
        ".exe", ".bat", ".cmd", ".com", ".scr", ".pif",
        ".vbs", ".js", ".jar", ".php", ".asp", ".jsp"
    ])
    
    # 恶意文件签名
    malicious_signatures: Dict[str, str] = Field(default_factory=lambda: {
        "PE": "4D5A",  # Windows PE
        "ELF": "7F454C46",  # Linux ELF
        "MACH_O_32": "FEEDFACE",  # Mach-O 32-bit
        "MACH_O_64": "FEEDFACF"   # Mach-O 64-bit
    })


class SecurityPolicyConfig(BaseModel):
    """
    安全策略配置
    """
    
    # 密码策略
    min_password_length: int = Field(default=8, description="最小密码长度")
    require_uppercase: bool = Field(default=True, description="要求大写字母")
    require_lowercase: bool = Field(default=True, description="要求小写字母")
    require_numbers: bool = Field(default=True, description="要求数字")
    require_special_chars: bool = Field(default=True, description="要求特殊字符")
    
    # 会话策略
    session_timeout_minutes: int = Field(default=30, description="会话超时时间（分钟）")
    max_concurrent_sessions: int = Field(default=5, description="最大并发会话数")
    
    # 访问控制策略
    enable_rbac: bool = Field(default=True, description="启用基于角色的访问控制")
    default_user_role: str = Field(default="viewer", description="默认用户角色")
    
    # 数据保护策略
    encrypt_sensitive_data: bool = Field(default=True, description="加密敏感数据")
    data_retention_days: int = Field(default=365, description="数据保留天数")
    
    # 审计策略
    audit_all_operations: bool = Field(default=True, description="审计所有操作")
    audit_retention_days: int = Field(default=90, description="审计日志保留天数")


# 全局安全配置实例
security_config = SecurityConfig()
threat_detection_config = ThreatDetectionConfig()
security_policy_config = SecurityPolicyConfig()


def get_security_config() -> SecurityConfig:
    """
    获取安全配置
    """
    return security_config


def get_threat_detection_config() -> ThreatDetectionConfig:
    """
    获取威胁检测配置
    """
    return threat_detection_config


def get_security_policy_config() -> SecurityPolicyConfig:
    """
    获取安全策略配置
    """
    return security_policy_config


def update_security_config(new_config: Dict) -> SecurityConfig:
    """
    更新安全配置
    
    Args:
        new_config: 新的配置字典
        
    Returns:
        SecurityConfig: 更新后的配置
    """
    global security_config
    
    # 验证配置
    updated_config = SecurityConfig(**{**security_config.dict(), **new_config})
    security_config = updated_config
    
    return security_config


def reset_security_config():
    """
    重置安全配置为默认值
    """
    global security_config, threat_detection_config, security_policy_config
    
    security_config = SecurityConfig()
    threat_detection_config = ThreatDetectionConfig()
    security_policy_config = SecurityPolicyConfig()


def validate_security_config() -> Dict[str, bool]:
    """
    验证安全配置的有效性
    
    Returns:
        Dict[str, bool]: 验证结果
    """
    validation_results = {
        'file_size_valid': security_config.max_file_size > 0,
        'rate_limit_valid': security_config.max_requests_per_minute > 0,
        'retry_config_valid': security_config.max_retry_attempts > 0,
        'timeout_valid': security_config.circuit_breaker_recovery_timeout > 0,
        'mime_types_valid': len(security_config.allowed_mime_types) > 0
    }
    
    return validation_results


def get_security_summary() -> Dict[str, any]:
    """
    获取安全配置摘要
    
    Returns:
        Dict[str, any]: 安全配置摘要
    """
    return {
        'input_validation': {
            'sql_injection_detection': security_config.enable_sql_injection_detection,
            'xss_detection': security_config.enable_xss_detection,
            'path_traversal_detection': security_config.enable_path_traversal_detection,
            'command_injection_detection': security_config.enable_command_injection_detection
        },
        'file_security': {
            'virus_scanning': security_config.enable_virus_scanning,
            'quarantine_enabled': security_config.quarantine_suspicious_files,
            'max_file_size_mb': security_config.max_file_size / (1024 * 1024),
            'allowed_types_count': len(security_config.allowed_mime_types)
        },
        'rate_limiting': {
            'enabled': security_config.enable_rate_limiting,
            'requests_per_minute': security_config.max_requests_per_minute,
            'requests_per_hour': security_config.max_requests_per_hour
        },
        'error_handling': {
            'circuit_breaker': security_config.enable_circuit_breaker,
            'max_retries': security_config.max_retry_attempts
        },
        'monitoring': {
            'security_logging': security_config.log_security_events,
            'request_tracing': security_config.enable_request_tracing,
            'ip_blocking': security_config.enable_ip_blocking
        }
    }