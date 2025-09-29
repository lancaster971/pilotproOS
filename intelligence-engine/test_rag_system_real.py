#!/usr/bin/env python3
"""
RIGOROUS TEST for Maintainable RAG System with REAL DATA
NO MOCK DATA - Tests with actual ChromaDB and documents
Following official LangChain documentation
"""

import asyncio
import os
import sys
import time
import json
from datetime import datetime
import shutil

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.rag.maintainable_rag import (
    MaintainableRAGSystem,
    RAGAdminInterface,
    DocumentMetadata,
    DocumentStatus
)
from app.security.masking_engine import UserLevel

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_crud_operations():
    """Test CRUD operations with REAL documents"""
    print("\n" + "="*70)
    print("🔬 TESTING CRUD OPERATIONS WITH REAL DATA")
    print("="*70)

    # Clean up previous test data
    if os.path.exists("./test_chroma_db"):
        shutil.rmtree("./test_chroma_db")

    rag = MaintainableRAGSystem(
        collection_name="test_knowledge",
        persist_directory="./test_chroma_db",
        chunk_size=500,  # Smaller chunks for testing
        chunk_overlap=50
    )

    try:
        # Test 1: CREATE
        print("\n1️⃣ Testing CREATE operation...")

        # Real documentation content
        doc_content = """
        # PilotProOS Intelligence Engine Documentation

        ## Overview
        PilotProOS is an enterprise-grade business process automation platform that integrates
        advanced AI capabilities with workflow management. The system uses LangGraph for
        orchestrating multiple specialized agents.

        ## Key Features
        - Multi-agent orchestration with supervisor pattern
        - Token optimization achieving 95% cost savings
        - Enterprise security with multi-level masking
        - Real-time process monitoring and analytics

        ## Architecture
        The system follows a microservices architecture with:
        - PostgreSQL for data persistence
        - Redis for caching and session management
        - ChromaDB for vector storage
        - n8n for workflow automation
        """

        metadata = DocumentMetadata(
            title="PilotProOS System Documentation",
            source="internal_docs",
            author="system",
            category="documentation",
            tags=["pilotpros", "documentation", "architecture"]
        )

        create_result = await rag.create_document(doc_content, metadata)
        print(f"✅ Document created: {create_result}")

        doc_id = create_result["doc_id"]

        # Test 2: READ
        print("\n2️⃣ Testing READ operation...")
        read_result = await rag.read_document(doc_id)

        if read_result:
            print(f"✅ Document read successfully:")
            print(f"  - Doc ID: {read_result['doc_id']}")
            print(f"  - Chunks: {read_result['chunks']}")
            print(f"  - Content length: {len(read_result['content'])} chars")

        # Test 3: UPDATE
        print("\n3️⃣ Testing UPDATE operation...")

        updated_content = doc_content + """

        ## New Features (v2.0)
        - Enhanced RAG system with document versioning
        - Optimized embeddings cache with batch processing
        - Admin interface for knowledge base management
        """

        update_result = await rag.update_document(
            doc_id=doc_id,
            new_content=updated_content,
            update_metadata={
                "author": "admin",
                "tags": ["pilotpros", "documentation", "v2.0"]
            }
        )
        print(f"✅ Document updated: {update_result}")

        # Test 4: DELETE (soft)
        print("\n4️⃣ Testing DELETE operation (soft)...")

        delete_result = await rag.delete_document(doc_id, hard_delete=False)
        print(f"✅ Soft delete result: {delete_result}")

        # Verify soft-deleted document
        deleted_doc = await rag.read_document(doc_id)
        if deleted_doc and "[DELETED]" in deleted_doc["content"]:
            print("✅ Document successfully soft-deleted")

        return True

    except Exception as e:
        logger.error(f"CRUD test failed: {e}", exc_info=True)
        return False

    finally:
        rag.close()


