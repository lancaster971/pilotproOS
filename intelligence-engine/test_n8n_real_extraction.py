#!/usr/bin/env python3
"""
TEST RIGOROSO N8N MESSAGE EXTRACTION
=====================================
Test with REAL data from database
NO MOCK - ONLY REAL DATABASE DATA
"""

import asyncio
import json
import sys
from datetime import datetime
from app.tools.n8n_message_tools import (
    get_last_message_from_workflow,
    extract_webhook_data,
    search_workflow_messages,
    get_workflow_execution_history,
    extract_batch_messages
)

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'


async def test_real_extraction():
    """Test message extraction with REAL database data"""

    print(f"{BOLD}{'='*80}{RESET}")
    print(f"{BLUE}{BOLD}🧪 N8N MESSAGE EXTRACTION - REAL DATA TEST{RESET}")
    print(f"{BOLD}{'='*80}{RESET}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    all_tests_passed = True

    # Test 1: Get workflows list first
    print(f"{YELLOW}📋 TEST 1: Search for Available Workflows{RESET}")
    print("-" * 40)

    try:
        result = await search_workflow_messages(
            search_term="",
            time_range_days=30,
            max_results=5
        )
        print(f"{GREEN}✅ Search completed{RESET}")
        print("Result preview:")
        print(result[:500] + "..." if len(result) > 500 else result)
        print()
    except Exception as e:
        print(f"{RED}❌ Search failed: {e}{RESET}")
        all_tests_passed = False

    # Test 2: Get last message from a specific workflow
    print(f"{YELLOW}📧 TEST 2: Get Last Message from Workflow{RESET}")
    print("-" * 40)

    # Try different workflow names
    test_workflows = ["test", "webhook", "chat", "outlook", "embedder"]

    message_found = False
    for wf_name in test_workflows:
        try:
            print(f"  Trying workflow: '{wf_name}'...")
            result = await get_last_message_from_workflow(wf_name)

            if "Nessuna elaborazione trovata" not in result:
                print(f"{GREEN}✅ Found execution for '{wf_name}'{RESET}")
                print("Message content:")
                print(result)
                message_found = True
                break
            else:
                print(f"  → No executions for '{wf_name}'")

        except Exception as e:
            print(f"  → Error for '{wf_name}': {e}")

    if not message_found:
        print(f"{YELLOW}⚠️  No workflow messages found (might be empty database){RESET}")

    print()

    # Test 3: Get execution history
    print(f"{YELLOW}📜 TEST 3: Get Execution History{RESET}")
    print("-" * 40)

    try:
        # Try with a known workflow or generic search
        result = await get_workflow_execution_history("", limit=5)
        print(f"{GREEN}✅ History retrieved{RESET}")
        print("History preview:")
        print(result[:500] + "..." if len(result) > 500 else result)
        print()
    except Exception as e:
        print(f"{RED}❌ History retrieval failed: {e}{RESET}")
        all_tests_passed = False

    # Test 4: Extract webhook data
    print(f"{YELLOW}🔗 TEST 4: Extract Webhook Data{RESET}")
    print("-" * 40)

    try:
        result = await extract_webhook_data("", time_range_hours=24*7)
        print(f"{GREEN}✅ Webhook data extracted{RESET}")
        print("Webhook data:")
        print(result[:500] + "..." if len(result) > 500 else result)
        print()
    except Exception as e:
        print(f"{RED}❌ Webhook extraction failed: {e}{RESET}")
        all_tests_passed = False

    # Test 5: Batch extraction
    print(f"{YELLOW}📊 TEST 5: Batch Message Extraction{RESET}")
    print("-" * 40)

    try:
        # Use empty list to get all workflows
        result = await extract_batch_messages(["outlook", "embedder", "chat"], time_range_hours=24*7)
        print(f"{GREEN}✅ Batch extraction completed{RESET}")
        print("Batch results:")
        print(result[:800] + "..." if len(result) > 800 else result)
        print()
    except Exception as e:
        print(f"{RED}❌ Batch extraction failed: {e}{RESET}")
        all_tests_passed = False

    # Summary
    print(f"{BOLD}{'='*80}{RESET}")
    print(f"{BLUE}{BOLD}📊 TEST SUMMARY{RESET}")
    print(f"{BOLD}{'='*80}{RESET}")

    if all_tests_passed:
        print(f"{GREEN}{BOLD}✅ ALL TESTS PASSED - N8N TOOLS WORKING!{RESET}")
        return True
    else:
        print(f"{RED}{BOLD}❌ SOME TESTS FAILED - CHECK LOGS{RESET}")
        return False


async def test_specific_execution():
    """Test extraction from a specific execution ID if we know one"""

    print(f"\n{YELLOW}🔍 DIRECT DATABASE TEST{RESET}")
    print("-" * 40)

    import asyncpg

    conn = await asyncpg.connect(
        'postgresql://pilotpros_user:pilotpros_secure_pass_2025@postgres-dev:5432/pilotpros_db'
    )

    # Get a real execution with data
    query = """
        SELECT
            e.id,
            w.name,
            ed.data
        FROM n8n.execution_entity e
        JOIN n8n.workflow_entity w ON e."workflowId" = w.id::text
        JOIN n8n.execution_data ed ON ed."executionId" = e.id
        WHERE ed.data IS NOT NULL
            AND ed.data != '{}'
        ORDER BY e.id DESC
        LIMIT 1;
    """

    result = await conn.fetchrow(query)

    if result:
        print(f"Found execution ID {result['id']} for workflow '{result['name']}'")

        # Parse the data
        if result['data']:
            try:
                data = json.loads(result['data'])

                # Try to find messages
                if 'resultData' in data and 'runData' in data['resultData']:
                    run_data = data['resultData']['runData']
                    print(f"Found {len(run_data)} nodes with data")

                    for node_name, node_data in run_data.items():
                        print(f"\n  Node: {node_name}")
                        if isinstance(node_data, list) and len(node_data) > 0:
                            first_run = node_data[0]
                            if 'data' in first_run and 'main' in first_run['data']:
                                main_data = first_run['data']['main']
                                if main_data and len(main_data) > 0 and len(main_data[0]) > 0:
                                    item = main_data[0][0]
                                    if 'json' in item:
                                        print(f"    Data keys: {list(item['json'].keys())[:10]}")
                                        # Look for message
                                        for key in ['message', 'text', 'content', 'output']:
                                            if key in item['json']:
                                                print(f"    → Found '{key}': {str(item['json'][key])[:100]}...")
                                                break
            except Exception as e:
                print(f"Error parsing data: {e}")
    else:
        print("No executions with data found")

    await conn.close()


if __name__ == "__main__":
    # Run main tests
    success = asyncio.run(test_real_extraction())

    # Run direct database test
    asyncio.run(test_specific_execution())

    sys.exit(0 if success else 1)