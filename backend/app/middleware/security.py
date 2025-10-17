"""
安全中间件
"""
import time
import logging
from typing import Dict, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security_validators import SecurityValidator, validate_request_size
from app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    安全中间件 - 提供请求验证、速率限制、安全头等功能
    """
    
    def __init__(self, app, enable_rate_limiting: bool = True, enable_security_headers: bool = True):
        super().__init__(app)
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_security_headers = enable_security_headers
        
        # 速率限制存储 - 在生产环境中应该使用Redis
        self.rate_limit_storage = defaultdict(lambda: deque())
        
        # 安全配置
        self.max_requests_per_minute = 60
        self.max_requests_per_hour = 1000
        self.blocked_ips = set()
        self.suspicious_patterns = []
        
        # 豁免路径 - 这些路径不进行严格的安全检查
        self.exempt_paths = [
            '/api/v1/auth/login',
            '/api/v1/auth/refresh',
            '/api/v1/auth/logout',
            '/docs',
            '/redoc',
            '/openapi.json',
            '/health',
            '/api/v1/errors/report'
        ]
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求
        """
        start_time = time.time()
        
        try:
            # 检查是否为豁免路径
            is_exempt = any(request.url.path.startswith(path) for path in self.exempt_paths)
            
            # 1. IP黑名单检查
            client_ip = self._get_client_ip(request)
            if client_ip in self.blocked_ips:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "IP_BLOCKED", "message": "您的IP已被阻止访问"}
                )
            
            # 2. 请求大小验证
            content_length = request.headers.get('content-length')
            if content_length:
                if not validate_request_size(int(content_length)):
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"error": "REQUEST_TOO_LARGE", "message": "请求体过大"}
                    )
            
            # 3. 速率限制检查
            if self.enable_rate_limiting:
                rate_limit_result = self._check_rate_limit(client_ip)
                if not rate_limit_result['allowed']:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "RATE_LIMIT_EXCEEDED",
                            "message": "请求频率过高，请稍后重试",
                            "retry_after": rate_limit_result['retry_after']
                        },
                        headers={"Retry-After": str(rate_limit_result['retry_after'])}
                    )
            
            # 4. 请求路径安全验证 (豁免路径跳过)
            if not is_exempt:
                path_validation_result = self._validate_request_path(request.url.path)
                if not path_validation_result['safe']:
                    logger.warning(f"Suspicious request path from {client_ip}: {request.url.path}")
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"error": "INVALID_REQUEST_PATH", "message": "请求路径无效"}
                    )
            
            # 5. 查询参数安全验证 (豁免路径跳过)
            if not is_exempt:
                query_validation_result = self._validate_query_params(request.query_params)
                if not query_validation_result['safe']:
                    logger.warning(f"Suspicious query parameters from {client_ip}: {dict(request.query_params)}")
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"error": "INVALID_QUERY_PARAMS", "message": "查询参数包含非法内容"}
                    )
            
            # 6. User-Agent检查 (豁免路径跳过严格检查)
            user_agent = request.headers.get('user-agent', '')
            if not is_exempt and not self._validate_user_agent(user_agent):
                logger.warning(f"Suspicious User-Agent from {client_ip}: {user_agent}")
                # 不阻止请求，只记录警告
            
            # 处理请求
            response = await call_next(request)
            
            # 7. 添加安全响应头
            if self.enable_security_headers:
                response = self._add_security_headers(response)
            
            # 8. 记录请求日志
            process_time = time.time() - start_time
            self._log_request(request, response, process_time, client_ip)
            
            return response
        
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "SECURITY_MIDDLEWARE_ERROR", "message": "安全检查失败"}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端IP地址
        """
        # 检查代理头
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else 'unknown'
    
    def _check_rate_limit(self, client_ip: str) -> Dict[str, any]:
        """
        检查速率限制
        """
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        # 获取IP的请求记录
        requests = self.rate_limit_storage[client_ip]
        
        # 清理过期记录
        while requests and requests[0] < hour_ago:
            requests.popleft()
        
        # 统计最近一分钟和一小时的请求数
        minute_requests = sum(1 for req_time in requests if req_time > minute_ago)
        hour_requests = len(requests)
        
        # 检查限制
        if minute_requests >= self.max_requests_per_minute:
            return {'allowed': False, 'retry_after': 60}
        
        if hour_requests >= self.max_requests_per_hour:
            return {'allowed': False, 'retry_after': 3600}
        
        # 记录当前请求
        requests.append(now)
        
        return {'allowed': True, 'retry_after': 0}
    
    def _validate_request_path(self, path: str) -> Dict[str, any]:
        """
        验证请求路径
        """
        result = {'safe': True, 'issues': []}
        
        # 路径遍历检查
        if not SecurityValidator.validate_path_traversal(path):
            result['safe'] = False
            result['issues'].append('PATH_TRAVERSAL')
        
        # 检查可疑路径模式
        suspicious_patterns = [
            '/admin', '/wp-admin', '/phpmyadmin', '/config',
            '/.env', '/.git', '/backup', '/test',
            '/shell', '/cmd', '/eval'
        ]
        
        path_lower = path.lower()
        for pattern in suspicious_patterns:
            if pattern in path_lower:
                result['issues'].append(f'SUSPICIOUS_PATH:{pattern}')
        
        # 检查文件扩展名
        dangerous_extensions = ['.php', '.asp', '.jsp', '.exe', '.bat', '.sh']
        for ext in dangerous_extensions:
            if path_lower.endswith(ext):
                result['safe'] = False
                result['issues'].append(f'DANGEROUS_EXTENSION:{ext}')
        
        return result
    
    def _validate_query_params(self, query_params) -> Dict[str, any]:
        """
        验证查询参数
        """
        result = {'safe': True, 'issues': []}
        
        for key, value in query_params.items():
            # SQL注入检查
            if not SecurityValidator.validate_sql_injection(str(value)):
                result['safe'] = False
                result['issues'].append(f'SQL_INJECTION:{key}')
            
            # XSS检查
            if not SecurityValidator.validate_xss(str(value)):
                result['safe'] = False
                result['issues'].append(f'XSS:{key}')
            
            # 命令注入检查
            if not SecurityValidator.validate_command_injection(str(value)):
                result['safe'] = False
                result['issues'].append(f'COMMAND_INJECTION:{key}')
        
        return result
    
    def _validate_user_agent(self, user_agent: str) -> bool:
        """
        验证User-Agent
        """
        if not user_agent:
            return False
        
        # 检查已知的恶意User-Agent模式
        malicious_patterns = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'zap',
            'burp', 'w3af', 'acunetix', 'nessus',
            'python-requests', 'curl', 'wget'  # 可能的自动化工具
        ]
        
        user_agent_lower = user_agent.lower()
        for pattern in malicious_patterns:
            if pattern in user_agent_lower:
                return False
        
        return True
    
    def _add_security_headers(self, response: Response) -> Response:
        """
        添加安全响应头
        """
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'X-Permitted-Cross-Domain-Policies': 'none'
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response
    
    def _log_request(self, request: Request, response: Response, process_time: float, client_ip: str):
        """
        记录请求日志
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'client_ip': client_ip,
            'method': request.method,
            'path': request.url.path,
            'query_params': dict(request.query_params),
            'user_agent': request.headers.get('user-agent', ''),
            'status_code': response.status_code,
            'process_time': round(process_time, 3),
            'content_length': response.headers.get('content-length', 0)
        }
        
        # 记录到日志
        if response.status_code >= 400:
            logger.warning(f"HTTP {response.status_code}: {log_data}")
        else:
            logger.info(f"Request processed: {client_ip} {request.method} {request.url.path} - {response.status_code}")
    
    def block_ip(self, ip: str):
        """
        阻止IP地址
        """
        self.blocked_ips.add(ip)
        logger.warning(f"IP blocked: {ip}")
    
    def unblock_ip(self, ip: str):
        """
        解除IP阻止
        """
        self.blocked_ips.discard(ip)
        logger.info(f"IP unblocked: {ip}")
    
    def get_rate_limit_stats(self) -> Dict[str, any]:
        """
        获取速率限制统计
        """
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        stats = {
            'total_ips': len(self.rate_limit_storage),
            'blocked_ips': len(self.blocked_ips),
            'active_ips': 0,
            'top_ips': []
        }
        
        ip_request_counts = []
        
        for ip, requests in self.rate_limit_storage.items():
            # 清理过期记录
            while requests and requests[0] < hour_ago:
                requests.popleft()
            
            if requests:
                stats['active_ips'] += 1
                ip_request_counts.append((ip, len(requests)))
        
        # 获取请求最多的IP
        ip_request_counts.sort(key=lambda x: x[1], reverse=True)
        stats['top_ips'] = ip_request_counts[:10]
        
        return stats


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF保护中间件
    """
    
    def __init__(self, app, exempt_paths: Optional[list] = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or ['/docs', '/redoc', '/openapi.json', '/health']
    
    async def dispatch(self, request: Request, call_next):
        """
        处理CSRF保护
        """
        # 跳过GET、HEAD、OPTIONS请求
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return await call_next(request)
        
        # 跳过豁免路径
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # 检查CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        if not csrf_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "CSRF_TOKEN_MISSING", "message": "缺少CSRF令牌"}
            )
        
        # 验证CSRF token（这里需要实现具体的验证逻辑）
        if not self._validate_csrf_token(csrf_token, request):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "CSRF_TOKEN_INVALID", "message": "CSRF令牌无效"}
            )
        
        return await call_next(request)
    
    def _validate_csrf_token(self, token: str, request: Request) -> bool:
        """
        验证CSRF令牌
        """
        # 这里应该实现具体的CSRF令牌验证逻辑
        # 例如：检查令牌是否与会话中的令牌匹配
        return True  # 临时返回True，实际应该实现验证逻辑


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """
    请求大小限制中间件
    """
    
    def __init__(self, app, max_size: int = 100 * 1024 * 1024):  # 100MB
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next):
        """
        检查请求大小
        """
        content_length = request.headers.get('content-length')
        
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error": "REQUEST_TOO_LARGE",
                    "message": f"请求体大小超过限制 ({self.max_size} bytes)"
                }
            )
        
        return await call_next(request)