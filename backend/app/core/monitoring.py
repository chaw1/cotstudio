"""
监控和日志收集系统
"""
import time
import psutil
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from contextlib import contextmanager
from app.core.app_logging import logger
from app.core.cache import cache_manager


@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    timestamp: datetime
    metric_name: str
    value: float
    tags: Dict[str, str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "metric_name": self.metric_name,
            "value": self.value,
            "tags": self.tags or {}
        }


@dataclass
class RequestMetric:
    """请求指标数据类"""
    timestamp: datetime
    method: str
    path: str
    status_code: int
    duration_ms: float
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "method": self.method,
            "path": self.path,
            "status_code": self.status_code,
            "duration_ms": self.duration_ms,
            "user_id": self.user_id,
            "ip_address": self.ip_address
        }


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.performance_metrics: deque = deque(maxlen=max_metrics)
        self.request_metrics: deque = deque(maxlen=max_metrics)
        self.error_counts = defaultdict(int)
        self.endpoint_stats = defaultdict(lambda: {"count": 0, "total_time": 0, "errors": 0})
        self._lock = threading.Lock()
        
        # 启动系统监控线程
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(target=self._system_monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def record_performance_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """记录性能指标"""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_name=metric_name,
            value=value,
            tags=tags
        )
        
        with self._lock:
            self.performance_metrics.append(metric)
        
        # 缓存最新指标
        cache_key = f"metric:{metric_name}:latest"
        cache_manager.set(cache_key, metric.to_dict(), expire=300)
    
    def record_request_metric(self, method: str, path: str, status_code: int, 
                            duration_ms: float, user_id: str = None, ip_address: str = None):
        """记录请求指标"""
        metric = RequestMetric(
            timestamp=datetime.utcnow(),
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            ip_address=ip_address
        )
        
        with self._lock:
            self.request_metrics.append(metric)
            
            # 更新端点统计
            endpoint_key = f"{method} {path}"
            self.endpoint_stats[endpoint_key]["count"] += 1
            self.endpoint_stats[endpoint_key]["total_time"] += duration_ms
            
            if status_code >= 400:
                self.endpoint_stats[endpoint_key]["errors"] += 1
                self.error_counts[status_code] += 1
    
    def get_performance_metrics(self, metric_name: str = None, 
                              since: datetime = None) -> List[Dict[str, Any]]:
        """获取性能指标"""
        with self._lock:
            metrics = list(self.performance_metrics)
        
        # 过滤条件
        if metric_name:
            metrics = [m for m in metrics if m.metric_name == metric_name]
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        return [m.to_dict() for m in metrics]
    
    def get_request_metrics(self, path: str = None, since: datetime = None) -> List[Dict[str, Any]]:
        """获取请求指标"""
        with self._lock:
            metrics = list(self.request_metrics)
        
        # 过滤条件
        if path:
            metrics = [m for m in metrics if m.path == path]
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        return [m.to_dict() for m in metrics]
    
    def get_endpoint_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取端点统计"""
        with self._lock:
            stats = {}
            for endpoint, data in self.endpoint_stats.items():
                avg_time = data["total_time"] / data["count"] if data["count"] > 0 else 0
                error_rate = data["errors"] / data["count"] if data["count"] > 0 else 0
                
                stats[endpoint] = {
                    "request_count": data["count"],
                    "average_response_time_ms": round(avg_time, 2),
                    "error_count": data["errors"],
                    "error_rate": round(error_rate * 100, 2)
                }
        
        return stats
    
    def get_error_summary(self) -> Dict[str, int]:
        """获取错误统计"""
        with self._lock:
            return dict(self.error_counts)
    
    def _system_monitor_loop(self):
        """系统监控循环"""
        while self._monitoring_active:
            try:
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                self.record_performance_metric("system.cpu_percent", cpu_percent)
                
                # 内存使用率
                memory = psutil.virtual_memory()
                self.record_performance_metric("system.memory_percent", memory.percent)
                self.record_performance_metric("system.memory_used_mb", memory.used / 1024 / 1024)
                
                # 磁盘使用率
                disk = psutil.disk_usage('/')
                self.record_performance_metric("system.disk_percent", disk.percent)
                
                # 网络IO
                net_io = psutil.net_io_counters()
                self.record_performance_metric("system.network_bytes_sent", net_io.bytes_sent)
                self.record_performance_metric("system.network_bytes_recv", net_io.bytes_recv)
                
                time.sleep(30)  # 每30秒收集一次系统指标
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                time.sleep(60)  # 出错时等待更长时间
    
    def stop_monitoring(self):
        """停止监控"""
        self._monitoring_active = False
        if self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)


class PerformanceProfiler:
    """性能分析器"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
    
    @contextmanager
    def profile_operation(self, operation_name: str, tags: Dict[str, str] = None):
        """性能分析上下文管理器"""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            duration_ms = (end_time - start_time) * 1000
            memory_delta = end_memory - start_memory
            
            # 记录性能指标
            self.metrics.record_performance_metric(
                f"operation.{operation_name}.duration_ms", 
                duration_ms, 
                tags
            )
            self.metrics.record_performance_metric(
                f"operation.{operation_name}.memory_delta_mb", 
                memory_delta, 
                tags
            )
    
    def profile_function(self, func_name: str = None, tags: Dict[str, str] = None):
        """函数性能分析装饰器"""
        def decorator(func):
            operation_name = func_name or f"{func.__module__}.{func.__name__}"
            
            def wrapper(*args, **kwargs):
                with self.profile_operation(operation_name, tags):
                    return func(*args, **kwargs)
            
            async def async_wrapper(*args, **kwargs):
                with self.profile_operation(operation_name, tags):
                    return await func(*args, **kwargs)
            
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return wrapper
        
        return decorator


