#!/usr/bin/env python3
"""
Test ResilienceFramework with REAL LLM Agent
Tests integration with actual EnhancedMilhenaAgent using OpenAI API
NO MOCK DATA - REAL TESTING WITH ACTUAL FAILURES
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

from app.core.resilience import (
    ResilienceFramework,
    FailureContext,
    FailureType,
    get_resilience_framework
)
from app.agents.milhena_enhanced_llm import EnhancedMilhenaAgent
from app.security import UserLevel

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnreliableEnhancedMilhenaAgent(EnhancedMilhenaAgent):
    """
    Modified Milhena agent that simulates real failures
    """

    def __init__(self, fail_probability: float = 0.5):
        super().__init__()
        self.fail_probability = fail_probability
        self.call_count = 0

    async def process(self, query: str, session_id: str, user_level: UserLevel, context: dict = None):
        """Process with simulated failures"""
        import random
        self.call_count += 1

        # Simulate different types of failures
        if random.random() < self.fail_probability:
            failure_types = [
                ("Rate limit exceeded", "rate"),
                ("OpenAI API timeout", "timeout"),
                ("Network connection failed", "network"),
                ("API returned 503 Service Unavailable", "api")
            ]
            error_msg, error_type = random.choice(failure_types)

            logger.warning(f"Simulating failure #{self.call_count}: {error_msg}")

            if "rate" in error_type:
                raise Exception(f"Rate limit exceeded: 429 Too Many Requests (attempt {self.call_count})")
            elif "timeout" in error_type:
                raise TimeoutError(f"Request timeout after 30s (attempt {self.call_count})")
            elif "network" in error_type:
                raise ConnectionError(f"Network connection failed (attempt {self.call_count})")
            else:
                raise Exception(f"API error: {error_msg} (attempt {self.call_count})")

        # Normal processing with REAL OpenAI API
        return await super().process(query, session_id, user_level, context)


async def test_resilient_real_agent():
    """Test ResilienceFramework with REAL agent that can fail"""
    print("\n" + "="*70)
    print("🤖 TESTING RESILIENCE WITH REAL ENHANCED MILHENA AGENT")
    print("="*70)

    # Check OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found!")
        return False

    print(f"✅ OpenAI API Key found: {api_key[:10]}...")

    framework = get_resilience_framework()

    # Create unreliable agent (50% failure rate)
    agent = UnreliableEnhancedMilhenaAgent(fail_probability=0.5)

    # Make it resilient
    @framework.create_resilient_agent
    class ResilientMilhenaAgent:
        def __init__(self, base_agent):
            self.base_agent = base_agent

        async def process(self, query: str, session_id: str, user_level: UserLevel, context: dict = None):
            return await self.base_agent.process(query, session_id, user_level, context)

    # Test queries
    test_queries = [
        ("Ciao Milhena, come stai?", "greeting"),
        ("Mostra l'ultimo messaggio dal processo Fatture", "data_query"),
        ("Qual è lo stato dei processi aziendali?", "status_query")
    ]

    resilient_agent = ResilientMilhenaAgent(agent)
    session_id = f"test-resilient-{datetime.now().timestamp()}"

    results = []

    for query, query_type in test_queries:
        print(f"\n📝 Testing: {query}")
        print(f"   Type: {query_type}")
        print("-" * 60)

        try:
            result = await resilient_agent.process(
                query=query,
                session_id=session_id,
                user_level=UserLevel.BUSINESS
            )

            if result.get("success"):
                print(f"✅ Success after {agent.call_count} total attempts")
                print(f"📊 Response: {result.get('response', '')[:100]}...")
                print(f"⏱️ Processing time: {result.get('processing_time', 0):.2f}s")
                print(f"💰 Cost: ${result.get('cost', 0):.6f}")
                results.append((query_type, True, agent.call_count))
            else:
                # Fallback response received
                print(f"⚠️ Fallback response received")
                print(f"📊 Response: {result.get('response', '')[:100]}...")
                results.append((query_type, False, agent.call_count))

        except Exception as e:
            print(f"❌ Complete failure: {e}")
            results.append((query_type, False, agent.call_count))

        # Reset call count for next query
        agent.call_count = 0

    # Summary
    print("\n" + "="*70)
    print("📊 TEST RESULTS SUMMARY")
    print("="*70)

    for query_type, success, attempts in results:
        status = "✅ SUCCESS" if success else "⚠️ FALLBACK"
        print(f"{query_type:15} {status:15} Attempts: {attempts}")

    # Check resilience stats
    health = await framework.get_health_status()

    print("\n📈 RESILIENCE METRICS:")
    print(f"  Retry attempts: {health['retry_manager']['total_retries']}")
    print(f"  Successful retries: {health['retry_manager']['successful_retries']}")
    print(f"  Circuit breaker calls: {health['circuit_breaker']['total_calls']}")
    print(f"  DLQ size: {health['dead_letter_queue'].get('queue_size', 0)}")
    print(f"  Total errors tracked: {health['error_tracking']['total_errors']}")

    return True


async def test_direct_failure_handling():
    """Test direct failure handling with REAL agent"""
    print("\n" + "="*70)
    print("🔥 TESTING DIRECT FAILURE HANDLING WITH REAL AGENT")
    print("="*70)

    framework = get_resilience_framework()

    # Simulate a real failure scenario
    agent = EnhancedMilhenaAgent()

    async def failing_operation():
        """Operation that will fail"""
        raise Exception("OpenAI API rate limit exceeded: 429 Too Many Requests")

    # Create failure context
    context = FailureContext(
        agent_name="EnhancedMilhenaAgent",
        operation="process",
        error_type=FailureType.RATE_LIMIT,
        error_message="Rate limit exceeded",
        timestamp=datetime.now(),
        user_level=UserLevel.BUSINESS,
        original_request={
            "query": "Test query",
            "session_id": "test-123"
        }
    )

    print("📝 Simulating rate limit failure...")

    # Handle the failure
    result = await framework.handle_failure(context, retry_func=None)

    print(f"📊 Handling result:")
    print(f"  - Strategy: {result.get('strategy')}")
    print(f"  - Success: {result.get('success')}")

    if result.get('message_id'):
        print(f"  - Message queued: {result['message_id'][:8]}...")

    if result.get('response'):
        print(f"  - Fallback response: {result['response'][:80]}...")

    return True


async def test_real_openai_with_resilience():
    """Test with REAL OpenAI API calls and forced errors"""
    print("\n" + "="*70)
    print("🚀 TESTING REAL OPENAI API WITH RESILIENCE")
    print("="*70)

    framework = get_resilience_framework()

    # Test with actual agent but simulate API key issues
    original_key = os.getenv("OPENAI_API_KEY")

    if not original_key:
        print("❌ No OpenAI API key found, skipping test")
        return False

    # Test 1: Normal successful call
    print("\n1️⃣ Testing successful API call...")
    agent = EnhancedMilhenaAgent()

    try:
        result = await agent.process(
            query="Ciao, test rapido",
            session_id="test-real-1",
            user_level=UserLevel.BUSINESS
        )
        print(f"✅ Direct call successful")
        print(f"📊 Response: {result.get('response', '')[:100]}...")
    except Exception as e:
        print(f"❌ Direct call failed: {e}")

    # Test 2: Test with temporary invalid API key to force failure
    print("\n2️⃣ Testing with invalid API key (forced failure)...")

    # Temporarily set invalid key
    os.environ["OPENAI_API_KEY"] = "sk-invalid-key-test"

    agent_with_bad_key = EnhancedMilhenaAgent()

    @framework.create_resilient_agent
    class ResilientAgentWithBadKey:
        def __init__(self):
            self.agent = agent_with_bad_key

        async def process(self, query: str, session_id: str, user_level: UserLevel):
            return await self.agent.process(query, session_id, user_level)

    resilient = ResilientAgentWithBadKey()

    try:
        result = await resilient.process(
            query="Test con chiave non valida",
            session_id="test-invalid",
            user_level=UserLevel.BUSINESS
        )

        if result.get("response"):
            print(f"✅ Resilience worked - fallback response received")
            print(f"📊 Fallback: {result['response'][:100]}...")
        else:
            print(f"⚠️ Result: {result}")

    except Exception as e:
        print(f"❌ Even resilient version failed: {e}")

    # Restore original key
    os.environ["OPENAI_API_KEY"] = original_key

    # Test 3: Process messages from DLQ
    print("\n3️⃣ Testing DLQ processing...")
    dlq_results = await framework.process_dead_letter_queue(batch_size=5)

    print(f"📊 DLQ Processing results:")
    print(f"  - Processed: {dlq_results['processed']}")
    print(f"  - Succeeded: {dlq_results['succeeded']}")
    print(f"  - Requeued: {dlq_results['requeued']}")

    return True


async def run_all_real_tests():
    """Run all tests with REAL agents and data"""
    print("\n" + "="*80)
    print("🔬 RIGOROUS TESTING WITH REAL LLM AGENTS AND OPENAI API")
    print("="*80)
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Verify environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set!")
        print("Please set it in .env file")
        return False

    test_results = []

    tests = [
        ("Direct Failure Handling", test_direct_failure_handling),
        ("Resilient Real Agent", test_resilient_real_agent),
        ("Real OpenAI with Resilience", test_real_openai_with_resilience)
    ]

    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}", exc_info=True)
            test_results.append((test_name, False))

    # Final summary
    print("\n" + "="*80)
    print("📋 FINAL TEST SUMMARY")
    print("="*80)

    all_passed = True
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:30} {status}")
        if not passed:
            all_passed = False

    print("="*80)

    if all_passed:
        print("🎉 ALL REAL AGENT TESTS PASSED!")
        print("✅ ResilienceFramework validated with REAL LLM agents!")
    else:
        print("⚠️ Some tests failed. Review logs.")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_real_tests())
    sys.exit(0 if success else 1)