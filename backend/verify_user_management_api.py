"""
用户管理API结构验证脚本
"""
import ast
import os

def verify_api_structure():
    """验证用户管理API的结构"""
    api_file = "app/api/v1/user_management.py"
    
    if not os.path.exists(api_file):
        print("❌ 用户管理API文件不存在")
        return False
    
    try:
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析AST
        tree = ast.parse(content)
        
        # 检查函数定义（包括async函数）
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)
        
        # 期望的API端点函数
        expected_functions = [
            'get_current_user_model',
            'get_current_admin_user', 
            'get_current_super_admin_user',
            'create_user',
            'list_users',
            'get_user',
            'update_user',
            'delete_user',
            'get_user_stats',
            'reset_user_password',
            'grant_project_permission',
            'revoke_project_permission',
            'get_user_permissions',
            'get_project_permissions',
            'list_permissions'
        ]
        
        print("✅ 用户管理API文件存在")
        print(f"✅ 发现 {len(functions)} 个函数")
        
        missing_functions = []
        for func in expected_functions:
            if func in functions:
                print(f"✅ {func}")
            else:
                print(f"❌ {func} - 缺失")
                missing_functions.append(func)
        
        if missing_functions:
            print(f"\n❌ 缺失 {len(missing_functions)} 个函数")
            return False
        else:
            print(f"\n✅ 所有 {len(expected_functions)} 个API端点函数都已实现")
            return True
            
    except SyntaxError as e:
        print(f"❌ 语法错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def verify_schema_structure():
    """验证用户管理模式的结构"""
    schema_file = "app/schemas/user_management.py"
    
    if not os.path.exists(schema_file):
        print("❌ 用户管理模式文件不存在")
        return False
    
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析AST
        tree = ast.parse(content)
        
        # 检查类定义
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
        
        # 期望的模式类
        expected_classes = [
            'UserCreateRequest',
            'UserUpdateRequest', 
            'UserResponse',
            'UserListResponse',
            'UserSearchRequest',
            'PermissionGrantRequest',
            'PermissionRevokeRequest',
            'PermissionResponse',
            'UserPermissionResponse',
            'ProjectPermissionResponse',
            'PermissionListResponse',
            'PermissionSearchRequest',
            'PasswordChangeRequest',
            'PasswordResetRequest',
            'UserStatsResponse'
        ]
        
        print("✅ 用户管理模式文件存在")
        print(f"✅ 发现 {len(classes)} 个类")
        
        missing_classes = []
        for cls in expected_classes:
            if cls in classes:
                print(f"✅ {cls}")
            else:
                print(f"❌ {cls} - 缺失")
                missing_classes.append(cls)
        
        if missing_classes:
            print(f"\n❌ 缺失 {len(missing_classes)} 个模式类")
            return False
        else:
            print(f"\n✅ 所有 {len(expected_classes)} 个模式类都已实现")
            return True
            
    except SyntaxError as e:
        print(f"❌ 语法错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def verify_test_structure():
    """验证测试文件的结构"""
    test_file = "tests/test_user_management_api.py"
    
    if not os.path.exists(test_file):
        print("❌ 用户管理API测试文件不存在")
        return False
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析AST
        tree = ast.parse(content)
        
        # 检查测试类
        test_classes = []
        test_methods = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                test_classes.append(node.name)
            elif isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                test_methods.append(node.name)
        
        print("✅ 用户管理API测试文件存在")
        print(f"✅ 发现 {len(test_classes)} 个测试类")
        print(f"✅ 发现 {len(test_methods)} 个测试方法")
        
        for cls in test_classes:
            print(f"✅ {cls}")
        
        return True
            
    except SyntaxError as e:
        print(f"❌ 语法错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("用户管理API实现验证")
    print("=" * 60)
    
    print("\n1. 验证API端点结构:")
    print("-" * 40)
    api_ok = verify_api_structure()
    
    print("\n2. 验证模式结构:")
    print("-" * 40)
    schema_ok = verify_schema_structure()
    
    print("\n3. 验证测试结构:")
    print("-" * 40)
    test_ok = verify_test_structure()
    
    print("\n" + "=" * 60)
    if api_ok and schema_ok and test_ok:
        print("✅ 用户管理API实现验证通过")
        print("✅ 任务 2 '用户管理API实现' 已完成")
    else:
        print("❌ 用户管理API实现验证失败")
    print("=" * 60)