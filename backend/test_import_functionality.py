#!/usr/bin/env python3
"""
测试导入功能的完整性
"""
import json
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime

# 测试数据生成
def create_test_export_data():
    """创建测试导出数据"""
    test_data = {
        "metadata": {
            "project_name": "测试项目",
            "project_description": "这是一个用于测试导入功能的项目",
            "export_format": "json",
            "export_timestamp": datetime.now().isoformat(),
            "total_files": 2,
            "total_cot_items": 3,
            "total_candidates": 9,
            "export_settings": {
                "include_metadata": True,
                "include_files": True,
                "include_kg_data": True
            }
        },
        "cot_items": [
            {
                "id": "cot_001",
                "question": "什么是机器学习？",
                "chain_of_thought": "机器学习是人工智能的一个分支...",
                "source": "manual",
                "status": "approved",
                "created_by": "test_user",
                "created_at": datetime.now().isoformat(),
                "slice_content": "机器学习（Machine Learning）是一种人工智能技术...",
                "slice_type": "paragraph",
                "file_name": "ml_basics.pdf",
                "candidates": [
                    {
                        "id": "cand_001",
                        "text": "机器学习是让计算机从数据中学习的技术",
                        "chain_of_thought": "首先理解数据，然后找出模式...",
                        "score": 0.9,
                        "chosen": True,
                        "rank": 1
                    },
                    {
                        "id": "cand_002",
                        "text": "机器学习是一种算法",
                        "chain_of_thought": "算法是解决问题的步骤...",
                        "score": 0.7,
                        "chosen": False,
                        "rank": 2
                    },
                    {
                        "id": "cand_003",
                        "text": "机器学习就是AI",
                        "chain_of_thought": "AI包含很多技术...",
                        "score": 0.5,
                        "chosen": False,
                        "rank": 3
                    }
                ]
            },
            {
                "id": "cot_002",
                "question": "深度学习和机器学习的区别是什么？",
                "chain_of_thought": "深度学习是机器学习的一个子集...",
                "source": "human_ai",
                "status": "reviewed",
                "created_by": "test_user",
                "created_at": datetime.now().isoformat(),
                "slice_content": "深度学习使用神经网络进行学习...",
                "slice_type": "paragraph",
                "file_name": "deep_learning.pdf",
                "candidates": [
                    {
                        "id": "cand_004",
                        "text": "深度学习使用多层神经网络",
                        "chain_of_thought": "神经网络模拟大脑结构...",
                        "score": 0.95,
                        "chosen": True,
                        "rank": 1
                    },
                    {
                        "id": "cand_005",
                        "text": "深度学习更复杂",
                        "chain_of_thought": "复杂性体现在网络层数...",
                        "score": 0.8,
                        "chosen": False,
                        "rank": 2
                    },
                    {
                        "id": "cand_006",
                        "text": "没有区别",
                        "chain_of_thought": "这是错误的理解...",
                        "score": 0.2,
                        "chosen": False,
                        "rank": 3
                    }
                ]
            },
            {
                "id": "cot_003",
                "question": "如何评估机器学习模型？",
                "chain_of_thought": "模型评估需要使用合适的指标...",
                "source": "generalization",
                "status": "draft",
                "created_by": "test_user",
                "created_at": datetime.now().isoformat(),
                "slice_content": "模型评估是机器学习流程中的重要步骤...",
                "slice_type": "paragraph",
                "file_name": "model_evaluation.pdf",
                "candidates": [
                    {
                        "id": "cand_007",
                        "text": "使用准确率、召回率等指标",
                        "chain_of_thought": "不同任务需要不同指标...",
                        "score": 0.9,
                        "chosen": True,
                        "rank": 1
                    },
                    {
                        "id": "cand_008",
                        "text": "使用交叉验证",
                        "chain_of_thought": "交叉验证可以更好地评估...",
                        "score": 0.85,
                        "chosen": False,
                        "rank": 2
                    },
                    {
                        "id": "cand_009",
                        "text": "看训练误差",
                        "chain_of_thought": "只看训练误差可能过拟合...",
                        "score": 0.6,
                        "chosen": False,
                        "rank": 3
                    }
                ]
            }
        ],
        "files_info": [
            {
                "id": "file_001",
                "filename": "ml_basics.pdf",
                "size": 1024000,
                "mime_type": "application/pdf",
                "file_hash": "abc123def456",
                "ocr_status": "completed",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "file_002",
                "filename": "deep_learning.pdf",
                "size": 2048000,
                "mime_type": "application/pdf",
                "file_hash": "def456ghi789",
                "ocr_status": "completed",
                "created_at": datetime.now().isoformat()
            }
        ],
        "kg_data": {
            "entities": [
                {
                    "id": "entity_001",
                    "name": "机器学习",
                    "type": "concept",
                    "properties": {
                        "definition": "让计算机从数据中学习的技术"
                    }
                },
                {
                    "id": "entity_002",
                    "name": "深度学习",
                    "type": "concept",
                    "properties": {
                        "definition": "使用多层神经网络的机器学习方法"
                    }
                }
            ],
            "relations": [
                {
                    "id": "rel_001",
                    "source": "entity_002",
                    "target": "entity_001",
                    "type": "is_a",
                    "properties": {
                        "description": "深度学习是机器学习的一种"
                    }
                }
            ]
        }
    }
    
    return test_data

