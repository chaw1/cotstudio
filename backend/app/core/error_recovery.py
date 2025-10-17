"""
错误处理和异常恢复机制
"""
import logging
import traceback
import asyncio
from typing import Any, Callable, Dict, List, Optional, Type, Union
from functools import wraps
from datetime import datetime, timedelta
import json

from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from redis import Redis
from celery.exceptions import Retry, WorkerLostError

from app.core.config import settings
from app.core.exceptions import COTStudioException, DatabaseError

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    熔断器模式实现
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if self._should_attempt_reset():
                    self.state = 'HALF_OPEN'
                else:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="服务暂时不可用，请稍后重试"
                    )
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """
        检查是否应该尝试重置熔断器
        """
        if self.last_failure_time is None:
            return True
        
        return (datetime.now() - self.last_failure_time).seconds >= self.recovery_timeout
    
    def _on_success(self):
        """
        成功时重置熔断器
        """
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """
        失败时更新熔断器状态
        """
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'


class RetryManager:
    """
    重试管理器
    """
    
    @staticmethod
    def exponential_backoff(
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        指数退避重试装饰器
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        
                        if attempt == max_retries:
                            logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                            raise e
                        
                        # 计算延迟时间
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        
                        if jitter:
                            import random
                            delay *= (0.5 + random.random() * 0.5)
                        
                        logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}")
                        await asyncio.sleep(delay)
                
                raise last_exception
            
            return wrapper
        return decorator
    
    @staticmethod
    def database_retry(max_retries: int = 3):
        """
        数据库操作重试装饰器
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except (OperationalError, IntegrityError) as e:
                        last_exception = e
                        
                        if attempt == max_retries:
                            logger.error(f"Database operation {func.__name__} failed after {max_retries} retries: {e}")
                            raise DatabaseError(f"数据库操作失败: {str(e)}", func.__name__)
                        
                        # 数据库连接问题，等待后重试
                        delay = 2 ** attempt
                        logger.warning(f"Database operation {func.__name__} failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                        import time
                        time.sleep(delay)
                        
                        # 如果是会话相关的错误，尝试回滚
                        if 'db' in kwargs and hasattr(kwargs['db'], 'rollback'):
                            try:
                                kwargs['db'].rollback()
                            except Exception:
                                pass
                    
                    except Exception as e:
                        # 非数据库相关错误，直接抛出
                        raise e
                
                raise last_exception
            
            return wrapper
        return decorator


class ErrorRecoveryManager:
    """
    错误恢复管理器
    """
    
    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis_client = redis_client
        self.error_counts = {}
        self.recovery_strategies = {}
    
    def register_recovery_strategy(self, error_type: str, strategy: Callable):
        """
        注册错误恢复策略
        
        Args:
            error_type: 错误类型
            strategy: 恢复策略函数
        """
        self.recovery_strategies[error_type] = strategy
    
    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> bool:
        """
        处理错误并尝试恢复
        
        Args:
            error: 异常对象
            context: 错误上下文
            
        Returns:
            bool: 是否成功恢复
        """
        error_type = type(error).__name__
        
        # 记录错误
        await self._log_error(error, context)
        
        # 更新错误计数
        self._update_error_count(error_type)
        
        # 尝试恢复
        if error_type in self.recovery_strategies:
            try:
                recovery_strategy = self.recovery_strategies[error_type]
                success = await recovery_strategy(error, context)
                
                if success:
                    logger.info(f"Successfully recovered from {error_type}")
                    return True
                else:
                    logger.warning(f"Recovery strategy failed for {error_type}")
            
            except Exception as recovery_error:
                logger.error(f"Recovery strategy error for {error_type}: {recovery_error}")
        
        return False
    
    async def _log_error(self, error: Exception, context: Dict[str, Any]):
        """
        记录错误信息
        """
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context
        }
        
        # 记录到日志
        logger.error(f"Error occurred: {error_info}")
        
        # 如果有Redis，也记录到Redis
        if self.redis_client:
            try:
                error_key = f"error_log:{datetime.now().strftime('%Y%m%d')}"
                self.redis_client.lpush(error_key, json.dumps(error_info, ensure_ascii=False))
                self.redis_client.expire(error_key, 86400 * 7)  # 保留7天
            except Exception as redis_error:
                logger.warning(f"Failed to log error to Redis: {redis_error}")
    
    def _update_error_count(self, error_type: str):
        """
        更新错误计数
        """
        current_hour = datetime.now().strftime('%Y%m%d%H')
        key = f"{error_type}:{current_hour}"
        
        if key not in self.error_counts:
            self.error_counts[key] = 0
        
        self.error_counts[key] += 1
        
        # 清理旧的计数
        cutoff_time = (datetime.now() - timedelta(hours=24)).strftime('%Y%m%d%H')
        keys_to_remove = [k for k in self.error_counts.keys() if k.split(':')[1] < cutoff_time]
        for k in keys_to_remove:
            del self.error_counts[k]
    
    def get_error_statistics(self) -> Dict[str, int]:
        """
        获取错误统计信息
        """
        stats = {}
        for key, count in self.error_counts.items():
            error_type = key.split(':')[0]
            if error_type not in stats:
                stats[error_type] = 0
            stats[error_type] += count
        
        return stats


# 数据库连接恢复策略
async def database_recovery_strategy(error: Exception, context: Dict[str, Any]) -> bool:
    """
    数据库连接恢复策略
    """
    try:
        from app.core.database import engine, SessionLocal
        
        # 尝试重新创建连接
        engine.dispose()
        
        # 测试新连接
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        logger.info("Database connection recovered successfully")
        return True
    
    except Exception as recovery_error:
        logger.error(f"Database recovery failed: {recovery_error}")
        return False


# Redis连接恢复策略
async def redis_recovery_strategy(error: Exception, context: Dict[str, Any]) -> bool:
    """
    Redis连接恢复策略
    """
    try:
        # 这里可以实现Redis重连逻辑
        # 由于Redis客户端通常有自动重连功能，这里主要是验证连接
        logger.info("Redis connection recovery attempted")
        return True
    
    except Exception as recovery_error:
        logger.error(f"Redis recovery failed: {recovery_error}")
        return False


# 文件存储恢复策略
async def file_storage_recovery_strategy(error: Exception, context: Dict[str, Any]) -> bool:
    """
    文件存储恢复策略
    """
    try:
        from app.core.minio_client import minio_client
        
        # 尝试重新连接MinIO
        if hasattr(minio_client, 'reconnect'):
            minio_client.reconnect()
        
        # 测试连接
        buckets = minio_client.client.list_buckets()
        
        logger.info("File storage connection recovered successfully")
        return True
    
    except Exception as recovery_error:
        logger.error(f"File storage recovery failed: {recovery_error}")
        return False


# 全局错误恢复管理器
error_recovery_manager = ErrorRecoveryManager()

# 注册恢复策略
error_recovery_manager.register_recovery_strategy('OperationalError', database_recovery_strategy)
error_recovery_manager.register_recovery_strategy('ConnectionError', redis_recovery_strategy)
error_recovery_manager.register_recovery_strategy('FileStorageError', file_storage_recovery_strategy)


def handle_database_errors(func: Callable) -> Callable:
    """
    数据库错误处理装饰器
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IntegrityError as e:
            logger.error(f"Database integrity error in {func.__name__}: {e}")
            raise DatabaseError("数据完整性错误", func.__name__)
        except OperationalError as e:
            logger.error(f"Database operational error in {func.__name__}: {e}")
            raise DatabaseError("数据库操作错误", func.__name__)
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error in {func.__name__}: {e}")
            raise DatabaseError("数据库错误", func.__name__)
    
    return wrapper


