"""
CacheManager - Smart caching with semantic similarity
Uses Redis for storage and embeddings for similarity matching
"""
from typing import Dict, Any, Optional, List, Tuple
import logging
import json
import hashlib
from datetime import datetime, timedelta
import redis
import asyncio
import numpy as np
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Smart cache with semantic similarity matching
    Improves cache hit rate by finding similar queries
    """

    def __init__(self, config: Any):
        self.config = config
        self.ttl = config.cache_ttl  # Default 5 minutes

        # Redis connection
        try:
            self.redis_client = redis.from_url(
                config.redis_url,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Cache Manager connected to Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory cache.")
            self.redis_client = None
            self.memory_cache: Dict[str, Any] = {}

        # Sentence transformer for semantic similarity
        if SentenceTransformer:
            try:
                self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Semantic encoder initialized")
            except Exception as e:
                logger.warning(f"Semantic encoder failed: {e}. Using exact matching only.")
                self.encoder = None
        else:
            logger.warning("sentence-transformers not installed. Using exact matching only.")
            self.encoder = None

        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "semantic_hits": 0
        }

    def _generate_key(self, query: str, session_id: Optional[str] = None) -> str:
        """
        Generate cache key

        Args:
            query: User query
            session_id: Optional session identifier

        Returns:
            Cache key
        """
        # Include session for personalization
        content = f"{query}:{session_id or 'global'}"
        return f"milhena:cache:{hashlib.md5(content.encode()).hexdigest()}"

    async def get(
        self,
        query: str,
        session_id: Optional[str] = None,
        use_semantic: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response

        Args:
            query: User query
            session_id: Session identifier
            use_semantic: Whether to use semantic similarity

        Returns:
            Cached response or None
        """
        try:
            # Try exact match first
            key = self._generate_key(query, session_id)
            result = await self._get_exact(key)

            if result:
                self.stats["hits"] += 1
                logger.info(f"Cache hit (exact): {query[:50]}...")
                return result

            # Try semantic similarity if enabled
            if use_semantic and self.encoder:
                result = await self._get_semantic(query, session_id)
                if result:
                    self.stats["semantic_hits"] += 1
                    logger.info(f"Cache hit (semantic): {query[:50]}...")
                    return result

            self.stats["misses"] += 1
            return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def _get_exact(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get exact match from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if self.redis_client:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
        else:
            # In-memory cache
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                # Check expiry
                if entry["expires"] > datetime.now():
                    return entry["data"]
                else:
                    del self.memory_cache[key]

        return None

    async def _get_semantic(
        self,
        query: str,
        session_id: Optional[str] = None,
        threshold: float = 0.85
    ) -> Optional[Dict[str, Any]]:
        """
        Get semantically similar cached response

        Args:
            query: User query
            session_id: Session identifier
            threshold: Similarity threshold (0-1)

        Returns:
            Best matching cached response or None
        """
        try:
            if not self.encoder:
                return None

            # Encode query
            query_embedding = self.encoder.encode(query)

            # Get all cache keys for this session
            pattern = f"milhena:cache:*"
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
            else:
                keys = [k for k in self.memory_cache.keys() if pattern.replace("*", "") in k]

            best_match = None
            best_score = 0.0

            # Compare with cached queries
            for key in keys[:100]:  # Limit to 100 most recent
                # Get cached entry
                if self.redis_client:
                    value = self.redis_client.get(key)
                    if not value:
                        continue
                    entry = json.loads(value)
                else:
                    if key not in self.memory_cache:
                        continue
                    entry = self.memory_cache[key]["data"]

                # Get cached query embedding
                if "embedding" in entry:
                    cached_embedding = np.array(entry["embedding"])

                    # Calculate cosine similarity
                    similarity = np.dot(query_embedding, cached_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(cached_embedding)
                    )

                    if similarity > threshold and similarity > best_score:
                        best_score = similarity
                        best_match = entry

            if best_match:
                logger.info(f"Semantic match found with {best_score:.2f} similarity")
                return best_match

        except Exception as e:
            logger.error(f"Semantic cache error: {e}")

        return None

    async def set(
        self,
        query: str,
        session_id: Optional[str],
        result: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """
        Cache a response

        Args:
            query: User query
            session_id: Session identifier
            result: Response to cache
            ttl: Time to live in seconds
        """
        try:
            key = self._generate_key(query, session_id)
            ttl = ttl or self.ttl

            # Add embedding if encoder available
            if self.encoder:
                embedding = self.encoder.encode(query)
                result["embedding"] = embedding.tolist()

            # Add metadata
            result["cached_at"] = datetime.now().isoformat()
            result["query"] = query

            # Store in cache
            if self.redis_client:
                self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(result)
                )

                # Also store in embedding index
                if self.encoder:
                    embedding_key = f"milhena:embeddings:{key}"
                    self.redis_client.setex(
                        embedding_key,
                        ttl,
                        json.dumps({"query": query, "key": key})
                    )
            else:
                # In-memory cache
                self.memory_cache[key] = {
                    "data": result,
                    "expires": datetime.now() + timedelta(seconds=ttl)
                }

            logger.debug(f"Cached response for: {query[:50]}...")

        except Exception as e:
            logger.error(f"Cache set error: {e}")

    async def invalidate(
        self,
        pattern: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Invalidate cached entries

        Args:
            pattern: Pattern to match keys
            session_id: Invalidate all entries for a session
        """
        try:
            if session_id:
                pattern = f"milhena:cache:*{session_id}*"
            elif not pattern:
                pattern = "milhena:cache:*"

            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} cache entries")
            else:
                # In-memory cache
                keys_to_delete = [k for k in self.memory_cache.keys() if pattern.replace("*", "") in k]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                logger.info(f"Invalidated {len(keys_to_delete)} cache entries")

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Cache statistics
        """
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0.0
        semantic_rate = self.stats["semantic_hits"] / total if total > 0 else 0.0

        stats = {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "semantic_hits": self.stats["semantic_hits"],
            "total_requests": total,
            "hit_rate": f"{hit_rate:.2%}",
            "semantic_hit_rate": f"{semantic_rate:.2%}",
            "cache_size": self._get_cache_size()
        }

        return stats

    def _get_cache_size(self) -> int:
        """Get number of cached entries"""
        try:
            if self.redis_client:
                return len(self.redis_client.keys("milhena:cache:*"))
            else:
                return len(self.memory_cache)
        except:
            return 0

    async def warm_cache(self, common_queries: List[Dict[str, Any]]):
        """
        Pre-populate cache with common queries

        Args:
            common_queries: List of common query/response pairs
        """
        for item in common_queries:
            await self.set(
                query=item["query"],
                session_id=None,  # Global cache
                result=item["response"],
                ttl=3600  # 1 hour for common queries
            )

        logger.info(f"Warmed cache with {len(common_queries)} common queries")

    async def cleanup_expired(self):
        """
        Clean up expired cache entries (for in-memory cache)
        """
        if not self.redis_client and self.memory_cache:
            now = datetime.now()
            expired_keys = [
                k for k, v in self.memory_cache.items()
                if v["expires"] < now
            ]

            for key in expired_keys:
                del self.memory_cache[key]

            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")