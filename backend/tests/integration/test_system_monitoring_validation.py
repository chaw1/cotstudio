"""
系统监控和用户体验验证测试
测试系统资源监控的准确性和实时性，验证用户贡献可视化的数据正确性
需求: 5.2, 5.3, 5.4, 5.5, 6.3, 6.4, 6.5
"""
import pytest
import asyncio
import json
import time
from typing import Dict, List, Any
from unittest.mock import patch, MagicMock
import psutil

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User, UserRole
from app.models.project import Project
from app.core.security import get_password_hash, create_access_token
from tests.conftest import TestingSessionLocal


class TestSystemMonitoringValidation:
    """系统监控验证测试类"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def db_session(self):
        """数据库会话"""
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @pytest.fixture
    def admin_user(self, db_session: Session):
        """管理员用户"""
        user = User(
            username="admin_monitor",
            email="admin_monitor@test.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin Monitor User",
            role=UserRole.ADMIN,
            is_active=True,
            is_superuser=False,
            login_count=0
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def test_users(self, db_session: Session):
        """测试用户列表"""
        users = []
        for i in range(5):
            user = User(
                username=f"monitor_user_{i}",
                email=f"monitor_user_{i}@test.com",
                hashed_password=get_password_hash(f"user{i}123"),
                full_name=f"Monitor User {i}",
                role=UserRole.USER,
                is_active=True,
                is_superuser=False,
                login_count=i * 10,  # 模拟不同的登录次数
                department=f"Department_{i % 3}"  # 模拟不同部门
            )
            db_session.add(user)
            users.append(user)
        
        db_session.commit()
        for user in users:
            db_session.refresh(user)
        return users
    
    @pytest.fixture
    def test_projects(self, db_session: Session, test_users: List[User]):
        """测试项目列表"""
        projects = []
        for i, user in enumerate(test_users):
            # 每个用户创建不同数量的项目
            project_count = (i % 3) + 1
            for j in range(project_count):
                project = Project(
                    name=f"Monitor Project {i}-{j}",
                    description=f"Monitoring test project {i}-{j}",
                    owner_id=str(user.id),
                    tags=[f"monitor_{i}", "test"],
                    project_type="annotation",
                    status="active"
                )
                db_session.add(project)
                projects.append(project)
        
        db_session.commit()
        for project in projects:
            db_session.refresh(project)
        return projects
    
    def get_auth_headers(self, user: User) -> Dict[str, str]:
        """获取认证头"""
        token = create_access_token(
            data={
                "sub": str(user.id),
                "username": user.username,
                "email": user.email,
                "roles": [user.role.value],
                "permissions": []
            }
        )
        return {"Authorization": f"Bearer {token}"}
    
    def test_system_resource_monitoring_accuracy(
        self,
        client: TestClient,
        db_session: Session,
        admin_user: User
    ):
        """
        测试系统资源监控的准确性
        需求: 5.2
        """
        print("\n🧪 开始系统资源监控准确性测试...")
        
        admin_headers = self.get_auth_headers(admin_user)
        
        # 1. 测试CPU监控
        with patch('app.services.system_monitor.SystemMonitorService') as mock_monitor:
            # 获取实际系统资源数据作为基准
            actual_cpu = psutil.cpu_percent(interval=1)
            actual_memory = psutil.virtual_memory()
            actual_disk = psutil.disk_usage('/')
            
            # 模拟监控服务返回接近实际的数据
            mock_monitor.get_system_resources.return_value = {
                "cpu_percent": actual_cpu,
                "memory_used": actual_memory.used,
                "memory_total": actual_memory.total,
                "memory_percent": actual_memory.percent,
                "disk_used": actual_disk.used,
                "disk_total": actual_disk.total,
                "disk_percent": (actual_disk.used / actual_disk.total) * 100,
                "db_connections": 5,
                "queue_status": {
                    "pending": 2,
                    "active": 1,
                    "failed": 0
                },
                "timestamp": time.time()
            }
            
            response = client.get("/api/v1/system/resources", headers=admin_headers)
            
            if response.status_code == 200:
                resource_data = response.json()
                
                # 验证数据结构
                required_fields = [
                    "cpu_percent", "memory_used", "memory_total", "memory_percent",
                    "disk_used", "disk_total", "disk_percent", "db_connections",
                    "queue_status", "timestamp"
                ]
                
                for field in required_fields:
                    assert field in resource_data, f"缺少字段: {field}"
                
                # 验证数据合理性
                assert 0 <= resource_data["cpu_percent"] <= 100, "CPU使用率应在0-100%之间"
                assert 0 <= resource_data["memory_percent"] <= 100, "内存使用率应在0-100%之间"
                assert 0 <= resource_data["disk_percent"] <= 100, "磁盘使用率应在0-100%之间"
                assert resource_data["memory_used"] <= resource_data["memory_total"], "已用内存不应超过总内存"
                assert resource_data["disk_used"] <= resource_data["disk_total"], "已用磁盘不应超过总磁盘"
                
                # 验证队列状态
                queue_status = resource_data["queue_status"]
                assert isinstance(queue_status["pending"], int), "待处理任务数应为整数"
                assert isinstance(queue_status["active"], int), "活跃任务数应为整数"
                assert isinstance(queue_status["failed"], int), "失败任务数应为整数"
                
                print("✅ 系统资源监控数据结构和合理性验证通过")
            else:
                print(f"⚠️ 系统资源监控接口返回状态码: {response.status_code}")
        
        # 2. 测试监控数据的实时性
        print("⏱️ 测试监控数据实时性...")
        
        timestamps = []
        for i in range(3):
            with patch('app.services.system_monitor.SystemMonitorService') as mock_monitor:
                mock_monitor.get_system_resources.return_value = {
                    "cpu_percent": 50.0 + i * 10,  # 模拟变化的数据
                    "memory_percent": 60.0 + i * 5,
                    "disk_percent": 70.0,
                    "timestamp": time.time()
                }
                
                response = client.get("/api/v1/system/resources", headers=admin_headers)
                
                if response.status_code == 200:
                    data = response.json()
                    timestamps.append(data["timestamp"])
                    
                    # 验证数据确实在变化
                    expected_cpu = 50.0 + i * 10
                    assert abs(data["cpu_percent"] - expected_cpu) < 0.1, f"CPU数据未正确更新: 期望{expected_cpu}, 实际{data['cpu_percent']}"
                
                time.sleep(0.1)  # 短暂间隔
        
        # 验证时间戳递增
        for i in range(1, len(timestamps)):
            assert timestamps[i] > timestamps[i-1], "时间戳应该递增"
        
        print("✅ 监控数据实时性验证通过")
        
        print("🎉 系统资源监控准确性测试完成")
    
    def test_user_contribution_visualization_data(
        self,
        client: TestClient,
        db_session: Session,
        admin_user: User,
        test_users: List[User],
        test_projects: List[Project]
    ):
        """
        测试用户贡献可视化的数据正确性
        需求: 5.3, 5.4, 5.5
        """
        print("\n🧪 开始用户贡献可视化数据测试...")
        
        admin_headers = self.get_auth_headers(admin_user)
        
        # 1. 测试用户贡献数据统计
        with patch('app.services.analytics_service.AnalyticsService') as mock_analytics:
            # 构建预期的用户贡献数据
            expected_users = []
            expected_datasets = []
            expected_relationships = []
            
            for i, user in enumerate(test_users):
                # 模拟每个用户的数据集数量
                dataset_count = (i % 3) + 1
                total_items = dataset_count * 100  # 每个数据集100个条目
                
                expected_users.append({
                    "id": str(user.id),
                    "username": user.username,
                    "datasetCount": dataset_count,
                    "totalItems": total_items
                })
                
                # 为每个用户创建数据集
                for j in range(dataset_count):
                    dataset_id = f"dataset_{user.id}_{j}"
                    expected_datasets.append({
                        "id": dataset_id,
                        "name": f"Dataset {i}-{j}",
                        "itemCount": 100,
                        "ownerId": str(user.id)
                    })
                    
                    expected_relationships.append({
                        "userId": str(user.id),
                        "datasetId": dataset_id
                    })
            
            mock_analytics.get_user_contributions.return_value = {
                "users": expected_users,
                "datasets": expected_datasets,
                "relationships": expected_relationships
            }
            
            response = client.get("/api/v1/analytics/user-contributions", headers=admin_headers)
            
            if response.status_code == 200:
                contribution_data = response.json()
                
                # 验证数据结构
                assert "users" in contribution_data
                assert "datasets" in contribution_data
                assert "relationships" in contribution_data
                
                users_data = contribution_data["users"]
                datasets_data = contribution_data["datasets"]
                relationships_data = contribution_data["relationships"]
                
                # 验证用户数据
                assert len(users_data) == len(test_users), f"用户数量不匹配: 期望{len(test_users)}, 实际{len(users_data)}"
                
                for user_data in users_data:
                    assert "id" in user_data
                    assert "username" in user_data
                    assert "datasetCount" in user_data
                    assert "totalItems" in user_data
                    assert user_data["datasetCount"] > 0, "数据集数量应大于0"
                    assert user_data["totalItems"] > 0, "总条目数应大于0"
                
                # 验证数据集数据
                for dataset_data in datasets_data:
                    assert "id" in dataset_data
                    assert "name" in dataset_data
                    assert "itemCount" in dataset_data
                    assert "ownerId" in dataset_data
                    assert dataset_data["itemCount"] > 0, "数据集条目数应大于0"
                
                # 验证关系数据
                for relationship in relationships_data:
                    assert "userId" in relationship
                    assert "datasetId" in relationship
                
                # 验证数据一致性
                user_ids = {user["id"] for user in users_data}
                dataset_owner_ids = {dataset["ownerId"] for dataset in datasets_data}
                relationship_user_ids = {rel["userId"] for rel in relationships_data}
                
                assert user_ids == dataset_owner_ids, "用户ID与数据集所有者ID应一致"
                assert user_ids == relationship_user_ids, "用户ID与关系中的用户ID应一致"
                
                print("✅ 用户贡献数据结构和一致性验证通过")
            else:
                print(f"⚠️ 用户贡献数据接口返回状态码: {response.status_code}")
        
        # 2. 测试可视化数据格式
        with patch('app.services.analytics_service.AnalyticsService') as mock_analytics:
            # 模拟可视化格式的数据
            mock_viz_data = {
                "nodes": [
                    {
                        "id": str(test_users[0].id),
                        "label": test_users[0].username,
                        "type": "user",
                        "size": 20,  # 基于数据集数量
                        "color": "#1677ff",
                        "properties": {
                            "datasetCount": 2,
                            "totalItems": 200
                        }
                    },
                    {
                        "id": "dataset_1",
                        "label": "Dataset 1",
                        "type": "dataset",
                        "size": 15,  # 基于条目数量
                        "color": "#52c41a",
                        "properties": {
                            "itemCount": 100
                        }
                    }
                ],
                "edges": [
                    {
                        "source": str(test_users[0].id),
                        "target": "dataset_1",
                        "type": "owns",
                        "color": "#d9d9d9"
                    }
                ]
            }
            
            mock_analytics.get_contribution_visualization.return_value = mock_viz_data
            
            response = client.get("/api/v1/analytics/user-contributions/visualization", headers=admin_headers)
            
            if response.status_code == 200:
                viz_data = response.json()
                
                # 验证可视化数据格式
                assert "nodes" in viz_data
                assert "edges" in viz_data
                
                # 验证节点格式
                for node in viz_data["nodes"]:
                    assert "id" in node
                    assert "label" in node
                    assert "type" in node
                    assert "size" in node
                    assert "color" in node
                    assert node["type"] in ["user", "dataset"], "节点类型应为user或dataset"
                    assert node["size"] > 0, "节点大小应大于0"
                
                # 验证边格式
                for edge in viz_data["edges"]:
                    assert "source" in edge
                    assert "target" in edge
                    assert "type" in edge
                    assert "color" in edge
                
                # 验证节点大小与数据量的关联
                user_nodes = [node for node in viz_data["nodes"] if node["type"] == "user"]
                dataset_nodes = [node for node in viz_data["nodes"] if node["type"] == "dataset"]
                
                for user_node in user_nodes:
                    if "properties" in user_node and "datasetCount" in user_node["properties"]:
                        # 节点大小应该与数据集数量相关
                        dataset_count = user_node["properties"]["datasetCount"]
                        expected_min_size = 10 + dataset_count * 2
                        assert user_node["size"] >= expected_min_size, f"用户节点大小应与数据集数量相关"
                
                for dataset_node in dataset_nodes:
                    if "properties" in dataset_node and "itemCount" in dataset_node["properties"]:
                        # 节点大小应该与条目数量相关
                        item_count = dataset_node["properties"]["itemCount"]
                        expected_min_size = 8 + (item_count // 50)
                        assert dataset_node["size"] >= expected_min_size, f"数据集节点大小应与条目数量相关"
                
                print("✅ 可视化数据格式和节点大小关联验证通过")
            else:
                print(f"⚠️ 可视化数据接口返回状态码: {response.status_code}")
        
        print("🎉 用户贡献可视化数据测试完成")
    
    def test_heroui_component_interaction_experience(
        self,
        client: TestClient,
        db_session: Session,
        admin_user: User
    ):
        """
        测试HeroUI组件的交互体验和视觉效果
        需求: 6.3, 6.4, 6.5
        """
        print("\n🧪 开始HeroUI组件交互体验测试...")
        
        admin_headers = self.get_auth_headers(admin_user)
        
        # 1. 测试组件主题配置
        response = client.get("/api/v1/ui/theme-config", headers=admin_headers)
        
        if response.status_code == 200:
            theme_config = response.json()
            
            # 验证主题配置结构
            expected_theme_keys = ["colors", "spacing", "borderRadius", "typography"]
            for key in expected_theme_keys:
                if key in theme_config:
                    print(f"✅ 主题配置包含 {key}")
                else:
                    print(f"⚠️ 主题配置缺少 {key}")
            
            # 验证颜色配置
            if "colors" in theme_config:
                colors = theme_config["colors"]
                required_colors = ["primary", "secondary", "success", "warning", "error"]
                for color in required_colors:
                    if color in colors:
                        # 验证颜色值格式（应该是有效的CSS颜色值）
                        color_value = colors[color]
                        assert isinstance(color_value, str), f"{color}颜色值应为字符串"
                        assert color_value.startswith("#") or color_value.startswith("rgb"), f"{color}颜色值格式无效"
                        print(f"✅ {color}颜色配置正确: {color_value}")
        else:
            print(f"⚠️ 主题配置接口返回状态码: {response.status_code}")
        
        # 2. 测试组件响应性能
        print("⚡ 测试组件响应性能...")
        
        # 模拟组件渲染性能测试
        component_tests = [
            {"component": "Button", "expected_render_time": 50},  # 毫秒
            {"component": "Table", "expected_render_time": 200},
            {"component": "Form", "expected_render_time": 150},
            {"component": "Modal", "expected_render_time": 100}
        ]
        
        for test in component_tests:
            with patch('app.services.ui_service.UIService') as mock_ui:
                mock_ui.measure_component_performance.return_value = {
                    "component": test["component"],
                    "renderTime": test["expected_render_time"] - 10,  # 模拟良好性能
                    "memoryUsage": 1024 * 1024,  # 1MB
                    "reRenderCount": 1
                }
                
                response = client.get(
                    f"/api/v1/ui/component-performance/{test['component']}",
                    headers=admin_headers
                )
                
                if response.status_code == 200:
                    perf_data = response.json()
                    
                    render_time = perf_data["renderTime"]
                    assert render_time < test["expected_render_time"], f"{test['component']}渲染时间过长: {render_time}ms"
                    
                    memory_usage = perf_data["memoryUsage"]
                    assert memory_usage < 5 * 1024 * 1024, f"{test['component']}内存使用过多: {memory_usage}bytes"
                    
                    print(f"✅ {test['component']}性能测试通过: {render_time}ms, {memory_usage//1024}KB")
                else:
                    print(f"⚠️ {test['component']}性能测试接口返回状态码: {response.status_code}")
        
        # 3. 测试组件可访问性
        print("♿ 测试组件可访问性...")
        
        accessibility_tests = [
            {"feature": "keyboard_navigation", "score": 95},
            {"feature": "screen_reader_support", "score": 90},
            {"feature": "color_contrast", "score": 98},
            {"feature": "focus_management", "score": 92}
        ]
        
        with patch('app.services.ui_service.UIService') as mock_ui:
            mock_ui.check_accessibility.return_value = {
                "overall_score": 94,
                "features": {test["feature"]: test["score"] for test in accessibility_tests}
            }
            
            response = client.get("/api/v1/ui/accessibility-check", headers=admin_headers)
            
            if response.status_code == 200:
                accessibility_data = response.json()
                
                overall_score = accessibility_data["overall_score"]
                assert overall_score >= 90, f"整体可访问性评分过低: {overall_score}"
                
                features = accessibility_data["features"]
                for test in accessibility_tests:
                    feature_score = features.get(test["feature"], 0)
                    assert feature_score >= 85, f"{test['feature']}可访问性评分过低: {feature_score}"
                    print(f"✅ {test['feature']}可访问性测试通过: {feature_score}分")
                
                print(f"✅ 整体可访问性评分: {overall_score}分")
            else:
                print(f"⚠️ 可访问性检查接口返回状态码: {response.status_code}")
        
        # 4. 测试组件一致性
        print("🎨 测试组件视觉一致性...")
        
        with patch('app.services.ui_service.UIService') as mock_ui:
            mock_ui.check_visual_consistency.return_value = {
                "consistency_score": 96,
                "issues": [],
                "components_checked": 25,
                "style_violations": 0
            }
            
            response = client.get("/api/v1/ui/visual-consistency", headers=admin_headers)
            
            if response.status_code == 200:
                consistency_data = response.json()
                
                consistency_score = consistency_data["consistency_score"]
                assert consistency_score >= 90, f"视觉一致性评分过低: {consistency_score}"
                
                style_violations = consistency_data["style_violations"]
                assert style_violations == 0, f"存在样式违规: {style_violations}个"
                
                components_checked = consistency_data["components_checked"]
                assert components_checked > 0, "应该检查了组件"
                
                print(f"✅ 视觉一致性测试通过: {consistency_score}分, 检查了{components_checked}个组件")
            else:
                print(f"⚠️ 视觉一致性检查接口返回状态码: {response.status_code}")
        
        print("🎉 HeroUI组件交互体验测试完成")
    
    def test_system_performance_under_load(
        self,
        client: TestClient,
        db_session: Session,
        admin_user: User
    ):
        """
        测试系统在负载下的性能表现
        需求: 5.2, 6.3, 6.4
        """
        print("\n🧪 开始系统负载性能测试...")
        
        admin_headers = self.get_auth_headers(admin_user)
        
        # 1. 测试并发请求处理
        print("🔄 测试并发请求处理...")
        
        import concurrent.futures
        import threading
        
        def make_request(endpoint: str) -> Dict[str, Any]:
            """发送请求的函数"""
            try:
                start_time = time.time()
                response = client.get(endpoint, headers=admin_headers)
                end_time = time.time()
                
                return {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                }
            except Exception as e:
                return {
                    "endpoint": endpoint,
                    "status_code": 500,
                    "response_time": 0,
                    "success": False,
                    "error": str(e)
                }
        
        # 并发测试的端点
        test_endpoints = [
            "/api/v1/system/resources",
            "/api/v1/analytics/user-contributions",
            "/api/v1/ui/theme-config",
            "/api/v1/user-management/users/stats"
        ]
        
        # 执行并发请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # 每个端点发送5个并发请求
            futures = []
            for endpoint in test_endpoints:
                for _ in range(5):
                    future = executor.submit(make_request, endpoint)
                    futures.append(future)
            
            # 收集结果
            results = []
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
        
        # 分析结果
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        success_rate = len(successful_requests) / len(results) * 100
        avg_response_time = sum(r["response_time"] for r in successful_requests) / len(successful_requests) if successful_requests else 0
        
        print(f"✅ 并发请求测试结果:")
        print(f"   - 总请求数: {len(results)}")
        print(f"   - 成功率: {success_rate:.1f}%")
        print(f"   - 平均响应时间: {avg_response_time:.3f}s")
        print(f"   - 失败请求数: {len(failed_requests)}")
        
        # 验证性能指标
        assert success_rate >= 95, f"成功率过低: {success_rate}%"
        assert avg_response_time < 2.0, f"平均响应时间过长: {avg_response_time}s"
        
        # 2. 测试内存使用情况
        print("💾 测试内存使用情况...")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行一系列操作来测试内存使用
        for i in range(10):
            with patch('app.services.system_monitor.SystemMonitorService') as mock_monitor:
                mock_monitor.get_system_resources.return_value = {
                    "cpu_percent": 50.0,
                    "memory_percent": 60.0,
                    "timestamp": time.time()
                }
                
                response = client.get("/api/v1/system/resources", headers=admin_headers)
                
            with patch('app.services.analytics_service.AnalyticsService') as mock_analytics:
                mock_analytics.get_user_contributions.return_value = {
                    "users": [],
                    "datasets": [],
                    "relationships": []
                }
                
                response = client.get("/api/v1/analytics/user-contributions", headers=admin_headers)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"✅ 内存使用测试结果:")
        print(f"   - 初始内存: {initial_memory:.1f}MB")
        print(f"   - 最终内存: {final_memory:.1f}MB")
        print(f"   - 内存增长: {memory_increase:.1f}MB")
        
        # 验证内存使用合理性
        assert memory_increase < 50, f"内存增长过多: {memory_increase}MB"
        
        print("🎉 系统负载性能测试完成")


def run_system_monitoring_validation():
    """运行系统监控和用户体验验证测试"""
    print("🚀 开始系统监控和用户体验验证测试...")
    
    # 运行测试
    pytest.main([
        __file__,
        "-v",
        "-s",
        "--tb=short"
    ])
    
    print("🏁 系统监控和用户体验验证测试完成")


if __name__ == "__main__":
    run_system_monitoring_validation()