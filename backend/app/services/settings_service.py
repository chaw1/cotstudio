import json
import os
from typing import Optional, Dict, Any
from pathlib import Path

from app.core.config import settings as app_settings
from app.schemas.settings import (
    SystemSettings,
    SystemSettingsUpdate,
    DEFAULT_SETTINGS,
    LLMProviderConfig,
    OCREngineConfig,
    SystemPromptTemplate,
    COTGenerationConfig
)
from app.core.app_logging import logger


class SettingsService:
    """系统设置服务"""
    
    def __init__(self):
        self.settings_file = Path("settings.json")
        self._cached_settings: Optional[SystemSettings] = None
    
    def get_settings(self) -> SystemSettings:
        """获取系统设置"""
        if self._cached_settings is None:
            self._load_settings()
        return self._cached_settings
    
    def update_settings(self, settings_update: SystemSettingsUpdate) -> SystemSettings:
        """更新系统设置"""
        current_settings = self.get_settings()
        
        # 更新各个配置项
        if settings_update.llm_providers is not None:
            current_settings.llm_providers = settings_update.llm_providers
        
        if settings_update.default_llm_provider is not None:
            current_settings.default_llm_provider = settings_update.default_llm_provider
        
        if settings_update.ocr_engines is not None:
            current_settings.ocr_engines = settings_update.ocr_engines
        
        if settings_update.default_ocr_engine is not None:
            current_settings.default_ocr_engine = settings_update.default_ocr_engine
        
        if settings_update.system_prompts is not None:
            current_settings.system_prompts = settings_update.system_prompts
        
        if settings_update.cot_generation is not None:
            current_settings.cot_generation = settings_update.cot_generation
        
        # 保存设置
        self._save_settings(current_settings)
        self._cached_settings = current_settings
        
        logger.info("System settings updated successfully")
        return current_settings
    
    def get_llm_provider_config(self, provider: str) -> Optional[LLMProviderConfig]:
        """获取指定LLM提供商配置"""
        settings = self.get_settings()
        for provider_config in settings.llm_providers:
            if provider_config.provider == provider:
                return provider_config
        return None
    
    def get_default_llm_provider_config(self) -> Optional[LLMProviderConfig]:
        """获取默认LLM提供商配置"""
        settings = self.get_settings()
        return self.get_llm_provider_config(settings.default_llm_provider)
    
    def get_ocr_engine_config(self, engine: str) -> Optional[OCREngineConfig]:
        """获取指定OCR引擎配置"""
        settings = self.get_settings()
        for engine_config in settings.ocr_engines:
            if engine_config.engine == engine:
                return engine_config
        return None
    
    def get_default_ocr_engine_config(self) -> Optional[OCREngineConfig]:
        """获取默认OCR引擎配置"""
        settings = self.get_settings()
        return self.get_ocr_engine_config(settings.default_ocr_engine)
    
    def get_enabled_llm_providers(self) -> list[LLMProviderConfig]:
        """获取启用的LLM提供商"""
        settings = self.get_settings()
        return [p for p in settings.llm_providers if p.enabled]
    
    def get_enabled_ocr_engines(self) -> list[OCREngineConfig]:
        """获取启用的OCR引擎"""
        settings = self.get_settings()
        return [e for e in settings.ocr_engines if e.enabled]
    
    def get_system_prompt(self, name: str) -> Optional[SystemPromptTemplate]:
        """获取指定系统提示词模板"""
        settings = self.get_settings()
        for prompt in settings.system_prompts:
            if prompt.name == name:
                return prompt
        return None
    
    def get_system_prompts_by_category(self, category: str) -> list[SystemPromptTemplate]:
        """根据分类获取系统提示词模板"""
        settings = self.get_settings()
        return [p for p in settings.system_prompts if p.category == category]
    
    def get_default_system_prompt(self, category: str) -> Optional[SystemPromptTemplate]:
        """获取指定分类的默认系统提示词模板"""
        prompts = self.get_system_prompts_by_category(category)
        for prompt in prompts:
            if prompt.is_default:
                return prompt
        return prompts[0] if prompts else None
    
    def reset_to_defaults(self) -> SystemSettings:
        """重置为默认设置"""
        self._cached_settings = DEFAULT_SETTINGS.copy(deep=True)
        self._save_settings(self._cached_settings)
        logger.info("System settings reset to defaults")
        return self._cached_settings
    
    def validate_llm_provider(self, provider_config: LLMProviderConfig) -> Dict[str, Any]:
        """验证LLM提供商配置"""
        # 这里可以添加实际的API连接测试
        # 目前只做基本验证
        result = {
            "valid": True,
            "message": "Configuration appears valid",
            "details": {}
        }
        
        if not provider_config.api_key and provider_config.provider != "local":
            result["valid"] = False
            result["message"] = "API key is required for this provider"
        
        if not provider_config.base_url:
            result["valid"] = False
            result["message"] = "Base URL is required"
        
        return result
    
    def validate_ocr_engine(self, engine_config: OCREngineConfig) -> Dict[str, Any]:
        """验证OCR引擎配置"""
        # 这里可以添加实际的引擎可用性检测
        result = {
            "valid": True,
            "message": "Configuration appears valid",
            "details": {}
        }
        
        # 基本参数验证
        if engine_config.engine == "paddleocr":
            if "lang" not in engine_config.parameters:
                result["details"]["warning"] = "Language parameter not specified, using default"
        
        return result
    
    def _load_settings(self):
        """从文件加载设置"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
                self._cached_settings = SystemSettings(**settings_data)
                logger.info("Settings loaded from file")
            except Exception as e:
                logger.error(f"Failed to load settings from file: {e}")
                self._cached_settings = DEFAULT_SETTINGS.copy(deep=True)
        else:
            logger.info("Settings file not found, using defaults")
            self._cached_settings = DEFAULT_SETTINGS.copy(deep=True)
    
    def _save_settings(self, settings: SystemSettings):
        """保存设置到文件"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings.dict(), f, indent=2, ensure_ascii=False)
            logger.info("Settings saved to file")
        except Exception as e:
            logger.error(f"Failed to save settings to file: {e}")
            raise
    
    def export_settings(self) -> Dict[str, Any]:
        """导出设置（用于备份）"""
        settings = self.get_settings()
        return settings.dict()
    
    def import_settings(self, settings_data: Dict[str, Any]) -> SystemSettings:
        """导入设置（用于恢复）"""
        try:
            imported_settings = SystemSettings(**settings_data)
            self._cached_settings = imported_settings
            self._save_settings(imported_settings)
            logger.info("Settings imported successfully")
            return imported_settings
        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            raise ValueError(f"Invalid settings data: {e}")


# 全局设置服务实例
settings_service = SettingsService()