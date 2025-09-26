"""
Configuration for Intelligence Engine
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra environment variables
    )

    # Service Configuration
    SERVICE_NAME: str = "Intelligence Engine"
    SERVICE_MODE: str = "all"  # all | api | ui
    API_PORT: int = 8000
    UI_PORT: int = 8501

    # Database
    DB_HOST: str = "postgres-dev"
    DB_PORT: int = 5432
    DB_NAME: str = "pilotpros_db"
    DB_USER: str = "pilotpros_user"
    DB_PASSWORD: str = "pilotpros_secure_pass_2025"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Redis
    REDIS_HOST: str = "redis-dev"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # LangChain Configuration
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_PROJECT: str = "pilotpros-intelligence"
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    # LLM Providers
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # Default Models
    DEFAULT_LLM_MODEL: str = "gpt-4o"
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 2000

    # n8n Integration
    N8N_URL: str = "http://automation-engine-dev:5678"
    N8N_API_KEY: Optional[str] = None
    N8N_WEBHOOK_URL: str = "http://automation-engine-dev:5678/webhook"

    # Backend Integration
    BACKEND_URL: str = "http://backend-dev:3001"
    BACKEND_API_KEY: Optional[str] = None

    # Security
    JWT_SECRET_KEY: str = "pilotpros_intelligence_jwt_secret_2025"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Monitoring
    ENABLE_MONITORING: bool = True
    METRICS_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json | text

    # Cache Configuration
    CACHE_TTL_SECONDS: int = 3600
    SEMANTIC_CACHE_ENABLED: bool = True
    SEMANTIC_CACHE_THRESHOLD: float = 0.95

    # Memory Configuration
    CONVERSATION_MEMORY_TYPE: str = "summary_buffer"  # summary_buffer | window | entity
    MEMORY_MAX_TOKENS: int = 2000
    MEMORY_WINDOW_SIZE: int = 10

    # Vector Store Configuration
    VECTOR_STORE_COLLECTION: str = "business_documents"
    VECTOR_DIMENSION: int = 1536  # OpenAI embeddings dimension
    SIMILARITY_TOP_K: int = 5

    # Development
    DEBUG: bool = False
    RELOAD: bool = True

settings = Settings()