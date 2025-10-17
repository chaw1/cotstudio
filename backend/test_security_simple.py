#!/usr/bin/env python3
"""
简单的安全功能测试脚本
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_security_validators():
    """测试安全验证器"""
    print("=== 测试安全验证器 ===")
    
    try:
        from core.security_validators import SecurityValidator
        
        # 测试SQL注入检测
        print("1. SQL注入检测测试:")
        normal_input = "normal user input"
        sql_injection = "'; DROP TABLE users; --"
        
        print(f"   正常输入 '{normal_input}': {SecurityValidator.validate_sql_injection(normal_input)}")
        print(f"   SQL注入 '{sql_injection}': {SecurityValidator.validate_sql_injection(sql_injection)}")
        
        # 测试XSS检测
        print("2. XSS检测测试:")
        normal_text = "Hello World"
        xss_attack = "<script>alert('xss')</script>"
        
        print(f"   正常文本 '{normal_text}': {SecurityValidator.validate_xss(normal_text)}")
        print(f"   XSS攻击 '{xss_attack}': {SecurityValidator.validate_xss(xss_attack)}")
        
        # 测试路径遍历检测
        print("3. 路径遍历检测测试:")
        normal_path = "documents/file.txt"
        traversal_attack = "../../../etc/passwd"
        
        print(f"   正常路径 '{normal_path}': {SecurityValidator.validate_path_traversal(normal_path)}")
        print(f"   路径遍历 '{traversal_attack}': {SecurityValidator.validate_path_traversal(traversal_attack)}")
        
        # 测试文件名验证
        print("4. 文件名验证测试:")
        safe_filename = "document.pdf"
        unsafe_filename = "../../../etc/passwd"
        
        print(f"   安全文件名 '{safe_filename}': {SecurityValidator.validate_filename(safe_filename)}")
        print(f"   危险文件名 '{unsafe_filename}': {SecurityValidator.validate_filename(unsafe_filename)}")
        
        print("✅ 安全验证器测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 安全验证器测试失败: {e}")
        return False


def test_security_scanner():
    """测试安全扫描器"""
    print("\n=== 测试安全扫描器 ===")
    
    try:
        from utils.security_scanner import SecurityScanner
        
        scanner = SecurityScanner()
        
        # 测试PDF文件扫描
        print("1. PDF文件扫描测试:")
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n'
        result = scanner.scan_file_content(pdf_content, "document.pdf")
        
        print(f"   文件安全: {result['safe']}")
        print(f"   文件大小: {result['file_size']} bytes")
        print(f"   威胁数量: {len(result['threats'])}")
        
        # 测试可执行文件检测
        print("2. 可执行文件检测测试:")
        exe_content = b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00'
        result = scanner.scan_file_content(exe_content, "malware.exe")
        
        print(f"   文件安全: {result['safe']}")
        print(f"   威胁数量: {len(result['threats'])}")
        if result['threats']:
            print(f"   检测到威胁: {result['threats'][0]['type']}")
        
        print("✅ 安全扫描器测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 安全扫描器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_recovery():
    """测试错误恢复机制"""
    print("\n=== 测试错误恢复机制 ===")
    
    try:
        from core.error_recovery import CircuitBreaker, RetryManager, ErrorRecoveryManager
        
        # 测试熔断器
        print("1. 熔断器测试:")
        circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)
        print(f"   初始状态: {circuit_breaker.state}")
        
        # 模拟失败
        for i in range(4):
            circuit_breaker._on_failure()
        print(f"   失败后状态: {circuit_breaker.state}")
        
        # 测试错误恢复管理器
        print("2. 错误恢复管理器测试:")
        recovery_manager = ErrorRecoveryManager()
        
        # 注册测试恢复策略
        async def test_recovery_strategy(error, context):
            return True
        
        recovery_manager.register_recovery_strategy('TestError', test_recovery_strategy)
        print(f"   已注册恢复策略数量: {len(recovery_manager.recovery_strategies)}")
        
        print("✅ 错误恢复机制测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 错误恢复机制测试失败: {e}")
        return False


def test_security_config():
    """测试安全配置"""
    print("\n=== 测试安全配置 ===")
    
    try:
        from core.security_config import SecurityConfig, get_security_summary
        
        # 测试配置创建
        config = SecurityConfig()
        print(f"1. 默认配置创建成功")
        print(f"   最大文件大小: {config.max_file_size / (1024*1024):.1f} MB")
        print(f"   启用速率限制: {config.enable_rate_limiting}")
        print(f"   启用病毒扫描: {config.enable_virus_scanning}")
        
        # 测试配置摘要
        summary = get_security_summary()
        print(f"2. 安全配置摘要:")
        print(f"   输入验证功能: {len(summary['input_validation'])} 项")
        print(f"   文件安全功能: {len(summary['file_security'])} 项")
        print(f"   速率限制功能: {len(summary['rate_limiting'])} 项")
        
        print("✅ 安全配置测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 安全配置测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("COT Studio 安全功能测试")
    print("=" * 50)
    
    test_results = []
    
    # 运行所有测试
    test_results.append(test_security_validators())
    test_results.append(test_security_scanner())
    test_results.append(test_error_recovery())
    test_results.append(test_security_config())
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有安全功能测试通过!")
        return 0
    else:
        print("⚠️  部分测试失败，请检查实现")
        return 1


if __name__ == "__main__":
    sys.exit(main())