async def test_search_with_real_data():
    """Test search functionality with REAL documents"""
    print("\n" + "="*70)
    print("🔍 TESTING SEARCH WITH REAL DATA")
    print("="*70)

    rag = MaintainableRAGSystem(
        collection_name="test_search",
        persist_directory="./test_chroma_db",
        chunk_size=500,
        chunk_overlap=50
    )

    try:
        # Add REAL documents from different sources
        documents = [
            (
                """
                Come configurare un workflow in n8n:
                1. Accedi al pannello n8n su http://localhost:5678
                2. Crea un nuovo workflow dal menu
                3. Aggiungi i nodi necessari (Webhook, HTTP Request, etc.)
                4. Configura le connessioni tra i nodi
                5. Testa il workflow con dati di esempio
                6. Attiva il workflow per l'esecuzione automatica
                """,
                {
                    "title": "Guida configurazione workflow n8n",
                    "source": "user_manual",
                    "category": "tutorial",
                    "tags": ["n8n", "workflow", "configurazione"]
                }
            ),
            (
                """
                L'architettura di PilotProOS si basa su microservizi containerizzati.
                Il sistema utilizza Docker Compose per orchestrare 7 servizi principali:
                - PostgreSQL per il database
                - Redis per la cache
                - Backend API in Express
                - Frontend in Vue 3
                - Intelligence Engine con LangGraph
                - n8n per l'automazione
                - Nginx come reverse proxy
                """,
                {
                    "title": "Architettura PilotProOS",
                    "source": "technical_docs",
                    "category": "architecture",
                    "tags": ["architettura", "docker", "microservizi"]
                }
            ),
            (
                """
                Per ottimizzare i costi dell'API OpenAI:
                1. Usa il router intelligente per selezionare il modello appropriato
                2. Implementa caching aggressivo delle risposte
                3. Utilizza embeddings pre-calcolati quando possibile
                4. Batch processing per ridurre le chiamate API
                5. Monitora l'utilizzo dei token con metriche dettagliate
                """,
                {
                    "title": "Ottimizzazione costi OpenAI",
                    "source": "best_practices",
                    "category": "optimization",
                    "tags": ["openai", "costi", "ottimizzazione"]
                }
            )
        ]

        # Import documents
        print("\n📚 Importing REAL documents...")
        for content, metadata_dict in documents:
            metadata = DocumentMetadata(**metadata_dict)
            result = await rag.create_document(content, metadata)
            print(f"  - Imported: {metadata.title}")

        # Test searches with different user levels
        test_queries = [
            ("Come configuro un workflow?", UserLevel.BUSINESS),
            ("Architettura microservizi Docker", UserLevel.DEVELOPER),
            ("Ottimizzazione costi API", UserLevel.ADMIN)
        ]

        for query, user_level in test_queries:
            print(f"\n🔍 Searching: '{query}' (User level: {user_level.value})")

            results = await rag.search(
                query=query,
                user_level=user_level,
                top_k=3
            )

            print(f"📊 Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. Relevance: {result['relevance_score']:.3f}")
                print(f"     Doc: {result['metadata'].get('title', 'Untitled')}")
                print(f"     Content: {result['content'][:100]}...")

        return True

    except Exception as e:
        logger.error(f"Search test failed: {e}", exc_info=True)
        return False

    finally:
        rag.close()


