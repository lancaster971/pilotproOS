#!/usr/bin/env python3
"""
ON-PREMISE Embedding Functions for ChromaDB
100% GRATUITO - ZERO token costs, ZERO API calls

Supporta:
- stella-en-1.5B-v5 (MIT License, MTEB retrieval leader)
- gte-Qwen2-1.5B-instruct (Apache 2.0, MTEB 70.24)
- nomic-embed-text-v1.5 (Apache 2.0, MTEB 62.39)
"""

from typing import List, Optional
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class StellaEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    Stella Embedding Function - ON-PREMISE (MIT License)

    Features:
    - MTEB retrieval leader (commercial-friendly)
    - 1.5B parameters
    - Dimensioni: 512, 768, 1024, 2048, 4096, 6144, 8192
    - Raccomandato: 1024d (optimal balance speed/accuracy)
    - Dual prompts: s2p_query (retrieval) + s2s (similarity)

    Usage:
        stella_ef = StellaEmbeddingFunction(dimension=1024)
        collection = client.get_or_create_collection(
            name="stella_collection",
            embedding_function=stella_ef
        )
    """

    def __init__(
        self,
        model_name: str = "dunzhang/stella_en_1.5B_v5",
        dimension: int = 1024,
        use_query_prompt: bool = True,
        device: Optional[str] = None
    ):
        """
        Initialize Stella embedding function

        Args:
            model_name: HuggingFace model identifier
            dimension: Embedding dimension (512, 768, 1024, 2048, 4096, 6144, 8192)
            use_query_prompt: Use s2p_query prompt for retrieval (recommended)
            device: Device for inference (None=auto, "cpu", "cuda", "mps")
        """
        logger.info(f"Initializing Stella embeddings (dimension={dimension}, device={device})")

        self.model = SentenceTransformer(
            model_name,
            trust_remote_code=True,
            device=device
        )
        self.dimension = dimension
        self.use_query_prompt = use_query_prompt

        logger.info(f"✅ Stella model loaded: {model_name} ({dimension}d)")

    def __call__(self, input: Documents) -> Embeddings:
        """
        Generate embeddings for documents

        Args:
            input: List of text documents

        Returns:
            List of embeddings (Python lists, not numpy arrays)
        """
        # Use s2p_query prompt for retrieval tasks
        if self.use_query_prompt:
            embeddings = self.model.encode(
                input,
                prompt_name="s2p_query",
                convert_to_numpy=True,
                show_progress_bar=False
            )
        else:
            embeddings = self.model.encode(
                input,
                convert_to_numpy=True,
                show_progress_bar=False
            )

        # ChromaDB expects Python lists, not numpy arrays
        return embeddings.tolist()


class GteQwenEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    GTE-Qwen2 Embedding Function - ON-PREMISE (Apache 2.0 License)

    Features:
    - MTEB score: 70.24 (Rank #1 English + Chinese)
    - 1.5B parameters
    - Dimensioni: 8192 (full), supporta dimensioni ridotte
    - Best multilingual performance

    Usage:
        gte_ef = GteQwenEmbeddingFunction()
        collection = client.get_or_create_collection(
            name="gte_collection",
            embedding_function=gte_ef
        )
    """

    def __init__(
        self,
        model_name: str = "Alibaba-NLP/gte-Qwen2-1.5B-instruct",
        device: Optional[str] = None
    ):
        """
        Initialize GTE-Qwen2 embedding function

        Args:
            model_name: HuggingFace model identifier
            device: Device for inference (None=auto, "cpu", "cuda", "mps")
        """
        logger.info(f"Initializing GTE-Qwen2 embeddings (device={device})")

        self.model = SentenceTransformer(
            model_name,
            trust_remote_code=True,
            device=device
        )

        logger.info(f"✅ GTE-Qwen2 model loaded: {model_name}")

    def __call__(self, input: Documents) -> Embeddings:
        """
        Generate embeddings for documents

        Args:
            input: List of text documents

        Returns:
            List of embeddings (Python lists)
        """
        embeddings = self.model.encode(
            input,
            convert_to_numpy=True,
            show_progress_bar=False
        )

        return embeddings.tolist()


class NomicEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    Nomic Embed Embedding Function - ON-PREMISE (Apache 2.0 License)

    Features:
    - MTEB score: 62.39
    - 137M parameters (MOLTO piccolo e veloce!)
    - Dimensioni: 768
    - Long context: 8192 tokens
    - Outperforms text-embedding-ada-002

    IMPORTANT: Nomic REQUIRES task prefixes:
    - "search_document:" for documents (RAG storage)
    - "search_query:" for queries (RAG retrieval)
    - "classification:" for classification tasks
    - "clustering:" for clustering tasks

    Usage:
        nomic_ef = NomicEmbeddingFunction(task_type="search_document")
        collection = client.get_or_create_collection(
            name="nomic_collection",
            embedding_function=nomic_ef
        )
    """

    def __init__(
        self,
        model_name: str = "nomic-ai/nomic-embed-text-v1.5",
        task_type: str = "search_document",
        device: Optional[str] = None
    ):
        """
        Initialize Nomic embedding function

        Args:
            model_name: HuggingFace model identifier
            task_type: Task prefix (search_document, search_query, classification, clustering)
            device: Device for inference (None=auto, "cpu", "cuda", "mps")
        """
        logger.info(f"Initializing Nomic embeddings (task={task_type}, device={device})")

        valid_tasks = ["search_document", "search_query", "classification", "clustering"]
        if task_type not in valid_tasks:
            raise ValueError(f"Invalid task_type: {task_type}. Must be one of {valid_tasks}")

        self.task_type = task_type

        self.model = SentenceTransformer(
            model_name,
            trust_remote_code=True,
            device=device
        )

        logger.info(f"✅ Nomic model loaded: {model_name} (task: {task_type})")

    def __call__(self, input: Documents) -> Embeddings:
        """
        Generate embeddings for documents with task prefix

        Args:
            input: List of text documents

        Returns:
            List of embeddings (Python lists)
        """
        # Add task prefix to each document (REQUIRED by nomic!)
        prefixed_input = [f"{self.task_type}: {text}" for text in input]

        embeddings = self.model.encode(
            prefixed_input,
            convert_to_numpy=True,
            show_progress_bar=False
        )

        return embeddings.tolist()


# Model registry for easy selection
AVAILABLE_MODELS = {
    "stella": {
        "name": "stella-en-1.5B-v5",
        "function": StellaEmbeddingFunction,
        "license": "MIT",
        "mteb_score": "Top MTEB retrieval (commercial)",
        "dimensions": [512, 768, 1024, 2048, 4096, 6144, 8192],
        "recommended_dim": 1024,
        "size": "1.5B params"
    },
    "gte-qwen2": {
        "name": "gte-Qwen2-1.5B-instruct",
        "function": GteQwenEmbeddingFunction,
        "license": "Apache 2.0",
        "mteb_score": "70.24",
        "dimensions": [8192],
        "recommended_dim": 8192,
        "size": "1.5B params"
    },
    "nomic": {
        "name": "nomic-embed-text-v1.5",
        "function": NomicEmbeddingFunction,
        "license": "Apache 2.0",
        "mteb_score": "62.39",
        "dimensions": [768],
        "recommended_dim": 768,
        "size": "137M params"
    }
}


def get_embedding_function(
    model_type: str = "stella",
    dimension: Optional[int] = None,
    device: Optional[str] = None
) -> EmbeddingFunction:
    """
    Factory function to get embedding function by type

    Args:
        model_type: Model type ("stella", "gte-qwen2", "nomic")
        dimension: Embedding dimension (only for stella)
        device: Device for inference

    Returns:
        EmbeddingFunction instance

    Example:
        # Stella with 1024d
        ef = get_embedding_function("stella", dimension=1024)

        # GTE-Qwen2 (auto-dimension)
        ef = get_embedding_function("gte-qwen2")

        # Nomic (smallest, fastest)
        ef = get_embedding_function("nomic")
    """
    if model_type not in AVAILABLE_MODELS:
        raise ValueError(
            f"Unknown model type: {model_type}. "
            f"Available: {list(AVAILABLE_MODELS.keys())}"
        )

    model_info = AVAILABLE_MODELS[model_type]
    function_class = model_info["function"]

    # Stella supports custom dimensions
    if model_type == "stella":
        dim = dimension or model_info["recommended_dim"]
        return function_class(dimension=dim, device=device)
    else:
        return function_class(device=device)


if __name__ == "__main__":
    # Test embedding functions
    print("🧪 Testing ON-PREMISE Embedding Functions\n")

    test_texts = [
        "Come gestisce PilotProOS gli errori nei workflow?",
        "PilotProOS è un sistema per automazione processi aziendali"
    ]

    for model_type in ["stella", "gte-qwen2", "nomic"]:
        print(f"Testing {model_type}...")
        try:
            ef = get_embedding_function(model_type)
            embeddings = ef(test_texts)
            print(f"✅ {model_type}: {len(embeddings)} embeddings, {len(embeddings[0])} dimensions")
        except Exception as e:
            print(f"❌ {model_type}: {e}")
        print()
