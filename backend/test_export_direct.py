#!/usr/bin/env python3
"""
直接测试导出功能
"""
import sys
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接导入需要的模块，避免循环依赖
from app.schemas.export import ExportFormat, ExportRequest, ExportMetadata, COTExportItem, ProjectExportData

async def test_export_schemas():
    """测试导出相关的数据结构"""
    print("开始测试导出数据结构...")
    
    try:
        # 测试导出请求
        export_request = ExportRequest(
            project_id="test-project-123",
            format=ExportFormat.JSON,
            include_metadata=True,
            include_files=True,
            include_kg_data=False
        )
        print("✓ 导出请求创建成功")
        print(f"  - 项目ID: {export_request.project_id}")
        print(f"  - 格式: {export_request.format}")
        
        # 测试导出元数据
        metadata = ExportMetadata(
            project_name="测试项目",
            project_description="这是一个测试项目",
            export_format=ExportFormat.JSON,
            export_timestamp=datetime.now(),
            total_files=5,
            total_cot_items=10,
            total_candidates=25,
            export_settings=export_request.dict()
        )
        print("✓ 导出元数据创建成功")
        print(f"  - 项目名称: {metadata.project_name}")
        print(f"  - CoT数据项: {metadata.total_cot_items}")
        
        # 测试CoT导出项
        cot_item = COTExportItem(
            id="cot-123",
            question="这是一个测试问题？",
            chain_of_thought="这是思维链内容",
            source="manual",
            status="completed",
            created_by="test_user",
            created_at=datetime.now(),
            slice_content="这是原文片段内容",
            slice_type="text",
            file_name="test_file.txt",
            candidates=[
                {
                    "id": "candidate-1",
                    "text": "候选答案1",
                    "chain_of_thought": "候选答案1的思维链",
                    "score": 0.9,
                    "chosen": True,
                    "rank": 1
                },
                {
                    "id": "candidate-2", 
                    "text": "候选答案2",
                    "chain_of_thought": "候选答案2的思维链",
                    "score": 0.7,
                    "chosen": False,
                    "rank": 2
                }
            ]
        )
        print("✓ CoT导出项创建成功")
        print(f"  - 问题: {cot_item.question}")
        print(f"  - 候选答案数量: {len(cot_item.candidates)}")
        
        # 测试项目导出数据
        project_data = ProjectExportData(
            metadata=metadata,
            cot_items=[cot_item],
            files_info=[
                {
                    "id": "file-123",
                    "filename": "test_file.txt",
                    "size": 1024,
                    "mime_type": "text/plain",
                    "file_hash": "abc123",
                    "ocr_status": "completed",
                    "created_at": datetime.now().isoformat()
                }
            ],
            kg_data=None
        )
        print("✓ 项目导出数据创建成功")
        
        # 测试JSON序列化
        export_dict = {
            "metadata": metadata.dict(),
            "cot_items": [item.dict() for item in project_data.cot_items],
            "files_info": project_data.files_info,
            "kg_data": project_data.kg_data
        }
        
        json_str = json.dumps(export_dict, ensure_ascii=False, indent=2, default=str)
        print("✓ JSON序列化成功")
        print(f"  - JSON长度: {len(json_str)} 字符")
        
        # 测试支持的格式
        formats = [format.value for format in ExportFormat]
        print(f"✓ 支持的导出格式: {formats}")
        
        print("\n导出数据结构测试完成!")
        return True
        
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_export_directory():
    """测试导出目录"""
    print("\n开始测试导出目录...")
    
    try:
        # 创建导出目录
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)
        print(f"✓ 导出目录创建成功: {export_dir.absolute()}")
        
        # 测试写入文件
        test_file = export_dir / "test_export.json"
        test_data = {
            "test": "data",
            "timestamp": datetime.now().isoformat(),
            "中文": "测试"
        }
        
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 测试文件写入成功: {test_file}")
        
        # 验证文件内容
        with open(test_file, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        
        if loaded_data["test"] == "data":
            print("✓ 文件内容验证成功")
        else:
            print("✗ 文件内容验证失败")
        
        # 清理测试文件
        test_file.unlink()
        print("✓ 测试文件清理完成")
        
        return True
        
    except Exception as e:
        print(f"✗ 导出目录测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("=" * 50)
    print("导出功能基础测试")
    print("=" * 50)
    
    success1 = await test_export_schemas()
    success2 = await test_export_directory()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✓ 所有测试通过！导出功能基础组件正常")
    else:
        print("✗ 部分测试失败，需要修复")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())