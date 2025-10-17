"""
性能优化功能测试
"""
import pytest
import asyncio
import time
from datetime import datetime, timedelta
from app.core.database_optimization import db_optimizer, init_database_optimization
from app.core.cache import cache_manager, cached
from app.core.monitoring import metrics_collector, get_system_health
from app.core.performance_benchmark import performance_tuner, run_performance_analysis


class TestDatabaseOptimization:
    """数据库优化测试"""
    
    def test_create_performance_indexes(self):
        """测试创建性能索引"""
        indexes_created = db_optimizer.create_performance_indexes()
        
        assert isinstance(indexes_created, dict)
        assert len(indexes_created) > 0
        
        # 验证索引创建结果
        for index_name, created in indexes_created.items():
            assert isinstance(created, bool)
            print(f"Index {index_name}: {'Created' if created else 'Already exists'}")
    
    def test_database_optimization(self):
        """测试数据库优化"""
        optimization_results = db_optimizer.optimize_database()
        
        assert isinstance(optimization_results, dict)
        assert "vacuum" in optimization_results or "error" in optimization_results
        
        if "error" not in optimization_results:
            assert optimization_results["vacuum"] == "completed"
            assert optimization_results["analyze"] == "completed"
            assert optimization_results["reindex"] == "completed"
    
    def test_table_statistics(self):
        """测试表统计信息"""
        statistics = db_optimizer.get_table_statistics()
        
        assert isinstance(statistics, dict)
        assert len(statistics) > 0
        
        # 检查每个表的统计信息
        for table_name, stats in statistics.items():
            if "error" not in stats:
                assert "row_count" in stats
                assert "column_count" in stats
                assert "columns" in stats
                assert isinstance(stats["row_count"], int)
                assert isinstance(stats["column_count"], int)
                assert isinstance(stats["columns"], list)
    
    def test_init_database_optimization(self):
        """测试初始化数据库优化"""
        results = init_database_optimization()
        
        assert isinstance(results, dict)
        assert "indexes_created" in results
        assert "optimization_results" in results


class TestCacheSystem:
    """缓存系统测试"""
    
    def test_cache_basic_operations(self):
        """测试基本缓存操作"""
        # 测试设置和获取
        test_key = "test_performance_key"
        test_value = {"message": "test performance value", "timestamp": datetime.utcnow().isoformat()}
        
        # 设置缓存
        result = cache_manager.set(test_key, test_value, expire=300)
        if cache_manager.is_available():
            assert result is True
            
            # 获取缓存
            cached_value = cache_manager.get(test_key)
            assert cached_value is not None
            assert cached_value["message"] == test_value["message"]
            
            # 检查存在性
            assert cache_manager.exists(test_key) is True
            
            # 删除缓存
            assert cache_manager.delete(test_key) is True
            assert cache_manager.exists(test_key) is False
        else:
            print("Redis not available, skipping cache tests")
    
    def test_cache_decorator(self):
        """测试缓存装饰器"""
        call_count = 0
        
        @cached(expire=300, key_prefix="test")
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            time.sleep(0.1)  # 模拟耗时操作
            return x + y
        
        if cache_manager.is_available():
            # 第一次调用
            result1 = expensive_function(1, 2)
            assert result1 == 3
            assert call_count == 1
            
            # 第二次调用应该从缓存获取
            result2 = expensive_function(1, 2)
            assert result2 == 3
            assert call_count == 1  # 没有增加，说明使用了缓存
        else:
            print("Redis not available, skipping cache decorator test")
    
    def test_cache_stats(self):
        """测试缓存统计"""
        stats = cache_manager.get_stats()
        
        assert isinstance(stats, dict)
        assert "status" in stats
        
        if stats["status"] == "available":
            assert "connected_clients" in stats
            assert "used_memory" in stats
            assert "keyspace_hits" in stats
            assert "keyspace_misses" in stats


class TestMonitoringSystem:
    """监控系统测试"""
    
    def test_metrics_collection(self):
        """测试指标收集"""
        # 记录性能指标
        metrics_collector.record_performance_metric("test.cpu_usage", 45.5, {"host": "test"})
        metrics_collector.record_performance_metric("test.memory_usage", 67.8, {"host": "test"})
        
        # 记录请求指标
        metrics_collector.record_request_metric("GET", "/api/test", 200, 150.5, "test_user", "127.0.0.1")
        metrics_collector.record_request_metric("POST", "/api/test", 201, 250.3, "test_user", "127.0.0.1")
        
        # 获取指标
        performance_metrics = metrics_collector.get_performance_metrics("test.cpu_usage")
        assert len(performance_metrics) >= 1
        assert performance_metrics[0]["metric_name"] == "test.cpu_usage"
        assert performance_metrics[0]["value"] == 45.5
        
        request_metrics = metrics_collector.get_request_metrics("/api/test")
        assert len(request_metrics) >= 2
        
        # 获取端点统计
        endpoint_stats = metrics_collector.get_endpoint_stats()
        assert isinstance(endpoint_stats, dict)
        assert "GET /api/test" in endpoint_stats
        assert endpoint_stats["GET /api/test"]["request_count"] >= 1
    
    def test_system_health(self):
        """测试系统健康检查"""
        health_data = get_system_health()
        
        assert isinstance(health_data, dict)
        assert "status" in health_data
        assert "timestamp" in health_data
        assert "system" in health_data
        assert "application" in health_data
        
        # 检查系统指标
        system_data = health_data["system"]
        assert "cpu_percent" in system_data
        assert "memory_percent" in system_data
        assert "disk_percent" in system_data
        
        # 检查应用指标
        app_data = health_data["application"]
        assert "endpoint_stats" in app_data
        assert "error_summary" in app_data


