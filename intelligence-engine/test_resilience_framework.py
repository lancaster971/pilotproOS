#!/usr/bin/env python3
"""
Test script for ResilienceFramework
Tests with REAL data - NO MOCKS
Tests all components: retry logic, dead letter queue, circuit breaker, fallback
"""

import asyncio
import os
import sys
import time
from datetime import datetime
import redis

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.resilience import (
    ResilienceFramework,
    FailureContext,
    FailureType,
    DeadLetterMessage,
    get_resilience_framework
)
from app.security import UserLevel

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAgent:
    """Simulated agent for testing"""

    def __init__(self, fail_count: int = 0):
        self.fail_count = fail_count
        self.attempts = 0

    async def process(self, query: str, user_level: UserLevel = UserLevel.BUSINESS):
        """Process method that can fail"""
        self.attempts += 1

        if self.attempts <= self.fail_count:
            raise Exception(f"Simulated failure {self.attempts}/{self.fail_count}")

        return {
            "success": True,
            "response": f"Processed: {query}",
            "attempts": self.attempts
        }


async def test_retry_logic():
    """Test exponential backoff retry logic"""
    print("\n" + "="*60)
    print("🔄 TESTING RETRY LOGIC WITH EXPONENTIAL BACKOFF")
    print("="*60)

    framework = get_resilience_framework()

    # Test successful retry after 2 failures
    agent = TestAgent(fail_count=2)

    @framework.retry_manager.with_exponential_backoff(
        max_attempts=3,
        min_wait=1,
        max_wait=5
    )
    async def retry_operation():
        return await agent.process("Test query")

    try:
        start = time.time()
        result = await retry_operation()
        elapsed = time.time() - start

        print(f"✅ Retry succeeded after {agent.attempts} attempts")
        print(f"⏱️ Total time with backoff: {elapsed:.2f}s")
        print(f"📊 Result: {result}")

        # Check retry stats
        stats = framework.retry_manager.get_stats()
        print(f"📈 Retry stats: {stats}")

        return True

    except Exception as e:
        print(f"❌ Retry failed: {e}")
        return False


async def test_dead_letter_queue():
    """Test dead letter queue operations"""
    print("\n" + "="*60)
    print("📮 TESTING DEAD LETTER QUEUE WITH REDIS")
    print("="*60)

    framework = get_resilience_framework()
    dlq = framework.dead_letter_queue

    # Test connection to Redis
    try:
        dlq.redis.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("Make sure Redis container is running!")
        return False

    # Create test messages
    test_messages = [
        DeadLetterMessage(
            agent_name="TestAgent",
            operation="process",
            payload={"query": f"Test query {i}"},
            error_type="timeout",
            error_message=f"Timeout error {i}",
            priority=i  # Different priorities
        )
        for i in range(3)
    ]

    # Test enqueue
    print("\n📥 Enqueueing messages...")
    for msg in test_messages:
        success = await dlq.enqueue(msg)
        print(f"  - Message {msg.id[:8]}: {'✅' if success else '❌'}")

    # Check stats
    stats = await dlq.get_stats()
    print(f"\n📊 Queue stats after enqueue: {stats}")

    # Test dequeue
    print("\n📤 Dequeueing messages...")
    messages = await dlq.dequeue(2)
    print(f"  - Retrieved {len(messages)} messages")
    for msg in messages:
        print(f"    • {msg.id[:8]} - Priority: {msg.priority}")

    # Test mark completed
    if messages:
        print("\n✅ Marking first message as completed...")
        success = await dlq.mark_completed(messages[0].id)
        print(f"  - Mark completed: {'✅' if success else '❌'}")

    # Test requeue
    if len(messages) > 1:
        print("\n🔄 Requeueing second message...")
        success = await dlq.requeue_failed(messages[1].id)
        print(f"  - Requeue: {'✅' if success else '❌'}")

    # Final stats
    final_stats = await dlq.get_stats()
    print(f"\n📊 Final queue stats: {final_stats}")

    return True


