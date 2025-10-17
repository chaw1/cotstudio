from typing import List, Optional
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "COT Studio"
    DEBUG: bool = False
    VERSION: str = "0.1.0"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./cot_studio.db"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379"
    
    # Neo4j配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4jpass"
    
    # MinIO配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET: str = "cot-studio"
    
    # RabbitMQ配置
    RABBITMQ_URL: str = "amqp://cotuser:cotpass@localhost:5672/"
    
    # CORS配置
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001", "http://localhost:3002", "http://127.0.0.1:3002"]
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES: List[str] = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/markdown",
        "application/x-latex",
        "application/json",
        # 额外支持的MIME类型
        "application/x-tex",
        "text/x-tex",
        "text/x-latex",
        "application/latex",
        "text/tex"
    ]
    
    # 文件安全配置
    ENABLE_VIRUS_SCAN: bool = False  # 在生产环境中可以启用
    MAX_FILES_PER_PROJECT: int = 1000
    QUARANTINE_SUSPICIOUS_FILES: bool = True
    
    # LLM配置
    # OpenAI配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # DeepSeek配置
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    # KIMI配置
    KIMI_API_KEY: Optional[str] = None
    KIMI_BASE_URL: str = "https://api.moonshot.cn"
    KIMI_MODEL: str = "kimi-k2-0905-preview"
    
    # LLM通用配置
    DEFAULT_LLM_PROVIDER: str = "deepseek"
    LLM_REQUEST_TIMEOUT: int = 60
    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_DELAY: float = 1.0
    
    # CoT生成配置
    COT_CANDIDATE_COUNT: int = 3
    COT_MAX_CANDIDATE_COUNT: int = 5
    COT_MIN_CANDIDATE_COUNT: int = 2
    COT_QUESTION_MAX_LENGTH: int = 500
    COT_ANSWER_MAX_LENGTH: int = 2000
    
    # 导出配置
    EXPORT_DIR: str = "exports"
    EXPORT_FILE_MAX_AGE_HOURS: int = 24
    EXPORT_MAX_FILE_SIZE: int = 1024 * 1024 * 1024  # 1GB
    
    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()