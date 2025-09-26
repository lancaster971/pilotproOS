"""
Database initialization and management
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncpg
from loguru import logger
from .config import settings

# Async engine for main operations
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
    pool_size=20,
    max_overflow=40
)

# Async session factory
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_database():
    """Initialize database with required extensions and tables"""
    try:
        # Create pgvector extension
        async with async_engine.begin() as conn:
            # Enable pgvector extension for embeddings
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("✅ pgvector extension enabled")

            # Create intelligence schema
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS intelligence"))
            logger.info("✅ Intelligence schema created")

            # Create embeddings table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS intelligence.embeddings (
                    id SERIAL PRIMARY KEY,
                    document_id VARCHAR(255),
                    content TEXT,
                    embedding vector(1536),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Create conversations table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS intelligence.conversations (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255),
                    session_id VARCHAR(255),
                    message TEXT,
                    response TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Create metrics table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS intelligence.metrics (
                    id SERIAL PRIMARY KEY,
                    metric_type VARCHAR(100),
                    metric_value JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Create indexes
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_embeddings_vector
                ON intelligence.embeddings USING ivfflat (embedding vector_cosine_ops)
            """))

            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_conversations_user
                ON intelligence.conversations (user_id)
            """))

            logger.info("✅ Database initialized successfully")

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

async def get_session() -> AsyncSession:
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        yield session

async def test_connection():
    """Test database connection"""
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False