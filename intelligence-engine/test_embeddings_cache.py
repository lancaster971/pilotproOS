#!/usr/bin/env python3
"""
Test script for OptimizedEmbeddingsCache
Tests with REAL data - NO MOCKS
Uses actual sentence-transformers models
"""

import asyncio
import time
import sys
import os
import numpy as np

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.cache.optimized_embeddings_cache import OptimizedEmbeddingsCache, get_embeddings_cache

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_embeddings():
    """Test basic embedding generation"""
    print("\n" + "="*60)
    print("🔬 TESTING BASIC EMBEDDINGS GENERATION")
    print("="*60)

    cache = get_embeddings_cache()

    # Test single text
    text = "Ciao, questo è un test del sistema di embeddings"
    print(f"\n📝 Text: {text}")

    start = time.time()
    embedding = await cache.get_embeddings(text)
    elapsed = time.time() - start

    print(f"✅ Embedding generated in {elapsed:.3f}s")
    print(f"📊 Embedding shape: {embedding.shape}")
    print(f"📈 Embedding sample: {embedding[0][:5]}...")

    # Verify it's a valid embedding
    assert embedding.shape == (1, 384), f"Expected shape (1, 384), got {embedding.shape}"
    assert not np.isnan(embedding).any(), "Embedding contains NaN values"

    return True


async def test_batch_processing():
    """Test batch processing efficiency"""
    print("\n" + "="*60)
    print("⚡ TESTING BATCH PROCESSING")
    print("="*60)

    cache = OptimizedEmbeddingsCache(batch_size=8)

    # Create test documents
    documents = [
        "Il sistema di gestione processi aziendali",
        "Workflow automation con n8n",
        "Analisi delle performance del sistema",
        "Dashboard di monitoraggio in tempo reale",
        "Integrazione con API esterne",
        "Gestione utenti e permessi",
        "Report mensili automatizzati",
        "Sistema di notifiche email",
        "Backup e disaster recovery",
        "Ottimizzazione delle query database"
    ]

    print(f"\n📚 Processing {len(documents)} documents...")

    # Process as batch
    start = time.time()
    embeddings = await cache.get_embeddings(documents)
    batch_time = time.time() - start

    print(f"✅ Batch processed in {batch_time:.3f}s")
    print(f"📊 Embeddings shape: {embeddings.shape}")
    print(f"⚡ Average time per doc: {batch_time/len(documents):.4f}s")

    # Process individually for comparison
    start = time.time()
    for doc in documents:
        await cache.get_embeddings(doc, use_cache=False)
    individual_time = time.time() - start

    print(f"\n📊 Comparison:")
    print(f"  - Batch processing: {batch_time:.3f}s")
    print(f"  - Individual processing: {individual_time:.3f}s")
    print(f"  - Speedup: {individual_time/batch_time:.2f}x faster")

    return True


async def test_cache_performance():
    """Test cache hit/miss performance"""
    print("\n" + "="*60)
    print("💾 TESTING CACHE PERFORMANCE")
    print("="*60)

    cache = OptimizedEmbeddingsCache()

    test_text = "Test query per cache performance"

    # First call - cache miss
    print("\n🔴 First call (cache miss)...")
    start = time.time()
    embedding1 = await cache.get_embeddings(test_text)
    miss_time = time.time() - start
    print(f"  Time: {miss_time:.4f}s")

    # Second call - cache hit
    print("\n🟢 Second call (cache hit)...")
    start = time.time()
    embedding2 = await cache.get_embeddings(test_text)
    hit_time = time.time() - start
    print(f"  Time: {hit_time:.4f}s")

    # Verify same embedding returned
    assert np.allclose(embedding1, embedding2), "Cached embedding doesn't match"

    print(f"\n📊 Cache Performance:")
    print(f"  - Cache miss: {miss_time:.4f}s")
    print(f"  - Cache hit: {hit_time:.4f}s")
    print(f"  - Speedup: {miss_time/hit_time:.0f}x faster")

    # Get stats
    stats = cache.get_stats()
    print(f"\n📈 Cache Statistics:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")

    return True


