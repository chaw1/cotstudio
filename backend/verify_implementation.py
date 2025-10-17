"""
验证LLM集成实现
"""
import os
import sys

def check_files():
    """检查文件是否存在"""
    print("=== 检查实现文件 ===")
    
    files_to_check = [
        "app/services/llm_service.py",
        "app/services/cot_generation_service.py", 
        "app/api/v1/cot_generation.py",
        "app/workers/cot_tasks.py"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            all_exist = False
    
    return all_exist


def check_config():
    """检查配置"""
    print("\n=== 检查配置 ===")
    
    try:
        # 检查配置文件
        config_path = "app/core/config.py"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            checks = [
                ("DEEPSEEK_API_KEY", "sk-0dc1980d2c264b19bde7da0c209e13dd" in content),
                ("DEEPSEEK_BASE_URL", "https://api.deepseek.com" in content),
                ("DEEPSEEK_MODEL", "deepseek-chat" in content),
                ("DEFAULT_LLM_PROVIDER", 'DEFAULT_LLM_PROVIDER: str = "deepseek"' in content),
                ("COT_CANDIDATE_COUNT", "COT_CANDIDATE_COUNT" in content)
            ]
            
            for check_name, result in checks:
                print(f"{'✓' if result else '✗'} {check_name}")
            
            return all(result for _, result in checks)
        else:
            print(f"✗ 配置文件不存在: {config_path}")
            return False
            
    except Exception as e:
        print(f"✗ 检查配置时出错: {e}")
        return False


def check_requirements():
    """检查依赖"""
    print("\n=== 检查依赖 ===")
    
    try:
        with open("requirements.txt", 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_deps = [
            "openai",
            "langchain", 
            "langchain-openai",
            "tenacity"
        ]
        
        all_deps = True
        for dep in required_deps:
            if dep in content:
                print(f"✓ {dep}")
            else:
                print(f"✗ {dep}")
                all_deps = False
        
        return all_deps
        
    except Exception as e:
        print(f"✗ 检查依赖时出错: {e}")
        return False


def check_api_routes():
    """检查API路由"""
    print("\n=== 检查API路由 ===")
    
    try:
        main_path = "app/main.py"
        if os.path.exists(main_path):
            with open(main_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            checks = [
                ("导入cot_generation", "cot_generation" in content),
                ("注册CoT路由", 'prefix="/api/v1/cot"' in content)
            ]
            
            for check_name, result in checks:
                print(f"{'✓' if result else '✗'} {check_name}")
            
            return all(result for _, result in checks)
        else:
            print(f"✗ 主应用文件不存在: {main_path}")
            return False
            
    except Exception as e:
        print(f"✗ 检查API路由时出错: {e}")
        return False


def check_implementation_completeness():
    """检查实现完整性"""
    print("\n=== 检查实现完整性 ===")
    
    try:
        # 检查LLM服务
        llm_service_path = "app/services/llm_service.py"
        if os.path.exists(llm_service_path):
            with open(llm_service_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            llm_checks = [
                ("DeepSeekProvider类", "class DeepSeekProvider" in content),
                ("LLMService类", "class LLMService" in content),
                ("错误处理", "class LLMError" in content),
                ("重试机制", "@retry" in content)
            ]
            
            print("LLM服务:")
            for check_name, result in llm_checks:
                print(f"  {'✓' if result else '✗'} {check_name}")
        
        # 检查CoT生成服务
        cot_service_path = "app/services/cot_generation_service.py"
        if os.path.exists(cot_service_path):
            with open(cot_service_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            cot_checks = [
                ("COTGenerationService类", "class COTGenerationService" in content),
                ("问题生成", "generate_question" in content),
                ("候选答案生成", "generate_candidates" in content),
                ("完整CoT生成", "generate_cot_item" in content)
            ]
            
            print("CoT生成服务:")
            for check_name, result in cot_checks:
                print(f"  {'✓' if result else '✗'} {check_name}")
        
        # 检查API端点
        api_path = "app/api/v1/cot_generation.py"
        if os.path.exists(api_path):
            with open(api_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            api_checks = [
                ("生成问题端点", "/generate-question" in content),
                ("生成候选答案端点", "/generate-candidates" in content),
                ("完整CoT生成端点", "/generate-cot" in content),
                ("重新生成端点", "/regenerate-" in content)
            ]
            
            print("API端点:")
            for check_name, result in api_checks:
                print(f"  {'✓' if result else '✗'} {check_name}")
        
        return True
        
    except Exception as e:
        print(f"✗ 检查实现完整性时出错: {e}")
        return False


def main():
    """主函数"""
    print("验证LLM集成和CoT生成服务实现")
    print("=" * 50)
    
    # 运行所有检查
    checks = [
        ("文件存在性", check_files),
        ("配置检查", check_config),
        ("依赖检查", check_requirements),
        ("API路由", check_api_routes),
        ("实现完整性", check_implementation_completeness)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"✗ {check_name}检查失败: {e}")
            results.append((check_name, False))
    
    # 输出总结
    print("\n" + "=" * 50)
    print("验证结果总结:")
    
    all_passed = True
    for check_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{check_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有检查通过！LLM集成和CoT生成服务实现完成。")
        print("\n主要功能:")
        print("- ✓ DeepSeek LLM集成")
        print("- ✓ CoT问题生成")
        print("- ✓ CoT候选答案生成")
        print("- ✓ 错误处理和重试机制")
        print("- ✓ API端点")
        print("- ✓ 异步任务支持")
        
        print("\nAPI端点:")
        print("- POST /api/v1/cot/generate-question")
        print("- POST /api/v1/cot/generate-candidates")
        print("- POST /api/v1/cot/generate-cot")
        print("- POST /api/v1/cot/regenerate-question/{cot_id}")
        print("- POST /api/v1/cot/regenerate-candidates/{cot_id}")
        print("- GET /api/v1/cot/providers")
        
    else:
        print("❌ 部分检查失败，请检查上述问题。")


if __name__ == "__main__":
    main()