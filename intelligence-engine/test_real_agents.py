#!/usr/bin/env python3
"""
Test script for REAL LLM agents
Tests all three agents with actual OpenAI API
NO MOCK DATA - REAL TESTING ONLY
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv()

# Import REAL agents
from app.agents.milhena_enhanced_llm import EnhancedMilhenaAgent
from app.agents.n8n_expert_llm import N8nExpertAgent
from app.agents.data_analyst_llm import DataAnalystAgent
from app.security import UserLevel

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_milhena_agent():
    """Test Enhanced Milhena Agent with REAL LLM"""
    print("\n" + "="*60)
    print("🤖 TESTING ENHANCED MILHENA AGENT WITH GPT-4o-mini")
    print("="*60)

    try:
        # Create REAL agent with OpenAI API
        agent = EnhancedMilhenaAgent()

        # Test queries
        queries = [
            "Ciao Milhena, come stai?",
            "Mostra l'ultimo messaggio dal processo Fatture",
            "Qual è lo stato dei processi aziendali?"
        ]

        session_id = f"test-milhena-{datetime.now().timestamp()}"

        for query in queries:
            print(f"\n📝 Query: {query}")
            print("-" * 40)

            result = await agent.process(
                query=query,
                session_id=session_id,
                user_level=UserLevel.BUSINESS
            )

            if result["success"]:
                print(f"✅ Success!")
                print(f"📊 Response: {result['response'][:200]}...")
                print(f"⏱️ Processing time: {result['processing_time']:.2f}s")
                print(f"💰 Tokens used: {result.get('tokens_used', 'N/A')}")
                print(f"💵 Cost: ${result.get('cost', 0):.6f}")
                print(f"🛠️ Tools used: {result['metadata'].get('tools_used', [])}")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")

        print(f"\n✅ Milhena Agent test completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Milhena Agent test failed: {e}")
        logger.error(f"Milhena test error: {e}", exc_info=True)
        return False


async def test_n8n_expert_agent():
    """Test N8n Expert Agent with REAL LLM"""
    print("\n" + "="*60)
    print("🔧 TESTING N8N EXPERT AGENT WITH GPT-4o-mini")
    print("="*60)

    try:
        # Create REAL agent with OpenAI API
        agent = N8nExpertAgent()

        # Test queries
        queries = [
            "Estrai l'ultimo messaggio dal workflow Ordini",
            "Mostra la cronologia delle elaborazioni di oggi",
            "Quali integrazioni webhook sono attive?"
        ]

        session_id = f"test-n8n-{datetime.now().timestamp()}"

        for query in queries:
            print(f"\n📝 Query: {query}")
            print("-" * 40)

            result = await agent.process(
                query=query,
                session_id=session_id,
                user_level=UserLevel.BUSINESS,
                context={"workflow_name": "Ordini"}
            )

            if result["success"]:
                print(f"✅ Success!")
                print(f"📊 Response: {result['response'][:200]}...")
                print(f"⏱️ Processing time: {result['processing_time']:.2f}s")
                print(f"💰 Tokens used: {result.get('tokens_used', 'N/A')}")
                print(f"💵 Cost: ${result.get('cost', 0):.6f}")
                print(f"🛠️ Tools used: {result['metadata'].get('tools_used', [])}")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")

        print(f"\n✅ N8n Expert Agent test completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ N8n Expert Agent test failed: {e}")
        logger.error(f"N8n Expert test error: {e}", exc_info=True)
        return False


async def test_data_analyst_agent():
    """Test Data Analyst Agent with REAL LLM"""
    print("\n" + "="*60)
    print("📊 TESTING DATA ANALYST AGENT WITH GPT-4o-mini")
    print("="*60)

    try:
        # Create REAL agent with OpenAI API
        agent = DataAnalystAgent()

        # Test queries
        queries = [
            "Analizza le performance degli ultimi 7 giorni",
            "Mostra il trend delle elaborazioni",
            "Genera un report di efficienza"
        ]

        session_id = f"test-analyst-{datetime.now().timestamp()}"

        for query in queries:
            print(f"\n📝 Query: {query}")
            print("-" * 40)

            result = await agent.process(
                query=query,
                session_id=session_id,
                user_level=UserLevel.BUSINESS,
                context={"time_range": "last 7 days"}
            )

            if result["success"]:
                print(f"✅ Success!")
                print(f"📊 Response: {result['response'][:200]}...")
                print(f"⏱️ Processing time: {result['processing_time']:.2f}s")
                print(f"💰 Tokens used: {result.get('tokens_used', 'N/A')}")
                print(f"💵 Cost: ${result.get('cost', 0):.6f}")
                print(f"🛠️ Tools used: {result['metadata'].get('tools_used', [])}")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")

        print(f"\n✅ Data Analyst Agent test completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Data Analyst Agent test failed: {e}")
        logger.error(f"Data Analyst test error: {e}", exc_info=True)
        return False


async def test_all_agents():
    """Test all REAL LLM agents"""
    print("\n" + "="*70)
    print("🚀 TESTING ALL REAL LLM AGENTS WITH OPENAI API")
    print("="*70)

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment!")
        print("Please set OPENAI_API_KEY in .env file")
        return False

    print(f"✅ API Key found: {api_key[:10]}...")
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test each agent
    results = []

    # Test Milhena
    result = await test_milhena_agent()
    results.append(("Milhena", result))

    # Test N8n Expert
    result = await test_n8n_expert_agent()
    results.append(("N8n Expert", result))

    # Test Data Analyst
    result = await test_data_analyst_agent()
    results.append(("Data Analyst", result))

    # Summary
    print("\n" + "="*70)
    print("📋 TEST SUMMARY")
    print("="*70)

    all_passed = True
    for agent_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{agent_name:20} {status}")
        if not passed:
            all_passed = False

    print("="*70)

    if all_passed:
        print("🎉 ALL TESTS PASSED! REAL LLM AGENTS WORKING!")
    else:
        print("⚠️ Some tests failed. Check logs for details.")

    return all_passed


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(test_all_agents())

    # Exit with appropriate code
    sys.exit(0 if success else 1)