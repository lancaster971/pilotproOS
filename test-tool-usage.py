#!/usr/bin/env python3
"""
Test DETTAGLIATO per verificare uso di get_system_context_tool
"""

import asyncio
import sys
import json

sys.path.insert(0, "/app")

from app.milhena.graph import MilhenaGraph, MilhenaState
from langchain_core.messages import HumanMessage

async def test_tool_usage():
    """Verifica che get_system_context_tool venga chiamato correttamente"""

    print("=" * 80)
    print("🔍 TEST get_system_context_tool USAGE")
    print("=" * 80)

    # Initialize graph
    graph = MilhenaGraph()
    await graph.async_init()

    # Test case: Query ambigua che DEVE chiamare il tool
    test_cases = [
        {
            "query": "clienti",
            "expected_tool_call": True,
            "reason": "Termine ambiguo - deve disambiguare"
        },
        {
            "query": "errori Flow_X",
            "expected_tool_call": True,
            "reason": "Workflow name da verificare"
        },
        {
            "query": "quali workflow?",
            "expected_tool_call": False,  # Query chiara
            "reason": "Query chiara - no disambiguazione"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST CASE {i}: '{test['query']}'")
        print(f"Expected tool call: {test['expected_tool_call']}")
        print(f"Reason: {test['reason']}")
        print("=" * 80)

        # Create state
        state = MilhenaState(
            query=test['query'],
            session_id=f"test-tool-{i}",
            messages=[HumanMessage(content=test['query'])],
            intent="GENERAL",
            supervisor_decision=None,
            waiting_clarification=False,
            context={}
        )

        # Call supervisor (includes ReAct Agent)
        result = await graph.supervisor_orchestrator(state)

        # Check decision
        decision = result.get("supervisor_decision", {})
        print(f"\n📊 RESULT:")
        print(f"   Category: {decision.get('category', 'UNKNOWN')}")
        print(f"   Confidence: {decision.get('confidence', 0)}")
        print(f"   LLM used: {decision.get('llm_used', 'unknown')}")

        # Check messages for tool calls
        messages = result.get("messages", [])
        print(f"\n📨 MESSAGE CHAIN ({len(messages)} messages):")

        tool_called = False
        for j, msg in enumerate(messages):
            msg_type = type(msg).__name__
            print(f"   [{j}] {msg_type}", end="")

            # Check for tool calls in AIMessage
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_called = True
                print(f" → TOOL CALLS: {len(msg.tool_calls)}")
                for tc in msg.tool_calls:
                    print(f"       └─ {tc.get('name', 'unknown')}({tc.get('args', {})})")
            # Check for tool messages
            elif hasattr(msg, 'name'):
                print(f" → Tool response: {msg.name}")
                if hasattr(msg, 'content'):
                    content_preview = str(msg.content)[:150]
                    print(f"       └─ {content_preview}...")
            else:
                if hasattr(msg, 'content'):
                    content_preview = str(msg.content)[:80]
                    print(f" → {content_preview}...")
                else:
                    print()

        # Verify expectation
        status = "✅" if tool_called == test['expected_tool_call'] else "❌"
        print(f"\n{status} Tool called: {tool_called} (expected: {test['expected_tool_call']})")

        if not tool_called and test['expected_tool_call']:
            print("⚠️  WARNING: Tool should have been called but wasn't!")
            print("   Possible reasons:")
            print("   - LLM didn't recognize need for disambiguation")
            print("   - Prompt not clear enough about when to call tool")
            print("   - Fast-path bypassed LLM entirely")

    print("\n" + "=" * 80)
    print("✅ TEST COMPLETATO")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_tool_usage())