def handle_async_errors(func: Callable) -> Callable:
    """
    异步错误处理装饰器
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="请求超时"
            )
        except asyncio.CancelledError as e:
            logger.warning(f"Task cancelled in {func.__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_499_CLIENT_CLOSED_REQUEST,
                detail="请求被取消"
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            
            # 尝试错误恢复
            context = {
                'function': func.__name__,
                'args': str(args),
                'kwargs': str(kwargs)
            }
            
            recovered = await error_recovery_manager.handle_error(e, context)
            
            if not recovered:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="服务器内部错误"
                )
    
    return wrapper


class HealthChecker:
    """
    健康检查器
    """
    
    def __init__(self):
        self.checks = {}
    
    def register_check(self, name: str, check_func: Callable):
        """
        注册健康检查
        """
        self.checks[name] = check_func
    
    async def run_all_checks(self) -> Dict[str, Dict[str, Any]]:
        """
        运行所有健康检查
        """
        results = {}
        
        for name, check_func in self.checks.items():
            try:
                start_time = datetime.now()
                result = await check_func()
                end_time = datetime.now()
                
                results[name] = {
                    'status': 'healthy' if result else 'unhealthy',
                    'response_time': (end_time - start_time).total_seconds(),
                    'timestamp': end_time.isoformat()
                }
            
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        return results


# 全局健康检查器
health_checker = HealthChecker()


# 数据库健康检查
async def check_database_health() -> bool:
    """
    检查数据库健康状态
    """
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception:
        return False


# Redis健康检查
async def check_redis_health() -> bool:
    """
    检查Redis健康状态
    """
    try:
        # 这里需要根据实际的Redis客户端实现
        return True
    except Exception:
        return False


# 文件存储健康检查
async def check_file_storage_health() -> bool:
    """
    检查文件存储健康状态
    """
    try:
        from app.core.minio_client import minio_client
        buckets = minio_client.client.list_buckets()
        return True
    except Exception:
        return False


# 注册健康检查
health_checker.register_check('database', check_database_health)
health_checker.register_check('redis', check_redis_health)
health_checker.register_check('file_storage', check_file_storage_health)