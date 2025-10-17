"""
COT Studio MVP 性能基准测试
执行系统性能测试并生成基准报告
"""
import time
import json
import statistics
import psutil
import asyncio
from typing import Dict, List, Any, Callable
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict

import pytest
from fastapi.testclient import TestClient

from app.main import app


@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    name: str
    value: float
    unit: str
    threshold: float
    passed: bool
    details: Dict[str, Any] = None


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    test_name: str
    duration: float
    metrics: List[PerformanceMetric]
    resource_usage: Dict[str, float]
    passed: bool
    error: str = None


class PerformanceBenchmark:
    """性能基准测试类"""
    
    def __init__(self):
        self.client = TestClient(app)
        self.results: List[BenchmarkResult] = []
        self.process = psutil.Process()
    
    def measure_resource_usage(self, func: Callable) -> Dict[str, Any]:
        """测量资源使用情况"""
        # 记录初始状态
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = self.process.cpu_percent()
        
        start_time = time.time()
        
        # 执行函数
        try:
            result = func()
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.time()
        
        # 记录最终状态
        final_memory = self.process.memory_info().rss / 1024 / 1024
        final_cpu = self.process.cpu_percent()
        
        return {
            "result": result,
            "success": success,
            "error": error,
            "duration": end_time - start_time,
            "memory_start_mb": initial_memory,
            "memory_end_mb": final_memory,
            "memory_delta_mb": final_memory - initial_memory,
            "cpu_start_percent": initial_cpu,
            "cpu_end_percent": final_cpu
        }
    
    def benchmark_api_response_times(self) -> BenchmarkResult:
        """API响应时间基准测试"""
        print("🚀 执行API响应时间基准测试...")
        
        # 测试不同API端点的响应时间
        endpoints = [
            ("GET", "/health", None),
            ("GET", "/api/v1/info", None),
            ("POST", "/api/v1/projects/", {"name": "Benchmark Test", "description": "Performance test"}),
        ]
        
        response_times = []
        metrics = []
        
        def test_endpoint(method: str, url: str, data: Dict = None):
            start = time.time()
            
            if method == "GET":
                response = self.client.get(url)
            elif method == "POST":
                response = self.client.post(url, json=data)
            
            duration = time.time() - start
            return duration, response.status_code
        
        # 执行多次测试获取统计数据
        for method, url, data in endpoints:
            endpoint_times = []
            
            for _ in range(10):  # 每个端点测试10次
                try:
                    duration, status_code = test_endpoint(method, url, data)
                    if status_code < 400:  # 只记录成功的请求
                        endpoint_times.append(duration)
                except Exception:
                    continue
            
            if endpoint_times:
                avg_time = statistics.mean(endpoint_times)
                p95_time = statistics.quantiles(endpoint_times, n=20)[18] if len(endpoint_times) >= 20 else max(endpoint_times)
                
                response_times.extend(endpoint_times)
                
                # 创建指标
                metrics.append(PerformanceMetric(
                    name=f"{method} {url} - Average Response Time",
                    value=avg_time,
                    unit="seconds",
                    threshold=2.0,  # 2秒阈值
                    passed=avg_time < 2.0,
                    details={"p95": p95_time, "samples": len(endpoint_times)}
                ))
        
        # 整体统计
        if response_times:
            overall_avg = statistics.mean(response_times)
            overall_p95 = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
            
            metrics.append(PerformanceMetric(
                name="Overall Average Response Time",
                value=overall_avg,
                unit="seconds", 
                threshold=1.0,
                passed=overall_avg < 1.0
            ))
            
            metrics.append(PerformanceMetric(
                name="Overall P95 Response Time",
                value=overall_p95,
                unit="seconds",
                threshold=2.0,
                passed=overall_p95 < 2.0
            ))
        
        # 资源使用情况
        resource_usage = {
            "memory_mb": self.process.memory_info().rss / 1024 / 1024,
            "cpu_percent": self.process.cpu_percent()
        }
        
        all_passed = all(m.passed for m in metrics)
        
        return BenchmarkResult(
            test_name="API Response Times",
            duration=sum(response_times) if response_times else 0,
            metrics=metrics,
            resource_usage=resource_usage,
            passed=all_passed
        )
    
    def benchmark_concurrent_requests(self) -> BenchmarkResult:
        """并发请求基准测试"""
        print("🔄 执行并发请求基准测试...")
        
        def make_request():
            """单个请求"""
            start = time.time()
            response = self.client.get("/health")
            duration = time.time() - start
            return duration, response.status_code
        
        # 测试不同并发级别
        concurrency_levels = [1, 5, 10]
        metrics = []
        
        for concurrency in concurrency_levels:
            print(f"  测试并发级别: {concurrency}")
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(make_request) for _ in range(concurrency * 2)]
                results = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            
            # 分析结果
            successful_requests = [r for r in results if r[1] < 400]
            if successful_requests:
                response_times = [r[0] for r in successful_requests]
                avg_response_time = statistics.mean(response_times)
                throughput = len(successful_requests) / total_time
                
                metrics.append(PerformanceMetric(
                    name=f"Concurrency {concurrency} - Average Response Time",
                    value=avg_response_time,
                    unit="seconds",
                    threshold=3.0,
                    passed=avg_response_time < 3.0
                ))
                
                metrics.append(PerformanceMetric(
                    name=f"Concurrency {concurrency} - Throughput",
                    value=throughput,
                    unit="requests/second",
                    threshold=1.0,
                    passed=throughput > 1.0
                ))
        
        resource_usage = {
            "memory_mb": self.process.memory_info().rss / 1024 / 1024,
            "cpu_percent": self.process.cpu_percent()
        }
        
        all_passed = all(m.passed for m in metrics)
        
        return BenchmarkResult(
            test_name="Concurrent Requests",
            duration=0,  # 总时间在各个测试中已计算
            metrics=metrics,
            resource_usage=resource_usage,
            passed=all_passed
        )
    
    def benchmark_memory_usage(self) -> BenchmarkResult:
        """内存使用基准测试"""
        print("💾 执行内存使用基准测试...")
        
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        
        # 执行一系列操作来测试内存使用
        operations = []
        
        # 创建多个项目
        for i in range(10):
            project_data = {
                "name": f"Memory Test Project {i}",
                "description": f"Memory benchmark test project {i}"
            }
            
            try:
                response = self.client.post("/api/v1/projects/", json=project_data)
                if response.status_code == 201:
                    operations.append("project_created")
            except Exception:
                operations.append("project_failed")
        
        # 查询项目列表多次
        for _ in range(20):
            try:
                response = self.client.get("/api/v1/projects/")
                if response.status_code == 200:
                    operations.append("list_success")
            except Exception:
                operations.append("list_failed")
        
        final_memory = self.process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        metrics = [
            PerformanceMetric(
                name="Memory Usage Increase",
                value=memory_increase,
                unit="MB",
                threshold=100.0,  # 不应增长超过100MB
                passed=memory_increase < 100.0,
                details={
                    "initial_mb": initial_memory,
                    "final_mb": final_memory,
                    "operations": len(operations)
                }
            ),
            PerformanceMetric(
                name="Memory per Operation",
                value=memory_increase / len(operations) if operations else 0,
                unit="MB/operation",
                threshold=5.0,
                passed=(memory_increase / len(operations) if operations else 0) < 5.0
            )
        ]
        
        resource_usage = {
            "memory_initial_mb": initial_memory,
            "memory_final_mb": final_memory,
            "memory_delta_mb": memory_increase,
            "operations_count": len(operations)
        }
        
        all_passed = all(m.passed for m in metrics)
        
        return BenchmarkResult(
            test_name="Memory Usage",
            duration=0,
            metrics=metrics,
            resource_usage=resource_usage,
            passed=all_passed
        )
    
    def benchmark_database_operations(self) -> BenchmarkResult:
        """数据库操作基准测试"""
        print("🗄️ 执行数据库操作基准测试...")
        
        metrics = []
        
        # 测试批量插入性能
        start_time = time.time()
        
        created_projects = []
        for i in range(50):  # 创建50个项目
            project_data = {
                "name": f"DB Benchmark Project {i}",
                "description": f"Database performance test {i}",
                "tags": [f"tag{i}", "benchmark"]
            }
            
            try:
                response = self.client.post("/api/v1/projects/", json=project_data)
                if response.status_code == 201:
                    created_projects.append(response.json()["id"])
            except Exception:
                continue
        
        insert_time = time.time() - start_time
        
        if created_projects:
            avg_insert_time = insert_time / len(created_projects)
            
            metrics.append(PerformanceMetric(
                name="Average Project Creation Time",
                value=avg_insert_time,
                unit="seconds",
                threshold=0.5,
                passed=avg_insert_time < 0.5,
                details={"total_created": len(created_projects)}
            ))
        
        # 测试批量查询性能
        start_time = time.time()
        
        successful_queries = 0
        for project_id in created_projects[:10]:  # 查询前10个项目
            try:
                response = self.client.get(f"/api/v1/projects/{project_id}")
                if response.status_code == 200:
                    successful_queries += 1
            except Exception:
                continue
        
        query_time = time.time() - start_time
        
        if successful_queries > 0:
            avg_query_time = query_time / successful_queries
            
            metrics.append(PerformanceMetric(
                name="Average Project Query Time",
                value=avg_query_time,
                unit="seconds",
                threshold=0.1,
                passed=avg_query_time < 0.1,
                details={"queries_executed": successful_queries}
            ))
        
        resource_usage = {
            "memory_mb": self.process.memory_info().rss / 1024 / 1024,
            "cpu_percent": self.process.cpu_percent()
        }
        
        all_passed = all(m.passed for m in metrics)
        
        return BenchmarkResult(
            test_name="Database Operations",
            duration=insert_time + query_time,
            metrics=metrics,
            resource_usage=resource_usage,
            passed=all_passed
        )
    
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """运行所有基准测试"""
        print("🎯 开始执行性能基准测试套件...")
        print("=" * 60)
        
        benchmarks = [
            self.benchmark_api_response_times,
            self.benchmark_concurrent_requests,
            self.benchmark_memory_usage,
            self.benchmark_database_operations
        ]
        
        start_time = time.time()
        
        for benchmark_func in benchmarks:
            try:
                result = benchmark_func()
                self.results.append(result)
                
                # 打印即时结果
                status = "✅ 通过" if result.passed else "❌ 失败"
                print(f"{result.test_name}: {status}")
                
                for metric in result.metrics:
                    metric_status = "✅" if metric.passed else "❌"
                    print(f"  {metric_status} {metric.name}: {metric.value:.3f} {metric.unit}")
                
                print()
                
            except Exception as e:
                error_result = BenchmarkResult(
                    test_name=benchmark_func.__name__,
                    duration=0,
                    metrics=[],
                    resource_usage={},
                    passed=False,
                    error=str(e)
                )
                self.results.append(error_result)
                print(f"❌ {benchmark_func.__name__}: 执行失败 - {e}")
        
        total_time = time.time() - start_time
        
        # 生成综合报告
        return self.generate_report(total_time)
    
    def generate_report(self, total_time: float) -> Dict[str, Any]:
        """生成性能基准报告"""
        all_passed = all(result.passed for result in self.results)
        
        # 统计指标
        total_metrics = sum(len(result.metrics) for result in self.results)
        passed_metrics = sum(
            len([m for m in result.metrics if m.passed]) 
            for result in self.results
        )
        
        # 性能等级评估
        pass_rate = passed_metrics / total_metrics if total_metrics > 0 else 0
        if pass_rate >= 0.9:
            performance_grade = "A"
        elif pass_rate >= 0.8:
            performance_grade = "B"
        elif pass_rate >= 0.7:
            performance_grade = "C"
        else:
            performance_grade = "D"
        
        report = {
            "summary": {
                "total_duration_seconds": total_time,
                "all_benchmarks_passed": all_passed,
                "performance_grade": performance_grade,
                "pass_rate": pass_rate,
                "total_metrics": total_metrics,
                "passed_metrics": passed_metrics,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "benchmarks": [asdict(result) for result in self.results],
            "system_info": {
                "memory_mb": self.process.memory_info().rss / 1024 / 1024,
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": self.process.cpu_percent()
            }
        }
        
        # 保存报告
        report_path = Path("test-results/benchmark-report.json")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report
    
    def print_summary(self, report: Dict[str, Any]):
        """打印基准测试摘要"""
        summary = report["summary"]
        
        print("=" * 60)
        print("📊 性能基准测试摘要")
        print("=" * 60)
        
        print(f"⏱️  总执行时间: {summary['total_duration_seconds']:.2f}秒")
        print(f"✅ 所有基准通过: {'是' if summary['all_benchmarks_passed'] else '否'}")
        print(f"📈 通过率: {summary['pass_rate']:.1%}")
        print(f"⭐ 性能等级: {summary['performance_grade']}")
        
        print(f"\n📋 基准测试结果:")
        for result in self.results:
            status = "✅ 通过" if result.passed else "❌ 失败"
            print(f"  {result.test_name}: {status}")
        
        print(f"\n💻 系统信息:")
        sys_info = report["system_info"]
        print(f"  内存使用: {sys_info['memory_mb']:.1f}MB")
        print(f"  CPU核心数: {sys_info['cpu_count']}")
        print(f"  CPU使用率: {sys_info['cpu_percent']:.1f}%")
        
        print("\n" + "=" * 60)
        
        if summary['all_benchmarks_passed']:
            print("🎉 所有性能基准测试通过！")
        else:
            print("⚠️  部分性能基准未达标，请检查详细报告。")
        
        print(f"📄 详细报告已保存到: test-results/benchmark-report.json")


def main():
    """主函数"""
    benchmark = PerformanceBenchmark()
    
    try:
        report = benchmark.run_all_benchmarks()
        benchmark.print_summary(report)
        
        return 0 if report["summary"]["all_benchmarks_passed"] else 1
        
    except Exception as e:
        print(f"❌ 基准测试执行失败: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())