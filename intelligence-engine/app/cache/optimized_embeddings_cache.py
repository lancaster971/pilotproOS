"""
Optimized Embeddings Cache for PilotProOS Intelligence Engine
=============================================================
Performance-optimized embeddings cache following TODO-MILHENA-EXPERT.md specs:
- Batch inference for efficiency
- Warm model pool (3 instances pre-loaded)
- Async processing with thread pool
- LRU eviction policy

NO MOCK DATA - REAL SENTENCE TRANSFORMERS
"""

import asyncio
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional, Union
import numpy as np
from collections import OrderedDict
import logging

from sentence_transformers import SentenceTransformer
import redis

logger = logging.getLogger(__name__)


class OptimizedEmbeddingsCache:
    """
    Performance-optimized embeddings cache:
    - Batch inference for efficiency
    - Warm model pool (3 instances pre-loaded)
    - Async processing with thread pool
    - LRU eviction policy
    """

    def __init__(
        self,
        model_name: str = 'all-MiniLM-L6-v2',
        pool_size: int = 3,
        batch_size: int = 32,
        cache_size: int = 10000,
        redis_client: Optional[redis.Redis] = None
    ):
        """
        Initialize embeddings cache with model pool

        Args:
            model_name: Sentence transformer model to use
            pool_size: Number of models to pre-load
            batch_size: Batch size for encoding
            cache_size: Maximum cache entries
            redis_client: Optional Redis client for distributed cache
        """
        logger.info(f"Initializing OptimizedEmbeddingsCache with {model_name}")

        # Pre-load model pool for parallel processing
        self.model_pool = []
        for i in range(pool_size):
            logger.info(f"Loading model {i+1}/{pool_size}...")
            model = SentenceTransformer(model_name)
            self.model_pool.append(model)

        self.model_name = model_name
        self.executor = ThreadPoolExecutor(max_workers=pool_size)
        self.batch_size = batch_size

        # Pending queries for batching
        self.pending_queries = []
        self.batch_lock = asyncio.Lock()
        self.last_batch_time = time.time()

        # LRU cache (in-memory)
        self.cache = OrderedDict()
        self.cache_size = cache_size

        # Redis for distributed cache (optional)
        if redis_client is None:
            try:
                # Try to connect to Redis
                self.redis = redis.Redis(
                    host='localhost',
                    port=6379,
                    decode_responses=False  # We'll handle encoding
                )
                self.redis.ping()
                logger.info("Connected to Redis for distributed cache")
            except:
                self.redis = None
                logger.info("Redis not available, using in-memory cache only")
        else:
            self.redis = redis_client

        # Statistics
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "batches_processed": 0,
            "total_embeddings": 0,
            "avg_batch_time": 0
        }

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(text.encode()).hexdigest()

    async def get_embeddings(
        self,
        texts: Union[str, List[str]],
        use_cache: bool = True
    ) -> np.ndarray:
        """
        Get embeddings for text(s) with caching

        Args:
            texts: Single text or list of texts
            use_cache: Whether to use cache

        Returns:
            Embeddings array
        """
        # Handle single text
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []
        texts_to_encode = []
        indices_to_encode = []

        # Check cache for each text
        for i, text in enumerate(texts):
            if use_cache:
                embedding = await self._get_from_cache(text)
                if embedding is not None:
                    embeddings.append(embedding)
                    self.stats["cache_hits"] += 1
                else:
                    texts_to_encode.append(text)
                    indices_to_encode.append(i)
                    self.stats["cache_misses"] += 1
            else:
                texts_to_encode.append(text)
                indices_to_encode.append(i)

        # Encode missing texts
        if texts_to_encode:
            new_embeddings = await self.get_embeddings_batch(texts_to_encode)

            # Store in cache
            if use_cache:
                for text, embedding in zip(texts_to_encode, new_embeddings):
                    await self._store_in_cache(text, embedding)

            # Insert new embeddings in correct positions
            for idx, embedding in zip(indices_to_encode, new_embeddings):
                embeddings.insert(idx, embedding)

        return np.array(embeddings)

    async def get_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """
        Batch processing for efficiency

        Args:
            texts: List of texts to encode

        Returns:
            Embeddings array
        """
        if not texts:
            return np.array([])

        # Get available model from pool
        model_idx = hash(texts[0]) % len(self.model_pool)
        model = self.model_pool[model_idx]

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        start_time = time.time()

        embeddings = await loop.run_in_executor(
            self.executor,
            lambda: model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            )
        )

        # Update statistics
        batch_time = time.time() - start_time
        self.stats["batches_processed"] += 1
        self.stats["total_embeddings"] += len(texts)
        self.stats["avg_batch_time"] = (
            (self.stats["avg_batch_time"] * (self.stats["batches_processed"] - 1) + batch_time) /
            self.stats["batches_processed"]
        )

        logger.info(f"Encoded batch of {len(texts)} texts in {batch_time:.2f}s")

        return embeddings

    async def smart_batching(self, text: str, timeout_ms: int = 50) -> np.ndarray:
        """
        Accumulate queries for batch processing

        Args:
            text: Text to encode
            timeout_ms: Maximum wait time in milliseconds

        Returns:
            Embedding for the text
        """
        async with self.batch_lock:
            # Add to pending queries
            self.pending_queries.append(text)

            # Check if we should process batch
            current_time = time.time()
            wait_time = (current_time - self.last_batch_time) * 1000  # Convert to ms

            if len(self.pending_queries) >= self.batch_size or \
               (len(self.pending_queries) > 0 and wait_time > timeout_ms):
                # Process batch
                batch = self.pending_queries[:self.batch_size]
                self.pending_queries = self.pending_queries[self.batch_size:]
                self.last_batch_time = current_time

                # Get embeddings for batch
                embeddings = await self.get_embeddings_batch(batch)

                # Find and return the embedding for our text
                idx = batch.index(text)
                return embeddings[idx]

        # If not processed in batch, wait a bit and try again
        await asyncio.sleep(timeout_ms / 1000)
        return await self.get_embeddings([text], use_cache=True)

    async def _get_from_cache(self, text: str) -> Optional[np.ndarray]:
        """Get embedding from cache (memory + Redis)"""
        cache_key = self._get_cache_key(text)

        # Check in-memory cache first
        if cache_key in self.cache:
            # Move to end (LRU)
            self.cache.move_to_end(cache_key)
            return self.cache[cache_key]

        # Check Redis if available
        if self.redis:
            try:
                data = self.redis.get(f"emb:{cache_key}")
                if data:
                    # Deserialize numpy array
                    embedding = np.frombuffer(data, dtype=np.float32)

                    # Store in memory cache
                    self._update_lru_cache(cache_key, embedding)

                    return embedding
            except Exception as e:
                logger.error(f"Redis cache error: {e}")

        return None

    async def _store_in_cache(self, text: str, embedding: np.ndarray):
        """Store embedding in cache (memory + Redis)"""
        cache_key = self._get_cache_key(text)

        # Store in memory cache
        self._update_lru_cache(cache_key, embedding)

        # Store in Redis if available
        if self.redis:
            try:
                # Serialize numpy array
                data = embedding.astype(np.float32).tobytes()

                # Store with 1 hour expiration
                self.redis.setex(
                    f"emb:{cache_key}",
                    3600,
                    data
                )
            except Exception as e:
                logger.error(f"Redis cache store error: {e}")

    def _update_lru_cache(self, key: str, value: np.ndarray):
        """Update LRU cache with size limit"""
        # Remove oldest if cache is full
        if key not in self.cache and len(self.cache) >= self.cache_size:
            # Remove oldest (first item)
            self.cache.popitem(last=False)

        # Add/update item (moves to end)
        self.cache[key] = value

    async def preload_embeddings(self, texts: List[str], batch_size: int = 100):
        """
        Preload embeddings for a list of texts

        Args:
            texts: List of texts to preload
            batch_size: Batch size for preloading
        """
        logger.info(f"Preloading {len(texts)} embeddings...")

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            await self.get_embeddings(batch, use_cache=True)

            # Log progress
            progress = min(i + batch_size, len(texts))
            logger.info(f"Preloaded {progress}/{len(texts)} embeddings")

        logger.info("Preloading complete")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_rate = (self.stats["cache_hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            **self.stats,
            "cache_size": len(self.cache),
            "hit_rate": f"{hit_rate:.1f}%",
            "model_pool_size": len(self.model_pool),
            "redis_connected": self.redis is not None
        }

    async def similarity_search(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find most similar documents to query

        Args:
            query: Query text
            documents: List of documents to search
            top_k: Number of top results to return

        Returns:
            List of results with scores
        """
        # Get query embedding
        query_embedding = await self.get_embeddings(query)

        # Get document embeddings (uses cache)
        doc_embeddings = await self.get_embeddings(documents)

        # Calculate cosine similarity
        query_norm = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        doc_norms = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)

        similarities = np.dot(doc_norms, query_norm.T).flatten()

        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        # Prepare results
        results = []
        for idx in top_indices:
            results.append({
                "document": documents[idx],
                "score": float(similarities[idx]),
                "index": int(idx)
            })

        return results

    def close(self):
        """Clean up resources"""
        self.executor.shutdown(wait=True)
        if self.redis:
            self.redis.close()
        logger.info("OptimizedEmbeddingsCache closed")


# Singleton instance
_embeddings_cache = None

def get_embeddings_cache() -> OptimizedEmbeddingsCache:
    """Get or create singleton embeddings cache"""
    global _embeddings_cache
    if _embeddings_cache is None:
        _embeddings_cache = OptimizedEmbeddingsCache()
    return _embeddings_cache