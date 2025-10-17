print("Starting OCR verification...")

try:
    print("1. Testing basic imports...")
    import sys
    import os
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    print("2. Testing app imports...")
    from app.services.ocr_service import FallbackOCREngine
    print("✓ FallbackOCREngine imported")
    
    print("3. Testing engine creation...")
    engine = FallbackOCREngine()
    print(f"✓ Engine created, available: {engine.is_available()}")
    
    print("4. Testing text extraction...")
    test_text = "Hello World"
    result = engine.extract_text(test_text.encode('utf-8'), "test.txt")
    print(f"✓ Text extracted: '{result.full_text}'")
    
    print("5. Testing slice models...")
    from app.models.slice import SliceType
    print(f"✓ SliceType imported: {SliceType.PARAGRAPH}")
    
    print("\n🎉 OCR verification completed successfully!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()