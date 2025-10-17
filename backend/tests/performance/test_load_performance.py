"""
性能和负载测试
测试系统在高负载下的表现
"""
import pytest
import asyncio
import time
import concurrent.futures
from typing import List
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestLoadPerformance:
    """负载性能测试"""
    
    def test_concurrent_file_uploads(self, client: TestClient, db_session: Session):
        """测试并发文件上传性能"""
        
        # 创建测试项目
        project_data = {"name": "性能测试项目", "description": "并发上传测试"}
        response = client.post("/api/v1/projects/", json=project_data)
        project_id = response.json()["id"]
        
        def upload_file(file_index: int):
            """单个文件上传函数"""
            content = f"测试文件内容 {file_index} " * 100  # 创建较大内容
            files = {"file": (f"test_{file_index}.txt", content.encode(), "text/plain")}
            
            start_time = time.time()
            response = client.post(f"/api/v1/projects/{project_id}/upload", files=files)
            end_time = time.time()
            
            return {
                "status_code": response.status_code,
                "duration": end_time - start_time,
                "file_index": file_index
            }
        
        # 并发上传测试
        concurrent_uploads = 10
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(upload_file, i) for i in range(concurrent_uploads)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # 验证结果
        successful_uploads = [r for r in results if r["status_code"] == 200]
        assert len(successful_uploads) == concurrent_uploads, f"只有 {len(successful_uploads)}/{concurrent_uploads} 个文件上传成功"
        
        # 性能指标
        avg_duration = sum(r["duration"] for r in results) / len(results)
        max_duration = max(r["duration"] for r in results)
        
        print(f"并发上传性能:")
        print(f"  总时间: {total_time:.2f}s")
        print(f"  平均单文件时间: {avg_duration:.2f}s")
        print(f"  最大单文件时间: {max_duration:.2f}s")
        print(f"  吞吐量: {concurrent_uploads/total_time:.2f} files/s")
        
        # 性能断言（根据实际需求调整）
        assert avg_duration < 5.0, f"平均上传时间过长: {avg_duration:.2f}s"
        assert max_duration < 10.0, f"最大上传时间过长: {max_duration:.2f}s"
    
    def test_concurrent_cot_generation(self, client: TestClient, db_session: Session):
        """测试并发CoT生成性能"""
        
        # 准备测试数据
        project_data = {"name": "CoT性能测试", "description": "并发CoT生成测试"}
        response = client.post("/api/v1/projects/", json=project_data)
        project_id = response.json()["id"]
        
        # 创建测试文件和切片
        content = "人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。"
        files = {"file": ("ai_test.txt", content.encode(), "text/plain")}
        response = client.post(f"/api/v1/projects/{project_id}/upload", files=files)
        file_id = response.json()["file_id"]
        
        # 触发OCR处理
        client.post(f"/api/v1/files/{file_id}/ocr")
        
        # 获取切片
        response = client.get(f"/api/v1/files/{file_id}/slices")
        slices = response.json()
        assert len(slices) > 0
        slice_id = slices[0]["id"]
        
        def generate_cot(request_index: int):
            """单个CoT生成函数"""
            cot_data = {
                "slice_id": slice_id,
                "question_prompt": f"生成关于人工智能的问题 {request_index}"
            }
            
            start_time = time.time()
            response = client.post("/api/v1/cot/generate", json=cot_data)
            end_time = time.time()
            
            return {
                "status_code": response.status_code,
                "duration": end_time - start_time,
                "request_index": request_index,
                "response_size": len(response.content) if response.status_code == 200 else 0
            }
        
        # 并发CoT生成测试
        concurrent_requests = 5  # CoT生成通常较慢，减少并发数
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(generate_cot, i) for i in range(concurrent_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # 验证结果
        successful_requests = [r for r in results if r["status_code"] == 200]
        
        if successful_requests:  # 如果有成功的请求
            avg_duration = sum(r["duration"] for r in successful_requests) / len(successful_requests)
            max_duration = max(r["duration"] for r in successful_requests)
            
            print(f"并发CoT生成性能:")
            print(f"  成功请求: {len(successful_requests)}/{concurrent_requests}")
            print(f"  总时间: {total_time:.2f}s")
            print(f"  平均生成时间: {avg_duration:.2f}s")
            print(f"  最大生成时间: {max_duration:.2f}s")
            
            # CoT生成可能较慢，设置较宽松的限制
            assert avg_duration < 30.0, f"平均CoT生成时间过长: {avg_duration:.2f}s"
    
    def test_database_query_performance(self, client: TestClient, db_session: Session):
        """测试数据库查询性能"""
        
        # 创建大量测试数据
        project_data = {"name": "数据库性能测试", "description": "大量数据查询测试"}
        response = client.post("/api/v1/projects/", json=project_data)
        project_id = response.json()["id"]
        
        # 批量创建CoT数据
        batch_size = 50
        for i in range(batch_size):
            cot_data = {
                "project_id": project_id,
                "question": f"测试问题 {i}",
                "candidates": [
                    {
                        "text": f"测试答案 {i}",
                        "chain_of_thought": f"测试推理 {i}",
                        "score": 0.8,
                        "chosen": True,
                        "rank": 1
                    }
                ]
            }
            client.post("/api/v1/cot/", json=cot_data)
        
        # 测试查询性能
        query_tests = [
            ("项目详情查询", f"/api/v1/projects/{project_id}"),
            ("CoT列表查询", f"/api/v1/projects/{project_id}/cot"),
            ("项目统计查询", f"/api/v1/projects/{project_id}/stats"),
        ]
        
        for test_name, endpoint in query_tests:
            # 多次查询测试
            durations = []
            for _ in range(10):
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()
                
                if response.status_code == 200:
                    durations.append(end_time - start_time)
            
            if durations:
                avg_duration = sum(durations) / len(durations)
                max_duration = max(durations)
                min_duration = min(durations)
                
                print(f"{test_name}性能:")
                print(f"  平均响应时间: {avg_duration:.3f}s")
                print(f"  最大响应时间: {max_duration:.3f}s")
                print(f"  最小响应时间: {min_duration:.3f}s")
                
                # 数据库查询应该很快
                assert avg_duration < 1.0, f"{test_name}平均响应时间过长: {avg_duration:.3f}s"
    
    def test_memory_usage_under_load(self, client: TestClient, db_session: Session):
        """测试负载下的内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建项目
        project_data = {"name": "内存测试项目", "description": "内存使用测试"}
        response = client.post("/api/v1/projects/", json=project_data)
        project_id = response.json()["id"]
        
        # 执行大量操作
        operations = 100
        for i in range(operations):
            # 上传文件
            content = f"测试内容 {i} " * 50
            files = {"file": (f"test_{i}.txt", content.encode(), "text/plain")}
            response = client.post(f"/api/v1/projects/{project_id}/upload", files=files)
            
            if i % 10 == 0:  # 每10次操作检查一次内存
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                
                print(f"操作 {i}: 内存使用 {current_memory:.1f}MB (+{memory_increase:.1f}MB)")
                
                # 内存增长不应该过快
                assert memory_increase < 500, f"内存增长过快: {memory_increase:.1f}MB"
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        
        print(f"最终内存使用: {final_memory:.1f}MB (+{total_increase:.1f}MB)")
        
        # 总内存增长限制
        assert total_increase < 1000, f"总内存增长过多: {total_increase:.1f}MB"
    
    def test_api_response_time_distribution(self, client: TestClient, db_session: Session):
        """测试API响应时间分布"""
        
        # 创建测试项目
        project_data = {"name": "响应时间测试", "description": "API响应时间分布测试"}
        response = client.post("/api/v1/projects/", json=project_data)
        project_id = response.json()["id"]
        
        # 测试不同API端点的响应时间
        endpoints = [
            ("GET", f"/api/v1/projects/{project_id}"),
            ("GET", "/api/v1/projects/"),
            ("POST", "/api/v1/projects/", {"name": "临时项目", "description": "测试"}),
        ]
        
        for method, endpoint, *data in endpoints:
            durations = []
            
            # 多次请求收集数据
            for _ in range(20):
                start_time = time.time()
                
                if method == "GET":
                    response = client.get(endpoint)
                elif method == "POST":
                    response = client.post(endpoint, json=data[0] if data else {})
                
                end_time = time.time()
                
                if response.status_code in [200, 201]:
                    durations.append(end_time - start_time)
            
            if durations:
                durations.sort()
                n = len(durations)
                
                # 计算百分位数
                p50 = durations[int(n * 0.5)]
                p90 = durations[int(n * 0.9)]
                p95 = durations[int(n * 0.95)]
                p99 = durations[int(n * 0.99)] if n >= 100 else durations[-1]
                
                print(f"{method} {endpoint} 响应时间分布:")
                print(f"  P50: {p50:.3f}s")
                print(f"  P90: {p90:.3f}s")
                print(f"  P95: {p95:.3f}s")
                print(f"  P99: {p99:.3f}s")
                
                # 性能要求
                assert p95 < 2.0, f"P95响应时间过长: {p95:.3f}s"
                assert p99 < 5.0, f"P99响应时间过长: {p99:.3f}s"