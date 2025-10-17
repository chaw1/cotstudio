"""
测试LLM集成和CoT生成服务
"""
import asyncio
import logging
from app.services.llm_service import LLMService, LLMMessage
from app.services.cot_generation_service import COTGenerationService
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_deepseek_connection():
    """测试DeepSeek连接"""
    print("=== 测试DeepSeek连接 ===")
    
    llm_service = LLMService()
    
    try:
        # 初始化服务
        await llm_service.initialize()
        print(f"可用的提供商: {llm_service.get_available_providers()}")
        print(f"默认提供商: {llm_service.default_provider}")
        
        # 测试简单对话
        messages = [
            LLMMessage(role="system", content="你是一个有用的助手。"),
            LLMMessage(role="user", content="你好，请简单介绍一下自己。")
        ]
        
        response = await llm_service.generate_completion(
            messages=messages,
            provider="deepseek",
            temperature=0.7,
            max_tokens=100
        )
        
        print(f"响应提供商: {response.provider}")
        print(f"响应模型: {response.model}")
        print(f"响应内容: {response.content}")
        print(f"使用情况: {response.usage}")
        
        return True
        
    except Exception as e:
        print(f"DeepSeek连接测试失败: {str(e)}")
        return False
    
    finally:
        await llm_service.close()


async def test_cot_question_generation():
    """测试CoT问题生成"""
    print("\n=== 测试CoT问题生成 ===")
    
    llm_service = LLMService()
    cot_service = COTGenerationService(llm_service)
    
    try:
        await llm_service.initialize()
        
        # 测试文本片段
        slice_content = """
        机器学习是人工智能的一个重要分支，它使计算机能够在没有明确编程的情况下学习和改进。
        机器学习算法通过分析大量数据来识别模式，并使用这些模式来对新数据做出预测或决策。
        常见的机器学习类型包括监督学习、无监督学习和强化学习。
        """
        
        # 生成问题
        question = await cot_service.generate_question(slice_content)
        print(f"生成的问题: {question}")
        
        return question
        
    except Exception as e:
        print(f"问题生成测试失败: {str(e)}")
        return None
    
    finally:
        await llm_service.close()


async def test_cot_candidates_generation():
    """测试CoT候选答案生成"""
    print("\n=== 测试CoT候选答案生成 ===")
    
    llm_service = LLMService()
    cot_service = COTGenerationService(llm_service)
    
    try:
        await llm_service.initialize()
        
        # 测试数据
        question = "机器学习中监督学习和无监督学习的主要区别是什么？请详细解释它们的工作原理。"
        slice_content = """
        机器学习是人工智能的一个重要分支，它使计算机能够在没有明确编程的情况下学习和改进。
        机器学习算法通过分析大量数据来识别模式，并使用这些模式来对新数据做出预测或决策。
        常见的机器学习类型包括监督学习、无监督学习和强化学习。
        """
        
        # 生成候选答案
        candidates = await cot_service.generate_candidates(
            question=question,
            slice_content=slice_content,
            candidate_count=3
        )
        
        print(f"生成了 {len(candidates)} 个候选答案:")
        for i, candidate in enumerate(candidates, 1):
            print(f"\n候选答案 {i}:")
            print(f"  排序: {candidate.rank}")
            print(f"  答案: {candidate.text[:100]}...")
            print(f"  思维链: {candidate.chain_of_thought[:100]}...")
            print(f"  分数: {candidate.score}")
            print(f"  选中: {candidate.chosen}")
        
        return candidates
        
    except Exception as e:
        print(f"候选答案生成测试失败: {str(e)}")
        return None
    
    finally:
        await llm_service.close()


async def test_complete_cot_generation():
    """测试完整CoT生成流程"""
    print("\n=== 测试完整CoT生成流程 ===")
    
    llm_service = LLMService()
    cot_service = COTGenerationService(llm_service)
    
    try:
        await llm_service.initialize()
        
        # 模拟数据
        from uuid import uuid4
        project_id = uuid4()
        slice_id = uuid4()
        slice_content = """
        深度学习是机器学习的一个子集，它使用人工神经网络来模拟人脑的学习过程。
        深度学习网络包含多个隐藏层，每一层都能学习数据的不同特征。
        这种分层的特征学习使得深度学习在图像识别、自然语言处理等领域取得了突破性进展。
        """
        
        # 生成完整CoT数据
        cot_create = await cot_service.generate_cot_item(
            project_id=project_id,
            slice_id=slice_id,
            slice_content=slice_content,
            created_by="test_user",
            candidate_count=3
        )
        
        print(f"项目ID: {cot_create.project_id}")
        print(f"切片ID: {cot_create.slice_id}")
        print(f"生成的问题: {cot_create.question}")
        print(f"候选答案数量: {len(cot_create.candidates)}")
        print(f"LLM元数据: {cot_create.llm_metadata}")
        
        return cot_create
        
    except Exception as e:
        print(f"完整CoT生成测试失败: {str(e)}")
        return None
    
    finally:
        await llm_service.close()


async def main():
    """主测试函数"""
    print("开始测试LLM集成和CoT生成服务...")
    print(f"DeepSeek API Key: {settings.DEEPSEEK_API_KEY[:10]}...")
    print(f"DeepSeek Base URL: {settings.DEEPSEEK_BASE_URL}")
    print(f"DeepSeek Model: {settings.DEEPSEEK_MODEL}")
    
    # 运行测试
    tests = [
        test_deepseek_connection,
        test_cot_question_generation,
        test_cot_candidates_generation,
        test_complete_cot_generation
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append((test.__name__, "PASSED" if result else "FAILED"))
        except Exception as e:
            print(f"测试 {test.__name__} 出现异常: {str(e)}")
            results.append((test.__name__, "ERROR"))
    
    # 输出测试结果
    print("\n=== 测试结果汇总 ===")
    for test_name, status in results:
        print(f"{test_name}: {status}")


if __name__ == "__main__":
    asyncio.run(main())