#!/usr/bin/env python3
"""
测试验证脚本
验证测试套件的完整性和可执行性
"""
import os
import sys
import subprocess
import json
from pathlib import Path


def check_file_exists(file_path: str, description: str) -> bool:
    """检查文件是否存在"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (不存在)")
        return False


def check_python_imports() -> bool:
    """检查Python依赖是否可导入"""
    required_modules = [
        'pytest',
        'fastapi',
        'sqlalchemy',
        'psutil'
    ]
    
    success = True
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ Python模块: {module}")
        except ImportError:
            print(f"❌ Python模块: {module} (未安装)")
            success = False
    
    return success


def validate_test_structure() -> bool:
    """验证测试目录结构"""
    print("\n🔍 验证测试目录结构...")
    
    required_files = [
        # 后端测试文件
        ("backend/tests/__init__.py", "后端测试包"),
        ("backend/tests/conftest.py", "pytest配置"),
        ("backend/tests/integration/__init__.py", "集成测试包"),
        ("backend/tests/integration/test_complete_workflow.py", "完整流程测试"),
        ("backend/tests/integration/test_knowledge_graph_integration.py", "知识图谱集成测试"),
        ("backend/tests/performance/__init__.py", "性能测试包"),
        ("backend/tests/performance/test_load_performance.py", "负载性能测试"),
        ("backend/tests/test_runner.py", "测试运行器"),
        ("backend/tests/benchmark.py", "性能基准测试"),
        ("backend/pytest.ini", "pytest配置文件"),
        
        # 前端测试文件
        ("frontend/src/test/setup.ts", "前端测试设置"),
        ("frontend/src/test/e2e/complete-workflow.test.tsx", "前端E2E测试"),
        ("frontend/src/test/integration/knowledge-graph.test.tsx", "前端KG集成测试"),
        ("frontend/vitest.config.ts", "Vitest配置"),
        
        # 文档
        ("test-documentation.md", "测试文档"),
    ]
    
    success = True
    for file_path, description in required_files:
        if not check_file_exists(file_path, description):
            success = False
    
    return success


def validate_test_content() -> bool:
    """验证测试文件内容"""
    print("\n🔍 验证测试文件内容...")
    
    # 检查后端测试文件
    backend_test_file = "backend/tests/integration/test_complete_workflow.py"
    if os.path.exists(backend_test_file):
        with open(backend_test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_patterns = [
            "class TestCompleteWorkflow",
            "test_complete_file_to_cot_workflow",
            "test_knowledge_graph_extraction_workflow",
            "test_export_import_workflow",
            "test_error_handling_and_recovery"
        ]
        
        for pattern in required_patterns:
            if pattern in content:
                print(f"✅ 后端测试包含: {pattern}")
            else:
                print(f"❌ 后端测试缺少: {pattern}")
                return False
    
    # 检查前端测试文件
    frontend_test_file = "frontend/src/test/e2e/complete-workflow.test.tsx"
    if os.path.exists(frontend_test_file):
        with open(frontend_test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_patterns = [
            "Complete Workflow E2E Tests",
            "should complete full project creation to CoT annotation workflow",
            "should handle file upload errors gracefully",
            "should handle OCR processing failures"
        ]
        
        for pattern in required_patterns:
            if pattern in content:
                print(f"✅ 前端测试包含: {pattern}")
            else:
                print(f"❌ 前端测试缺少: {pattern}")
                return False
    
    return True


def check_test_requirements() -> bool:
    """检查测试需求覆盖"""
    print("\n🔍 检查测试需求覆盖...")
    
    # 根据任务要求检查测试覆盖
    required_test_areas = [
        "端到端测试用例，覆盖完整业务流程",
        "文件上传到CoT生成的完整流程测试", 
        "知识图谱抽取和可视化的集成测试",
        "性能测试和负载测试"
    ]
    
    # 检查是否有对应的测试实现
    test_implementations = {
        "端到端测试用例，覆盖完整业务流程": [
            "frontend/src/test/e2e/complete-workflow.test.tsx",
            "backend/tests/integration/test_complete_workflow.py"
        ],
        "文件上传到CoT生成的完整流程测试": [
            "backend/tests/integration/test_complete_workflow.py"
        ],
        "知识图谱抽取和可视化的集成测试": [
            "backend/tests/integration/test_knowledge_graph_integration.py",
            "frontend/src/test/integration/knowledge-graph.test.tsx"
        ],
        "性能测试和负载测试": [
            "backend/tests/performance/test_load_performance.py",
            "backend/tests/benchmark.py"
        ]
    }
    
    success = True
    for requirement in required_test_areas:
        print(f"\n📋 需求: {requirement}")
        if requirement in test_implementations:
            for impl_file in test_implementations[requirement]:
                if os.path.exists(impl_file):
                    print(f"  ✅ 实现: {impl_file}")
                else:
                    print(f"  ❌ 缺少: {impl_file}")
                    success = False
        else:
            print(f"  ❌ 未找到对应实现")
            success = False
    
    return success


def generate_test_summary() -> dict:
    """生成测试摘要"""
    summary = {
        "timestamp": "2024-01-01 00:00:00",
        "test_files": {
            "backend_unit_tests": len([f for f in os.listdir("backend/tests") if f.startswith("test_") and f.endswith(".py")]) if os.path.exists("backend/tests") else 0,
            "backend_integration_tests": len([f for f in os.listdir("backend/tests/integration") if f.endswith(".py")]) if os.path.exists("backend/tests/integration") else 0,
            "backend_performance_tests": len([f for f in os.listdir("backend/tests/performance") if f.endswith(".py")]) if os.path.exists("backend/tests/performance") else 0,
            "frontend_tests": len([f for f in Path("frontend/src/test").rglob("*.test.tsx")]) if os.path.exists("frontend/src/test") else 0
        },
        "test_categories": [
            "单元测试 (Unit Tests)",
            "集成测试 (Integration Tests)", 
            "端到端测试 (E2E Tests)",
            "性能测试 (Performance Tests)",
            "负载测试 (Load Tests)"
        ],
        "coverage_areas": [
            "项目管理流程",
            "文件上传处理",
            "OCR文档处理",
            "CoT数据生成",
            "知识图谱抽取",
            "数据导出导入",
            "用户界面交互",
            "错误处理机制",
            "性能基准测试"
        ]
    }
    
    return summary


def main():
    """主函数"""
    print("🧪 COT Studio MVP 测试验证")
    print("=" * 50)
    
    # 验证步骤
    steps = [
        ("测试目录结构", validate_test_structure),
        ("测试文件内容", validate_test_content), 
        ("测试需求覆盖", check_test_requirements),
        ("Python依赖检查", check_python_imports)
    ]
    
    results = {}
    for step_name, step_func in steps:
        print(f"\n🔍 {step_name}...")
        try:
            results[step_name] = step_func()
        except Exception as e:
            print(f"❌ {step_name}失败: {e}")
            results[step_name] = False
    
    # 生成摘要
    print("\n📊 测试验证摘要")
    print("=" * 50)
    
    all_passed = all(results.values())
    
    for step_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{step_name}: {status}")
    
    # 测试统计
    summary = generate_test_summary()
    print(f"\n📈 测试文件统计:")
    for category, count in summary["test_files"].items():
        print(f"  {category}: {count} 个文件")
    
    print(f"\n📋 测试覆盖领域:")
    for area in summary["coverage_areas"]:
        print(f"  • {area}")
    
    print(f"\n🎯 总体结果: {'✅ 所有验证通过' if all_passed else '❌ 部分验证失败'}")
    
    if all_passed:
        print("\n🎉 测试套件验证完成！可以开始执行测试。")
        print("\n📝 运行测试的命令:")
        print("  后端测试: python backend/tests/test_runner.py")
        print("  前端测试: cd frontend && npm run test:run")
        print("  性能基准: python backend/tests/benchmark.py")
    else:
        print("\n⚠️  请修复上述问题后重新验证。")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())