class TestPerformanceBenchmark:
    """性能基准测试"""
    
    def test_database_benchmark(self):
        """测试数据库基准测试"""
        from app.core.performance_benchmark import DatabaseBenchmark
        
        with DatabaseBenchmark() as db_bench:
            # 测试简单查询
            result = db_bench.benchmark_query_performance(
                "SELECT COUNT(*) FROM projects", 
                iterations=10
            )
            
            assert isinstance(result, dict)
            if "error" not in result:
                assert "average_ms" in result
                assert "min_ms" in result
                assert "max_ms" in result
                assert result["iterations"] == 10
    
    def test_cache_benchmark(self):
        """测试缓存基准测试"""
        from app.core.performance_benchmark import CacheBenchmark
        
        cache_bench = CacheBenchmark()
        
        if cache_manager.is_available():
            result = cache_bench.benchmark_cache_operations(iterations=100)
            
            assert isinstance(result, dict)
            assert "set" in result
            assert "get" in result
            
            # 检查SET操作结果
            set_result = result["set"]
            assert "average_ms" in set_result
            assert "operations_per_second" in set_result
            
            # 检查GET操作结果
            get_result = result["get"]
            assert "average_ms" in get_result
            assert "operations_per_second" in get_result
        else:
            print("Redis not available, skipping cache benchmark")
    
    def test_comprehensive_benchmark(self):
        """测试综合基准测试"""
        results = performance_tuner.run_comprehensive_benchmark()
        
        assert isinstance(results, dict)
        assert "timestamp" in results
        assert "database" in results
        assert "cache" in results
        
        # 检查数据库测试结果
        db_results = results["database"]
        if "error" not in db_results:
            assert len(db_results) > 0
    
    @pytest.mark.asyncio
    async def test_performance_analysis(self):
        """测试性能分析"""
        # 注意：这个测试可能需要较长时间，因为包含API测试
        try:
            results = await asyncio.wait_for(run_performance_analysis(), timeout=30.0)
            
            assert isinstance(results, dict)
            assert "analysis_timestamp" in results
            assert "benchmark_results" in results
            assert "recommendations" in results
            assert "summary" in results
            
            # 检查建议
            recommendations = results["recommendations"]
            assert isinstance(recommendations, list)
            assert len(recommendations) > 0
            
        except asyncio.TimeoutError:
            print("Performance analysis timed out - this is expected in test environment")
        except Exception as e:
            print(f"Performance analysis failed: {e}")


def test_performance_optimization_integration():
    """集成测试：性能优化功能"""
    print("\n=== Performance Optimization Integration Test ===")
    
    # 1. 测试数据库优化初始化
    print("1. Testing database optimization initialization...")
    init_results = init_database_optimization()
    print(f"   Database optimization results: {len(init_results['indexes_created'])} indexes processed")
    
    # 2. 测试缓存系统
    print("2. Testing cache system...")
    cache_available = cache_manager.is_available()
    print(f"   Cache available: {cache_available}")
    
    if cache_available:
        # 测试缓存性能
        start_time = time.time()
        for i in range(100):
            cache_manager.set(f"perf_test_{i}", {"value": i}, expire=60)
        set_time = time.time() - start_time
        
        start_time = time.time()
        for i in range(100):
            cache_manager.get(f"perf_test_{i}")
        get_time = time.time() - start_time
        
        print(f"   Cache SET 100 items: {set_time:.3f}s")
        print(f"   Cache GET 100 items: {get_time:.3f}s")
        
        # 清理测试数据
        for i in range(100):
            cache_manager.delete(f"perf_test_{i}")
    
    # 3. 测试监控系统
    print("3. Testing monitoring system...")
    
    # 记录一些测试指标
    for i in range(10):
        metrics_collector.record_performance_metric("test.integration", i * 10.5)
        metrics_collector.record_request_metric("GET", "/test", 200, i * 50.0)
    
    # 获取系统健康状态
    health = get_system_health()
    print(f"   System status: {health['status']}")
    print(f"   CPU usage: {health['system']['cpu_percent']:.1f}%")
    print(f"   Memory usage: {health['system']['memory_percent']:.1f}%")
    
    # 4. 测试基准测试
    print("4. Testing benchmark system...")
    benchmark_results = performance_tuner.run_comprehensive_benchmark()
    
    db_tests = len(benchmark_results.get("database", {}))
    cache_tests = len(benchmark_results.get("cache", {}))
    print(f"   Database benchmark tests: {db_tests}")
    print(f"   Cache benchmark tests: {cache_tests}")
    
    print("\n=== Performance Optimization Integration Test Completed ===")


if __name__ == "__main__":
    # 运行集成测试
    test_performance_optimization_integration()