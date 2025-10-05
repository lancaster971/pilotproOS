"""
NOMIC Embeddings Function for PilotProOS RAG System
====================================================
100% FREE on-premise embeddings with nomic-embed-text-v1.5

Performance:
- 137M parameters (~500MB)
- 2-3GB RAM required
- <30 seconds loading time
- MTEB Score: 62.39 (outperforms OpenAI ada-002)
- Long context: 8192 tokens
- Cost: $0 (vs $12,000/year OpenAI)

License: Apache 2.0 (commercial use OK)
"""

from typing import List
from sentence_transformers import SentenceTransformer
from chromadb import Documents, EmbeddingFunction, Embeddings
import logging

logger = logging.getLogger(__name__)


class NomicEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    NOMIC embedding function for ChromaDB
    100% FREE on-premise embeddings
    """

    def __init__(self, model_name: str = "nomic-ai/nomic-embed-text-v1.5"):
        """
        Initialize NOMIC embedding model

        Args:
            model_name: HuggingFace model name (default: nomic-ai/nomic-embed-text-v1.5)
        """
        logger.info(f"🔄 Loading NOMIC model: {model_name}")

        self.model = SentenceTransformer(
            model_name,
            trust_remote_code=True
        )

        self._model_name = model_name

        logger.info(f"✅ NOMIC model loaded successfully")
        logger.info(f"💰 Cost: $0/year (vs $12,000/year OpenAI)")
        logger.info(f"📦 Model size: 137M params (~500MB)")
        logger.info(f"🧠 RAM required: 2-3GB")

    @staticmethod
    def name() -> str:
        """
        ChromaDB requires name() as a static method
        Following official ChromaDB pattern (OpenAI: @staticmethod)
        """
        return "nomic"

    def __call__(self, input: Documents) -> Embeddings:
        """
        Generate embeddings for documents (ChromaDB batch operation)

        Following official ChromaDB documentation:
        https://docs.trychroma.com/docs/embeddings/embedding-functions

        Args:
            input: Documents (list of strings) from ChromaDB

        Returns:
            Embeddings (list of lists of floats) - 768 dimensions for NOMIC
        """
        embeddings = self.model.encode(
            input,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        return embeddings.tolist()


def get_nomic_embedding_function() -> NomicEmbeddingFunction:
    """
    Factory function to get NOMIC embedding function

    Returns:
        Configured NomicEmbeddingFunction instance
    """
    return NomicEmbeddingFunction()
