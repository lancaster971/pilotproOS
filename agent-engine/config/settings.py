"""
Configuration settings for Agent Engine
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support
    """

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_JOB_TTL: int = 86400  # 24 hours
    REDIS_RESULT_TTL: int = 604800  # 7 days

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://pilotpros_user:pilotpros_secure_pass_2025@localhost:5432/pilotpros_db"
    )

    # n8n Integration
    N8N_WEBHOOK_SECRET: str = os.getenv("N8N_WEBHOOK_SECRET", "pilotpros_n8n_secret_2025")
    N8N_URL: str = os.getenv("N8N_URL", "http://n8n-dev:5678")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://backend-dev:3001")

    # JWT Authentication (match Node.js backend)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "pilotpros_dev_jwt_secret_2025_secure")
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "pilotpros-backend"
    JWT_AUDIENCE: list = ["pilotpros-frontend", "pilotpros-agent-engine"]

    # LLM Providers
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    # Rate Limiting
    RATE_LIMIT_ANALYSIS: int = 10  # per minute per user
    RATE_LIMIT_STATUS: int = 60  # per minute per user

    # Job Processing
    MAX_CONCURRENT_JOBS: int = 5
    JOB_TIMEOUT: int = 3600  # 1 hour
    JOB_MAX_RETRIES: int = 3
    JOB_RETRY_DELAY: int = 60  # seconds

    # Agent Engine Configuration (our rebrand of CrewAI)
    AGENT_ENGINE_MAX_ITERATIONS: int = 10
    AGENT_ENGINE_TIMEOUT: int = 1800  # 30 minutes
    AGENT_VERBOSE: bool = DEBUG  # Verbose only in debug mode

    # WebSocket
    WEBSOCKET_PING_INTERVAL: int = 25  # seconds
    WEBSOCKET_PING_TIMEOUT: int = 5  # seconds

    # Monitoring
    METRICS_ENABLED: bool = True
    HEALTH_CHECK_INTERVAL: int = 30  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()