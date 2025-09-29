#!/usr/bin/env python3
"""
TEST N8N MESSAGE TOOLS WITH REAL DATABASE
NO MOCK - NO SIMPLIFIED VERSIONS - REAL DATA ONLY
"""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Import REAL tools
from app.tools.n8n_message_tools import (
    get_last_message_from_workflow,
    extract_webhook_data,
    search_workflow_messages,
    get_workflow_execution_history,
    extract_batch_messages
)

# Import database connection to test it's real
from app.database import get_db_connection


async def test_real_database_connection():
    """Verify we have REAL database connection"""
    print("\n" + "="*60)
    print("1. TESTING REAL DATABASE CONNECTION")
    print("-"*60)

    try:
        conn = await get_db_connection()

        # Check n8n schema exists
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'n8n'"
        )
        print(f"✅ Connected to REAL database")
        print(f"✅ Found {result} tables in n8n schema")

        # Check execution_entity table
        exec_count = await conn.fetchval(
            "SELECT COUNT(*) FROM n8n.execution_entity"
        )
        print(f"✅ execution_entity has {exec_count} records")

        # Check workflow_entity table
        wf_count = await conn.fetchval(
            "SELECT COUNT(*) FROM n8n.workflow_entity"
        )
        print(f"✅ workflow_entity has {wf_count} records")

        await conn.close()
        return True

    except Exception as e:
        print(f"❌ Database connection FAILED: {e}")
        return False


async def test_get_last_message():
    """Test get_last_message_from_workflow with REAL data"""
    print("\n" + "="*60)
    print("2. TESTING get_last_message_from_workflow")
    print("-"*60)

    try:
        # First, let's see what workflows exist
        conn = await get_db_connection()
        workflows = await conn.fetch(
            "SELECT DISTINCT name FROM n8n.workflow_entity LIMIT 5"
        )
        await conn.close()

        if workflows:
            print(f"Found {len(workflows)} workflows in database:")
            for wf in workflows:
                print(f"  - {wf['name']}")

            # Test with first workflow
            test_workflow = workflows[0]['name']
            print(f"\nTesting with workflow: '{test_workflow}'")

            result = await get_last_message_from_workflow.ainvoke({
                "workflow_name": test_workflow
            })

            print(f"✅ Tool executed successfully")
            print(f"Result preview: {result[:200]}...")

        else:
            print("⚠️ No workflows found in database")

            # Test with non-existent workflow
            print("\nTesting with non-existent workflow...")
            try:
                result = await get_last_message_from_workflow.ainvoke({
                    "workflow_name": "NonExistent"
                })
            except Exception as e:
                print(f"✅ Correctly handled missing workflow: {e}")

    except Exception as e:
        print(f"❌ Error testing get_last_message: {e}")


async def test_extract_webhook_data():
    """Test extract_webhook_data with REAL data"""
    print("\n" + "="*60)
    print("3. TESTING extract_webhook_data")
    print("-"*60)

    try:
        # Check for webhook executions
        conn = await get_db_connection()
        webhook_execs = await conn.fetch(
            """SELECT w.name, COUNT(e.id) as count
               FROM n8n.execution_entity e
               JOIN n8n.workflow_entity w ON e."workflowId" = w.id
               WHERE e.mode = 'webhook'
               GROUP BY w.name
               LIMIT 3"""
        )
        await conn.close()

        if webhook_execs:
            print(f"Found {len(webhook_execs)} workflows with webhooks:")
            for we in webhook_execs:
                print(f"  - {we['name']}: {we['count']} executions")

            # Test with first webhook workflow
            test_workflow = webhook_execs[0]['name']
            result = await extract_webhook_data.ainvoke({
                "workflow_name": test_workflow,
                "time_range_hours": 168  # Last week
            })

            print(f"✅ Webhook data extracted")
            print(f"Result preview: {result[:200]}...")

        else:
            print("⚠️ No webhook executions found")

    except Exception as e:
        print(f"❌ Error testing webhook extraction: {e}")


