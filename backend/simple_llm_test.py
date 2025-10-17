"""
简单的LLM测试脚本
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from openai import AsyncOpenAI
    print("✓ OpenAI库导入成功")
except ImportError as e:
    print(f"✗ OpenAI库导入失败: {e}")
    sys.exit(1)


async def test_deepseek_direct():
    """直接测试DeepSeek API"""
    print("=== 直接测试DeepSeek API ===")
    
    # DeepSeek配置
    api_key = "sk-0dc1980d2c264b19bde7da0c209e13dd"
    base_url = "https://api.deepseek.com"
    model = "deepseek-chat"
    
    try:
        # 创建客户端
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=60
        )
        
        print(f"✓ 客户端创建成功")
        print(f"  API Key: {api_key[:10]}...")
        print(f"  Base URL: {base_url}")
        print(f"  Model: {model}")
        
        # 发送测试请求
        messages = [
            {"role": "system", "content": "你是一个有用的助手。"},
            {"role": "user", "content": "请简单介绍一下机器学习。"}
        ]
        
        print("发送请求...")
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )
        
        print("✓ 请求成功")
        print(f"响应内容: {response.choices[0].message.content}")
        
        if response.usage:
            print(f"Token使用: {response.usage.model_dump()}")
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"✗ 请求失败: {str(e)}")
        return False


async def test_cot_prompt():
    """测试CoT提示词"""
    print("\n=== 测试CoT提示词 ===")
    
    api_key = "sk-0dc1980d2c264b19bde7da0c209e13dd"
    base_url = "https://api.deepseek.com"
    model = "deepseek-chat"
    
    try:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=60
        )
        
        # CoT问题生成提示词
        system_prompt = """你是一个专业的学术研究助手，擅长基于给定文本生成高质量的Chain-of-Thought (CoT)问题。

请根据以下文本片段，生成一个需要深度思考和推理的学术级别问题。问题应该：
1. 需要多步推理才能回答
2. 具有学术价值和深度
3. 能够引导出清晰的思维链条
4. 适合进行CoT格式的回答

请直接返回问题，不要包含其他解释。问题长度控制在100字以内。"""

        user_content = """文本片段：
机器学习是人工智能的一个重要分支，它使计算机能够在没有明确编程的情况下学习和改进。
机器学习算法通过分析大量数据来识别模式，并使用这些模式来对新数据做出预测或决策。
常见的机器学习类型包括监督学习、无监督学习和强化学习。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        print("生成CoT问题...")
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.8,
            max_tokens=200
        )
        
        question = response.choices[0].message.content.strip()
        print(f"✓ 生成的问题: {question}")
        
        # 测试候选答案生成
        answer_prompt = f"""你是一个专业的学术研究助手，擅长生成高质量的Chain-of-Thought (CoT)格式答案。

请基于给定的问题和文本片段，生成3个不同的CoT格式答案。每个答案都应该：
1. 包含清晰的思维步骤
2. 逻辑推理过程完整
3. 结论明确且有依据
4. 风格和角度略有不同

请按以下JSON格式返回：
{{
    "candidates": [
        {{
            "text": "最终答案内容",
            "chain_of_thought": "详细的思维推理过程，包含步骤1、步骤2等"
        }},
        {{
            "text": "最终答案内容",
            "chain_of_thought": "详细的思维推理过程，包含步骤1、步骤2等"
        }},
        {{
            "text": "最终答案内容", 
            "chain_of_thought": "详细的思维推理过程，包含步骤1、步骤2等"
        }}
    ]
}}

确保返回有效的JSON格式，每个答案都有完整的思维链条。

问题：{question}

文本片段：
{user_content.replace('文本片段：', '').strip()}"""

        answer_messages = [
            {"role": "user", "content": answer_prompt}
        ]
        
        print("生成候选答案...")
        answer_response = await client.chat.completions.create(
            model=model,
            messages=answer_messages,
            temperature=0.9,
            max_tokens=1500
        )
        
        answer_content = answer_response.choices[0].message.content
        print(f"✓ 生成的候选答案: {answer_content[:200]}...")
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"✗ CoT提示词测试失败: {str(e)}")
        return False


async def main():
    """主函数"""
    print("开始LLM集成测试...")
    
    # 运行测试
    test1_result = await test_deepseek_direct()
    test2_result = await test_cot_prompt()
    
    print("\n=== 测试结果 ===")
    print(f"DeepSeek直接测试: {'✓ 通过' if test1_result else '✗ 失败'}")
    print(f"CoT提示词测试: {'✓ 通过' if test2_result else '✗ 失败'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！LLM集成准备就绪。")
    else:
        print("\n❌ 部分测试失败，请检查配置。")


if __name__ == "__main__":
    asyncio.run(main())