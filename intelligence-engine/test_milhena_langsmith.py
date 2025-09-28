#!/usr/bin/env python3
"""
Test Milhena v3.0 with LangSmith Tracing
This script tests Milhena and shows traces in LangSmith dashboard
"""
import asyncio
import os
from datetime import datetime
import requests
import json
from typing import Dict, Any

# Configure LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "milhena-v3-production"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")

# API Configuration
BASE_URL = "http://localhost:8000"
MILHENA_API = f"{BASE_URL}/api/milhena"

def print_header(text: str):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60)

def print_result(label: str, value: Any):
    """Print formatted result"""
    print(f"  {label}: {value}")

async def test_health():
    """Test health endpoint"""
    print_header("Testing Health Endpoint")

    response = requests.get(f"{MILHENA_API}/health")
    result = response.json()

    print_result("Status", result.get("status"))
    print_result("Service", result.get("service"))
    print_result("LangSmith", result.get("langsmith"))

    return result.get("langsmith") == "enabled"

async def test_chat(query: str, session_id: str = None) -> Dict[str, Any]:
    """Test chat endpoint"""
    print_header(f"Testing Chat: {query[:50]}...")

    payload = {
        "query": query,
        "session_id": session_id
    }

    response = requests.post(f"{MILHENA_API}/chat", json=payload)
    result = response.json()

    print_result("Success", result.get("success"))
    print_result("Intent", result.get("intent"))
    print_result("Cached", result.get("cached"))
    print_result("Response", result.get("response")[:100] + "...")
    print_result("Trace ID", result.get("trace_id"))

    return result

async def test_feedback(session_id: str, query: str, response: str, feedback_type: str):
    """Test feedback endpoint"""
    print_header(f"Submitting {feedback_type} Feedback")

    payload = {
        "session_id": session_id,
        "query": query,
        "response": response,
        "feedback_type": feedback_type
    }

    response = requests.post(f"{MILHENA_API}/feedback", json=payload)
    result = response.json()

    print_result("Status", result.get("status"))
    print_result("Message", result.get("message"))

    return result

async def test_stats():
    """Test stats endpoint"""
    print_header("Testing Stats Endpoint")

    response = requests.get(f"{MILHENA_API}/stats")
    result = response.json()

    print_result("Total Queries", result.get("total_queries"))
    print_result("Cache Hit Rate", f"{result.get('cache_hit_rate', 0)*100:.1f}%")
    print_result("Accuracy Rate", f"{result.get('accuracy_rate', 0)*100:.1f}%")

    return result

async def run_test_suite():
    """Run complete test suite"""
    print("\n" + "🚀"*20)
    print(" MILHENA v3.0 - LANGSMITH INTEGRATION TEST")
    print("🚀"*20)

    # Check LangSmith API key
    if not os.getenv("LANGCHAIN_API_KEY"):
        print("\n⚠️  WARNING: LANGCHAIN_API_KEY not set!")
        print("   Set it to see traces in LangSmith dashboard")
        print("   export LANGCHAIN_API_KEY='your-key-here'")
    else:
        print(f"\n✅ LangSmith API Key configured")
        print(f"📊 Project: milhena-v3-production")
        print(f"🔗 Dashboard: https://smith.langchain.com")

    # Test health
    langsmith_enabled = await test_health()

    if not langsmith_enabled:
        print("\n⚠️  LangSmith is not enabled. Set LANGCHAIN_API_KEY to enable tracing.")

    # Test queries
    test_queries = [
        {
            "query": "Ciao Milhena, come stai oggi?",
            "expected_intent": "GENERAL"
        },
        {
            "query": "Il sistema è andato a puttane, cosa è successo?",
            "expected_intent": "ERROR"
        },
        {
            "query": "Qual è lo stato dei processi attivi?",
            "expected_intent": "STATUS"
        },
        {
            "query": "Mostrami le metriche di performance di oggi",
            "expected_intent": "METRIC"
        },
        {
            "query": "Come configuro un nuovo workflow?",
            "expected_intent": "CONFIG"
        },
        {
            "query": "Aiutami a capire come funziona il sistema",
            "expected_intent": "HELP"
        }
    ]

    session_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    for test in test_queries:
        result = await test_chat(test["query"], session_id)

        # Verify intent
        if result.get("intent") == test["expected_intent"]:
            print(f"  ✅ Intent correctly identified as {test['expected_intent']}")
        else:
            print(f"  ❌ Expected {test['expected_intent']}, got {result.get('intent')}")

        # Test feedback
        feedback_type = "positive" if result.get("intent") == test["expected_intent"] else "negative"
        await test_feedback(
            session_id=session_id,
            query=test["query"],
            response=result.get("response", ""),
            feedback_type=feedback_type
        )

        await asyncio.sleep(1)  # Rate limiting

    # Test cache hit
    print_header("Testing Cache Hit (Repeating Query)")
    cached_result = await test_chat("Qual è lo stato dei processi attivi?", session_id)

    if cached_result.get("cached"):
        print("  ✅ Cache working correctly")
    else:
        print("  ⚠️  Cache miss on repeated query")

    # Get stats
    stats = await test_stats()

    # Summary
    print_header("TEST SUMMARY")
    print(f"""
  📊 LangSmith Project: milhena-v3-production
  🔗 View traces at: https://smith.langchain.com

  ✅ Endpoints tested:
     - Health Check
     - Chat (with {len(test_queries)} queries)
     - Feedback submission
     - Statistics
     - Cache functionality

  📈 Performance:
     - Total queries: {stats.get('total_queries', 0)}
     - Cache hit rate: {stats.get('cache_hit_rate', 0)*100:.1f}%
     - Accuracy: {stats.get('accuracy_rate', 0)*100:.1f}%

  💡 Next Steps:
     1. Check LangSmith dashboard for detailed traces
     2. Review conversation flow visualization
     3. Analyze token usage and costs
     4. Monitor learning system improvements
    """)

    if langsmith_enabled:
        print("\n🎉 SUCCESS: Milhena is fully integrated with LangSmith!")
        print("   Go to https://smith.langchain.com to see all traces")
    else:
        print("\n⚠️  Set LANGCHAIN_API_KEY to enable full LangSmith integration")

async def test_single_query(query: str):
    """Test a single query for quick debugging"""
    print_header(f"Single Query Test")
    result = await test_chat(query)

    print("\n📊 Full Response:")
    print(json.dumps(result, indent=2))

    if result.get("trace_id"):
        print(f"\n🔗 View trace: https://smith.langchain.com/public/{result['trace_id']}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Test single query from command line
        query = " ".join(sys.argv[1:])
        asyncio.run(test_single_query(query))
    else:
        # Run full test suite
        asyncio.run(run_test_suite())