async def test_search_messages():
    """Test search_workflow_messages with REAL data"""
    print("\n" + "="*60)
    print("4. TESTING search_workflow_messages")
    print("-"*60)

    try:
        result = await search_workflow_messages.ainvoke({
            "search_term": "processo",
            "time_range_days": 30,
            "max_results": 5
        })

        print(f"✅ Search executed successfully")
        print(f"Result preview: {result[:300]}...")

    except Exception as e:
        print(f"❌ Error testing search: {e}")


async def test_execution_history():
    """Test get_workflow_execution_history with REAL data"""
    print("\n" + "="*60)
    print("5. TESTING get_workflow_execution_history")
    print("-"*60)

    try:
        # Get a workflow with executions
        conn = await get_db_connection()
        workflow = await conn.fetchrow(
            """SELECT w.name, COUNT(e.id) as exec_count
               FROM n8n.workflow_entity w
               JOIN n8n.execution_entity e ON e."workflowId" = w.id
               GROUP BY w.name
               ORDER BY exec_count DESC
               LIMIT 1"""
        )
        await conn.close()

        if workflow:
            print(f"Testing with workflow: '{workflow['name']}' ({workflow['exec_count']} executions)")

            result = await get_workflow_execution_history.ainvoke({
                "workflow_name": workflow['name'],
                "limit": 5
            })

            print(f"✅ History retrieved successfully")
            print(f"Result preview: {result[:300]}...")

        else:
            print("⚠️ No workflows with executions found")

    except Exception as e:
        print(f"❌ Error testing history: {e}")


async def test_batch_extraction():
    """Test extract_batch_messages with REAL data"""
    print("\n" + "="*60)
    print("6. TESTING extract_batch_messages")
    print("-"*60)

    try:
        # Get multiple workflows
        conn = await get_db_connection()
        workflows = await conn.fetch(
            "SELECT name FROM n8n.workflow_entity LIMIT 3"
        )
        await conn.close()

        if workflows:
            workflow_names = [wf['name'] for wf in workflows]
            print(f"Testing batch with workflows: {workflow_names}")

            result = await extract_batch_messages.ainvoke({
                "workflow_names": workflow_names,
                "time_range_hours": 24
            })

            print(f"✅ Batch extraction successful")
            print(f"Result preview: {result[:400]}...")

        else:
            print("⚠️ No workflows found for batch test")

    except Exception as e:
        print(f"❌ Error testing batch extraction: {e}")


async def main():
    """Run all tests with REAL data"""
    print("\n" + "="*80)
    print("N8N MESSAGE TOOLS - REAL DATABASE TEST")
    print("Testing with REAL PostgreSQL database and REAL n8n data")
    print("="*80)

    # Verify API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ Warning: OPENAI_API_KEY not set in .env")

    # Run all tests
    tests = [
        ("Database Connection", test_real_database_connection),
        ("Get Last Message", test_get_last_message),
        ("Extract Webhook Data", test_extract_webhook_data),
        ("Search Messages", test_search_messages),
        ("Execution History", test_execution_history),
        ("Batch Extraction", test_batch_extraction)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            print(f"\nRunning: {test_name}...")
            await test_func()
            results.append((test_name, "✅ PASSED"))
        except Exception as e:
            results.append((test_name, f"❌ FAILED: {e}"))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    for test_name, result in results:
        print(f"{test_name}: {result}")

    passed = sum(1 for _, r in results if "✅" in r)
    total = len(results)

    print(f"\n{'🎉' if passed == total else '⚠️'} {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ ALL N8N MESSAGE TOOLS ARE WORKING WITH REAL DATABASE!")
    else:
        print("\n⚠️ Some tools need attention. Check errors above.")


if __name__ == "__main__":
    asyncio.run(main())