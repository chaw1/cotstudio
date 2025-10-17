"""
性能基准测试和调优
"""
import time
import asyncio
import statistics
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import httpx
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.core.cache import cache_manager
from app.core.monitoring import performance_profiler
from app.core.app_logging import logger


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time_seconds: float
    average_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    percentile_95_ms: float
    requests_per_second: float
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "total_time_seconds": self.total_time_seconds,
            "average_response_time_ms": self.average_response_time_ms,
            "min_response_time_ms": self.min_response_time_ms,
            "max_response_time_ms": self.max_response_time_ms,
            "percentile_95_ms": self.percentile_95_ms,
            "requests_per_second": self.requests_per_second,
            "success_rate": (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
            "error_count": len(self.errors),
            "timestamp": datetime.utcnow().isoformat()
        }


class DatabaseBenchmark:
    """数据库性能基准测试"""
    
    def __init__(self):
        self.session = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def benchmark_query_performance(self, query: str, params: Dict = None, iterations: int = 100) -> Dict[str, Any]:
        """基准测试查询性能"""
        response_times = []
        errors = []
        
        for i in range(iterations):
            start_time = time.time()
            try:
                result = self.session.execute(query, params or {})
                result.fetchall()  # 确保完全执行
                end_time = time.time()
                response_times.append((end_time - start_time) * 1000)  # 转换为毫秒
            except Exception as e:
                errors.append(str(e))
                end_time = time.time()
                response_times.append((end_time - start_time) * 1000)
        
        if response_times:
            return {
                "query": query,
                "iterations": iterations,
                "average_ms": statistics.mean(response_times),
                "min_ms": min(response_times),
                "max_ms": max(response_times),
                "median_ms": statistics.median(response_times),
                "percentile_95_ms": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times),
                "total_errors": len(errors),
                "errors": errors[:5]  # 只返回前5个错误
            }
        else:
            return {"error": "No successful queries"}
    
    def benchmark_crud_operations(self, iterations: int = 50) -> Dict[str, Any]:
        """基准测试CRUD操作性能"""
        results = {}
        
        # 测试插入性能
        insert_times = []
        for i in range(iterations):
            start_time = time.time()
            try:
                # 创建测试项目
                self.session.execute(
                    "INSERT INTO projects (id, name, owner_id, description, tags, project_type, status) "
                    "VALUES (:id, :name, :owner_id, :description, :tags, :project_type, :status)",
                    {
                        "id": f"bench_project_{i}",
                        "name": f"Benchmark Project {i}",
                        "owner_id": "benchmark_user",
                        "description": "Benchmark test project",
                        "tags": '["benchmark", "test"]',
                        "project_type": "standard",
                        "status": "active"
                    }
                )
                self.session.commit()
                end_time = time.time()
                insert_times.append((end_time - start_time) * 1000)
            except Exception as e:
                logger.error(f"Insert benchmark error: {e}")
        
        results["insert"] = {
            "average_ms": statistics.mean(insert_times) if insert_times else 0,
            "min_ms": min(insert_times) if insert_times else 0,
            "max_ms": max(insert_times) if insert_times else 0
        }
        
        # 测试查询性能
        select_times = []
        for i in range(iterations):
            start_time = time.time()
            try:
                result = self.session.execute(
                    "SELECT * FROM projects WHERE name LIKE :pattern",
                    {"pattern": f"Benchmark Project%"}
                )
                result.fetchall()
                end_time = time.time()
                select_times.append((end_time - start_time) * 1000)
            except Exception as e:
                logger.error(f"Select benchmark error: {e}")
        
        results["select"] = {
            "average_ms": statistics.mean(select_times) if select_times else 0,
            "min_ms": min(select_times) if select_times else 0,
            "max_ms": max(select_times) if select_times else 0
        }
        
        # 清理测试数据
        try:
            self.session.execute("DELETE FROM projects WHERE name LIKE 'Benchmark Project%'")
            self.session.commit()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        
        return results


