"""
Milhena Feedback Store - PostgreSQL implementation
Stores and retrieves user feedback for continuous learning
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncpg
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class FeedbackStore:
    """
    PostgreSQL-based storage for user feedback and learning data
    Following LangSmith patterns for feedback collection
    """

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """Initialize database connection pool and create tables"""
        self.pool = await asyncpg.create_pool(self.db_url, min_size=2, max_size=10)

        await self._create_tables()

        logger.info("FeedbackStore initialized with PostgreSQL")

    async def _create_tables(self):
        """Create necessary tables for feedback storage"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS milhena_feedback (
                    id SERIAL PRIMARY KEY,
                    feedback_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
                    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
                    session_id VARCHAR(255) NOT NULL,
                    message_id VARCHAR(255),
                    run_id VARCHAR(255),

                    -- Query and response info
                    query TEXT NOT NULL,
                    response TEXT,
                    detected_intent VARCHAR(50),
                    confidence FLOAT,

                    -- Feedback type
                    feedback_type VARCHAR(20) NOT NULL,
                    score FLOAT,
                    comment TEXT,

                    -- Context
                    llm_used VARCHAR(50),
                    response_time_ms INTEGER,

                    -- Learning flags
                    is_reformulation BOOLEAN DEFAULT FALSE,
                    corrected_query TEXT,
                    correct_intent VARCHAR(50),

                    -- Metadata
                    metadata JSONB,

                    -- Indexes
                    INDEX idx_session_id (session_id),
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_feedback_type (feedback_type),
                    INDEX idx_detected_intent (detected_intent)
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS milhena_learned_patterns (
                    id SERIAL PRIMARY KEY,
                    pattern_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

                    -- Pattern info
                    pattern_type VARCHAR(50) NOT NULL,

                    -- Original and corrected
                    original_query TEXT,
                    corrected_query TEXT,
                    original_intent VARCHAR(50),
                    correct_intent VARCHAR(50),

                    -- Learning data
                    key_terms_added TEXT[],
                    key_terms_removed TEXT[],
                    confidence_threshold FLOAT,

                    -- Usage stats
                    usage_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,

                    -- Metadata
                    metadata JSONB,

                    -- Indexes
                    INDEX idx_pattern_type (pattern_type),
                    INDEX idx_correct_intent (correct_intent)
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS milhena_daily_metrics (
                    id SERIAL PRIMARY KEY,
                    metric_date DATE UNIQUE NOT NULL,

                    -- Query metrics
                    total_queries INTEGER DEFAULT 0,
                    successful_disambiguations INTEGER DEFAULT 0,
                    failed_disambiguations INTEGER DEFAULT 0,
                    reformulations INTEGER DEFAULT 0,

                    -- Feedback metrics
                    positive_feedback INTEGER DEFAULT 0,
                    negative_feedback INTEGER DEFAULT 0,

                    -- Performance metrics
                    cache_hits INTEGER DEFAULT 0,
                    cache_misses INTEGER DEFAULT 0,
                    avg_confidence FLOAT,
                    avg_response_time_ms INTEGER,

                    -- LLM usage
                    groq_usage INTEGER DEFAULT 0,
                    openai_usage INTEGER DEFAULT 0,

                    -- Cost tracking
                    token_count INTEGER DEFAULT 0,
                    estimated_cost FLOAT DEFAULT 0.0,

                    -- Learning metrics
                    patterns_learned INTEGER DEFAULT 0,

                    -- Computed metrics
                    accuracy FLOAT,
                    reformulation_rate FLOAT,
                    satisfaction_rate FLOAT,
                    cache_hit_rate FLOAT,

                    INDEX idx_metric_date (metric_date)
                )
            """)

            logger.info("Feedback tables created/verified")

    async def save_feedback(
        self,
        session_id: str,
        query: str,
        feedback_type: str,
        message_id: Optional[str] = None,
        run_id: Optional[str] = None,
        response: Optional[str] = None,
        detected_intent: Optional[str] = None,
        confidence: Optional[float] = None,
        score: Optional[float] = None,
        comment: Optional[str] = None,
        llm_used: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        is_reformulation: bool = False,
        corrected_query: Optional[str] = None,
        correct_intent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Save feedback entry
        Returns feedback_id
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO milhena_feedback (
                    session_id, message_id, run_id,
                    query, response, detected_intent, confidence,
                    feedback_type, score, comment,
                    llm_used, response_time_ms,
                    is_reformulation, corrected_query, correct_intent,
                    metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                RETURNING feedback_id
            """,
                session_id, message_id, run_id,
                query, response, detected_intent, confidence,
                feedback_type, score, comment,
                llm_used, response_time_ms,
                is_reformulation, corrected_query, correct_intent,
                json.dumps(metadata) if metadata else None
            )

            feedback_id = str(row['feedback_id'])

            logger.info(f"Saved feedback: {feedback_id} ({feedback_type})")

            return feedback_id

    async def get_recent_feedback(
        self,
        limit: int = 100,
        feedback_type: Optional[str] = None
    ) -> List[Dict]:
        """Get recent feedback entries"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT * FROM milhena_feedback
                WHERE 1=1
            """
            params = []

            if feedback_type:
                query += " AND feedback_type = $1"
                params.append(feedback_type)

            query += " ORDER BY timestamp DESC LIMIT $" + str(len(params) + 1)
            params.append(limit)

            rows = await conn.fetch(query, *params)

            return [dict(row) for row in rows]

    async def get_reformulations(
        self,
        days: int = 7
    ) -> List[Dict]:
        """Get reformulation patterns for learning"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM milhena_feedback
                WHERE is_reformulation = TRUE
                  AND timestamp > NOW() - INTERVAL '$1 days'
                ORDER BY timestamp DESC
            """, days)

            return [dict(row) for row in rows]

    async def save_learned_pattern(
        self,
        pattern_type: str,
        original_query: Optional[str],
        corrected_query: Optional[str],
        original_intent: Optional[str],
        correct_intent: Optional[str],
        key_terms_added: Optional[List[str]] = None,
        key_terms_removed: Optional[List[str]] = None,
        confidence_threshold: float = 0.7,
        metadata: Optional[Dict] = None
    ) -> str:
        """Save a learned pattern"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO milhena_learned_patterns (
                    pattern_type,
                    original_query, corrected_query,
                    original_intent, correct_intent,
                    key_terms_added, key_terms_removed,
                    confidence_threshold,
                    metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING pattern_id
            """,
                pattern_type,
                original_query, corrected_query,
                original_intent, correct_intent,
                key_terms_added or [],
                key_terms_removed or [],
                confidence_threshold,
                json.dumps(metadata) if metadata else None
            )

            pattern_id = str(row['pattern_id'])

            logger.info(f"Learned pattern: {pattern_id} ({pattern_type})")

            return pattern_id

    async def get_learned_patterns(
        self,
        pattern_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get learned patterns"""
        async with self.pool.acquire() as conn:
            if pattern_type:
                rows = await conn.fetch("""
                    SELECT *
                    FROM milhena_learned_patterns
                    WHERE pattern_type = $1
                    ORDER BY usage_count DESC, success_count DESC
                    LIMIT $2
                """, pattern_type, limit)
            else:
                rows = await conn.fetch("""
                    SELECT *
                    FROM milhena_learned_patterns
                    ORDER BY usage_count DESC, success_count DESC
                    LIMIT $1
                """, limit)

            return [dict(row) for row in rows]

    async def increment_pattern_usage(
        self,
        pattern_id: str,
        successful: bool = True
    ):
        """Increment pattern usage counter"""
        async with self.pool.acquire() as conn:
            if successful:
                await conn.execute("""
                    UPDATE milhena_learned_patterns
                    SET usage_count = usage_count + 1,
                        success_count = success_count + 1,
                        updated_at = NOW()
                    WHERE pattern_id = $1
                """, pattern_id)
            else:
                await conn.execute("""
                    UPDATE milhena_learned_patterns
                    SET usage_count = usage_count + 1,
                        updated_at = NOW()
                    WHERE pattern_id = $1
                """, pattern_id)

    async def update_daily_metrics(
        self,
        metric_date: datetime,
        **metrics
    ):
        """Update daily metrics"""
        async with self.pool.acquire() as conn:
            set_clauses = []
            params = [metric_date.date()]
            param_count = 2

            for key, value in metrics.items():
                set_clauses.append(f"{key} = ${param_count}")
                params.append(value)
                param_count += 1

            if set_clauses:
                await conn.execute(f"""
                    INSERT INTO milhena_daily_metrics (metric_date, {', '.join(metrics.keys())})
                    VALUES ($1, {', '.join(f'${i}' for i in range(2, param_count))})
                    ON CONFLICT (metric_date)
                    DO UPDATE SET {', '.join(set_clauses)}
                """, *params)

    async def get_daily_metrics(
        self,
        days: int = 7
    ) -> List[Dict]:
        """Get daily metrics for period"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM milhena_daily_metrics
                WHERE metric_date > CURRENT_DATE - INTERVAL '$1 days'
                ORDER BY metric_date DESC
            """, days)

            return [dict(row) for row in rows]

    async def get_error_patterns(
        self,
        days: int = 7
    ) -> List[Dict]:
        """Analyze error patterns from negative feedback"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    detected_intent,
                    COUNT(*) as error_count,
                    AVG(confidence) as avg_confidence,
                    ARRAY_AGG(DISTINCT query) as example_queries
                FROM milhena_feedback
                WHERE feedback_type = 'negative'
                  AND timestamp > NOW() - INTERVAL '$1 days'
                GROUP BY detected_intent
                ORDER BY error_count DESC
                LIMIT 20
            """, days)

            return [dict(row) for row in rows]

    async def close(self):
        """Close database pool"""
        if self.pool:
            await self.pool.close()
            logger.info("FeedbackStore closed")