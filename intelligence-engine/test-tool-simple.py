#!/usr/bin/env python3
"""
Test SEMPLICE: Verifica chiamata get_system_context_tool
"""

import asyncio
import sys
sys.path.insert(0, "/app")

from app.milhena.business_tools import get_system_context_tool
from app.milhena.graph import MilhenaGraph, MilhenaState
from langchain_core.messages import HumanMessage

async def main():
    print("=" * 80)
    print("TEST 1: Chiamata DIRETTA al tool")
    print("=" * 80)

    result = get_system_context_tool.invoke({})  # LangChain tool requires invoke
    print(f"✅ Tool eseguito - Output length: {len(result)} chars")
    print(f"✅ First 200 chars: {result[:200]}...")

    print("\n" + "=" * 80)
    print("TEST 2: ReAct Agent con query 'clienti'")
    print("=" * 80)

    graph = MilhenaGraph()
    await graph.async_init()

    state = MilhenaState(
        query="clienti",
        session_id="test-direct-tool",
        messages=[HumanMessage(content="clienti")],
        intent="GENERAL",
        supervisor_decision=None,
        waiting_clarification=False,
        context={}
    )

    print(f"\n📤 INPUT: '{state['query']}'")
    result = await graph.supervisor_orchestrator(state)

    messages = result.get("messages", [])
    print(f"\n📨 MESSAGE CHAIN: {len(messages)} messages\n")

    tool_found = False
    for i, msg in enumerate(messages):
        msg_type = type(msg).__name__
        print(f"[{i}] {msg_type}")

        # AIMessage with tool_calls
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            tool_found = True
            print(f"    └─ 🔧 TOOL CALLS: {len(msg.tool_calls)}")
            for tc in msg.tool_calls:
                print(f"        • {tc.get('name', 'unknown')}")

        # ToolMessage (tool response)
        if msg_type == "ToolMessage":
            tool_found = True
            print(f"    └─ 📦 Tool: {getattr(msg, 'name', 'unknown')}")
            content_len = len(msg.content) if hasattr(msg, 'content') else 0
            print(f"        • Response length: {content_len} chars")

    decision = result.get("supervisor_decision", {})
    print(f"\n📊 DECISION:")
    print(f"   Category: {decision.get('category')}")
    print(f"   Confidence: {decision.get('confidence')}")
    print(f"   LLM: {decision.get('llm_used')}")

    if tool_found:
        print(f"\n✅ Tool chiamato correttamente!")
    else:
        print(f"\n❌ Tool NON chiamato - Agent ha classificato senza disambiguazione")
        print(f"   Possible reasons:")
        print(f"   - Agent ha riconosciuto direttamente 'clienti' come EMAIL_ACTIVITY")
        print(f"   - Prompt non abbastanza esplicito su quando chiamare tool")
        print(f"   - LLM ha confidence sufficiente senza tool")

if __name__ == "__main__":
    asyncio.run(main())
