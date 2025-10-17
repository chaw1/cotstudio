#!/usr/bin/env python3

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("Verifying Settings Implementation...")
    
    try:
        # Test schema imports
        from app.schemas.settings import SystemSettings, DEFAULT_SETTINGS
        print("✓ Settings schemas imported successfully")
        
        # Test service import
        from app.services.settings_service import settings_service
        print("✓ Settings service imported successfully")
        
        # Test API import
        from app.api.v1.settings import router
        print("✓ Settings API router imported successfully")
        
        # Test default settings
        default_settings = DEFAULT_SETTINGS
        print(f"✓ Default settings loaded with {len(default_settings.llm_providers)} LLM providers")
        print(f"✓ Default LLM provider: {default_settings.default_llm_provider}")
        print(f"✓ Default OCR engine: {default_settings.default_ocr_engine}")
        print(f"✓ System prompts: {len(default_settings.system_prompts)}")
        print(f"✓ CoT candidate count: {default_settings.cot_generation.candidate_count}")
        
        # Test service functionality
        settings = settings_service.get_settings()
        print(f"✓ Settings service working, got {len(settings.llm_providers)} providers")
        
        print("\n🎉 All settings components verified successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)