"""
测试OCR任务集成
"""
import os
import sys
import tempfile
import sqlite3
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ocr_task_imports():
    """测试OCR任务相关的导入"""
    print("Testing OCR task imports...")
    
    try:
        # 测试基础导入
        from app.workers.tasks import ocr_processing
        print("✓ OCR processing task imported")
        
        from app.services.ocr_service import ocr_service
        print("✓ OCR service imported")
        
        from app.services.slice_service import slice_service
        print("✓ Slice service imported")
        
        from app.models.file import File, OCRStatus
        print("✓ File model imported")
        
        from app.models.slice import Slice, SliceType
        print("✓ Slice model imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ocr_service_basic():
    """测试OCR服务基本功能"""
    print("\nTesting OCR service basic functionality...")
    
    try:
        from app.services.ocr_service import ocr_service, FallbackOCREngine
        
        # 测试引擎可用性
        engines = ocr_service.get_available_engines()
        print(f"✓ Available engines: {engines}")
        
        # 测试回退引擎
        engine = FallbackOCREngine()
        assert engine.is_available(), "Fallback engine should be available"
        
        # 测试文本提取
        test_text = """# 测试标题

这是第一段内容。

这是第二段内容。

## 子标题

子标题下的内容。"""
        
        result = engine.extract_text(test_text.encode('utf-8'), "test.md")
        
        print(f"✓ Text extracted: {len(result.full_text)} characters")
        print(f"✓ Pages: {result.total_pages}")
        print(f"✓ Text blocks: {len(result.text_blocks)}")
        
        assert result.full_text == test_text, "Text should match"
        assert result.total_pages == 1, "Should have 1 page"
        
        return True
        
    except Exception as e:
        print(f"❌ OCR service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_slice_service_basic():
    """测试切片服务基本功能"""
    print("\nTesting slice service basic functionality...")
    
    try:
        from app.services.slice_service import DocumentSlicer
        from app.services.ocr_service import FallbackOCREngine
        
        # 创建测试文档
        test_text = """# 主标题

第一段内容，包含一些测试文本。

第二段内容，用于测试切片功能。

## 子标题

子标题下的内容。

表格内容：
| 列1 | 列2 |
|-----|-----|
| 值1 | 值2 |"""
        
        # 提取文档结构
        engine = FallbackOCREngine()
        document = engine.extract_text(test_text.encode('utf-8'), "test.md")
        
        # 创建模拟文件对象
        class MockFile:
            def __init__(self):
                self.id = "test-file-123"
                self.filename = "test.md"
        
        file_obj = MockFile()
        
        # 测试切片
        slicer = DocumentSlicer()
        slices = slicer.slice_document(document, file_obj)
        
        print(f"✓ Generated {len(slices)} slices")
        
        # 验证切片
        assert len(slices) > 0, "Should generate slices"
        
        # 打印切片信息
        for i, slice_obj in enumerate(slices[:3]):
            print(f"  Slice {i+1}: {slice_obj.slice_type.value} - {slice_obj.content[:30]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Slice service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_models():
    """测试数据库模型"""
    print("\nTesting database models...")
    
    try:
        from app.models.file import File, OCRStatus
        from app.models.slice import Slice, SliceType
        from app.models.base import Base
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # 创建内存数据库
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        print("✓ Database tables created")
        
        # 测试创建文件记录
        file_data = {
            'project_id': 'test-project-123',
            'filename': 'test.txt',
            'original_filename': 'test.txt',
            'file_path': '/test/path/test.txt',
            'file_hash': 'abcd1234',
            'size': 1024,
            'mime_type': 'text/plain',
            'ocr_status': OCRStatus.PENDING
        }
        
        file_record = File(**file_data)
        db.add(file_record)
        db.commit()
        db.refresh(file_record)
        
        print(f"✓ File record created: {file_record.id}")
        
        # 测试创建切片记录
        slice_data = {
            'file_id': file_record.id,
            'content': 'Test slice content',
            'slice_type': SliceType.PARAGRAPH,
            'page_number': 1,
            'sequence_number': 1,
            'start_offset': 0,
            'end_offset': 18
        }
        
        slice_record = Slice(**slice_data)
        db.add(slice_record)
        db.commit()
        db.refresh(slice_record)
        
        print(f"✓ Slice record created: {slice_record.id}")
        
        # 验证关系
        file_slices = db.query(Slice).filter(Slice.file_id == file_record.id).all()
        assert len(file_slices) == 1, "Should have one slice"
        
        print("✓ Database relationships working")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("=== OCR Task Integration Test ===\n")
    
    tests = [
        test_ocr_task_imports,
        test_ocr_service_basic,
        test_slice_service_basic,
        test_database_models
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✓ PASSED\n")
            else:
                failed += 1
                print("❌ FAILED\n")
        except Exception as e:
            failed += 1
            print(f"❌ FAILED with exception: {e}\n")
    
    print(f"=== Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! OCR integration is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit(main())