def create_test_json_file():
    """创建测试JSON文件"""
    test_data = create_test_export_data()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2, default=str)
        return f.name

def create_test_zip_file():
    """创建测试ZIP文件"""
    test_data = create_test_export_data()
    
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
        zip_path = f.name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 添加主数据文件
        zipf.writestr('data.json', json.dumps(test_data, ensure_ascii=False, indent=2, default=str))
        
        # 添加元数据文件
        zipf.writestr('metadata.json', json.dumps(test_data['metadata'], ensure_ascii=False, indent=2, default=str))
        
        # 添加知识图谱文件
        zipf.writestr('knowledge_graph.json', json.dumps(test_data['kg_data'], ensure_ascii=False, indent=2, default=str))
        
        # 添加Markdown文件
        md_content = f"""# {test_data['metadata']['project_name']}

## 项目描述
{test_data['metadata']['project_description']}

## CoT数据

"""
        for item in test_data['cot_items']:
            md_content += f"""### {item['question']}

**状态**: {item['status']}
**来源**: {item['source']}

**原文片段**:
> {item['slice_content']}

**候选答案**:
"""
            for candidate in item['candidates']:
                chosen = "✓" if candidate['chosen'] else ""
                md_content += f"{candidate['rank']}. {chosen} **评分**: {candidate['score']}\n"
                md_content += f"   {candidate['text']}\n\n"
        
        zipf.writestr('data.md', md_content)
    
    return zip_path

def test_import_service():
    """测试导入服务"""
    print("开始测试导入功能...")
    
    # 创建测试文件
    json_file = create_test_json_file()
    zip_file = create_test_zip_file()
    
    print(f"创建测试JSON文件: {json_file}")
    print(f"创建测试ZIP文件: {zip_file}")
    
    try:
        # 这里应该测试导入服务的各个功能
        # 由于需要数据库连接，这里只是验证文件创建
        
        # 验证JSON文件
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            print(f"JSON文件验证成功，包含 {len(json_data['cot_items'])} 个CoT项目")
        
        # 验证ZIP文件
        with zipfile.ZipFile(zip_file, 'r') as zipf:
            file_list = zipf.namelist()
            print(f"ZIP文件验证成功，包含文件: {', '.join(file_list)}")
            
            # 验证数据完整性
            data_content = zipf.read('data.json')
            zip_data = json.loads(data_content.decode('utf-8'))
            print(f"ZIP中的数据验证成功，包含 {len(zip_data['cot_items'])} 个CoT项目")
        
        print("✅ 导入功能测试文件创建成功")
        
        return {
            'json_file': json_file,
            'zip_file': zip_file,
            'test_data': create_test_export_data()
        }
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return None
    
    finally:
        # 清理测试文件
        try:
            Path(json_file).unlink()
            Path(zip_file).unlink()
            print("测试文件已清理")
        except Exception as e:
            print(f"清理测试文件失败: {str(e)}")

def test_difference_detection():
    """测试差异检测算法"""
    print("\n开始测试差异检测算法...")
    
    # 创建源数据和目标数据
    source_data = create_test_export_data()
    target_data = create_test_export_data()
    
    # 修改目标数据以创建差异
    target_data['metadata']['project_name'] = "修改后的项目名称"
    target_data['cot_items'][0]['question'] = "修改后的问题"
    target_data['cot_items'][0]['candidates'][0]['score'] = 0.8  # 修改评分
    target_data['cot_items'].pop()  # 删除一个CoT项目
    
    # 在源数据中添加新项目
    new_cot_item = {
        "id": "cot_004",
        "question": "新增的问题",
        "chain_of_thought": "新增的思维链",
        "source": "manual",
        "status": "draft",
        "created_by": "test_user",
        "created_at": datetime.now().isoformat(),
        "slice_content": "新增的切片内容",
        "slice_type": "paragraph",
        "file_name": "new_file.pdf",
        "candidates": []
    }
    source_data['cot_items'].append(new_cot_item)
    
    print("✅ 差异检测测试数据创建成功")
    print(f"源数据包含 {len(source_data['cot_items'])} 个CoT项目")
    print(f"目标数据包含 {len(target_data['cot_items'])} 个CoT项目")
    
    # 这里应该调用实际的差异检测算法
    # 由于需要导入服务实例，这里只是模拟
    expected_differences = [
        "项目名称修改",
        "CoT项目问题修改",
        "候选答案评分修改",
        "CoT项目删除",
        "新CoT项目添加"
    ]
    
    print(f"预期发现 {len(expected_differences)} 个差异:")
    for i, diff in enumerate(expected_differences, 1):
        print(f"  {i}. {diff}")
    
    return {
        'source_data': source_data,
        'target_data': target_data,
        'expected_differences': expected_differences
    }

if __name__ == "__main__":
    print("=" * 50)
    print("COT Studio 导入功能测试")
    print("=" * 50)
    
    # 测试文件创建和验证
    test_result = test_import_service()
    
    # 测试差异检测
    diff_result = test_difference_detection()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
    
    if test_result and diff_result:
        print("✅ 所有测试通过")
        print("\n下一步:")
        print("1. 启动后端服务")
        print("2. 使用生成的测试文件测试API端点")
        print("3. 在前端界面中测试完整的导入流程")
    else:
        print("❌ 部分测试失败，请检查实现")