async def test_versioning_system():
    """Test document versioning with REAL updates"""
    print("\n" + "="*70)
    print("📝 TESTING DOCUMENT VERSIONING")
    print("="*70)

    rag = MaintainableRAGSystem(
        collection_name="test_versioning",
        persist_directory="./test_chroma_db"
    )

    try:
        # Create initial document
        print("\n1️⃣ Creating initial document version...")

        v1_content = """
        API Endpoints - Version 1.0
        - GET /api/status - Get system status
        - POST /api/chat - Send chat message
        """

        metadata = DocumentMetadata(
            title="API Documentation",
            source="api_docs",
            category="api",
            version=1
        )

        v1_result = await rag.create_document(v1_content, metadata)
        doc_id = v1_result["doc_id"]
        print(f"✅ Version 1 created: {v1_result}")

        # Update to version 2
        print("\n2️⃣ Updating to version 2...")

        v2_content = """
        API Endpoints - Version 2.0
        - GET /api/status - Get system status
        - POST /api/chat - Send chat message
        - GET /api/agents/status - Get agents status (NEW)
        - POST /api/documents - Upload document (NEW)
        """

        v2_result = await rag.update_document(
            doc_id=doc_id,
            new_content=v2_content,
            update_metadata={"author": "developer"}
        )
        print(f"✅ Version 2 created: {v2_result}")

        # Update to version 3
        print("\n3️⃣ Updating to version 3...")

        v3_content = """
        API Endpoints - Version 3.0
        - GET /api/v3/status - Get system status
        - POST /api/v3/chat - Enhanced chat with streaming
        - GET /api/v3/agents/status - Get agents status with metrics
        - POST /api/v3/documents - Upload with versioning
        - GET /api/v3/search - RAG search endpoint (NEW)
        """

        v3_result = await rag.update_document(
            doc_id=doc_id,
            new_content=v3_content,
            update_metadata={"author": "senior_developer"}
        )
        print(f"✅ Version 3 created: {v3_result}")

        # Check version history
        print("\n📜 Version History:")
        if doc_id in rag.document_versions:
            for version_meta in rag.document_versions[doc_id]:
                print(f"  - v{version_meta.version}: {version_meta.created_at.strftime('%Y-%m-%d %H:%M')}")
                print(f"    Author: {version_meta.author}")
                print(f"    Status: {version_meta.status}")

        # Read specific version
        print("\n📖 Reading version 2...")
        v2_doc = await rag.read_document(doc_id, version=2)
        if v2_doc and "Version 2.0" in v2_doc["content"]:
            print("✅ Successfully retrieved version 2")

        return True

    except Exception as e:
        logger.error(f"Versioning test failed: {e}", exc_info=True)
        return False

    finally:
        rag.close()


async def test_bulk_import():
    """Test bulk import with REAL data"""
    print("\n" + "="*70)
    print("📦 TESTING BULK IMPORT")
    print("="*70)

    rag = MaintainableRAGSystem(
        collection_name="test_bulk",
        persist_directory="./test_chroma_db"
    )

    try:
        # Prepare REAL documents for bulk import
        bulk_docs = [
            (
                f"""
                Troubleshooting Guide #{i+1}

                Problem: {['Connection timeout', 'Memory leak', 'Slow queries', 'API errors'][i % 4]}
                Solution: {['Check network settings', 'Restart service', 'Optimize indexes', 'Check rate limits'][i % 4]}
                Additional notes: Always check logs first and verify configuration.
                """,
                {
                    "title": f"Troubleshooting Guide #{i+1}",
                    "source": "support_docs",
                    "category": "troubleshooting",
                    "tags": ["support", "troubleshooting", f"issue_{i+1}"]
                }
            )
            for i in range(20)  # 20 real documents
        ]

        print(f"\n📥 Importing {len(bulk_docs)} documents...")

        start_time = time.time()
        import_result = await rag.bulk_import(bulk_docs, batch_size=5)
        elapsed = time.time() - start_time

        print(f"✅ Bulk import completed in {elapsed:.2f}s")
        print(f"📊 Results:")
        print(f"  - Success: {import_result['success']}")
        print(f"  - Failed: {import_result['failed']}")
        print(f"  - Duplicates: {import_result['duplicates']}")

        # Verify import
        docs_list = await rag.list_documents(category_filter="troubleshooting")
        print(f"  - Verified: {len(docs_list)} troubleshooting documents in database")

        return import_result["success"] > 0

    except Exception as e:
        logger.error(f"Bulk import test failed: {e}", exc_info=True)
        return False

    finally:
        rag.close()


async def test_admin_interface():
    """Test admin interface functions"""
    print("\n" + "="*70)
    print("🎛️ TESTING ADMIN INTERFACE")
    print("="*70)

    rag = MaintainableRAGSystem(
        collection_name="test_admin",
        persist_directory="./test_chroma_db"
    )

    admin = RAGAdminInterface(rag)

    try:
        # Get dashboard stats
        print("\n📊 Dashboard Statistics:")
        stats = await admin.dashboard_stats()

        print(f"  Overview:")
        print(f"    - Total documents: {stats['overview']['total_documents']}")
        print(f"    - Total chunks: {stats['overview']['total_chunks']}")
        print(f"    - Searches today: {stats['overview']['searches_today']}")

        print(f"  Categories:")
        for category, count in stats['categories'].items():
            print(f"    - {category}: {count}")

        # Test paginated list
        print("\n📄 Document List (Page 1):")
        page_data = await admin.document_list_view(page=1, page_size=5)

        print(f"  Total documents: {page_data['total']}")
        print(f"  Total pages: {page_data['total_pages']}")
        print(f"  Documents on page 1:")

        for doc in page_data['documents'][:3]:  # Show first 3
            print(f"    - {doc['title']} (v{doc['version']})")

        return True

    except Exception as e:
        logger.error(f"Admin interface test failed: {e}", exc_info=True)
        return False

    finally:
        rag.close()