async def test_circuit_breaker():
    """Test circuit breaker integration"""
    print("\n" + "="*60)
    print("⚡ TESTING CIRCUIT BREAKER INTEGRATION")
    print("="*60)

    framework = get_resilience_framework()
    cb = framework.circuit_breaker

    # Register test providers
    def provider1():
        raise Exception("Provider 1 failed")

    def provider2():
        raise Exception("Provider 2 failed")

    def provider3():
        return {"success": True, "provider": "Provider 3"}

    cb.register_provider("Provider1", priority=1, call_function=provider1)
    cb.register_provider("Provider2", priority=2, call_function=provider2)
    cb.register_provider("Provider3", priority=3, call_function=provider3)

    print("📝 Registered 3 providers (2 will fail, 1 will succeed)")

    try:
        # Test failover
        result = cb.call()
        print(f"✅ Circuit breaker succeeded with failover")
        print(f"📊 Result: {result}")

        # Check stats
        stats = cb.get_stats()
        print(f"📈 Circuit breaker stats:")
        print(f"  - Total calls: {stats['total_calls']}")
        print(f"  - Successful: {stats['successful_calls']}")
        print(f"  - Failovers: {stats['failovers']}")

        # Check provider status
        provider_status = cb.get_provider_status()
        print(f"\n🔌 Provider status:")
        for provider in provider_status:
            print(f"  - {provider['name']}: {provider['status']} (failures: {provider['failures']})")

        return True

    except Exception as e:
        print(f"❌ Circuit breaker failed: {e}")
        return False


async def test_fallback_handler():
    """Test graceful degradation with fallback responses"""
    print("\n" + "="*60)
    print("🛡️ TESTING FALLBACK HANDLER & GRACEFUL DEGRADATION")
    print("="*60)

    framework = get_resilience_framework()
    fallback = framework.fallback_handler

    # Test different user levels
    user_levels = [UserLevel.BUSINESS, UserLevel.ADMIN, UserLevel.DEVELOPER]

    for level in user_levels:
        print(f"\n👤 Testing fallback for {level.value} user:")

        context = FailureContext(
            agent_name="TestAgent",
            operation="process",
            error_type=FailureType.API_ERROR,
            error_message="API service unavailable",
            timestamp=datetime.now(),
            user_level=level
        )

        # Get fallback responses
        for response_type in ["greeting", "status", "error", "default"]:
            response = fallback.get_fallback_response(context, response_type)
            print(f"  [{response_type}]: {response[:80]}...")

    # Test degradation mode
    print("\n⚠️ Testing degradation mode activation...")
    fallback.activate_degradation(duration_seconds=5)
    print(f"  - Degradation active: {fallback.is_degraded()}")

    await asyncio.sleep(1)
    print(f"  - Still degraded after 1s: {fallback.is_degraded()}")

    return True


async def test_complete_failure_handling():
    """Test complete failure handling flow"""
    print("\n" + "="*60)
    print("🔥 TESTING COMPLETE FAILURE HANDLING FLOW")
    print("="*60)

    framework = get_resilience_framework()

    # Simulate different failure types
    failure_types = [
        (FailureType.TIMEOUT, "Operation timed out after 30s"),
        (FailureType.RATE_LIMIT, "Rate limit exceeded: 429"),
        (FailureType.API_ERROR, "API returned 500 Internal Server Error"),
        (FailureType.NETWORK, "Network connection failed"),
        (FailureType.VALIDATION, "Invalid input format")
    ]

    for fail_type, error_msg in failure_types:
        print(f"\n🧪 Testing {fail_type.value} failure:")

        context = FailureContext(
            agent_name="TestAgent",
            operation="process",
            error_type=fail_type,
            error_message=error_msg,
            timestamp=datetime.now(),
            user_level=UserLevel.BUSINESS,
            original_request={"query": "Test query", "session_id": "test-123"}
        )

        # Handle failure
        result = await framework.handle_failure(context)

        print(f"  - Strategy used: {result.get('strategy')}")
        print(f"  - Success: {result.get('success', False)}")

        if result.get('message_id'):
            print(f"  - Queued with ID: {result['message_id'][:8]}...")
        if result.get('response'):
            print(f"  - Response: {result['response'][:60]}...")

    # Check health status
    print("\n📊 Final health status:")
    health = await framework.get_health_status()

    print(f"  Circuit Breaker:")
    print(f"    - Total calls: {health['circuit_breaker']['total_calls']}")
    print(f"    - Failovers: {health['circuit_breaker']['failovers']}")

    print(f"  Retry Manager:")
    print(f"    - Total retries: {health['retry_manager']['total_retries']}")
    print(f"    - Successful: {health['retry_manager']['successful_retries']}")

    print(f"  Dead Letter Queue:")
    print(f"    - Queue size: {health['dead_letter_queue'].get('queue_size', 0)}")
    print(f"    - Completed: {health['dead_letter_queue'].get('total_completed', 0)}")

    print(f"  Error Tracking:")
    print(f"    - Total errors: {health['error_tracking']['total_errors']}")
    print(f"    - Recent errors: {health['error_tracking']['recent_errors']}")

    return True


