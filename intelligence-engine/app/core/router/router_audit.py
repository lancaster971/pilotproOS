"""
Router Audit Logger
Tracks and audits all routing decisions for analysis and optimization
"""
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import asyncio
import aiofiles
from dataclasses import asdict
import logging
import asyncpg

logger = logging.getLogger(__name__)

class RouterAuditLogger:
    """
    Comprehensive audit logging for routing decisions
    Stores decisions in database and file for analysis
    """

    def __init__(self, log_dir: str = "logs/router_audit"):
        """
        Initialize audit logger

        Args:
            log_dir: Directory for audit logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Current log file (rotated daily)
        self.current_date = datetime.now().date()
        self.log_file = self._get_log_file()

        # In-memory buffer for batch writing
        self.buffer = []
        self.buffer_size = 10
        self.flush_task = None

        logger.info(f"RouterAuditLogger initialized with log dir: {log_dir}")

    def _get_log_file(self) -> Path:
        """Get current log file path"""
        date_str = self.current_date.strftime("%Y%m%d")
        return self.log_dir / f"router_audit_{date_str}.jsonl"

    async def log_decision(self, decision: Any, query: str, user_id: Optional[str] = None):
        """
        Log a routing decision

        Args:
            decision: RoutingDecision object
            query: Original query
            user_id: Optional user identifier
        """
        # Check if we need to rotate log file
        if datetime.now().date() != self.current_date:
            await self._rotate_log_file()

        # Create audit entry
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "query_hash": hashlib.md5(query.encode()).hexdigest(),
            "query_preview": query[:100] if len(query) > 100 else query,
            "user_id": user_id,
            "decision": {
                "model_tier": decision.model_tier.value,
                "model_name": decision.model_name,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "estimated_tokens": decision.estimated_tokens,
                "estimated_cost": decision.estimated_cost,
                "cached": decision.cached
            },
            "features": decision.features,
            "metadata": {
                "query_length": len(query),
                "response_time_ms": None  # Will be updated after execution
            }
        }

        # Add to buffer
        self.buffer.append(audit_entry)

        # Flush if buffer is full
        if len(self.buffer) >= self.buffer_size:
            await self._flush_buffer()

        # Also log to database for real-time analysis
        await self._log_to_database(audit_entry)

    async def _flush_buffer(self):
        """Flush buffer to file"""
        if not self.buffer:
            return

        try:
            async with aiofiles.open(self.log_file, 'a') as f:
                for entry in self.buffer:
                    await f.write(json.dumps(entry) + '\n')

            logger.debug(f"Flushed {len(self.buffer)} audit entries to file")
            self.buffer.clear()

        except Exception as e:
            logger.error(f"Failed to flush audit buffer: {e}")

    async def _log_to_database(self, audit_entry: Dict):
        """Log audit entry to database"""
        try:
            # Get database connection from environment
            import os
            DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/pilotpros")
            conn = await asyncpg.connect(DATABASE_URL)

            # Create table if not exists
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS router_audit (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    query_hash VARCHAR(32) NOT NULL,
                    user_id VARCHAR(255),
                    model_tier VARCHAR(50) NOT NULL,
                    model_name VARCHAR(100) NOT NULL,
                    confidence FLOAT NOT NULL,
                    reasoning TEXT,
                    estimated_tokens INT,
                    estimated_cost FLOAT,
                    cached BOOLEAN,
                    features JSONB,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert audit entry
            await conn.execute("""
                INSERT INTO router_audit (
                    timestamp, query_hash, user_id, model_tier, model_name,
                    confidence, reasoning, estimated_tokens, estimated_cost,
                    cached, features, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """,
                datetime.fromisoformat(audit_entry["timestamp"]),
                audit_entry["query_hash"],
                audit_entry["user_id"],
                audit_entry["decision"]["model_tier"],
                audit_entry["decision"]["model_name"],
                audit_entry["decision"]["confidence"],
                audit_entry["decision"]["reasoning"],
                audit_entry["decision"]["estimated_tokens"],
                audit_entry["decision"]["estimated_cost"],
                audit_entry["decision"]["cached"],
                json.dumps(audit_entry["features"]),
                json.dumps(audit_entry["metadata"])
            )

            await conn.close()

        except Exception as e:
            logger.error(f"Failed to log to database: {e}")

    async def _rotate_log_file(self):
        """Rotate log file when date changes"""
        # Flush current buffer
        await self._flush_buffer()

        # Update date and file
        self.current_date = datetime.now().date()
        self.log_file = self._get_log_file()

        logger.info(f"Rotated log file to: {self.log_file}")

    async def get_statistics(self, date: Optional[datetime] = None) -> Dict:
        """
        Get routing statistics for analysis

        Args:
            date: Date to analyze (default: today)

        Returns:
            Statistics dictionary
        """
        if date is None:
            date = datetime.now()

        try:
            import os
            DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/pilotpros")
            conn = await asyncpg.connect(DATABASE_URL)

            # Get daily statistics
            result = await conn.fetch("""
                SELECT
                    model_tier,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence,
                    SUM(estimated_tokens) as total_tokens,
                    SUM(estimated_cost) as total_cost,
                    COUNT(CASE WHEN cached THEN 1 END) as cached_count
                FROM router_audit
                WHERE DATE(timestamp) = DATE($1)
                GROUP BY model_tier
            """, date)

            stats = {
                "date": date.isoformat(),
                "by_tier": {},
                "totals": {
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0.0,
                    "cache_hits": 0
                }
            }

            for row in result:
                tier_stats = {
                    "count": row["count"],
                    "avg_confidence": float(row["avg_confidence"]) if row["avg_confidence"] else 0,
                    "total_tokens": row["total_tokens"] or 0,
                    "total_cost": float(row["total_cost"]) if row["total_cost"] else 0,
                    "cached_count": row["cached_count"]
                }
                stats["by_tier"][row["model_tier"]] = tier_stats

                # Update totals
                stats["totals"]["requests"] += tier_stats["count"]
                stats["totals"]["tokens"] += tier_stats["total_tokens"]
                stats["totals"]["cost"] += tier_stats["total_cost"]
                stats["totals"]["cache_hits"] += tier_stats["cached_count"]

            # Calculate savings
            if stats["totals"]["tokens"] > 0:
                # Assume premium model cost as baseline
                premium_cost = stats["totals"]["tokens"] / 1000 * 0.005  # $0.005 per 1k tokens
                actual_cost = stats["totals"]["cost"]
                stats["savings"] = {
                    "amount": premium_cost - actual_cost,
                    "percentage": ((premium_cost - actual_cost) / premium_cost * 100) if premium_cost > 0 else 0
                }

            await conn.close()
            return stats

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}

    async def get_routing_patterns(self, days: int = 7) -> List[Dict]:
        """
        Analyze routing patterns over time

        Args:
            days: Number of days to analyze

        Returns:
            List of pattern insights
        """
        try:
            import os
            DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/pilotpros")
            conn = await asyncpg.connect(DATABASE_URL)

            # Get pattern data
            result = await conn.fetch("""
                SELECT
                    DATE(timestamp) as date,
                    EXTRACT(HOUR FROM timestamp) as hour,
                    model_tier,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence
                FROM router_audit
                WHERE timestamp >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY DATE(timestamp), EXTRACT(HOUR FROM timestamp), model_tier
                ORDER BY date, hour, model_tier
            """, days)

            patterns = []
            for row in result:
                patterns.append({
                    "date": row["date"].isoformat(),
                    "hour": int(row["hour"]),
                    "model_tier": row["model_tier"],
                    "count": row["count"],
                    "avg_confidence": float(row["avg_confidence"]) if row["avg_confidence"] else 0
                })

            await conn.close()
            return patterns

        except Exception as e:
            logger.error(f"Failed to get routing patterns: {e}")
            return []

    async def cleanup_old_logs(self, days_to_keep: int = 30):
        """
        Clean up old log files

        Args:
            days_to_keep: Number of days of logs to keep
        """
        cutoff_date = datetime.now().date() - timedelta(days=days_to_keep)

        for log_file in self.log_dir.glob("router_audit_*.jsonl"):
            try:
                # Extract date from filename
                date_str = log_file.stem.split("_")[-1]
                file_date = datetime.strptime(date_str, "%Y%m%d").date()

                if file_date < cutoff_date:
                    log_file.unlink()
                    logger.info(f"Deleted old log file: {log_file}")

            except Exception as e:
                logger.warning(f"Failed to process log file {log_file}: {e}")

        # Also cleanup database
        try:
            import os
            DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/pilotpros")
            conn = await asyncpg.connect(DATABASE_URL)
            await conn.execute("""
                DELETE FROM router_audit
                WHERE timestamp < CURRENT_DATE - INTERVAL '%s days'
            """, days_to_keep)
            await conn.close()
            logger.info(f"Cleaned up database audit logs older than {days_to_keep} days")

        except Exception as e:
            logger.error(f"Failed to cleanup database logs: {e}")

    async def close(self):
        """Close logger and flush remaining data"""
        await self._flush_buffer()
        logger.info("RouterAuditLogger closed")