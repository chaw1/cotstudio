from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator


class LLMProviderConfig(BaseModel):
    """LLM提供商配置"""
    provider: str = Field(..., description="提供商名称")
    api_key: Optional[str] = Field(None, description="API密钥")
    base_url: str = Field(..., description="API基础URL")
    model: str = Field(..., description="模型名称")
    enabled: bool = Field(True, description="是否启用")
    timeout: int = Field(60, description="请求超时时间(秒)")
    max_retries: int = Field(3, description="最大重试次数")
    retry_delay: float = Field(1.0, description="重试延迟(秒)")
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed_providers = ['openai', 'deepseek', 'kimi', 'claude', 'gemini']
        if v.lower() not in allowed_providers:
            raise ValueError(f'Provider must be one of: {allowed_providers}')
        return v.lower()


class OCREngineConfig(BaseModel):
    """OCR引擎配置"""
    engine: str = Field(..., description="OCR引擎名称")
    enabled: bool = Field(True, description="是否启用")
    priority: int = Field(1, description="优先级(数字越小优先级越高)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="引擎参数")
    
    @validator('engine')
    def validate_engine(cls, v):
        allowed_engines = ['paddleocr', 'mineru', 'alibaba_advanced']
        if v.lower() not in allowed_engines:
            raise ValueError(f'Engine must be one of: {allowed_engines}')
        return v.lower()


class SystemPromptTemplate(BaseModel):
    """系统提示词模板"""
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    template: str = Field(..., description="提示词模板内容")
    variables: List[str] = Field(default_factory=list, description="模板变量")
    category: str = Field("general", description="模板分类")
    is_default: bool = Field(False, description="是否为默认模板")


class COTGenerationConfig(BaseModel):
    """CoT生成配置"""
    candidate_count: int = Field(3, ge=2, le=5, description="候选答案数量")
    question_max_length: int = Field(500, ge=50, le=1000, description="问题最大长度")
    answer_max_length: int = Field(2000, ge=100, le=5000, description="答案最大长度")
    enable_auto_generation: bool = Field(True, description="是否启用自动生成")
    quality_threshold: float = Field(0.7, ge=0.0, le=1.0, description="质量阈值")


class SystemSettings(BaseModel):
    """系统设置"""
    llm_providers: List[LLMProviderConfig] = Field(default_factory=list, description="LLM提供商配置")
    default_llm_provider: str = Field("deepseek", description="默认LLM提供商")
    ocr_engines: List[OCREngineConfig] = Field(default_factory=list, description="OCR引擎配置")
    default_ocr_engine: str = Field("paddleocr", description="默认OCR引擎")
    system_prompts: List[SystemPromptTemplate] = Field(default_factory=list, description="系统提示词模板")
    cot_generation: COTGenerationConfig = Field(default_factory=COTGenerationConfig, description="CoT生成配置")
    
    @validator('default_llm_provider')
    def validate_default_llm_provider(cls, v, values):
        if 'llm_providers' in values:
            provider_names = [p.provider for p in values['llm_providers']]
            if v not in provider_names:
                raise ValueError(f'Default LLM provider must be one of configured providers: {provider_names}')
        return v
    
    @validator('default_ocr_engine')
    def validate_default_ocr_engine(cls, v, values):
        if 'ocr_engines' in values:
            engine_names = [e.engine for e in values['ocr_engines']]
            if v not in engine_names:
                raise ValueError(f'Default OCR engine must be one of configured engines: {engine_names}')
        return v


class SystemSettingsUpdate(BaseModel):
    """系统设置更新"""
    llm_providers: Optional[List[LLMProviderConfig]] = None
    default_llm_provider: Optional[str] = None
    ocr_engines: Optional[List[OCREngineConfig]] = None
    default_ocr_engine: Optional[str] = None
    system_prompts: Optional[List[SystemPromptTemplate]] = None
    cot_generation: Optional[COTGenerationConfig] = None


class SettingsResponse(BaseModel):
    """设置响应"""
    settings: SystemSettings
    message: str = "Settings retrieved successfully"


class SettingsUpdateResponse(BaseModel):
    """设置更新响应"""
    settings: SystemSettings
    message: str = "Settings updated successfully"


# 默认配置
DEFAULT_LLM_PROVIDERS = [
    LLMProviderConfig(
        provider="openai",
        api_key=None,
        base_url="https://api.openai.com/v1",
        model="gpt-3.5-turbo",
        enabled=False
    ),
    LLMProviderConfig(
        provider="deepseek",
        api_key="sk-0dc1980d2c264b19bde7da0c209e13dd",
        base_url="https://api.deepseek.com",
        model="deepseek-chat",
        enabled=True
    ),
    LLMProviderConfig(
        provider="kimi",
        api_key="sk-v8EMwOjH07p2SUGN4DswMqcsOFLQeHsmkUt8zPdlt1sfK55R",
        base_url="https://api.moonshot.cn",
        model="kimi-k2-0905-preview",
        enabled=True
    )
]

DEFAULT_OCR_ENGINES = [
    OCREngineConfig(
        engine="paddleocr",
        enabled=True,
        priority=1,
        parameters={
            "use_angle_cls": True,
            "lang": "ch",
            "use_gpu": False
        }
    ),
    OCREngineConfig(
        engine="mineru",
        enabled=True,
        priority=2,
        parameters={
            "layout_detection": True,
            "formula_detection": True,
            "table_detection": True
        }
    ),
    OCREngineConfig(
        engine="alibaba_advanced",
        enabled=False,
        priority=3,
        parameters={
            "output_format": "json",
            "enable_table": True,
            "enable_formula": True
        }
    )
]

DEFAULT_SYSTEM_PROMPTS = [
    SystemPromptTemplate(
        name="academic_question_generation",
        description="学术级别问题生成模板",
        template="""基于以下文本内容，生成一个学术水平的问题。问题应该：
1. 具有一定的深度和复杂性
2. 需要推理和分析能力
3. 与文本内容密切相关
4. 适合Chain-of-Thought回答

文本内容：
{text_content}

请生成一个高质量的学术问题：""",
        variables=["text_content"],
        category="question_generation",
        is_default=True
    ),
    SystemPromptTemplate(
        name="cot_answer_generation",
        description="CoT答案生成模板",
        template="""请基于以下问题和文本内容，生成一个Chain-of-Thought格式的答案。

问题：{question}

参考文本：{text_content}

请按照以下格式回答：
1. 首先分析问题的关键点
2. 逐步推理和分析
3. 得出最终答案

答案应该逻辑清晰、推理严密、有理有据。""",
        variables=["question", "text_content"],
        category="answer_generation",
        is_default=True
    ),
    SystemPromptTemplate(
        name="knowledge_extraction",
        description="知识抽取模板",
        template="""从以下CoT数据中抽取知识图谱信息：

问题：{question}
答案：{answer}

请识别并抽取：
1. 实体（人物、地点、概念、事件等）
2. 关系（实体之间的关联）
3. 属性（实体的特征和属性）

输出格式为JSON：
{
  "entities": [{"name": "实体名", "type": "实体类型", "properties": {}}],
  "relations": [{"source": "源实体", "target": "目标实体", "type": "关系类型"}],
  "attributes": [{"entity": "实体名", "attribute": "属性名", "value": "属性值"}]
}""",
        variables=["question", "answer"],
        category="knowledge_extraction",
        is_default=True
    )
]

DEFAULT_SETTINGS = SystemSettings(
    llm_providers=DEFAULT_LLM_PROVIDERS,
    default_llm_provider="deepseek",
    ocr_engines=DEFAULT_OCR_ENGINES,
    default_ocr_engine="paddleocr",
    system_prompts=DEFAULT_SYSTEM_PROMPTS,
    cot_generation=COTGenerationConfig()
)