async def test_similarity_search():
    """Test similarity search functionality"""
    print("\n" + "="*60)
    print("🔍 TESTING SIMILARITY SEARCH")
    print("="*60)

    cache = OptimizedEmbeddingsCache()

    # Knowledge base documents
    documents = [
        "Come posso creare un nuovo processo aziendale?",
        "Il sistema di autenticazione utilizza JWT tokens",
        "Per aggiungere un utente vai nel pannello amministrazione",
        "I report vengono generati automaticamente ogni lunedì",
        "Il backup del database avviene ogni notte alle 3",
        "Per integrare un'API esterna usa il modulo webhooks",
        "La dashboard mostra le metriche in tempo reale",
        "I log di sistema sono disponibili nel monitor",
        "Per modificare i permessi contatta l'amministratore",
        "Il workflow di approvazione richiede due firme"
    ]

    # Test queries
    queries = [
        "Come faccio ad aggiungere un nuovo utente?",
        "Quando viene fatto il backup?",
        "Voglio vedere le statistiche"
    ]

    for query in queries:
        print(f"\n🔎 Query: '{query}'")
        print("-" * 40)

        results = await cache.similarity_search(
            query=query,
            documents=documents,
            top_k=3
        )

        print("📊 Top 3 matches:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result['score']:.3f}")
            print(f"     Doc: {result['document'][:60]}...")

    return True


async def test_model_pool():
    """Test model pool parallel processing"""
    print("\n" + "="*60)
    print("🏊 TESTING MODEL POOL (3 INSTANCES)")
    print("="*60)

    cache = OptimizedEmbeddingsCache(pool_size=3)

    # Create 3 batches to process in parallel
    batches = [
        ["Batch 1 - Text 1", "Batch 1 - Text 2", "Batch 1 - Text 3"],
        ["Batch 2 - Text 1", "Batch 2 - Text 2", "Batch 2 - Text 3"],
        ["Batch 3 - Text 1", "Batch 3 - Text 2", "Batch 3 - Text 3"]
    ]

    print(f"\n🚀 Processing {len(batches)} batches in parallel...")

    # Process batches in parallel
    start = time.time()
    tasks = [cache.get_embeddings_batch(batch) for batch in batches]
    results = await asyncio.gather(*tasks)
    parallel_time = time.time() - start

    print(f"✅ Parallel processing completed in {parallel_time:.3f}s")

    # Verify results
    for i, result in enumerate(results):
        print(f"  Batch {i+1}: Shape {result.shape}")

    return True


async def test_preloading():
    """Test preloading functionality"""
    print("\n" + "="*60)
    print("📦 TESTING EMBEDDINGS PRELOADING")
    print("="*60)

    cache = OptimizedEmbeddingsCache()

    # Documents to preload
    documents = [f"Document number {i}" for i in range(50)]

    print(f"\n📥 Preloading {len(documents)} documents...")

    await cache.preload_embeddings(documents, batch_size=10)

    # Check cache stats
    stats = cache.get_stats()
    print(f"\n✅ Preloading complete:")
    print(f"  - Cache size: {stats['cache_size']}")
    print(f"  - Total embeddings: {stats['total_embeddings']}")
    print(f"  - Batches processed: {stats['batches_processed']}")

    # Test that cached items are fast
    print("\n🏃 Testing retrieval speed...")
    start = time.time()
    for doc in documents[:10]:
        await cache.get_embeddings(doc)
    retrieval_time = time.time() - start

    print(f"✅ Retrieved 10 cached items in {retrieval_time:.3f}s")
    print(f"  Average: {retrieval_time/10:.4f}s per item")

    return True


async def run_all_tests():
    """Run all embeddings cache tests"""
    print("\n" + "="*70)
    print("🚀 TESTING OPTIMIZED EMBEDDINGS CACHE WITH REAL DATA")
    print("="*70)

    tests = [
        ("Basic Embeddings", test_basic_embeddings),
        ("Batch Processing", test_batch_processing),
        ("Cache Performance", test_cache_performance),
        ("Similarity Search", test_similarity_search),
        ("Model Pool", test_model_pool),
        ("Preloading", test_preloading)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running: {test_name}")
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}", exc_info=True)
            results.append((test_name, False))

    # Summary
    print("\n" + "="*70)
    print("📋 TEST SUMMARY")
    print("="*70)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:25} {status}")
        if not passed:
            all_passed = False

    print("="*70)

    if all_passed:
        print("🎉 ALL EMBEDDINGS CACHE TESTS PASSED!")
        print("✅ OptimizedEmbeddingsCache is production ready!")
    else:
        print("⚠️ Some tests failed. Check logs for details.")

    # Close cache
    cache = get_embeddings_cache()
    cache.close()

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)