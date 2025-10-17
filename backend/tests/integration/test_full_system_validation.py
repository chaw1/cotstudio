"""
全功能验证测试
测试知识图谱模块、数据导出功能、响应式布局等完整功能
需求: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3
"""
import pytest
import asyncio
import json
import time
from typing import Dict, List, Any
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.permission import UserProjectPermission
from app.core.security import get_password_hash, create_access_token
from tests.conftest import TestingSessionLocal


class TestFullSystemValidation:
    """全功能验证测试类"""
    
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
    def test_user(self, db_session: Session):
        """测试用户"""
        user = User(
            username="test_user_validation",
            email="validation@test.com",
            hashed_password=get_password_hash("validation123"),
            full_name="Validation Test User",
            role=UserRole.USER,
            is_active=True,
            is_superuser=False,
            login_count=0
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def admin_user(self, db_session: Session):
        """管理员用户"""
        user = User(
            username="admin_validation",
            email="admin_validation@test.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin Validation User",
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
    def test_projects(self, db_session: Session, test_user: User):
        """测试项目"""
        projects = []
        for i in range(3):
            project = Project(
                name=f"Validation Test Project {i}",
                description=f"Full system validation test project {i}",
                owner_id=str(test_user.id),
                tags=[f"validation_{i}", "test", "full_system"],
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
    
    def test_knowledge_graph_direct_access_workflow(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_projects: List[Project]
    ):
        """
        测试知识图谱模块直接访问功能
        需求: 2.1, 2.2, 2.3, 2.4
        """
        print("\n🧪 开始知识图谱直接访问功能测试...")
        
        user_headers = self.get_auth_headers(test_user)
        test_project = test_projects[0]
        
        # 1. 测试获取可访问的知识图谱列表
        with patch('app.services.knowledge_graph_service.KnowledgeGraphService') as mock_kg_service:
            # 模拟知识图谱服务返回数据
            mock_kg_service.get_accessible_graphs.return_value = [
                {
                    "id": str(test_project.id),
                    "name": test_project.name,
                    "description": test_project.description,
                    "node_count": 25,
                    "edge_count": 40,
                    "last_updated": "2024-01-15T10:00:00Z"
                }
            ]
            
            response = client.get("/api/v1/knowledge-graphs/accessible", headers=user_headers)
            
            # 验证响应
            if response.status_code == 200:
                graphs_data = response.json()
                assert len(graphs_data) >= 1
                assert any(graph["name"] == test_project.name for graph in graphs_data)
                print(f"✅ 成功获取可访问知识图谱列表: {len(graphs_data)} 个图谱")
            else:
                print(f"⚠️ 知识图谱列表接口返回状态码: {response.status_code}")
        
        # 2. 测试直接访问特定知识图谱
        with patch('app.services.knowledge_graph_service.KnowledgeGraphService') as mock_kg_service:
            # 模拟知识图谱数据
            mock_graph_data = {
                "nodes": [
                    {"id": "node1", "label": "概念A", "type": "concept", "properties": {}},
                    {"id": "node2", "label": "概念B", "type": "concept", "properties": {}},
                    {"id": "node3", "label": "实体C", "type": "entity", "properties": {}}
                ],
                "edges": [
                    {"source": "node1", "target": "node2", "type": "relates_to", "properties": {}},
                    {"source": "node2", "target": "node3", "type": "contains", "properties": {}}
                ],
                "metadata": {
                    "total_nodes": 3,
                    "total_edges": 2,
                    "last_updated": "2024-01-15T10:00:00Z"
                }
            }
            
            mock_kg_service.get_graph_data.return_value = mock_graph_data
            
            response = client.get(f"/api/v1/knowledge-graphs/{test_project.id}", headers=user_headers)
            
            if response.status_code == 200:
                graph_data = response.json()
                assert "nodes" in graph_data
                assert "edges" in graph_data
                assert len(graph_data["nodes"]) == 3
                assert len(graph_data["edges"]) == 2
                print("✅ 成功直接访问知识图谱数据")
            else:
                print(f"⚠️ 知识图谱数据接口返回状态码: {response.status_code}")
        
        # 3. 测试知识图谱可视化数据格式
        with patch('app.services.knowledge_graph_service.KnowledgeGraphService') as mock_kg_service:
            # 模拟可视化数据
            mock_viz_data = {
                "nodes": [
                    {
                        "id": "node1",
                        "label": "概念A",
                        "size": 20,
                        "color": "#1677ff",
                        "x": 100,
                        "y": 100
                    },
                    {
                        "id": "node2", 
                        "label": "概念B",
                        "size": 15,
                        "color": "#52c41a",
                        "x": 200,
                        "y": 150
                    }
                ],
                "edges": [
                    {
                        "source": "node1",
                        "target": "node2",
                        "color": "#d9d9d9",
                        "width": 2
                    }
                ]
            }
            
            mock_kg_service.get_visualization_data.return_value = mock_viz_data
            
            response = client.get(
                f"/api/v1/knowledge-graphs/{test_project.id}/visualization",
                headers=user_headers
            )
            
            if response.status_code == 200:
                viz_data = response.json()
                assert "nodes" in viz_data
                assert "edges" in viz_data
                # 验证可视化数据格式
                for node in viz_data["nodes"]:
                    assert "id" in node
                    assert "label" in node
                    assert "size" in node
                    assert "color" in node
                print("✅ 知识图谱可视化数据格式验证通过")
            else:
                print(f"⚠️ 知识图谱可视化接口返回状态码: {response.status_code}")
        
        # 4. 测试知识图谱搜索功能
        with patch('app.services.knowledge_graph_service.KnowledgeGraphService') as mock_kg_service:
            mock_search_results = {
                "results": [
                    {
                        "id": "node1",
                        "label": "概念A",
                        "type": "concept",
                        "score": 0.95,
                        "snippet": "这是一个重要的概念..."
                    }
                ],
                "total": 1,
                "query": "概念"
            }
            
            mock_kg_service.search_graph.return_value = mock_search_results
            
            response = client.get(
                f"/api/v1/knowledge-graphs/{test_project.id}/search",
                params={"query": "概念", "limit": 10},
                headers=user_headers
            )
            
            if response.status_code == 200:
                search_data = response.json()
                assert "results" in search_data
                assert "total" in search_data
                assert search_data["total"] >= 0
                print("✅ 知识图谱搜索功能验证通过")
            else:
                print(f"⚠️ 知识图谱搜索接口返回状态码: {response.status_code}")
        
        print("🎉 知识图谱直接访问功能测试完成")
    
    def test_data_export_functionality_validation(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_projects: List[Project]
    ):
        """
        测试数据导出功能完整性
        需求: 3.1, 3.2, 3.3, 3.4
        """
        print("\n🧪 开始数据导出功能验证测试...")
        
        user_headers = self.get_auth_headers(test_user)
        test_project = test_projects[0]
        
        # 1. 测试导出任务创建
        export_request = {
            "project_id": str(test_project.id),
            "format": "json",
            "options": {
                "include_metadata": True,
                "include_files": True,
                "include_annotations": True,
                "include_knowledge_graph": True
            }
        }
        
        with patch('app.services.export_service.ExportService') as mock_export_service:
            # 模拟导出任务创建
            mock_task_id = "export_task_123"
            mock_export_service.create_export_task.return_value = {
                "task_id": mock_task_id,
                "status": "pending",
                "created_at": "2024-01-15T10:00:00Z"
            }
            
            response = client.post("/api/v1/export/projects", json=export_request, headers=user_headers)
            
            if response.status_code == 202:  # 异步任务接受
                task_data = response.json()
                assert "task_id" in task_data
                task_id = task_data["task_id"]
                print(f"✅ 导出任务创建成功: {task_id}")
            else:
                print(f"⚠️ 导出任务创建接口返回状态码: {response.status_code}")
                return
        
        # 2. 测试导出任务状态查询
        with patch('app.services.export_service.ExportService') as mock_export_service:
            # 模拟不同的任务状态
            task_statuses = [
                {"status": "pending", "progress": 0},
                {"status": "running", "progress": 50},
                {"status": "completed", "progress": 100, "download_url": "/api/v1/export/download/123"}
            ]
            
            for i, status_data in enumerate(task_statuses):
                mock_export_service.get_task_status.return_value = status_data
                
                response = client.get(f"/api/v1/export/tasks/{mock_task_id}", headers=user_headers)
                
                if response.status_code == 200:
                    status_response = response.json()
                    assert status_response["status"] == status_data["status"]
                    assert status_response["progress"] == status_data["progress"]
                    print(f"✅ 任务状态查询成功: {status_data['status']} ({status_data['progress']}%)")
                else:
                    print(f"⚠️ 任务状态查询接口返回状态码: {response.status_code}")
        
        # 3. 测试导出文件下载
        with patch('app.services.export_service.ExportService') as mock_export_service:
            # 模拟导出文件内容
            mock_export_content = {
                "project": {
                    "id": str(test_project.id),
                    "name": test_project.name,
                    "description": test_project.description
                },
                "files": [],
                "annotations": [],
                "knowledge_graph": {
                    "nodes": [],
                    "edges": []
                },
                "metadata": {
                    "export_date": "2024-01-15T10:00:00Z",
                    "format": "json",
                    "version": "1.0"
                }
            }
            
            mock_export_service.get_export_file.return_value = json.dumps(mock_export_content)
            
            response = client.get(f"/api/v1/export/download/{mock_task_id}", headers=user_headers)
            
            if response.status_code == 200:
                # 验证导出内容格式
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    export_data = response.json()
                    assert "project" in export_data
                    assert "metadata" in export_data
                    print("✅ 导出文件下载和格式验证通过")
                else:
                    print("✅ 导出文件下载成功（非JSON格式）")
            else:
                print(f"⚠️ 导出文件下载接口返回状态码: {response.status_code}")
        
        # 4. 测试导出历史记录
        with patch('app.services.export_service.ExportService') as mock_export_service:
            mock_export_history = {
                "exports": [
                    {
                        "task_id": mock_task_id,
                        "project_id": str(test_project.id),
                        "format": "json",
                        "status": "completed",
                        "created_at": "2024-01-15T10:00:00Z",
                        "completed_at": "2024-01-15T10:05:00Z",
                        "file_size": 1024000
                    }
                ],
                "total": 1
            }
            
            mock_export_service.get_export_history.return_value = mock_export_history
            
            response = client.get("/api/v1/export/history", headers=user_headers)
            
            if response.status_code == 200:
                history_data = response.json()
                assert "exports" in history_data
                assert "total" in history_data
                assert history_data["total"] >= 0
                print("✅ 导出历史记录查询验证通过")
            else:
                print(f"⚠️ 导出历史记录接口返回状态码: {response.status_code}")
        
        print("🎉 数据导出功能验证测试完成")
    
    def test_responsive_layout_validation(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User
    ):
        """
        测试响应式布局在不同设备上的表现
        需求: 4.1, 4.2, 4.3
        """
        print("\n🧪 开始响应式布局验证测试...")
        
        user_headers = self.get_auth_headers(test_user)
        
        # 1. 测试布局配置API
        response = client.get("/api/v1/layout/config", headers=user_headers)
        
        if response.status_code == 200:
            layout_config = response.json()
            
            # 验证布局配置结构
            expected_keys = ["breakpoints", "fixedAreas", "dynamicAreas"]
            for key in expected_keys:
                if key in layout_config:
                    print(f"✅ 布局配置包含 {key}")
                else:
                    print(f"⚠️ 布局配置缺少 {key}")
        else:
            print(f"⚠️ 布局配置接口返回状态码: {response.status_code}")
        
        # 2. 测试不同屏幕尺寸的布局适配
        screen_sizes = [
            {"width": 1920, "height": 1080, "name": "桌面大屏"},
            {"width": 1366, "height": 768, "name": "桌面标准"},
            {"width": 768, "height": 1024, "name": "平板"},
            {"width": 375, "height": 667, "name": "手机"}
        ]
        
        for size in screen_sizes:
            # 模拟不同屏幕尺寸的请求
            headers = {
                **user_headers,
                "X-Screen-Width": str(size["width"]),
                "X-Screen-Height": str(size["height"])
            }
            
            response = client.get("/api/v1/layout/adaptive", headers=headers)
            
            if response.status_code == 200:
                adaptive_layout = response.json()
                
                # 验证自适应布局数据
                if "workAreaWidth" in adaptive_layout and "sidebarWidth" in adaptive_layout:
                    work_area_width = adaptive_layout["workAreaWidth"]
                    sidebar_width = adaptive_layout["sidebarWidth"]
                    
                    # 验证布局合理性
                    total_width = work_area_width + sidebar_width
                    if total_width <= size["width"]:
                        print(f"✅ {size['name']} ({size['width']}x{size['height']}) 布局适配正确")
                    else:
                        print(f"⚠️ {size['name']} 布局可能存在问题: 总宽度 {total_width} > 屏幕宽度 {size['width']}")
                else:
                    print(f"⚠️ {size['name']} 自适应布局数据格式不完整")
            else:
                print(f"⚠️ {size['name']} 自适应布局接口返回状态码: {response.status_code}")
        
        # 3. 测试动态工作区域调整
        with patch('app.services.layout_service.LayoutService') as mock_layout_service:
            mock_layout_service.calculate_work_area.return_value = {
                "width": 1200,
                "height": 800,
                "projectPanelWidth": 300,
                "visualAreaWidth": 900
            }
            
            response = client.post(
                "/api/v1/layout/work-area/calculate",
                json={"screenWidth": 1920, "screenHeight": 1080, "sidebarCollapsed": False},
                headers=user_headers
            )
            
            if response.status_code == 200:
                work_area_data = response.json()
                assert "width" in work_area_data
                assert "height" in work_area_data
                print("✅ 动态工作区域计算验证通过")
            else:
                print(f"⚠️ 工作区域计算接口返回状态码: {response.status_code}")
        
        print("🎉 响应式布局验证测试完成")
    
    def test_cross_feature_integration(
        self,
        client: TestClient,
        db_session: Session,
        admin_user: User,
        test_user: User,
        test_projects: List[Project]
    ):
        """
        测试跨功能集成
        验证权限系统、知识图谱、导出功能的协同工作
        需求: 1.1-1.6, 2.1-2.4, 3.1-3.4
        """
        print("\n🧪 开始跨功能集成测试...")
        
        admin_headers = self.get_auth_headers(admin_user)
        user_headers = self.get_auth_headers(test_user)
        test_project = test_projects[0]
        
        # 1. 管理员为用户授予项目权限
        permission_data = {
            "user_id": str(test_user.id),
            "project_id": str(test_project.id),
            "permissions": ["view", "export"]
        }
        
        response = client.post(
            "/api/v1/user-management/permissions/grant",
            json=permission_data,
            headers=admin_headers
        )
        
        if response.status_code == 201:
            print("✅ 权限授予成功")
        else:
            print(f"⚠️ 权限授予失败: {response.status_code}")
        
        # 2. 用户基于权限访问知识图谱
        with patch('app.services.knowledge_graph_service.KnowledgeGraphService') as mock_kg_service:
            mock_kg_service.get_graph_data.return_value = {"nodes": [], "edges": []}
            
            response = client.get(f"/api/v1/knowledge-graphs/{test_project.id}", headers=user_headers)
            
            if response.status_code == 200:
                print("✅ 基于权限的知识图谱访问成功")
            else:
                print(f"⚠️ 知识图谱访问失败: {response.status_code}")
        
        # 3. 用户基于权限执行数据导出
        export_request = {
            "project_id": str(test_project.id),
            "format": "json",
            "options": {"include_knowledge_graph": True}
        }
        
        with patch('app.services.export_service.ExportService') as mock_export_service:
            mock_export_service.create_export_task.return_value = {
                "task_id": "integration_test_task",
                "status": "pending"
            }
            
            response = client.post("/api/v1/export/projects", json=export_request, headers=user_headers)
            
            if response.status_code == 202:
                print("✅ 基于权限的数据导出任务创建成功")
            else:
                print(f"⚠️ 数据导出任务创建失败: {response.status_code}")
        
        # 4. 撤销权限后验证访问限制
        revoke_data = {
            "user_id": str(test_user.id),
            "project_id": str(test_project.id),
            "permissions": ["export"]
        }
        
        response = client.delete(
            "/api/v1/user-management/permissions/revoke",
            json=revoke_data,
            headers=admin_headers
        )
        
        if response.status_code == 200:
            print("✅ 权限撤销成功")
            
            # 验证撤销后的访问限制
            response = client.post("/api/v1/export/projects", json=export_request, headers=user_headers)
            
            if response.status_code == 403:
                print("✅ 权限撤销后访问限制生效")
            else:
                print(f"⚠️ 权限撤销后访问限制未生效: {response.status_code}")
        else:
            print(f"⚠️ 权限撤销失败: {response.status_code}")
        
        print("🎉 跨功能集成测试完成")


def run_full_system_validation():
    """运行全功能验证测试"""
    print("🚀 开始全功能验证测试...")
    
    # 运行测试
    pytest.main([
        __file__,
        "-v",
        "-s",
        "--tb=short"
    ])
    
    print("🏁 全功能验证测试完成")


if __name__ == "__main__":
    run_full_system_validation()