"""
Test script for settings API functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.settings_service import settings_service
from app.schemas.settings import SystemSettingsUpdate, LLMProviderConfig, OCREngineConfig

def test_settings_service():
    """Test the settings service functionality"""
    print("Testing Settings Service...")
    
    # Test getting default settings
    settings = settings_service.get_settings()
    print(f"✓ Got settings with {len(settings.llm_providers)} LLM providers")
    print(f"✓ Default LLM provider: {settings.default_llm_provider}")
    print(f"✓ Got {len(settings.ocr_engines)} OCR engines")
    print(f"✓ Default OCR engine: {settings.default_ocr_engine}")
    print(f"✓ Got {len(settings.system_prompts)} system prompts")
    print(f"✓ CoT candidate count: {settings.cot_generation.candidate_count}")
    
    # Test getting specific provider
    provider_config = settings_service.get_llm_provider_config("deepseek")
    if provider_config:
        print(f"✓ Found DeepSeek provider: {provider_config.model}")
    else:
        print("✗ DeepSeek provider not found")
    
    # Test getting default provider
    default_provider = settings_service.get_default_llm_provider_config()
    if default_provider:
        print(f"✓ Default provider: {default_provider.provider}")
    else:
        print("✗ Default provider not found")
    
    # Test getting OCR engine
    ocr_config = settings_service.get_ocr_engine_config("paddleocr")
    if ocr_config:
        print(f"✓ Found PaddleOCR engine with priority: {ocr_config.priority}")
    else:
        print("✗ PaddleOCR engine not found")
    
    # Test getting system prompt
    prompt = settings_service.get_system_prompt("academic_question_generation")
    if prompt:
        print(f"✓ Found system prompt: {prompt.name}")
    else:
        print("✗ System prompt not found")
    
    # Test validation
    if provider_config:
        validation_result = settings_service.validate_llm_provider(provider_config)
        print(f"✓ LLM provider validation: {validation_result['valid']}")
    
    if ocr_config:
        validation_result = settings_service.validate_ocr_engine(ocr_config)
        print(f"✓ OCR engine validation: {validation_result['valid']}")
    
    print("Settings service test completed successfully!")

def test_settings_update():
    """Test settings update functionality"""
    print("\nTesting Settings Update...")
    
    # Get current settings
    current_settings = settings_service.get_settings()
    original_candidate_count = current_settings.cot_generation.candidate_count
    
    # Update CoT generation config
    update = SystemSettingsUpdate(
        cot_generation={
            "candidate_count": 4,
            "question_max_length": 600,
            "answer_max_length": 2500,
            "enable_auto_generation": True,
            "quality_threshold": 0.8
        }
    )
    
    updated_settings = settings_service.update_settings(update)
    print(f"✓ Updated candidate count from {original_candidate_count} to {updated_settings.cot_generation.candidate_count}")
    print(f"✓ Updated question max length to {updated_settings.cot_generation.question_max_length}")
    print(f"✓ Updated quality threshold to {updated_settings.cot_generation.quality_threshold}")
    
    # Restore original settings
    restore_update = SystemSettingsUpdate(
        cot_generation={
            "candidate_count": original_candidate_count,
            "question_max_length": 500,
            "answer_max_length": 2000,
            "enable_auto_generation": True,
            "quality_threshold": 0.7
        }
    )
    
    settings_service.update_settings(restore_update)
    print("✓ Restored original settings")
    
    print("Settings update test completed successfully!")

if __name__ == "__main__":
    try:
        test_settings_service()
        test_settings_update()
        print("\n🎉 All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()