class AlertManager:
    """告警管理器"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.alert_rules = {
            "high_cpu": {"threshold": 80, "duration": 300},  # CPU > 80% 持续5分钟
            "high_memory": {"threshold": 85, "duration": 300},  # 内存 > 85% 持续5分钟
            "high_error_rate": {"threshold": 5, "duration": 60},  # 错误率 > 5% 持续1分钟
            "slow_response": {"threshold": 5000, "duration": 60}  # 响应时间 > 5秒持续1分钟
        }
        self.active_alerts = {}
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """检查告警条件"""
        alerts = []
        now = datetime.utcnow()
        
        # 检查CPU告警
        cpu_metrics = self.metrics.get_performance_metrics(
            "system.cpu_percent", 
            since=now - timedelta(seconds=self.alert_rules["high_cpu"]["duration"])
        )
        if cpu_metrics:
            avg_cpu = sum(m["value"] for m in cpu_metrics) / len(cpu_metrics)
            if avg_cpu > self.alert_rules["high_cpu"]["threshold"]:
                alerts.append({
                    "type": "high_cpu",
                    "severity": "warning",
                    "message": f"High CPU usage: {avg_cpu:.1f}%",
                    "timestamp": now.isoformat()
                })
        
        # 检查内存告警
        memory_metrics = self.metrics.get_performance_metrics(
            "system.memory_percent",
            since=now - timedelta(seconds=self.alert_rules["high_memory"]["duration"])
        )
        if memory_metrics:
            avg_memory = sum(m["value"] for m in memory_metrics) / len(memory_metrics)
            if avg_memory > self.alert_rules["high_memory"]["threshold"]:
                alerts.append({
                    "type": "high_memory",
                    "severity": "warning",
                    "message": f"High memory usage: {avg_memory:.1f}%",
                    "timestamp": now.isoformat()
                })
        
        # 检查错误率告警
        endpoint_stats = self.metrics.get_endpoint_stats()
        for endpoint, stats in endpoint_stats.items():
            if stats["error_rate"] > self.alert_rules["high_error_rate"]["threshold"]:
                alerts.append({
                    "type": "high_error_rate",
                    "severity": "critical",
                    "message": f"High error rate for {endpoint}: {stats['error_rate']:.1f}%",
                    "timestamp": now.isoformat()
                })
        
        return alerts


# 全局监控实例
metrics_collector = MetricsCollector()
performance_profiler = PerformanceProfiler(metrics_collector)
alert_manager = AlertManager(metrics_collector)


def get_system_health() -> Dict[str, Any]:
    """获取系统健康状态"""
    try:
        # 系统资源
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 应用指标
        endpoint_stats = metrics_collector.get_endpoint_stats()
        error_summary = metrics_collector.get_error_summary()
        
        # 缓存状态
        cache_stats = cache_manager.get_stats()
        
        # 检查告警
        alerts = alert_manager.check_alerts()
        
        return {
            "status": "healthy" if not alerts else "warning",
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / 1024 / 1024 / 1024, 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
            },
            "application": {
                "endpoint_stats": endpoint_stats,
                "error_summary": error_summary,
                "total_requests": sum(stats["request_count"] for stats in endpoint_stats.values()),
                "total_errors": sum(error_summary.values())
            },
            "cache": cache_stats,
            "alerts": alerts
        }
        
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


def cleanup_monitoring():
    """清理监控资源"""
    metrics_collector.stop_monitoring()
    logger.info("Monitoring cleanup completed")