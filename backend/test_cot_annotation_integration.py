"""
CoT标注API集成测试
"""
import requests
import json
from uuid import uuid4


def test_cot_annotation_api():
    """测试CoT标注API基本功能"""
    base_url = "http://localhost:8000"
    
    # 测试数据
    test_user = {
        "username": "test_cot_user",
        "email": "test_cot@example.com", 
        "password": "test_password"
    }
    
    try:
        # 1. 注册用户
        print("1. 注册用户...")
        register_response = requests.post(f"{base_url}/api/v1/auth/register", json=test_user)
        print(f"注册响应: {register_response.status_code}")
        
        # 2. 登录获取token
        print("2. 用户登录...")
        login_response = requests.post(f"{base_url}/api/v1/auth/login", json={
            "username": test_user["username"],
            "password": test_user["password"]
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("登录成功，获取到token")
        else:
            print(f"登录失败: {login_response.status_code} - {login_response.text}")
            return
        
        # 3. 创建项目
        print("3. 创建测试项目...")
        project_data = {
            "name": "CoT Annotation Test Project",
            "description": "Test project for CoT annotation API"
        }
        project_response = requests.post(f"{base_url}/api/v1/projects", json=project_data, headers=headers)
        
        if project_response.status_code == 201:
            project_id = project_response.json()["id"]
            print(f"项目创建成功: {project_id}")
        else:
            print(f"项目创建失败: {project_response.status_code} - {project_response.text}")
            return
        
        # 4. 测试CoT标注API端点
        print("4. 测试CoT标注API端点...")
        
        # 模拟slice_id（在实际应用中需要先上传文件和OCR处理）
        slice_id = str(uuid4())
        
        # 创建CoT标注数据
        cot_data = {
            "project_id": project_id,
            "slice_id": slice_id,
            "question": "What is the main topic discussed in this text segment?",
            "chain_of_thought": "Let me analyze this step by step to understand the content...",
            "source": "manual",
            "candidates": [
                {
                    "text": "The text discusses machine learning algorithms and their applications.",
                    "chain_of_thought": "Based on the technical terms and context, this appears to be about ML.",
                    "score": 0.9,
                    "chosen": True,
                    "rank": 1
                },
                {
                    "text": "The text is about data processing techniques.",
                    "chain_of_thought": "The content mentions data handling which could indicate processing.",
                    "score": 0.7,
                    "chosen": False,
                    "rank": 2
                },
                {
                    "text": "The text covers software development practices.",
                    "chain_of_thought": "Some programming concepts are mentioned in the text.",
                    "score": 0.5,
                    "chosen": False,
                    "rank": 3
                }
            ]
        }
        
        # 测试创建CoT标注
        print("   - 测试创建CoT标注...")
        create_response = requests.post(f"{base_url}/api/v1/cot-annotation/", json=cot_data, headers=headers)
        print(f"   创建响应: {create_response.status_code}")
        
        if create_response.status_code == 200:
            cot_id = create_response.json()["id"]
            print(f"   CoT标注创建成功: {cot_id}")
            
            # 测试获取CoT标注
            print("   - 测试获取CoT标注...")
            get_response = requests.get(f"{base_url}/api/v1/cot-annotation/{cot_id}", headers=headers)
            print(f"   获取响应: {get_response.status_code}")
            
            # 测试验证CoT标注
            print("   - 测试验证CoT标注...")
            validate_response = requests.get(f"{base_url}/api/v1/cot-annotation/{cot_id}/validate", headers=headers)
            print(f"   验证响应: {validate_response.status_code}")
            if validate_response.status_code == 200:
                validation_result = validate_response.json()
                print(f"   验证结果: valid={validation_result['is_valid']}")
            
            # 测试更新候选答案排序
            print("   - 测试更新候选答案排序...")
            candidates = create_response.json()["candidates"]
            if candidates:
                update_data = [
                    {
                        "candidate_id": candidates[0]["id"],
                        "score": 0.95,
                        "chosen": True,
                        "rank": 1
                    }
                ]
                update_response = requests.patch(
                    f"{base_url}/api/v1/cot-annotation/{cot_id}/candidates",
                    json=update_data,
                    headers=headers
                )
                print(f"   更新响应: {update_response.status_code}")
            
            # 测试更新状态
            print("   - 测试更新状态...")
            status_data = {"status": "reviewed"}
            status_response = requests.patch(
                f"{base_url}/api/v1/cot-annotation/{cot_id}/status",
                json=status_data,
                headers=headers
            )
            print(f"   状态更新响应: {status_response.status_code}")
        
        # 测试项目统计
        print("   - 测试项目统计...")
        stats_response = requests.get(f"{base_url}/api/v1/cot-annotation/project/{project_id}/stats", headers=headers)
        print(f"   统计响应: {stats_response.status_code}")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"   统计结果: total={stats['total_count']}, completion_rate={stats['completion_rate']}")
        
        # 测试质量指标
        print("   - 测试质量指标...")
        metrics_response = requests.get(f"{base_url}/api/v1/cot-annotation/project/{project_id}/quality-metrics", headers=headers)
        print(f"   指标响应: {metrics_response.status_code}")
        if metrics_response.status_code == 200:
            metrics = metrics_response.json()
            print(f"   质量指标: average_score={metrics['average_score']}")
        
        print("\n✅ CoT标注API测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保应用正在运行在 http://localhost:8000")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")


if __name__ == "__main__":
    test_cot_annotation_api()