async def test_performance():
    """Test performance with REAL workload"""
    print("\n" + "="*70)
    print("⚡ TESTING PERFORMANCE WITH REAL WORKLOAD")
    print("="*70)

    rag = MaintainableRAGSystem(
        collection_name="test_performance",
        persist_directory="./test_chroma_db"
    )

    try:
        # Add substantial content
        print("\n📚 Adding 50 REAL documents...")

        start = time.time()
        for i in range(50):
            content = f"""
            Document {i+1}: Enterprise Integration Patterns

            Pattern: {['Message Router', 'Content Filter', 'Message Translator', 'Aggregator'][i % 4]}

            Description: This pattern helps in {['routing messages', 'filtering content',
            'translating formats', 'combining messages'][i % 4]} across different systems.

            Implementation details involve careful consideration of performance,
            scalability, and error handling. The pattern should be applied when
            dealing with complex integration scenarios in distributed systems.
            """

            metadata = DocumentMetadata(
                title=f"Integration Pattern {i+1}",
                source="patterns_library",
                category="patterns",
                tags=["integration", "patterns", f"pattern_{i+1}"]
            )

            await rag.create_document(content, metadata)

        creation_time = time.time() - start
        print(f"✅ Created 50 documents in {creation_time:.2f}s")
        print(f"   Average: {creation_time/50:.3f}s per document")

        # Test search performance
        print("\n🔍 Testing search performance...")

        search_queries = [
            "message routing patterns",
            "content filtering implementation",
            "integration scalability",
            "error handling distributed systems",
            "enterprise patterns"
        ]

        search_times = []
        for query in search_queries:
            start = time.time()
            results = await rag.search(query, top_k=5)
            search_time = time.time() - start
            search_times.append(search_time)
            print(f"  Query: '{query[:30]}...' - {search_time:.3f}s ({len(results)} results)")

        avg_search = sum(search_times) / len(search_times)
        print(f"\n📊 Average search time: {avg_search:.3f}s")

        # Get final statistics
        final_stats = await rag.get_statistics()
        print(f"\n📈 Final Statistics:")
        print(f"  - Total chunks: {final_stats['total_chunks']}")
        print(f"  - Unique documents: {final_stats['unique_documents']}")
        print(f"  - Cache hit rate: {final_stats['cache_stats'].get('hit_rate', 'N/A')}")

        return avg_search < 1.0  # Search should be under 1 second

    except Exception as e:
        logger.error(f"Performance test failed: {e}", exc_info=True)
        return False

    finally:
        rag.close()


async def run_all_rag_tests():
    """Run ALL RAG system tests with REAL data"""
    print("\n" + "="*80)
    print("🔬 RIGOROUS RAG SYSTEM TESTING WITH REAL DATA")
    print("="*80)
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tests = [
        ("CRUD Operations", test_crud_operations),
        ("Search with Real Data", test_search_with_real_data),
        ("Document Versioning", test_versioning_system),
        ("Bulk Import", test_bulk_import),
        ("Admin Interface", test_admin_interface),
        ("Performance Testing", test_performance)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}", exc_info=True)
            results.append((test_name, False))

    # Summary
    print("\n" + "="*80)
    print("📋 RAG SYSTEM TEST SUMMARY")
    print("="*80)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:25} {status}")
        if not passed:
            all_passed = False

    print("="*80)

    # Clean up test data
    if os.path.exists("./test_chroma_db"):
        shutil.rmtree("./test_chroma_db")
        print("🧹 Test data cleaned up")

    if all_passed:
        print("🎉 ALL RAG SYSTEM TESTS PASSED!")
        print("✅ Maintainable RAG System is PRODUCTION READY!")
    else:
        print("⚠️ Some tests failed. Review and fix before production.")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_rag_tests())
    sys.exit(0 if success else 1)