class CacheBenchmark:
    """缓存性能基准测试"""
    
    def benchmark_cache_operations(self, iterations: int = 1000) -> Dict[str, Any]:
        """基准测试缓存操作性能"""
        results = {}
        
        # 测试SET操作
        set_times = []
        for i in range(iterations):
            start_time = time.time()
            cache_manager.set(f"benchmark_key_{i}", f"benchmark_value_{i}", expire=300)
            end_time = time.time()
            set_times.append((end_time - start_time) * 1000)
        
        results["set"] = {
            "average_ms": statistics.mean(set_times),
            "min_ms": min(set_times),
            "max_ms": max(set_times),
            "operations_per_second": 1000 / statistics.mean(set_times) if statistics.mean(set_times) > 0 else 0
        }
        
        # 测试GET操作
        get_times = []
        for i in range(iterations):
            start_time = time.time()
            cache_manager.get(f"benchmark_key_{i}")
            end_time = time.time()
            get_times.append((end_time - start_time) * 1000)
        
        results["get"] = {
            "average_ms": statistics.mean(get_times),
            "min_ms": min(get_times),
            "max_ms": max(get_times),
            "operations_per_second": 1000 / statistics.mean(get_times) if statistics.mean(get_times) > 0 else 0
        }
        
        # 清理测试数据
        for i in range(iterations):
            cache_manager.delete(f"benchmark_key_{i}")
        
        return results


