"""
HTTP Client for ON-PREMISE Embeddings Service
==============================================
Replaces local model loading with API calls to pilotpros-embeddings-dev container

BENEFITS:
- ZERO RAM in Intelligence Engine (no model loading)
- Single model instance shared across services
- Centralized embeddings management
- Easy model switching via API
"""

import httpx
from typing import List, Optional, Literal
from loguru import logger
import os


class EmbeddingsClient:
    """
    HTTP client for ON-PREMISE Embeddings Service

    Usage:
        client = EmbeddingsClient()
        embeddings = await client.embed(["text1", "text2"], model="nomic")
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Literal["stella", "gte-qwen2", "nomic"] = "nomic",
        dimension: Optional[int] = None,
        timeout: float = 30.0
    ):
        """
        Initialize Embeddings HTTP client

        Args:
            base_url: Embeddings service URL (default: http://pilotpros-embeddings-dev:8001)
            model: Default embedding model
            dimension: Embedding dimension (only for stella)
            timeout: HTTP timeout in seconds
        """
        # Docker internal network URL (container-to-container communication)
        self.base_url = base_url or os.getenv(
            "EMBEDDINGS_SERVICE_URL",
            "http://pilotpros-embeddings-dev:8001"
        )
        self.model = model
        self.dimension = dimension
        self.timeout = timeout
        self._model_name = f"embeddings-{model}"  # Store for name() method

        # HTTP client (persistent connection pool)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

        logger.info(f"EmbeddingsClient initialized: {self.base_url} (model: {model})")

    def name(self) -> str:
        """
        Model name method for ChromaDB compatibility

        ChromaDB expects embedding_function.name() as a METHOD (not attribute).
        Returns the model identifier string.
        """
        return self._model_name

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
        dimension: Optional[int] = None
    ) -> List[List[float]]:
        """
        Generate embeddings via HTTP API

        Args:
            texts: List of texts to embed
            model: Embedding model (overrides default)
            dimension: Dimension (only for stella, overrides default)

        Returns:
            List of embeddings (list of float vectors)

        Raises:
            httpx.HTTPError: If API call fails
        """
        try:
            # Prepare request payload
            payload = {
                "texts": texts,
                "model": model or self.model
            }

            # Add dimension only for stella
            if (model or self.model) == "stella" and (dimension or self.dimension):
                payload["dimension"] = dimension or self.dimension

            # Call embeddings API
            response = await self.client.post("/embed", json=payload)
            response.raise_for_status()

            # Parse response
            data = response.json()
            embeddings = data["embeddings"]

            logger.debug(
                f"Generated {len(embeddings)} embeddings "
                f"(model: {data['model']}, dim: {data['dimension']})"
            )

            return embeddings

        except httpx.HTTPError as e:
            logger.error(f"Embeddings API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in embed(): {e}")
            raise

    async def health_check(self) -> dict:
        """
        Check embeddings service health

        Returns:
            Service health status
        """
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def list_models(self) -> dict:
        """
        List available embedding models

        Returns:
            Available models info
        """
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return {"models": {}}

    async def close(self):
        """Close HTTP client connection pool"""
        await self.client.aclose()
        logger.info("EmbeddingsClient closed")

    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        Synchronous wrapper for ChromaDB v0.4.16+ compatibility

        ChromaDB v0.4.16+ expects EmbeddingFunction interface:
        __call__(self, input: Documents) -> Embeddings

        This method wraps the async embed() in a sync interface.

        Args:
            input: List of texts to embed (ChromaDB Documents)

        Returns:
            List of embeddings (ChromaDB Embeddings)
        """
        import asyncio
        import concurrent.futures
        import threading

        def run_async_in_thread(coro):
            """Run coroutine in a new thread with its own event loop"""
            result = None
            exception = None

            def thread_target():
                nonlocal result, exception
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(coro)
                    finally:
                        loop.close()
                except Exception as e:
                    exception = e

            thread = threading.Thread(target=thread_target)
            thread.start()
            thread.join(timeout=self.timeout)

            if thread.is_alive():
                raise TimeoutError(f"Embedding operation timed out after {self.timeout}s")

            if exception:
                raise exception

            return result

        try:
            # Check if we're in an async context
            try:
                asyncio.get_running_loop()
                # We're in async context (FastAPI), run in separate thread
                return run_async_in_thread(self.embed(input))
            except RuntimeError:
                # No running loop, create new one and run directly
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.embed(input))
                finally:
                    loop.close()

        except Exception as e:
            logger.error(f"Error in sync embed wrapper: {e}")
            raise

    def embed_query(self, input: str) -> List[float]:
        """
        ChromaDB v0.4.16+ query embedding method

        ChromaDB calls this for .query() operations (single query text).
        Delegates to __call__() with list wrapper.

        Args:
            input: Single query text (ChromaDB query string)

        Returns:
            Single embedding vector
        """
        # Wrap single query in list, call __call__, return first result
        embeddings = self.__call__([input])
        return embeddings[0]


# Singleton instance
_embeddings_client: Optional[EmbeddingsClient] = None


def get_embeddings_client(
    model: Literal["stella", "gte-qwen2", "nomic"] = "nomic",
    dimension: Optional[int] = None
) -> EmbeddingsClient:
    """
    Get or create singleton Embeddings client

    Args:
        model: Embedding model
        dimension: Dimension (only for stella)

    Returns:
        EmbeddingsClient instance
    """
    global _embeddings_client

    if _embeddings_client is None:
        _embeddings_client = EmbeddingsClient(model=model, dimension=dimension)
        logger.info(f"✅ Created singleton EmbeddingsClient (model: {model})")

    return _embeddings_client
