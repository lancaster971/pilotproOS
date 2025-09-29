#!/usr/bin/env python3
"""
Test Supervisor with Real OpenAI API
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.agents import SupervisorAgent, AgentType
from app.core.router import RouterConfig
from app.security import MaskingConfig, UserLevel


async def test_real_openai():
    """Test with real OpenAI API"""
    print("Testing Supervisor with Real OpenAI API")
    print("=" * 60)

    # Check API key
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if not openai_key or len(openai_key) < 20:
        print("❌ No OpenAI API key found in .env")
        return

    print(f"✅ OpenAI API key loaded: {openai_key[:20]}...")

    # Create supervisor with real API
    router_config = RouterConfig(
        groq_api_key=os.environ.get("GROQ_API_KEY", ""),
        openai_api_key=openai_key,
        google_api_key=os.environ.get("GOOGLE_API_KEY", ""),
        audit_enabled=True
    )

    masking_config = MaskingConfig(
        user_level=UserLevel.BUSINESS,
        strict_mode=True,
        audit_enabled=True
    )

    print("\nInitializing Supervisor...")
    supervisor = SupervisorAgent(router_config, masking_config)

    # Check if OpenAI was loaded
    if hasattr(supervisor.supervisor_llm, '__class__'):
        llm_type = supervisor.supervisor_llm.__class__.__name__
        print(f"LLM Type: {llm_type}")

    # Test queries
    test_queries = [
        "Ciao Milhena, come stai?",
        "Mostra l'ultimo messaggio del workflow Fatture",
        "Analizza i dati del sistema e genera un report"
    ]

    print("\n" + "-" * 60)
    print("TESTING QUERIES WITH REAL OPENAI")
    print("-" * 60)

    for query in test_queries:
        print(f"\nQuery: '{query}'")

        try:
            result = await supervisor.process(
                query=query,
                session_id=f"real-test-{test_queries.index(query)}",
                user_level=UserLevel.BUSINESS
            )

            if result["success"]:
                print(f"✅ Response: '{result['response'][:100]}...'")

                # Show routing info if available
                if result.get("routing"):
                    routing = result["routing"]
                    print(f"   → Routed to: {routing.target_agent.value if hasattr(routing, 'target_agent') else 'N/A'}")
                    print(f"   → Confidence: {routing.confidence if hasattr(routing, 'confidence') else 'N/A'}")

                # Show metadata
                if result.get("metadata"):
                    meta = result["metadata"]
                    if "routing" in meta:
                        print(f"   → Agent: {meta['routing'].get('agent', 'N/A')}")
                    if "tokens_used" in meta:
                        print(f"   → Tokens: {meta['tokens_used']}")
                    if "cost" in meta:
                        print(f"   → Cost: ${meta['cost']:.6f}")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Exception: {e}")

    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_real_openai())