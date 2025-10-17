"""
LLM服务抽象层
支持多个LLM提供商的统一接口
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
from openai import AsyncOpenAI

from ..core.config import settings


logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """LLM提供商枚举"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    KIMI = "kimi"


@dataclass
class LLMMessage:
    """LLM消息数据类"""
    role: str  # system, user, assistant
    content: str


@dataclass
class LLMResponse:
    """LLM响应数据类"""
    content: str
    provider: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMError(Exception):
    """LLM服务异常"""
    def __init__(self, message: str, provider: str = None, error_code: str = None):
        self.message = message
        self.provider = provider
        self.error_code = error_code
        super().__init__(self.message)


class BaseLLMProvider(ABC):
    """LLM提供商基类"""
    
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.client = None
    
    @abstractmethod
    async def initialize(self):
        """初始化客户端"""
        pass
    
    @abstractmethod
    async def generate_completion(
        self, 
        messages: List[LLMMessage], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """生成文本完成"""
        pass
    
    @abstractmethod
    async def close(self):
        """关闭客户端连接"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI提供商实现"""
    
    async def initialize(self):
        """初始化OpenAI客户端"""
        if not self.api_key:
            raise LLMError("OpenAI API key is required", provider="openai")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=settings.LLM_REQUEST_TIMEOUT
        )
    
    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.LLM_RETRY_DELAY),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def generate_completion(
        self, 
        messages: List[LLMMessage], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """生成OpenAI文本完成"""
        try:
            # 转换消息格式
            openai_messages = [
                {"role": msg.role, "content": msg.content} 
                for msg in messages
            ]
            
            # 调用OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # 提取响应内容
            content = response.choices[0].message.content
            usage = response.usage.model_dump() if response.usage else None
            
            return LLMResponse(
                content=content,
                provider="openai",
                model=self.model,
                usage=usage,
                metadata={"response_id": response.id}
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise LLMError(f"OpenAI API error: {str(e)}", provider="openai")
    
    async def close(self):
        """关闭OpenAI客户端"""
        if self.client:
            await self.client.close()


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek提供商实现"""
    
    async def initialize(self):
        """初始化DeepSeek客户端"""
        if not self.api_key:
            raise LLMError("DeepSeek API key is required", provider="deepseek")
        
        # DeepSeek使用OpenAI兼容的API
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=settings.LLM_REQUEST_TIMEOUT
        )
    
    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.LLM_RETRY_DELAY),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def generate_completion(
        self, 
        messages: List[LLMMessage], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """生成DeepSeek文本完成"""
        try:
            # 转换消息格式
            deepseek_messages = [
                {"role": msg.role, "content": msg.content} 
                for msg in messages
            ]
            
            # 调用DeepSeek API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=deepseek_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # 提取响应内容
            content = response.choices[0].message.content
            usage = response.usage.model_dump() if response.usage else None
            
            return LLMResponse(
                content=content,
                provider="deepseek",
                model=self.model,
                usage=usage,
                metadata={"response_id": response.id}
            )
            
        except Exception as e:
            logger.error(f"DeepSeek API error: {str(e)}")
            raise LLMError(f"DeepSeek API error: {str(e)}", provider="deepseek")
    
    async def close(self):
        """关闭DeepSeek客户端"""
        if self.client:
            await self.client.close()


class KimiProvider(BaseLLMProvider):
    """KIMI提供商实现"""
    
    async def initialize(self):
        """初始化KIMI客户端"""
        if not self.api_key:
            raise LLMError("KIMI API key is required", provider="kimi")
        
        # KIMI使用OpenAI兼容的API
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=settings.LLM_REQUEST_TIMEOUT
        )
    
    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.LLM_RETRY_DELAY),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def generate_completion(
        self, 
        messages: List[LLMMessage], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """生成KIMI文本完成"""
        try:
            # 转换消息格式
            kimi_messages = [
                {"role": msg.role, "content": msg.content} 
                for msg in messages
            ]
            
            # 调用KIMI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=kimi_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # 提取响应内容
            content = response.choices[0].message.content
            usage = response.usage.model_dump() if response.usage else None
            
            return LLMResponse(
                content=content,
                provider="kimi",
                model=self.model,
                usage=usage,
                metadata={"response_id": response.id}
            )
            
        except Exception as e:
            logger.error(f"KIMI API error: {str(e)}")
            raise LLMError(f"KIMI API error: {str(e)}", provider="kimi")
    
    async def close(self):
        """关闭KIMI客户端"""
        if self.client:
            await self.client.close()


class LLMService:
    """LLM服务管理器"""
    
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.default_provider = settings.DEFAULT_LLM_PROVIDER
        self._initialized = False
    
    async def initialize(self):
        """初始化所有可用的LLM提供商"""
        if self._initialized:
            return
        
        # 初始化OpenAI
        if settings.OPENAI_API_KEY:
            openai_provider = OpenAIProvider(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                model=settings.OPENAI_MODEL
            )
            await openai_provider.initialize()
            self.providers["openai"] = openai_provider
            logger.info("OpenAI provider initialized")
        
        # 初始化DeepSeek
        if settings.DEEPSEEK_API_KEY:
            deepseek_provider = DeepSeekProvider(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
                model=settings.DEEPSEEK_MODEL
            )
            await deepseek_provider.initialize()
            self.providers["deepseek"] = deepseek_provider
            logger.info("DeepSeek provider initialized")
        
        # 初始化KIMI
        if settings.KIMI_API_KEY:
            kimi_provider = KimiProvider(
                api_key=settings.KIMI_API_KEY,
                base_url=settings.KIMI_BASE_URL,
                model=settings.KIMI_MODEL
            )
            await kimi_provider.initialize()
            self.providers["kimi"] = kimi_provider
            logger.info("KIMI provider initialized")
        
        if not self.providers:
            raise LLMError("No LLM providers configured")
        
        # 检查默认提供商是否可用
        if self.default_provider not in self.providers:
            self.default_provider = list(self.providers.keys())[0]
            logger.warning(f"Default provider not available, using {self.default_provider}")
        
        self._initialized = True
        logger.info(f"LLM service initialized with providers: {list(self.providers.keys())}")
    
    async def generate_completion(
        self,
        messages: List[LLMMessage],
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """生成文本完成"""
        if not self._initialized:
            await self.initialize()
        
        # 选择提供商
        provider_name = provider or self.default_provider
        if provider_name not in self.providers:
            raise LLMError(f"Provider {provider_name} not available")
        
        provider_instance = self.providers[provider_name]
        
        try:
            return await provider_instance.generate_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error generating completion with {provider_name}: {str(e)}")
            # 如果默认提供商失败，尝试其他提供商
            if provider_name == self.default_provider and len(self.providers) > 1:
                for fallback_provider in self.providers:
                    if fallback_provider != provider_name:
                        try:
                            logger.info(f"Trying fallback provider: {fallback_provider}")
                            return await self.providers[fallback_provider].generate_completion(
                                messages=messages,
                                temperature=temperature,
                                max_tokens=max_tokens,
                                **kwargs
                            )
                        except Exception as fallback_error:
                            logger.error(f"Fallback provider {fallback_provider} also failed: {str(fallback_error)}")
                            continue
            
            raise e
    
    async def close(self):
        """关闭所有提供商连接"""
        for provider in self.providers.values():
            await provider.close()
        self.providers.clear()
        self._initialized = False
        logger.info("LLM service closed")
    
    def get_available_providers(self) -> List[str]:
        """获取可用的提供商列表"""
        return list(self.providers.keys())


# 全局LLM服务实例
llm_service = LLMService()