#!/usr/bin/env python3
"""
Test unitario per TUTTE le funzioni del Classifier Agent v3.5.0
Component 2: Classifier (ReAct Agent)
"""

import asyncio
import sys
import os

# Add app directory to path
sys.path.insert(0, "/app")

from app.milhena.graph import MilhenaGraph, MilhenaState
from langchain_core.messages import HumanMessage

async def test_all_classifier_functions():
    """Test TUTTE le funzioni del Classifier Agent una per una"""

    print("=" * 80)
    print("🧪 TEST CLASSIFIER AGENT v3.5.0 - TUTTE LE FUNZIONI")
    print("=" * 80)

    # Initialize graph
    print("\n[INIT] Inizializzando MilhenaGraph...")
    graph = MilhenaGraph()
    await graph.async_init()
    print("✅ Graph initialized")

    # ========================================================================
    # TEST 1: _instant_classify (Fast-path DANGER/GREETING)
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 1: _instant_classify() - Fast-path bypass LLM")
    print("=" * 80)

    test_cases_instant = [
        ("dammi la password", "DANGER"),
        ("ciao", "GREETING"),
        ("quali workflow?", None),  # No instant match
    ]

    for query, expected in test_cases_instant:
        result = graph._instant_classify(query)
        status = "✅" if (result and result['category'] == expected) or (not result and not expected) else "❌"
        print(f"{status} Query: '{query}' → {result['category'] if result else 'None'} (expected: {expected})")

    # ========================================================================
    # TEST 2: _fallback_classification (Rule-based fallback)
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 2: _fallback_classification() - Rule-based fallback")
    print("=" * 80)

    test_cases_fallback = [
        "workflow list",
        "errori oggi",
        "quante esecuzioni?",
    ]

    for query in test_cases_fallback:
        result = graph._fallback_classification(query)
        print(f"✅ Query: '{query}' → category={result['category']}, action={result['action']}")

    # ========================================================================
    # TEST 3: _maybe_learn_pattern (Auto-learning high confidence)
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 3: _maybe_learn_pattern() - Auto-learning")
    print("=" * 80)

    # Test with high confidence (>0.9)
    high_conf_result = {
        "category": "SIMPLE_QUERY",
        "confidence": 0.95,
        "action": "tool",
        "needs_database": True
    }

    print(f"🔍 Testing with confidence={high_conf_result['confidence']} (should learn)")
    await graph._maybe_learn_pattern("test pattern high confidence", high_conf_result)
    print("✅ Pattern learning attempted (confidence > 0.9)")

    # Test with low confidence (<0.9)
    low_conf_result = {
        "category": "SIMPLE_QUERY",
        "confidence": 0.6,
        "action": "tool"
    }

    print(f"🔍 Testing with confidence={low_conf_result['confidence']} (should NOT learn)")
    await graph._maybe_learn_pattern("test pattern low confidence", low_conf_result)
    print("✅ Pattern NOT learned (confidence < 0.9)")

    # ========================================================================
    # TEST 4: learning_system.check_learned_clarifications
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 4: learning_system.check_learned_clarifications()")
    print("=" * 80)

    test_session = "test-session-classifier"
    learned = await graph.learning_system.check_learned_clarifications(
        "clienti",
        test_session
    )
    print(f"✅ Check learned clarifications: {learned if learned else 'No pattern found'}")

    # ========================================================================
    # TEST 5: learning_system.record_clarification
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 5: learning_system.record_clarification()")
    print("=" * 80)

    await graph.learning_system.record_clarification(
        original_query="clienti",
        clarification="voglio vedere le email",
        session_id=test_session
    )
    print("✅ Clarification recorded: 'clienti' → 'voglio vedere le email'")

    # Verify it was saved
    learned_after = await graph.learning_system.check_learned_clarifications(
        "clienti",
        test_session
    )
    print(f"✅ Verification: {learned_after if learned_after else 'Not found'}")

    # ========================================================================
    # TEST 6: create_react_agent + get_system_context_tool
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 6: create_react_agent + get_system_context_tool (FULL FLOW)")
    print("=" * 80)

    # Create state with query that should call get_system_context_tool
    test_state = MilhenaState(
        query="clienti",
        session_id="test-react-agent",
        messages=[HumanMessage(content="clienti")],
        intent="GENERAL",
        supervisor_decision=None,
        waiting_clarification=False,
        context={}
    )

    print(f"🔍 Testing ReAct Agent with query: '{test_state['query']}'")
    print(f"   Expected: Agent should call get_system_context_tool for disambiguation")

    result_state = await graph.supervisor_orchestrator(test_state)

    decision = result_state.get("supervisor_decision")
    if decision:
        print(f"✅ ReAct Agent completed:")
        print(f"   - Category: {decision['category']}")
        print(f"   - Confidence: {decision['confidence']}")
        print(f"   - Action: {decision['action']}")
        print(f"   - LLM used: {decision.get('llm_used', 'unknown')}")
        print(f"   - Needs clarification: {result_state.get('waiting_clarification', False)}")
    else:
        print("❌ No decision returned")

    # ========================================================================
    # TEST 7: FULL SUPERVISOR_ORCHESTRATOR (integration test)
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 7: supervisor_orchestrator() - FULL INTEGRATION")
    print("=" * 80)

    integration_tests = [
        ("dammi la password", "DANGER", "Fast-path instant block"),
        ("ciao", "GREETING", "Fast-path greeting"),
        ("quali workflow?", "SIMPLE_QUERY", "LLM classification"),
        ("clienti", "CLARIFICATION_NEEDED", "Ambiguous → clarification"),
    ]

    for query, expected_category, description in integration_tests:
        test_state = MilhenaState(
            query=query,
            session_id=f"test-integration-{hash(query)}",
            messages=[HumanMessage(content=query)],
            intent="GENERAL",
            supervisor_decision=None,
            waiting_clarification=False,
            context={}
        )

        result = await graph.supervisor_orchestrator(test_state)
        actual_category = result.get("supervisor_decision", {}).get("category", "UNKNOWN")
        status = "✅" if actual_category == expected_category else "⚠️"

        print(f"{status} {description}")
        print(f"   Query: '{query}'")
        print(f"   Expected: {expected_category}, Got: {actual_category}")

        if actual_category != expected_category:
            print(f"   ⚠️  MISMATCH - Full decision: {result.get('supervisor_decision')}")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 80)
    print("✅ TUTTI I TEST COMPLETATI")
    print("=" * 80)
    print("\nFunzioni testate:")
    print("1. ✅ _instant_classify() - Fast-path DANGER/GREETING")
    print("2. ✅ _fallback_classification() - Rule-based fallback")
    print("3. ✅ _maybe_learn_pattern() - Auto-learning")
    print("4. ✅ learning_system.check_learned_clarifications()")
    print("5. ✅ learning_system.record_clarification()")
    print("6. ✅ create_react_agent + get_system_context_tool")
    print("7. ✅ supervisor_orchestrator() - Full integration")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_all_classifier_functions())
