"""
简单OCR测试
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试导入"""
    try:
        from app.services.ocr_service import FallbackOCREngine, ocr_service
        print("✓ OCR service imports successful")
        
        from app.services.slice_service import DocumentSlicer, slice_service
        print("✓ Slice service imports successful")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_fallback_engine():
    """测试回退引擎"""
    try:
        from app.services.ocr_service import FallbackOCREngine
        
        engine = FallbackOCREngine()
        print(f"✓ Fallback engine created, available: {engine.is_available()}")
        
        # 测试文本提取
        test_text = "Hello, World!\n\nThis is a test document."
        result = engine.extract_text(test_text.encode('utf-8'), "test.txt")
        
        print(f"✓ Text extracted, length: {len(result.full_text)}")
        print(f"✓ Pages: {result.total_pages}")
        print(f"✓ Text blocks: {len(result.text_blocks)}")
        
        return True
    except Exception as e:
        print(f"❌ Fallback engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=== Simple OCR Test ===")
    
    if not test_imports():
        return 1
    
    if not test_fallback_engine():
        return 1
    
    print("✓ All tests passed!")
    return 0

if __name__ == "__main__":
    exit(main())