"""
监控和性能API端点
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.core.monitoring import (
    get_system_health, 
    metrics_collector, 
    performance_profiler,
    alert_manager
)
from app.core.database_optimization import (
    db_optimizer, 
    get_database_performance_stats,
    init_database_optimization
)
from app.core.cache import cache_manager, api_cache
from app.core.performance_benchmark import performance_tuner, run_performance_analysis
from app.core.app_logging import logger
from app.middleware.auth import get_current_user_optional

router = APIRouter()


@router.get("/health")
async def get_health_status():
    """获取系统健康状态"""
    try:
        health_data = get_system_health()
        return JSONResponse(content=health_data)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Health check failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/metrics/performance")
async def get_performance_metrics(
    metric_name: Optional[str] = Query(None, description="指标名称过滤"),
    hours: int = Query(1, description="获取过去N小时的数据", ge=1, le=24),
    current_user = Depends(get_current_user_optional)
):
    """获取性能指标"""
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        metrics = metrics_collector.get_performance_metrics(
            metric_name=metric_name,
            since=since
        )
        
        return {
            "metrics": metrics,
            "total_count": len(metrics),
            "time_range": {
                "since": since.isoformat(),
                "until": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/requests")
async def get_request_metrics(
    path: Optional[str] = Query(None, description="API路径过滤"),
    hours: int = Query(1, description="获取过去N小时的数据", ge=1, le=24),
    current_user = Depends(get_current_user_optional)
):
    """获取请求指标"""
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        metrics = metrics_collector.get_request_metrics(
            path=path,
            since=since
        )
        
        return {
            "metrics": metrics,
            "total_count": len(metrics),
            "time_range": {
                "since": since.isoformat(),
                "until": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Failed to get request metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/endpoints")
async def get_endpoint_statistics(current_user = Depends(get_current_user_optional)):
    """获取API端点统计"""
    try:
        endpoint_stats = metrics_collector.get_endpoint_stats()
        error_summary = metrics_collector.get_error_summary()
        
        return {
            "endpoint_statistics": endpoint_stats,
            "error_summary": error_summary,
            "total_endpoints": len(endpoint_stats),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get endpoint statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/stats")
async def get_database_statistics(current_user = Depends(get_current_user_optional)):
    """获取数据库统计信息"""
    try:
        stats = get_database_performance_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get database statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/database/optimize")
async def optimize_database(current_user = Depends(get_current_user_optional)):
    """执行数据库优化"""
    try:
        optimization_results = db_optimizer.optimize_database()
        return {
            "message": "Database optimization completed",
            "results": optimization_results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/database/create-indexes")
async def create_performance_indexes(current_user = Depends(get_current_user_optional)):
    """创建性能优化索引"""
    try:
        indexes_created = db_optimizer.create_performance_indexes()
        return {
            "message": "Performance indexes creation completed",
            "indexes_created": indexes_created,
            "total_new_indexes": sum(indexes_created.values()),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to create performance indexes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_statistics(current_user = Depends(get_current_user_optional)):
    """获取缓存统计信息"""
    try:
        cache_stats = cache_manager.get_stats()
        return {
            "cache_statistics": cache_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get cache statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache(
    pattern: Optional[str] = Query(None, description="清除匹配模式的缓存键"),
    current_user = Depends(get_current_user_optional)
):
    """清除缓存"""
    try:
        if pattern:
            cleared_count = cache_manager.clear_pattern(pattern)
            message = f"Cleared {cleared_count} cache keys matching pattern: {pattern}"
        else:
            # 清除所有缓存（谨慎操作）
            cleared_count = cache_manager.clear_pattern("*")
            message = f"Cleared all cache keys: {cleared_count}"
        
        return {
            "message": message,
            "cleared_count": cleared_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_active_alerts(current_user = Depends(get_current_user_optional)):
    """获取活动告警"""
    try:
        alerts = alert_manager.check_alerts()
        return {
            "alerts": alerts,
            "alert_count": len(alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/benchmark/run")
async def run_benchmark_tests(
    include_api: bool = Query(True, description="是否包含API基准测试"),
    current_user = Depends(get_current_user_optional)
):
    """运行性能基准测试"""
    try:
        logger.info("Starting performance benchmark tests...")
        
        if include_api:
            # 运行完整的性能分析（包括API测试）
            results = await run_performance_analysis()
        else:
            # 只运行数据库和缓存测试
            results = {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "benchmark_results": performance_tuner.run_comprehensive_benchmark(),
                "recommendations": [],
                "summary": {"note": "API tests skipped"}
            }
            
            # 生成建议
            results["recommendations"] = performance_tuner.generate_performance_recommendations(
                results["benchmark_results"]
            )
        
        logger.info("Performance benchmark tests completed")
        return results
        
    except Exception as e:
        logger.error(f"Benchmark tests failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmark/history")
async def get_benchmark_history(
    days: int = Query(7, description="获取过去N天的基准测试历史", ge=1, le=30),
    current_user = Depends(get_current_user_optional)
):
    """获取基准测试历史"""
    try:
        # 从缓存中获取历史数据
        history_key = f"benchmark_history:{days}d"
        cached_history = cache_manager.get(history_key)
        
        if cached_history:
            return cached_history
        
        # 如果没有缓存，返回空历史
        empty_history = {
            "history": [],
            "time_range": {
                "since": (datetime.utcnow() - timedelta(days=days)).isoformat(),
                "until": datetime.utcnow().isoformat()
            },
            "note": "Benchmark history not available in cache"
        }
        
        return empty_history
        
    except Exception as e:
        logger.error(f"Failed to get benchmark history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/init-optimization")
async def initialize_optimization(current_user = Depends(get_current_user_optional)):
    """初始化性能优化"""
    try:
        logger.info("Initializing performance optimization...")
        
        # 初始化数据库优化
        db_results = init_database_optimization()
        
        # 检查缓存状态
        cache_available = cache_manager.is_available()
        
        return {
            "message": "Performance optimization initialized",
            "database_optimization": db_results,
            "cache_available": cache_available,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance-report")
async def get_performance_report(current_user = Depends(get_current_user_optional)):
    """获取综合性能报告"""
    try:
        # 获取系统健康状态
        health_data = get_system_health()
        
        # 获取数据库统计
        db_stats = get_database_performance_stats()
        
        # 获取缓存统计
        cache_stats = cache_manager.get_stats()
        
        # 获取端点统计
        endpoint_stats = metrics_collector.get_endpoint_stats()
        
        # 获取告警
        alerts = alert_manager.check_alerts()
        
        report = {
            "report_timestamp": datetime.utcnow().isoformat(),
            "system_health": health_data,
            "database_performance": db_stats,
            "cache_performance": cache_stats,
            "api_performance": {
                "endpoint_count": len(endpoint_stats),
                "total_requests": sum(stats["request_count"] for stats in endpoint_stats.values()),
                "average_response_time": sum(stats["average_response_time_ms"] for stats in endpoint_stats.values()) / len(endpoint_stats) if endpoint_stats else 0,
                "total_errors": sum(stats["error_count"] for stats in endpoint_stats.values())
            },
            "alerts": alerts,
            "recommendations": []
        }
        
        # 生成性能建议
        if health_data["system"]["cpu_percent"] > 80:
            report["recommendations"].append("CPU使用率较高，建议检查系统负载")
        
        if health_data["system"]["memory_percent"] > 85:
            report["recommendations"].append("内存使用率较高，建议优化内存使用")
        
        if cache_stats.get("status") != "available":
            report["recommendations"].append("缓存服务不可用，建议检查Redis连接")
        
        if not report["recommendations"]:
            report["recommendations"].append("系统性能表现良好")
        
        return report
        
    except Exception as e:
        logger.error(f"Failed to generate performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))