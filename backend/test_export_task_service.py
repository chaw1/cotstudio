#!/usr/bin/env python3
"""
测试导出任务服务
"""
import sys
import os
import asyncio
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.export_task_service import ExportTaskService
from app.schemas.export import ExportRequest, ExportFormat
from app.models import User, Project

async def test_export_task_service():
    """测试导出任务服务"""
    print("开始测试导出任务服务...")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        task_service = ExportTaskService(db)
        print("✓ 导出任务服务创建成功")
        
        # 检查是否有用户和项目数据
        user = db.query(User).first()
        project = db.query(Project).first()
        
        if not user or not project:
            print("⚠ 数据库中没有用户或项目数据，跳过测试")
            return
        
        print(f"✓ 找到测试用户: {user.username}")
        print(f"✓ 找到测试项目: {project.name}")
        
        # 创建导出请求
        export_request = ExportRequest(
            project_id=project.id,
            format=ExportFormat.JSON,
            include_metadata=True,
            include_files=False,
            include_kg_data=False
        )
        
        # 创建导出任务
        task_id = "test-task-123"
        export_task = await task_service.create_export_task(
            task_id=task_id,
            project_id=project.id,
            user_id=user.id,
            export_request=export_request,
            export_type="single"
        )
        
        print("✓ 导出任务创建成功")
        print(f"  - 任务ID: {export_task.task_id}")
        print(f"  - 状态: {export_task.status}")
        print(f"  - 进度: {export_task.progress}%")
        
        # 更新任务状态
        updated_task = await task_service.update_task_status(
            task_id=task_id,
            status="processing",
            progress=50.0,
            message="正在处理中..."
        )
        
        print("✓ 任务状态更新成功")
        print(f"  - 新状态: {updated_task.status}")
        print(f"  - 新进度: {updated_task.progress}%")
        print(f"  - 消息: {updated_task.message}")
        
        # 完成任务
        completed_task = await task_service.update_task_status(
            task_id=task_id,
            status="completed",
            progress=100.0,
            message="导出完成",
            file_path="/exports/test_file.json",
            file_size=1024,
            download_url="/api/v1/export/download/test_file.json",
            checksum="abc123",
            total_items=10
        )
        
        print("✓ 任务完成状态更新成功")
        print(f"  - 文件路径: {completed_task.file_path}")
        print(f"  - 文件大小: {completed_task.file_size} bytes")
        print(f"  - 下载链接: {completed_task.download_url}")
        
        # 获取任务
        retrieved_task = await task_service.get_task_by_id(task_id)
        print("✓ 任务检索成功")
        print(f"  - 检索到的任务状态: {retrieved_task.status}")
        
        # 获取用户任务列表
        user_tasks, total = await task_service.get_user_tasks(
            user_id=user.id,
            limit=10,
            offset=0
        )
        
        print(f"✓ 用户任务列表获取成功，共 {total} 个任务")
        for task in user_tasks:
            print(f"  - 任务 {task.task_id}: {task.status}")
        
        # 获取项目导出历史
        project_tasks, project_total = await task_service.get_project_export_history(
            project_id=project.id,
            user_id=user.id,
            limit=10,
            offset=0
        )
        
        print(f"✓ 项目导出历史获取成功，共 {project_total} 个任务")
        
        # 转换为响应对象
        response = task_service.task_to_response(completed_task)
        print("✓ 任务响应对象转换成功")
        print(f"  - 响应状态: {response.status}")
        print(f"  - 响应进度: {response.progress}")
        
        print("\n导出任务服务测试完成!")
        
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_export_task_service())