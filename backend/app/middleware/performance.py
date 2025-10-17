"""
性能监控中间件
"""
import time
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from app.core.monitoring import metrics_collector
from app.core.cache import api_cache
from app.core.app_logging import logger


async def performance_monitoring_middleware(request: Request, call_next: Callable) -> Response:
    """性能监控中间件"""
    start_time = time.time()
    
    # 获取请求信息
    method = request.method
    path = request.url.path
    user_id = getattr(request.state, 'user_id', None)
    client_ip = request.client.host if request.client else None
    
    try:
        # 执行请求
        response = await call_next(request)
        
        # 计算响应时间
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # 记录请求指标
        metrics_collector.record_request_metric(
            method=method,
            path=path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            ip_address=client_ip
        )
        
        # 添加性能头信息
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        response.headers["X-Request-ID"] = getattr(request.state, 'request_id', 'unknown')
        
        # 记录慢请求
        if duration_ms > 5000:  # 超过5秒的请求
            logger.warning(
                f"Slow request detected: {method} {path} took {duration_ms:.2f}ms",
                extra={
                    "method": method,
                    "path": path,
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                    "user_id": user_id,
                    "ip_address": client_ip
                }
            )
        
        return response
        
    except Exception as e:
        # 计算错误响应时间
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # 记录错误请求指标
        metrics_collector.record_request_metric(
            method=method,
            path=path,
            status_code=500,
            duration_ms=duration_ms,
            user_id=user_id,
            ip_address=client_ip
        )
        
        # 记录错误日志
        logger.error(
            f"Request error: {method} {path}",
            extra={
                "method": method,
                "path": path,
                "duration_ms": duration_ms,
                "error": str(e),
                "user_id": user_id,
                "ip_address": client_ip
            }
        )
        
        # 返回错误响应
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "request_id": getattr(request.state, 'request_id', 'unknown')
            },
            headers={
                "X-Response-Time": f"{duration_ms:.2f}ms",
                "X-Request-ID": getattr(request.state, 'request_id', 'unknown')
            }
        )


async def response_caching_middleware(request: Request, call_next: Callable) -> Response:
    """响应缓存中间件"""
    # 只对GET请求进行缓存
    if request.method != "GET":
        return await call_next(request)
    
    # 排除某些不需要缓存的路径
    excluded_paths = [
        "/health",
        "/metrics",
        "/monitoring",
        "/docs",
        "/redoc",
        "/openapi.json"
    ]
    
    path = request.url.path
    if any(excluded in path for excluded in excluded_paths):
        return await call_next(request)
    
    # 生成缓存键
    query_params = str(request.query_params) if request.query_params else ""
    user_id = getattr(request.state, 'user_id', 'anonymous')
    cache_key = f"{path}:{query_params}:{user_id}"
    
    # 尝试从缓存获取响应
    cached_response = api_cache.get_cached_response(cache_key)
    if cached_response:
        logger.debug(f"Cache hit for {path}")
        return JSONResponse(
            content=cached_response["content"],
            status_code=cached_response["status_code"],
            headers={
                **cached_response.get("headers", {}),
                "X-Cache": "HIT"
            }
        )
    
    # 执行请求
    response = await call_next(request)
    
    # 只缓存成功的响应
    if response.status_code == 200:
        try:
            # 读取响应内容
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # 解析JSON内容
            import json
            content = json.loads(response_body.decode())
            
            # 缓存响应（5分钟）
            cached_data = {
                "content": content,
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }
            api_cache.cache_response(cache_key, cached_data, expire=300)
            
            # 重新创建响应
            return JSONResponse(
                content=content,
                status_code=response.status_code,
                headers={
                    **dict(response.headers),
                    "X-Cache": "MISS"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to cache response for {path}: {e}")
            # 如果缓存失败，返回原始响应
            return response
    
    # 添加缓存状态头
    response.headers["X-Cache"] = "SKIP"
    return response