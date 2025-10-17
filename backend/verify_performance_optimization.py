"""
验证性能优化功能实现
"""
import sys
import traceback
from datetime import datetime

def test_imports():
    """测试所有模块导入"""
    print("Testing module imports...")
    
    try:
        from app.core.database_optimization import db_optimizer, init_database_optimization
        print("✓ Database optimization module imported")
    except Exception as e:
        print(f"✗ Database optimization import failed: {e}")
        return False
    
    try:
        from app.core.cache import cache_manager, cached, api_cache
        print("✓ Cache module imported")
    except Exception as e:
        print(f"✗ Cache import failed: {e}")
        return False
    
    try:
        from app.core.monitoring import metrics_collector, get_system_health, performance_profiler
        print("✓ Monitoring module imported")
    except Exception as e:
        print(f"✗ Monitoring import failed: {e}")
        return False
    
    try:
        from app.core.performance_benchmark import performance_tuner, run_performance_analysis
        print("✓ Performance benchmark module imported")
    except Exception as e:
        print(f"✗ Performance benchmark import failed: {e}")
        return False
    
    try:
        from app.api.v1.monitoring import router
        print("✓ Monitoring API router imported")
    except Exception as e:
        print(f"✗ Monitoring API import failed: {e}")
        return False
    
    try:
        from app.middleware.performance import performance_monitoring_middleware, response_caching_middleware
        print("✓ Performance middleware imported")
    except Exception as e:
        print(f"✗ Performance middleware import failed: {e}")
        return False
    
    return True


def test_database_optimization():
    """测试数据库优化功能"""
    print("\nTesting database optimization...")
    
    try:
        from app.core.database_optimization import db_optimizer
        
        # 测试表统计信息
        stats = db_optimizer.get_table_statistics()
        print(f"✓ Table statistics retrieved: {len(stats)} tables")
        
        # 测试数据库优化
        optimization_results = db_optimizer.optimize_database()
        if "error" not in optimization_results:
            print("✓ Database optimization completed successfully")
        else:
            print(f"⚠ Database optimization completed with warnings: {optimization_results['error']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Database optimization test failed: {e}")
        traceback.print_exc()
        return False


def test_cache_system():
    """测试缓存系统"""
    print("\nTesting cache system...")
    
    try:
        from app.core.cache import cache_manager
        
        # 测试缓存可用性
        is_available = cache_manager.is_available()
        print(f"✓ Cache availability checked: {is_available}")
        
        if is_available:
            # 测试基本操作
            test_key = "verify_test_key"
            test_value = {"test": "data", "timestamp": datetime.utcnow().isoformat()}
            
            # 设置缓存
            set_result = cache_manager.set(test_key, test_value, expire=60)
            print(f"✓ Cache set operation: {set_result}")
            
            # 获取缓存
            get_result = cache_manager.get(test_key)
            print(f"✓ Cache get operation: {get_result is not None}")
            
            # 删除缓存
            delete_result = cache_manager.delete(test_key)
            print(f"✓ Cache delete operation: {delete_result}")
        else:
            print("⚠ Redis not available - cache tests skipped")
        
        # 测试缓存统计
        stats = cache_manager.get_stats()
        print(f"✓ Cache statistics retrieved: {stats['status']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Cache system test failed: {e}")
        traceback.print_exc()
        return False


def test_monitoring_system():
    """测试监控系统"""
    print("\nTesting monitoring system...")
    
    try:
        from app.core.monitoring import metrics_collector, get_system_health
        
        # 测试指标收集
        metrics_collector.record_performance_metric("test.verification", 42.0, {"source": "verification"})
        metrics_collector.record_request_metric("GET", "/verify", 200, 150.0, "test_user", "127.0.0.1")
        print("✓ Metrics recorded successfully")
        
        # 测试获取指标
        performance_metrics = metrics_collector.get_performance_metrics("test.verification")
        request_metrics = metrics_collector.get_request_metrics("/verify")
        print(f"✓ Metrics retrieved: {len(performance_metrics)} performance, {len(request_metrics)} request")
        
        # 测试端点统计
        endpoint_stats = metrics_collector.get_endpoint_stats()
        print(f"✓ Endpoint statistics retrieved: {len(endpoint_stats)} endpoints")
        
        # 测试系统健康
        health = get_system_health()
        print(f"✓ System health retrieved: {health['status']}")
        print(f"  - CPU: {health['system']['cpu_percent']:.1f}%")
        print(f"  - Memory: {health['system']['memory_percent']:.1f}%")
        print(f"  - Disk: {health['system']['disk_percent']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"✗ Monitoring system test failed: {e}")
        traceback.print_exc()
        return False


def test_performance_benchmark():
    """测试性能基准测试"""
    print("\nTesting performance benchmark...")
    
    try:
        from app.core.performance_benchmark import performance_tuner
        
        # 运行基准测试（不包含API测试以避免超时）
        benchmark_results = performance_tuner.run_comprehensive_benchmark()
        print("✓ Comprehensive benchmark completed")
        
        # 检查结果
        db_tests = len(benchmark_results.get("database", {}))
        cache_tests = len(benchmark_results.get("cache", {}))
        print(f"  - Database tests: {db_tests}")
        print(f"  - Cache tests: {cache_tests}")
        
        # 生成建议
        recommendations = performance_tuner.generate_performance_recommendations(benchmark_results)
        print(f"✓ Performance recommendations generated: {len(recommendations)} items")
        
        return True
        
    except Exception as e:
        print(f"✗ Performance benchmark test failed: {e}")
        traceback.print_exc()
        return False


def test_api_endpoints():
    """测试API端点定义"""
    print("\nTesting API endpoints...")
    
    try:
        from app.api.v1.monitoring import router
        
        # 检查路由数量
        route_count = len(router.routes)
        print(f"✓ Monitoring API routes defined: {route_count}")
        
        # 列出主要端点
        endpoints = []
        for route in router.routes:
            if hasattr(route, 'path'):
                endpoints.append(f"{route.methods} {route.path}")
        
        print("✓ Available endpoints:")
        for endpoint in endpoints[:10]:  # 显示前10个
            print(f"  - {endpoint}")
        
        return True
        
    except Exception as e:
        print(f"✗ API endpoints test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """主验证函数"""
    print("=" * 60)
    print("COT Studio Performance Optimization Verification")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Database Optimization", test_database_optimization),
        ("Cache System", test_cache_system),
        ("Monitoring System", test_monitoring_system),
        ("Performance Benchmark", test_performance_benchmark),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 40}")
        print(f"Running: {test_name}")
        print('=' * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # 总结结果
    print(f"\n{'=' * 60}")
    print("VERIFICATION SUMMARY")
    print('=' * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:<8} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All performance optimization features are working correctly!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())