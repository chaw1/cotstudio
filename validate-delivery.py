#!/usr/bin/env python3
"""
COT Studio MVP 交付验证脚本
验证交付包的完整性和功能
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any


class DeliveryValidator:
    """交付验证器"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        
    def validate_project_structure(self) -> bool:
        """验证项目结构"""
        print("🔍 验证项目结构...")
        
        required_files = [
            # 核心配置文件
            "docker-compose.yml",
            "docker-compose.prod.yml", 
            ".env.example",
            "Makefile",
            "README.md",
            
            # 后端文件
            "backend/requirements.txt",
            "backend/Dockerfile",
            "backend/app/main.py",
            "backend/alembic.ini",
            "backend/pytest.ini",
            
            # 前端文件
            "frontend/package.json",
            "frontend/Dockerfile",
            "frontend/vite.config.ts",
            "frontend/vitest.config.ts",
            
            # 文档文件
            "docs/README.md",
            "docs/deployment.md",
            "docs/development.md",
            "docs/user-guide.md",
            
            # 测试文件
            "test-documentation.md",
            "validate-tests.py",
            
            # 交付文件
            "DELIVERY_PACKAGE.md",
            "demo-data/sample-project.json",
            "demo-data/usage-examples.md"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
                print(f"  ❌ 缺少文件: {file_path}")
            else:
                print(f"  ✅ 文件存在: {file_path}")
        
        if missing_files:
            self.errors.extend(missing_files)
            return False
        
        return True
    
    def validate_backend_structure(self) -> bool:
        """验证后端结构"""
        print("\n🔍 验证后端结构...")
        
        backend_dirs = [
            "backend/app/api/v1",
            "backend/app/core",
            "backend/app/models", 
            "backend/app/schemas",
            "backend/app/services",
            "backend/app/utils",
            "backend/tests",
            "backend/tests/integration",
            "backend/tests/performance",
            "backend/alembic/versions"
        ]
        
        missing_dirs = []
        for dir_path in backend_dirs:
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_path)
                print(f"  ❌ 缺少目录: {dir_path}")
            else:
                print(f"  ✅ 目录存在: {dir_path}")
        
        # 检查关键API文件
        api_files = [
            "backend/app/api/v1/projects.py",
            "backend/app/api/v1/files.py",
            "backend/app/api/v1/cot_annotation.py",
            "backend/app/api/v1/knowledge_graph.py",
            "backend/app/api/v1/export.py"
        ]
        
        for file_path in api_files:
            if not os.path.exists(file_path):
                missing_dirs.append(file_path)
                print(f"  ❌ 缺少API文件: {file_path}")
            else:
                print(f"  ✅ API文件存在: {file_path}")
        
        if missing_dirs:
            self.errors.extend(missing_dirs)
            return False
        
        return True
    
    def validate_frontend_structure(self) -> bool:
        """验证前端结构"""
        print("\n🔍 验证前端结构...")
        
        frontend_dirs = [
            "frontend/src/components",
            "frontend/src/pages",
            "frontend/src/services",
            "frontend/src/stores",
            "frontend/src/types",
            "frontend/src/test",
            "frontend/src/test/e2e",
            "frontend/src/test/integration"
        ]
        
        missing_dirs = []
        for dir_path in frontend_dirs:
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_path)
                print(f"  ❌ 缺少目录: {dir_path}")
            else:
                print(f"  ✅ 目录存在: {dir_path}")
        
        # 检查关键组件文件
        component_files = [
            "frontend/src/components/project/ProjectList.tsx",
            "frontend/src/components/annotation/AnnotationWorkspace.tsx",
            "frontend/src/components/knowledge-graph/KnowledgeGraphViewer.tsx",
            "frontend/src/pages/Dashboard.tsx",
            "frontend/src/services/projectService.ts"
        ]
        
        for file_path in component_files:
            if not os.path.exists(file_path):
                missing_dirs.append(file_path)
                print(f"  ❌ 缺少组件文件: {file_path}")
            else:
                print(f"  ✅ 组件文件存在: {file_path}")
        
        if missing_dirs:
            self.errors.extend(missing_dirs)
            return False
        
        return True
    
    def validate_test_structure(self) -> bool:
        """验证测试结构"""
        print("\n🔍 验证测试结构...")
        
        test_files = [
            # 后端测试
            "backend/tests/__init__.py",
            "backend/tests/conftest.py",
            "backend/tests/test_runner.py",
            "backend/tests/benchmark.py",
            "backend/tests/integration/test_system_integration.py",
            "backend/tests/integration/test_complete_workflow.py",
            "backend/tests/integration/test_knowledge_graph_integration.py",
            "backend/tests/performance/test_load_performance.py",
            
            # 前端测试
            "frontend/src/test/setup.ts",
            "frontend/src/test/e2e/complete-workflow.test.tsx",
            "frontend/src/test/integration/knowledge-graph.test.tsx"
        ]
        
        missing_files = []
        for file_path in test_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
                print(f"  ❌ 缺少测试文件: {file_path}")
            else:
                print(f"  ✅ 测试文件存在: {file_path}")
        
        if missing_files:
            self.errors.extend(missing_files)
            return False
        
        return True
    
    def validate_docker_configuration(self) -> bool:
        """验证Docker配置"""
        print("\n🔍 验证Docker配置...")
        
        docker_files = [
            "docker-compose.yml",
            "docker-compose.prod.yml",
            "backend/Dockerfile",
            "frontend/Dockerfile"
        ]
        
        for file_path in docker_files:
            if not os.path.exists(file_path):
                print(f"  ❌ 缺少Docker文件: {file_path}")
                return False
            else:
                print(f"  ✅ Docker文件存在: {file_path}")
                
                # 检查文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if file_path == "docker-compose.yml":
                    required_services = ["backend", "frontend", "postgres", "neo4j", "redis", "minio"]
                    for service in required_services:
                        if service in content:
                            print(f"    ✅ 服务配置: {service}")
                        else:
                            print(f"    ❌ 缺少服务: {service}")
                            return False
        
        return True
    
    def validate_documentation(self) -> bool:
        """验证文档完整性"""
        print("\n🔍 验证文档完整性...")
        
        doc_files = [
            ("README.md", "项目说明"),
            ("DELIVERY_PACKAGE.md", "交付包文档"),
            ("docs/deployment.md", "部署文档"),
            ("docs/development.md", "开发文档"),
            ("docs/user-guide.md", "用户指南"),
            ("docs/api.md", "API文档"),
            ("test-documentation.md", "测试文档"),
            ("demo-data/usage-examples.md", "使用示例")
        ]
        
        for file_path, description in doc_files:
            if not os.path.exists(file_path):
                print(f"  ❌ 缺少文档: {description} ({file_path})")
                return False
            else:
                # 检查文件大小，确保不是空文件
                file_size = os.path.getsize(file_path)
                if file_size < 100:  # 小于100字节认为是空文件
                    print(f"  ⚠️  文档过小: {description} ({file_size} bytes)")
                else:
                    print(f"  ✅ 文档完整: {description} ({file_size} bytes)")
        
        return True
    
    def validate_demo_data(self) -> bool:
        """验证演示数据"""
        print("\n🔍 验证演示数据...")
        
        demo_file = "demo-data/sample-project.json"
        if not os.path.exists(demo_file):
            print(f"  ❌ 缺少演示数据: {demo_file}")
            return False
        
        try:
            with open(demo_file, 'r', encoding='utf-8') as f:
                demo_data = json.load(f)
            
            # 验证数据结构
            required_keys = ["project", "files", "slices", "cot_items", "knowledge_graph", "metadata"]
            for key in required_keys:
                if key in demo_data:
                    print(f"  ✅ 数据结构: {key}")
                else:
                    print(f"  ❌ 缺少数据: {key}")
                    return False
            
            # 验证数据内容
            if len(demo_data["files"]) >= 2:
                print(f"  ✅ 演示文件: {len(demo_data['files'])} 个")
            else:
                print(f"  ❌ 演示文件不足: {len(demo_data['files'])} 个")
                return False
            
            if len(demo_data["cot_items"]) >= 2:
                print(f"  ✅ CoT数据: {len(demo_data['cot_items'])} 个")
            else:
                print(f"  ❌ CoT数据不足: {len(demo_data['cot_items'])} 个")
                return False
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON格式错误: {e}")
            return False
        except Exception as e:
            print(f"  ❌ 数据验证失败: {e}")
            return False
    
    def validate_configuration_files(self) -> bool:
        """验证配置文件"""
        print("\n🔍 验证配置文件...")
        
        config_files = [
            ("backend/requirements.txt", "Python依赖"),
            ("frontend/package.json", "Node.js依赖"),
            ("backend/pytest.ini", "测试配置"),
            ("frontend/vitest.config.ts", "前端测试配置"),
            (".env.example", "环境变量示例")
        ]
        
        for file_path, description in config_files:
            if not os.path.exists(file_path):
                print(f"  ❌ 缺少配置: {description} ({file_path})")
                return False
            else:
                print(f"  ✅ 配置存在: {description}")
                
                # 检查关键配置内容
                if file_path == "backend/requirements.txt":
                    with open(file_path, 'r') as f:
                        content = f.read()
                        required_deps = ["fastapi", "sqlalchemy", "pytest", "celery"]
                        for dep in required_deps:
                            if dep in content:
                                print(f"    ✅ 依赖: {dep}")
                            else:
                                print(f"    ❌ 缺少依赖: {dep}")
                                return False
        
        return True
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        validation_steps = [
            ("项目结构", self.validate_project_structure),
            ("后端结构", self.validate_backend_structure),
            ("前端结构", self.validate_frontend_structure),
            ("测试结构", self.validate_test_structure),
            ("Docker配置", self.validate_docker_configuration),
            ("文档完整性", self.validate_documentation),
            ("演示数据", self.validate_demo_data),
            ("配置文件", self.validate_configuration_files)
        ]
        
        results = {}
        all_passed = True
        
        for step_name, step_func in validation_steps:
            try:
                result = step_func()
                results[step_name] = result
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ {step_name}验证失败: {e}")
                results[step_name] = False
                all_passed = False
        
        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "all_passed": all_passed,
            "results": results,
            "errors": self.errors,
            "summary": {
                "total_checks": len(validation_steps),
                "passed_checks": sum(1 for r in results.values() if r),
                "failed_checks": sum(1 for r in results.values() if not r)
            }
        }
    
    def print_summary(self, report: Dict[str, Any]):
        """打印验证摘要"""
        print("\n" + "="*60)
        print("📊 COT Studio MVP 交付验证摘要")
        print("="*60)
        
        summary = report["summary"]
        print(f"⏱️  验证时间: {report['timestamp']}")
        print(f"✅ 验证结果: {'通过' if report['all_passed'] else '失败'}")
        print(f"📋 检查项目: {summary['total_checks']}")
        print(f"✅ 通过项目: {summary['passed_checks']}")
        print(f"❌ 失败项目: {summary['failed_checks']}")
        
        print(f"\n📋 详细结果:")
        for check_name, passed in report["results"].items():
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"  {check_name}: {status}")
        
        if report["errors"]:
            print(f"\n❌ 发现的问题:")
            for error in report["errors"]:
                print(f"  • {error}")
        
        print("\n" + "="*60)
        
        if report["all_passed"]:
            print("🎉 COT Studio MVP 交付包验证通过！")
            print("📦 系统已准备就绪，可以进行部署。")
            print("\n📝 下一步操作:")
            print("  1. 运行 docker-compose up -d 启动系统")
            print("  2. 访问 http://localhost:3000 使用前端界面")
            print("  3. 查看 http://localhost:8000/docs 了解API")
            print("  4. 参考 demo-data/usage-examples.md 学习使用")
        else:
            print("⚠️  交付包验证失败，请修复上述问题。")
            print("📖 请参考 DELIVERY_PACKAGE.md 了解完整要求。")
        
        return 0 if report["all_passed"] else 1


def main():
    """主函数"""
    print("🚀 开始验证 COT Studio MVP 交付包...")
    print("="*60)
    
    validator = DeliveryValidator()
    report = validator.generate_validation_report()
    
    # 保存验证报告
    os.makedirs("test-results", exist_ok=True)
    with open("test-results/delivery-validation-report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return validator.print_summary(report)


if __name__ == "__main__":
    sys.exit(main())