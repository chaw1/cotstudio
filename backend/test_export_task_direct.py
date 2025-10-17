#!/usr/bin/env python3
"""
直接测试导出任务功能
"""
import sys
import os
import asyncio
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.export_task import ExportTask
from app.schemas.export import ExportFormat

async def test_export_task_model():
    """测试导出任务模型"""
    print("开始测试导出任务模型...")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 创建测试任务
        test_task = ExportTask(
            task_id="test-task-456",
            project_id="test-project-123",
            user_id="test-user-123",
            export_format=ExportFormat.JSON.value,
            export_type="single",
            export_options={
                "include_metadata": True,
                "include_files": False,
                "include_kg_data": False
            },
            status="pending",
            progress=0.0,
            message="任务已创建"
        )
        
        # 保存到数据库
        db.add(test_task)
        db.commit()
        db.refresh(test_task)
        
        print("✓ 导出任务创建成功")
        print(f"  - ID: {test_task.id}")
        print(f"  - 任务ID: {test_task.task_id}")
        print(f"  - 状态: {test_task.status}")
        print(f"  - 格式: {test_task.export_format}")
        print(f"  - 类型: {test_task.export_type}")
        
        # 更新任务状态
        test_task.status = "processing"
        test_task.progress = 50.0
        test_task.message = "正在处理中..."
        test_task.started_at = datetime.utcnow()
        
        db.commit()
        db.refresh(test_task)
        
        print("✓ 任务状态更新成功")
        print(f"  - 新状态: {test_task.status}")
        print(f"  - 新进度: {test_task.progress}%")
        print(f"  - 开始时间: {test_task.started_at}")
        
        # 完成任务
        test_task.status = "completed"
        test_task.progress = 100.0
        test_task.message = "导出完成"
        test_task.completed_at = datetime.utcnow()
        test_task.file_path = "/exports/test_export.json"
        test_task.file_size = 2048
        test_task.download_url = "/api/v1/export/download/test_export.json"
        test_task.checksum = "def456"
        test_task.total_items = 25
        
        db.commit()
        db.refresh(test_task)
        
        print("✓ 任务完成状态更新成功")
        print(f"  - 完成时间: {test_task.completed_at}")
        print(f"  - 文件路径: {test_task.file_path}")
        print(f"  - 文件大小: {test_task.file_size} bytes")
        print(f"  - 数据项数量: {test_task.total_items}")
        
        # 查询任务
        retrieved_task = db.query(ExportTask).filter(
            ExportTask.task_id == "test-task-456"
        ).first()
        
        if retrieved_task:
            print("✓ 任务查询成功")
            print(f"  - 查询到的任务状态: {retrieved_task.status}")
        else:
            print("✗ 任务查询失败")
        
        # 测试to_dict方法
        task_dict = test_task.to_dict()
        print("✓ 任务字典转换成功")
        print(f"  - 字典包含 {len(task_dict)} 个字段")
        
        # 清理测试数据
        db.delete(test_task)
        db.commit()
        print("✓ 测试数据清理完成")
        
        print("\n导出任务模型测试完成!")
        
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_export_task_model())