"""
综合测试运行器
执行所有测试套件并生成报告
"""
import pytest
import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, List, Any
import subprocess
import psutil


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.results = {
            "unit_tests": {},
            "integration_tests": {},
            "performance_tests": {},
            "coverage": {},
            "summary": {}
        }
        self.start_time = time.time()
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """运行单元测试"""
        print("🧪 运行单元测试...")
        
        # 运行单元测试
        result = pytest.main([
            "tests/",
            "--ignore=tests/integration/",
            "--ignore=tests/performance/",
            "-v",
            "--tb=short",
            "--cov=app",
            "--cov-report=json",
            "--cov-report=term-missing",
            "--junit-xml=test-results/unit-tests.xml"
        ])
        
        # 读取覆盖率报告
        coverage_data = {}
        try:
            with open("coverage.json", "r") as f:
                coverage_data = json.load(f)
        except FileNotFoundError:
            pass
        
        return {
            "exit_code": result,
            "coverage": coverage_data,
            "passed": result == 0
        }
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """运行集成测试"""
        print("🔗 运行集成测试...")
        
        # 确保测试数据库存在
        self._setup_test_database()
        
        result = pytest.main([
            "tests/integration/",
            "-v",
            "--tb=short",
            "--junit-xml=test-results/integration-tests.xml"
        ])
        
        return {
            "exit_code": result,
            "passed": result == 0
        }
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """运行性能测试"""
        print("⚡ 运行性能测试...")
        
        # 记录系统资源使用
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()
        
        result = pytest.main([
            "tests/performance/",
            "-v",
            "--tb=short",
            "-s",  # 显示print输出
            "--junit-xml=test-results/performance-tests.xml"
        ])
        
        final_memory = process.memory_info().rss / 1024 / 1024
        final_cpu = process.cpu_percent()
        
        return {
            "exit_code": result,
            "passed": result == 0,
            "resource_usage": {
                "memory_start_mb": initial_memory,
                "memory_end_mb": final_memory,
                "memory_delta_mb": final_memory - initial_memory,
                "cpu_start_percent": initial_cpu,
                "cpu_end_percent": final_cpu
            }
        }
    
    def run_frontend_tests(self) -> Dict[str, Any]:
        """运行前端测试"""
        print("🎨 运行前端测试...")
        
        # 切换到前端目录
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        
        try:
            # 运行前端测试
            result = subprocess.run([
                "npm", "run", "test", "--", "--run", "--reporter=json"
            ], 
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
            )
            
            # 解析测试结果
            test_output = {}
            if result.stdout:
                try:
                    test_output = json.loads(result.stdout)
                except json.JSONDecodeError:
                    test_output = {"raw_output": result.stdout}
            
            return {
                "exit_code": result.returncode,
                "passed": result.returncode == 0,
                "output": test_output,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "passed": False,
                "error": "Frontend tests timed out"
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "passed": False,
                "error": str(e)
            }
    
    def _setup_test_database(self):
        """设置测试数据库"""
        # 创建测试数据库目录
        os.makedirs("test-results", exist_ok=True)
        
        # 清理旧的测试数据库
        test_db_files = ["test.db", "test_integration.db"]
        for db_file in test_db_files:
            if os.path.exists(db_file):
                os.remove(db_file)
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total_time = time.time() - self.start_time
        
        # 统计测试结果
        all_passed = all([
            self.results["unit_tests"].get("passed", False),
            self.results["integration_tests"].get("passed", False),
            self.results["performance_tests"].get("passed", False),
            self.results["frontend_tests"].get("passed", False)
        ])
        
        summary = {
            "total_duration_seconds": total_time,
            "all_tests_passed": all_passed,
            "test_suites": {
                "unit_tests": self.results["unit_tests"].get("passed", False),
                "integration_tests": self.results["integration_tests"].get("passed", False),
                "performance_tests": self.results["performance_tests"].get("passed", False),
                "frontend_tests": self.results["frontend_tests"].get("passed", False)
            },
            "coverage": self.results["unit_tests"].get("coverage", {}),
            "performance_metrics": self.results["performance_tests"].get("resource_usage", {}),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 保存报告
        os.makedirs("test-results", exist_ok=True)
        with open("test-results/test-report.json", "w", encoding="utf-8") as f:
            json.dump({
                "summary": summary,
                "detailed_results": self.results
            }, f, indent=2, ensure_ascii=False)
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """打印测试摘要"""
        print("\n" + "="*60)
        print("📊 测试执行摘要")
        print("="*60)
        
        print(f"⏱️  总执行时间: {summary['total_duration_seconds']:.2f}秒")
        print(f"✅ 所有测试通过: {'是' if summary['all_tests_passed'] else '否'}")
        
        print("\n📋 测试套件结果:")
        for suite_name, passed in summary["test_suites"].items():
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"  {suite_name}: {status}")
        
        # 覆盖率信息
        coverage = summary.get("coverage", {})
        if coverage and "totals" in coverage:
            total_coverage = coverage["totals"].get("percent_covered", 0)
            print(f"\n📈 代码覆盖率: {total_coverage:.1f}%")
        
        # 性能指标
        perf_metrics = summary.get("performance_metrics", {})
        if perf_metrics:
            print(f"\n⚡ 性能指标:")
            print(f"  内存使用变化: {perf_metrics.get('memory_delta_mb', 0):.1f}MB")
        
        print("\n" + "="*60)
        
        if not summary['all_tests_passed']:
            print("❌ 部分测试失败，请检查详细日志")
            return 1
        else:
            print("🎉 所有测试通过！")
            return 0
    
    def run_all_tests(self) -> int:
        """运行所有测试"""
        print("🚀 开始执行完整测试套件...")
        
        # 运行各类测试
        self.results["unit_tests"] = self.run_unit_tests()
        self.results["integration_tests"] = self.run_integration_tests()
        self.results["performance_tests"] = self.run_performance_tests()
        self.results["frontend_tests"] = self.run_frontend_tests()
        
        # 生成报告
        summary = self.generate_report()
        
        # 打印摘要
        return self.print_summary(summary)


def main():
    """主函数"""
    runner = TestRunner()
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        
        if test_type == "unit":
            result = runner.run_unit_tests()
            return 0 if result["passed"] else 1
        elif test_type == "integration":
            result = runner.run_integration_tests()
            return 0 if result["passed"] else 1
        elif test_type == "performance":
            result = runner.run_performance_tests()
            return 0 if result["passed"] else 1
        elif test_type == "frontend":
            result = runner.run_frontend_tests()
            return 0 if result["passed"] else 1
        else:
            print(f"未知的测试类型: {test_type}")
            print("可用选项: unit, integration, performance, frontend")
            return 1
    
    # 运行所有测试
    return runner.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())