"""
Redis缓存和API响应优化
"""
import json
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import redis
from redis import Redis
from app.core.config import settings
from app.core.app_logging import logger


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis_client: Optional[Redis] = None
        self._connect()
    
    def _connect(self):
        """连接Redis"""
        try:
            self._redis_client = redis.from_url(
                self.redis_url,
                decode_responses=False,  # 保持二进制数据
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # 测试连接
            self._redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis_client = None
    
    @property
    def redis(self) -> Optional[Redis]:
        """获取Redis客户端"""
        if self._redis_client is None:
            self._connect()
        return self._redis_client
    
    def is_available(self) -> bool:
        """检查Redis是否可用"""
        try:
            return self.redis is not None and self.redis.ping()
        except Exception:
            return False
    
    def set(self, key: str, value: Any, expire: int = 3600, serialize: str = "json") -> bool:
        """设置缓存值"""
        if not self.is_available():
            return False
        
        try:
            # 序列化数据
            if serialize == "json":
                serialized_value = json.dumps(value, default=str)
            elif serialize == "pickle":
                serialized_value = pickle.dumps(value)
            else:
                serialized_value = str(value)
            
            # 设置缓存
            result = self.redis.setex(key, expire, serialized_value)
            logger.debug(f"Cache set: {key} (expire: {expire}s)")
            return result
            
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False
    
    def get(self, key: str, serialize: str = "json") -> Optional[Any]:
        """获取缓存值"""
        if not self.is_available():
            return None
        
        try:
            value = self.redis.get(key)
            if value is None:
                return None
            
            # 反序列化数据
            if serialize == "json":
                return json.loads(value)
            elif serialize == "pickle":
                return pickle.loads(value)
            else:
                return value.decode('utf-8') if isinstance(value, bytes) else value
                
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.is_available():
            return False
        
        try:
            result = self.redis.delete(key)
            logger.debug(f"Cache deleted: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self.is_available():
            return False
        
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"Cache exists check failed for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        if not self.is_available():
            return 0
        
        try:
            keys = self.redis.keys(pattern)
            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"Cleared {deleted} cache keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache pattern clear failed for pattern {pattern}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if not self.is_available():
            return {"status": "unavailable"}
        
        try:
            info = self.redis.info()
            return {
                "status": "available",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"status": "error", "error": str(e)}


# 全局缓存管理器实例
cache_manager = CacheManager()


def cache_key_generator(*args, **kwargs) -> str:
    """生成缓存键"""
    # 创建基于参数的唯一键
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items()) if kwargs else {}
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(expire: int = 3600, key_prefix: str = "", serialize: str = "json"):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{cache_key_generator(*args, **kwargs)}"
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key, serialize=serialize)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            cache_manager.set(cache_key, result, expire=expire, serialize=serialize)
            logger.debug(f"Cache miss, stored: {cache_key}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{cache_key_generator(*args, **kwargs)}"
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key, serialize=serialize)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            cache_manager.set(cache_key, result, expire=expire, serialize=serialize)
            logger.debug(f"Cache miss, stored: {cache_key}")
            
            return result
        
        # 根据函数类型返回对应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class APIResponseCache:
    """API响应缓存"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    def cache_response(self, request_key: str, response_data: Any, expire: int = 300):
        """缓存API响应"""
        cache_key = f"api_response:{request_key}"
        return self.cache.set(cache_key, response_data, expire=expire)
    
    def get_cached_response(self, request_key: str) -> Optional[Any]:
        """获取缓存的API响应"""
        cache_key = f"api_response:{request_key}"
        return self.cache.get(cache_key)
    
    def invalidate_project_cache(self, project_id: str):
        """使项目相关缓存失效"""
        patterns = [
            f"api_response:*project:{project_id}*",
            f"project_stats:{project_id}*",
            f"project_files:{project_id}*",
            f"project_cot:{project_id}*"
        ]
        
        for pattern in patterns:
            self.cache.clear_pattern(pattern)
    
    def invalidate_user_cache(self, user_id: str):
        """使用户相关缓存失效"""
        patterns = [
            f"api_response:*user:{user_id}*",
            f"user_projects:{user_id}*",
            f"user_stats:{user_id}*"
        ]
        
        for pattern in patterns:
            self.cache.clear_pattern(pattern)


# 全局API响应缓存实例
api_cache = APIResponseCache(cache_manager)


# 常用缓存装饰器预设
def cache_project_data(expire: int = 1800):
    """项目数据缓存装饰器"""
    return cached(expire=expire, key_prefix="project_data")


def cache_file_data(expire: int = 3600):
    """文件数据缓存装饰器"""
    return cached(expire=expire, key_prefix="file_data")


def cache_cot_data(expire: int = 900):
    """CoT数据缓存装饰器"""
    return cached(expire=expire, key_prefix="cot_data")


def cache_stats(expire: int = 300):
    """统计数据缓存装饰器"""
    return cached(expire=expire, key_prefix="stats")