class APIBenchmark:
    """API性能基准测试"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def benchmark_endpoint(self, endpoint: str, method: str = "GET", 
                                data: Dict = None, concurrent_requests: int = 10, 
                                total_requests: int = 100) -> BenchmarkResult:
        """基准测试API端点"""
        url = f"{self.base_url}{endpoint}"
        response_times = []
        errors = []
        successful_requests = 0
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 创建信号量限制并发数
            semaphore = asyncio.Semaphore(concurrent_requests)
            
            async def make_request():
                async with semaphore:
                    request_start = time.time()
                    try:
                        if method.upper() == "GET":
                            response = await client.get(url)
                        elif method.upper() == "POST":
                            response = await client.post(url, json=data)
                        else:
                            raise ValueError(f"Unsupported method: {method}")
                        
                        request_end = time.time()
                        response_time_ms = (request_end - request_start) * 1000
                        response_times.append(response_time_ms)
                        
                        if response.status_code < 400:
                            return True
                        else:
                            errors.append(f"HTTP {response.status_code}: {response.text[:100]}")
                            return False
                            
                    except Exception as e:
                        request_end = time.time()
                        response_time_ms = (request_end - request_start) * 1000
                        response_times.append(response_time_ms)
                        errors.append(str(e))
                        return False
            
            # 执行所有请求
            tasks = [make_request() for _ in range(total_requests)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_requests = sum(1 for result in results if result is True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 计算统计信息
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            percentile_95 = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max_response_time
        else:
            avg_response_time = min_response_time = max_response_time = percentile_95 = 0
        
        return BenchmarkResult(
            test_name=f"{method} {endpoint}",
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=total_requests - successful_requests,
            total_time_seconds=total_time,
            average_response_time_ms=avg_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            percentile_95_ms=percentile_95,
            requests_per_second=total_requests / total_time if total_time > 0 else 0,
            errors=errors[:10]  # 只保留前10个错误
        )


class PerformanceTuner:
    """性能调优器"""
    
    def __init__(self):
        self.db_benchmark = DatabaseBenchmark()
        self.cache_benchmark = CacheBenchmark()
        self.api_benchmark = APIBenchmark()
    
    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """运行综合性能基准测试"""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": {},
            "cache": {},
            "api": {}
        }
        
        # 数据库基准测试
        try:
            with DatabaseBenchmark() as db_bench:
                # 测试常用查询
                common_queries = [
                    ("SELECT COUNT(*) FROM projects", "project_count"),
                    ("SELECT * FROM projects WHERE status = 'active' LIMIT 10", "active_projects"),
                    ("SELECT * FROM files WHERE ocr_status = 'completed' LIMIT 10", "completed_files"),
                    ("SELECT * FROM cot_items WHERE status = 'approved' LIMIT 10", "approved_cot")
                ]
                
                for query, test_name in common_queries:
                    results["database"][test_name] = db_bench.benchmark_query_performance(query, iterations=50)
                
                # CRUD操作测试
                results["database"]["crud_operations"] = db_bench.benchmark_crud_operations(iterations=20)
                
        except Exception as e:
            logger.error(f"Database benchmark failed: {e}")
            results["database"]["error"] = str(e)
        
        # 缓存基准测试
        try:
            if cache_manager.is_available():
                results["cache"] = self.cache_benchmark.benchmark_cache_operations(iterations=500)
            else:
                results["cache"]["error"] = "Cache not available"
        except Exception as e:
            logger.error(f"Cache benchmark failed: {e}")
            results["cache"]["error"] = str(e)
        
        return results
    
    async def run_api_benchmark(self) -> Dict[str, Any]:
        """运行API基准测试"""
        results = {}
        
        # 测试关键API端点
        endpoints_to_test = [
            ("/", "GET"),
            ("/health", "GET"),
            ("/api/v1/projects", "GET"),
        ]
        
        for endpoint, method in endpoints_to_test:
            try:
                result = await self.api_benchmark.benchmark_endpoint(
                    endpoint, method, 
                    concurrent_requests=5, 
                    total_requests=50
                )
                results[f"{method}_{endpoint.replace('/', '_')}"] = result.to_dict()
            except Exception as e:
                logger.error(f"API benchmark failed for {endpoint}: {e}")
                results[f"{method}_{endpoint.replace('/', '_')}"] = {"error": str(e)}
        
        return results
    
    def generate_performance_recommendations(self, benchmark_results: Dict[str, Any]) -> List[str]:
        """生成性能优化建议"""
        recommendations = []
        
        # 数据库性能建议
        if "database" in benchmark_results:
            db_results = benchmark_results["database"]
            
            # 检查查询性能
            for test_name, result in db_results.items():
                if isinstance(result, dict) and "average_ms" in result:
                    if result["average_ms"] > 100:  # 超过100ms
                        recommendations.append(
                            f"数据库查询 '{test_name}' 平均响应时间 {result['average_ms']:.1f}ms，建议优化索引或查询语句"
                        )
        
        # 缓存性能建议
        if "cache" in benchmark_results:
            cache_results = benchmark_results["cache"]
            
            if "get" in cache_results and cache_results["get"]["average_ms"] > 10:
                recommendations.append(
                    f"缓存GET操作平均响应时间 {cache_results['get']['average_ms']:.1f}ms，建议检查Redis配置"
                )
        
        # API性能建议
        if "api" in benchmark_results:
            api_results = benchmark_results["api"]
            
            for endpoint, result in api_results.items():
                if isinstance(result, dict) and "average_response_time_ms" in result:
                    if result["average_response_time_ms"] > 1000:  # 超过1秒
                        recommendations.append(
                            f"API端点 '{endpoint}' 平均响应时间 {result['average_response_time_ms']:.1f}ms，建议优化业务逻辑或添加缓存"
                        )
                    
                    if result.get("success_rate", 100) < 95:  # 成功率低于95%
                        recommendations.append(
                            f"API端点 '{endpoint}' 成功率 {result['success_rate']:.1f}%，建议检查错误处理"
                        )
        
        if not recommendations:
            recommendations.append("系统性能表现良好，暂无优化建议")
        
        return recommendations


# 全局性能调优器实例
performance_tuner = PerformanceTuner()


async def run_performance_analysis() -> Dict[str, Any]:
    """运行性能分析"""
    logger.info("Starting performance analysis...")
    
    # 运行基准测试
    benchmark_results = performance_tuner.run_comprehensive_benchmark()
    
    # 运行API基准测试
    api_results = await performance_tuner.run_api_benchmark()
    benchmark_results["api"] = api_results
    
    # 生成优化建议
    recommendations = performance_tuner.generate_performance_recommendations(benchmark_results)
    
    analysis_result = {
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "benchmark_results": benchmark_results,
        "recommendations": recommendations,
        "summary": {
            "total_tests": len([k for k in benchmark_results.keys() if k != "timestamp"]),
            "database_tests": len(benchmark_results.get("database", {})),
            "cache_available": cache_manager.is_available(),
            "api_tests": len(benchmark_results.get("api", {}))
        }
    }
    
    logger.info("Performance analysis completed")
    return analysis_result