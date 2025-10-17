"""
简单的导出功能测试
"""

def test_basic_imports():
    """测试基本导入"""
    try:
        from app.schemas.export import ExportFormat, ExportRequest
        print("✅ 导出模式导入成功")
        
        # 测试创建导出请求
        request = ExportRequest(
            project_id="test",
            format=ExportFormat.JSON
        )
        print(f"✅ 导出请求创建成功: {request.format}")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_service_import():
    """测试服务导入"""
    try:
        from app.services.export_service import ExportService
        print("✅ 导出服务导入成功")
        return True
    except Exception as e:
        print(f"❌ 服务导入失败: {e}")
        return False

if __name__ == "__main__":
    print("🔍 测试导出功能基本组件...")
    
    success = True
    success &= test_basic_imports()
    success &= test_service_import()
    
    if success:
        print("🎉 基本测试通过！")
    else:
        print("❌ 测试失败")