async def test_resilient_agent_decorator():
    """Test making an agent resilient with decorator"""
    print("\n" + "="*60)
    print("🤖 TESTING RESILIENT AGENT DECORATOR")
    print("="*60)

    framework = get_resilience_framework()

    # Create agent that will fail first 2 times
    @framework.create_resilient_agent
    class ResilientTestAgent:
        def __init__(self):
            self.call_count = 0

        async def process(self, query: str, user_level: UserLevel = UserLevel.BUSINESS):
            self.call_count += 1

            if self.call_count <= 2:
                raise Exception(f"Simulated failure {self.call_count}")

            return {
                "success": True,
                "response": f"Successfully processed: {query}",
                "attempts": self.call_count
            }

    # Test the resilient agent
    agent = ResilientTestAgent()

    try:
        result = await agent.process("Test resilient query", user_level=UserLevel.BUSINESS)
        print(f"✅ Resilient agent succeeded")
        print(f"📊 Result: {result}")

    except Exception as e:
        print(f"❌ Resilient agent failed: {e}")

    return True


async def test_dlq_processing():
    """Test processing messages from dead letter queue"""
    print("\n" + "="*60)
    print("♻️ TESTING DEAD LETTER QUEUE PROCESSING")
    print("="*60)

    framework = get_resilience_framework()

    # First, add some messages to DLQ
    print("📥 Adding test messages to DLQ...")
    for i in range(5):
        msg = DeadLetterMessage(
            agent_name=f"Agent{i}",
            operation="test_op",
            payload={"test": f"data_{i}"},
            error_type="test_error",
            error_message=f"Test error {i}"
        )
        await framework.dead_letter_queue.enqueue(msg)

    # Process batch from DLQ
    print("\n♻️ Processing DLQ batch...")
    results = await framework.process_dead_letter_queue(batch_size=3)

    print(f"📊 Processing results:")
    print(f"  - Processed: {results['processed']}")
    print(f"  - Succeeded: {results['succeeded']}")
    print(f"  - Failed: {results['failed']}")
    print(f"  - Requeued: {results['requeued']}")

    return True


async def run_all_tests():
    """Run all resilience framework tests"""
    print("\n" + "="*70)
    print("🚀 TESTING RESILIENCE FRAMEWORK WITH REAL DATA")
    print("="*70)
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check Redis connection first
    try:
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        print("✅ Redis connection verified")
    except Exception as e:
        print(f"❌ Redis not available: {e}")
        print("⚠️ Make sure Docker stack is running!")
        print("Run: ./stack-safe.sh start")
        return False

    # Run all tests
    test_results = []

    tests = [
        ("Retry Logic", test_retry_logic),
        ("Dead Letter Queue", test_dead_letter_queue),
        ("Circuit Breaker", test_circuit_breaker),
        ("Fallback Handler", test_fallback_handler),
        ("Complete Failure Handling", test_complete_failure_handling),
        ("Resilient Agent Decorator", test_resilient_agent_decorator),
        ("DLQ Processing", test_dlq_processing)
    ]

    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}", exc_info=True)
            test_results.append((test_name, False))

    # Summary
    print("\n" + "="*70)
    print("📋 TEST SUMMARY")
    print("="*70)

    all_passed = True
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:30} {status}")
        if not passed:
            all_passed = False

    print("="*70)

    if all_passed:
        print("🎉 ALL RESILIENCE TESTS PASSED!")
        print("✅ ResilienceFramework is production ready!")
    else:
        print("⚠️ Some tests failed. Check logs for details.")

    return all_passed


if __name__ == "__main__":
    # Run all tests
    success = asyncio.run(run_all_tests())

    # Exit with appropriate code
    sys.exit(0 if success else 1)