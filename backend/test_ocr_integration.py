"""
OCR集成测试
"""
import os
import sys
import tempfile
from io import BytesIO

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ocr_service import ocr_service, FallbackOCREngine
from app.services.slice_service import DocumentSlicer
from app.models.file import File
from app.models.slice import SliceType


def test_fallback_ocr_engine():
    """测试回退OCR引擎"""
    print("Testing Fallback OCR Engine...")
    
    # 创建测试文本
    test_text = """# 测试文档标题

这是第一个段落，包含一些中文文本。这个段落用于测试OCR引擎的基本文本提取功能。

这是第二个段落。它包含更多的内容，用于测试段落分割功能。

## 子标题

这是子标题下的内容。

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |

页脚信息 - 第1页
"""
    
    # 测试回退引擎
    engine = FallbackOCREngine()
    assert engine.is_available(), "Fallback engine should always be available"
    
    # 提取文本
    file_content = test_text.encode('utf-8')
    result = engine.extract_text(file_content, "test.txt")
    
    print(f"Extracted text length: {len(result.full_text)}")
    print(f"Total pages: {result.total_pages}")
    print(f"Text blocks count: {len(result.text_blocks)}")
    
    assert result.full_text == test_text, "Text should match exactly"
    assert result.total_pages == 1, "Should have 1 page"
    assert len(result.text_blocks) == 1, "Should have 1 text block"
    
    print("✓ Fallback OCR engine test passed")


def test_document_slicer():
    """测试文档切片器"""
    print("\nTesting Document Slicer...")
    
    # 创建测试文档结构
    test_text = """# 主标题

这是第一个段落。包含一些测试内容。

这是第二个段落。

## 子标题

子标题下的内容。

| 表格 | 数据 |
|------|------|
| 行1  | 值1  |

页脚 - 第1页"""
    
    # 使用回退引擎提取文档结构
    engine = FallbackOCREngine()
    document = engine.extract_text(test_text.encode('utf-8'), "test.md")
    
    # 创建模拟文件记录
    class MockFile:
        def __init__(self):
            self.id = "test-file-id"
            self.filename = "test.md"
    
    file_record = MockFile()
    
    # 测试切片器
    slicer = DocumentSlicer()
    slices = slicer.slice_document(document, file_record)
    
    print(f"Generated {len(slices)} slices")
    
    # 验证切片
    assert len(slices) > 0, "Should generate at least one slice"
    
    # 检查切片类型
    slice_types = [slice_obj.slice_type for slice_obj in slices]
    print(f"Slice types: {[t.value for t in slice_types]}")
    
    # 应该包含标题和段落
    has_header = any(t == SliceType.HEADER for t in slice_types)
    has_paragraph = any(t == SliceType.PARAGRAPH for t in slice_types)
    
    print(f"Has header slices: {has_header}")
    print(f"Has paragraph slices: {has_paragraph}")
    
    # 打印前几个切片的内容
    for i, slice_obj in enumerate(slices[:3]):
        print(f"Slice {i+1} ({slice_obj.slice_type.value}): {slice_obj.content[:50]}...")
    
    print("✓ Document slicer test passed")


def test_ocr_service():
    """测试OCR服务"""
    print("\nTesting OCR Service...")
    
    # 获取可用引擎
    available_engines = ocr_service.get_available_engines()
    print(f"Available engines: {available_engines}")
    
    assert 'fallback' in available_engines, "Fallback engine should be available"
    
    # 测试文本提取
    test_content = "这是一个简单的测试文档。\n\n包含多个段落。"
    file_content = test_content.encode('utf-8')
    
    result = ocr_service.extract_text(file_content, "test.txt", "fallback")
    
    print(f"OCR result text length: {len(result.full_text)}")
    assert result.full_text == test_content, "OCR should extract text correctly"
    
    print("✓ OCR service test passed")


def test_pdf_processing_availability():
    """测试PDF处理能力"""
    print("\nTesting PDF processing availability...")
    
    try:
        from app.services.ocr_service import PaddleOCREngine
        paddle_engine = PaddleOCREngine()
        
        if paddle_engine.is_available():
            print("✓ PaddleOCR is available")
        else:
            print("⚠ PaddleOCR is not available (this is expected in test environment)")
        
        # 检查PDF依赖
        try:
            import pdf2image
            print("✓ pdf2image is available")
        except ImportError:
            print("⚠ pdf2image is not available")
        
        try:
            from PIL import Image
            print("✓ PIL (Pillow) is available")
        except ImportError:
            print("⚠ PIL (Pillow) is not available")
            
    except ImportError as e:
        print(f"⚠ PaddleOCR dependencies not available: {e}")


def main():
    """运行所有测试"""
    print("=== OCR Integration Tests ===\n")
    
    try:
        test_fallback_ocr_engine()
        test_document_slicer()
        test_ocr_service()
        test_pdf_processing_availability()
        
        print("\n=== All Tests Completed ===")
        print("✓ Basic OCR functionality is working")
        print("✓ Document slicing is working")
        print("✓ OCR service integration is working")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())