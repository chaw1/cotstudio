from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.core.permissions import PermissionChecker, PermissionError
from app.schemas.settings import (
    SystemSettings,
    SystemSettingsUpdate,
    SettingsResponse,
    SettingsUpdateResponse,
    LLMProviderConfig,
    OCREngineConfig,
    SystemPromptTemplate
)
from app.services.settings_service import settings_service
from app.core.app_logging import logger

router = APIRouter()


async def get_current_user_model(
    current_user_data: Dict[str, Any] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户的数据库模型对象"""
    from app.services.user_service import user_service
    user = user_service.get(db, current_user_data["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


def get_current_admin_user(
    current_user: User = Depends(get_current_user_model)
) -> User:
    """获取当前管理员用户"""
    if not PermissionChecker.check_admin_permission_sync(current_user):
        raise PermissionError("需要管理员权限访问系统设置")
    return current_user


@router.get("/settings", response_model=SettingsResponse)
async def get_system_settings(
    current_user: User = Depends(get_current_admin_user)
):
    """获取系统设置（需要管理员权限）"""
    try:
        settings = settings_service.get_settings()
        return SettingsResponse(settings=settings)
    except Exception as e:
        logger.error(f"Failed to get system settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system settings")


@router.put("/settings", response_model=SettingsUpdateResponse)
async def update_system_settings(
    settings_update: SystemSettingsUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    """更新系统设置（需要管理员权限）"""
    try:
        updated_settings = settings_service.update_settings(settings_update)
        return SettingsUpdateResponse(settings=updated_settings)
    except ValueError as e:
        logger.error(f"Invalid settings update: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update system settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update system settings")


@router.post("/settings/reset")
async def reset_system_settings(
    current_user: User = Depends(get_current_admin_user)
):
    """重置系统设置为默认值（需要管理员权限）"""
    try:
        default_settings = settings_service.reset_to_defaults()
        return SettingsResponse(
            settings=default_settings,
            message="Settings reset to defaults successfully"
        )
    except Exception as e:
        logger.error(f"Failed to reset system settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset system settings")


@router.get("/settings/llm-providers")
async def get_llm_providers():
    """获取LLM提供商配置"""
    try:
        settings = settings_service.get_settings()
        return {
            "providers": settings.llm_providers,
            "default_provider": settings.default_llm_provider,
            "enabled_providers": settings_service.get_enabled_llm_providers()
        }
    except Exception as e:
        logger.error(f"Failed to get LLM providers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve LLM providers")


@router.get("/settings/llm-providers/{provider}")
async def get_llm_provider(provider: str):
    """获取指定LLM提供商配置"""
    try:
        provider_config = settings_service.get_llm_provider_config(provider)
        if not provider_config:
            raise HTTPException(status_code=404, detail=f"LLM provider '{provider}' not found")
        return provider_config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get LLM provider {provider}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve LLM provider")


@router.post("/settings/llm-providers/{provider}/validate")
async def validate_llm_provider(provider: str, provider_config: LLMProviderConfig):
    """验证LLM提供商配置"""
    try:
        validation_result = settings_service.validate_llm_provider(provider_config)
        return validation_result
    except Exception as e:
        logger.error(f"Failed to validate LLM provider {provider}: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate LLM provider")


@router.get("/settings/ocr-engines")
async def get_ocr_engines():
    """获取OCR引擎配置"""
    try:
        settings = settings_service.get_settings()
        return {
            "engines": settings.ocr_engines,
            "default_engine": settings.default_ocr_engine,
            "enabled_engines": settings_service.get_enabled_ocr_engines()
        }
    except Exception as e:
        logger.error(f"Failed to get OCR engines: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve OCR engines")


@router.get("/settings/ocr-engines/{engine}")
async def get_ocr_engine(engine: str):
    """获取指定OCR引擎配置"""
    try:
        engine_config = settings_service.get_ocr_engine_config(engine)
        if not engine_config:
            raise HTTPException(status_code=404, detail=f"OCR engine '{engine}' not found")
        return engine_config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get OCR engine {engine}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve OCR engine")


@router.post("/settings/ocr-engines/{engine}/validate")
async def validate_ocr_engine(engine: str, engine_config: OCREngineConfig):
    """验证OCR引擎配置"""
    try:
        validation_result = settings_service.validate_ocr_engine(engine_config)
        return validation_result
    except Exception as e:
        logger.error(f"Failed to validate OCR engine {engine}: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate OCR engine")


@router.get("/settings/system-prompts")
async def get_system_prompts():
    """获取系统提示词模板"""
    try:
        settings = settings_service.get_settings()
        return {
            "prompts": settings.system_prompts,
            "categories": list(set(p.category for p in settings.system_prompts))
        }
    except Exception as e:
        logger.error(f"Failed to get system prompts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system prompts")


@router.get("/settings/system-prompts/category/{category}")
async def get_system_prompts_by_category(category: str):
    """根据分类获取系统提示词模板"""
    try:
        prompts = settings_service.get_system_prompts_by_category(category)
        default_prompt = settings_service.get_default_system_prompt(category)
        return {
            "prompts": prompts,
            "default_prompt": default_prompt,
            "category": category
        }
    except Exception as e:
        logger.error(f"Failed to get system prompts for category {category}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system prompts")


@router.get("/settings/system-prompts/{name}")
async def get_system_prompt(name: str):
    """获取指定系统提示词模板"""
    try:
        prompt = settings_service.get_system_prompt(name)
        if not prompt:
            raise HTTPException(status_code=404, detail=f"System prompt '{name}' not found")
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get system prompt {name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system prompt")


@router.get("/settings/cot-generation")
async def get_cot_generation_config():
    """获取CoT生成配置"""
    try:
        settings = settings_service.get_settings()
        return settings.cot_generation
    except Exception as e:
        logger.error(f"Failed to get CoT generation config: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve CoT generation config")


@router.get("/settings/export")
async def export_settings():
    """导出系统设置"""
    try:
        settings_data = settings_service.export_settings()
        return {
            "settings": settings_data,
            "export_time": "2024-01-01T00:00:00Z",
            "version": "1.0"
        }
    except Exception as e:
        logger.error(f"Failed to export settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to export settings")


@router.post("/settings/import")
async def import_settings(settings_data: Dict[str, Any]):
    """导入系统设置"""
    try:
        imported_settings = settings_service.import_settings(settings_data)
        return SettingsResponse(
            settings=imported_settings,
            message="Settings imported successfully"
        )
    except ValueError as e:
        logger.error(f"Invalid settings import data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to import settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to import settings")