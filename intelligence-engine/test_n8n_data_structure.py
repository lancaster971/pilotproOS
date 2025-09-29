#!/usr/bin/env python3
"""
Test N8N Data Structure - REAL DATABASE
Explore the execution_entity.data field to understand structure
"""

import asyncio
import json
import asyncpg
import os
from datetime import datetime

async def explore_n8n_data():
    """Explore real n8n execution data structure"""

    # Database connection - Using correct credentials from .env
    DATABASE_URL = 'postgresql://pilotpros_user:pilotpros_secure_pass_2025@postgres-dev:5432/pilotpros_db'

    print("🔍 Exploring N8N Execution Data Structure\n")
    print("=" * 80)

    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database\n")

        # 1. Check table structure
        print("📊 EXECUTION_ENTITY COLUMNS:")
        print("-" * 40)

        columns_query = """
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = 'n8n'
            AND table_name = 'execution_entity'
            ORDER BY ordinal_position;
        """

        columns = await conn.fetch(columns_query)
        for col in columns:
            print(f"  • {col['column_name']}: {col['data_type']}")
            if col['column_name'] == 'data':
                print(f"    → This is where execution data is stored!")

        print("\n" + "=" * 80)

        # 2. Get a sample execution with data
        print("\n📦 SAMPLE EXECUTION DATA:")
        print("-" * 40)

        sample_query = """
            SELECT
                e.id,
                e."workflowId",
                e."startedAt",
                e."stoppedAt",
                e.status,
                e.mode,
                e.data,
                w.name as workflow_name
            FROM n8n.execution_entity e
            JOIN n8n.workflow_entity w ON e."workflowId" = w.id::text
            WHERE e.data IS NOT NULL
                AND e.data != '{}'::jsonb
            ORDER BY e."stoppedAt" DESC
            LIMIT 1;
        """

        result = await conn.fetchrow(sample_query)

        if result:
            print(f"Workflow: {result['workflow_name']}")
            print(f"Status: {result['status']}")
            print(f"Mode: {result['mode']}")
            print(f"Started: {result['startedAt']}")
            print(f"Data field type: {type(result['data'])}")

            # Parse the data field
            if result['data']:
                print("\n🔎 DATA FIELD STRUCTURE:")
                print("-" * 40)

                # Convert to dict if it's a JSON string
                if isinstance(result['data'], str):
                    data = json.loads(result['data'])
                else:
                    data = result['data']

                # Explore structure
                print(f"Top-level keys: {list(data.keys())[:10]}")

                # Look for execution data
                if 'executionData' in data:
                    exec_data = data['executionData']
                    print(f"\nexecutionData keys: {list(exec_data.keys())}")

                    # Check for resultData
                    if 'resultData' in exec_data:
                        result_data = exec_data['resultData']
                        print(f"resultData type: {type(result_data)}")

                        if isinstance(result_data, dict) and 'runData' in result_data:
                            run_data = result_data['runData']
                            print(f"\nrunData keys (nodes): {list(run_data.keys())[:5]}")

                            # Get data from first node
                            for node_name, node_data in run_data.items():
                                if node_data and len(node_data) > 0:
                                    print(f"\n📌 Node '{node_name}' data structure:")
                                    first_run = node_data[0]

                                    if 'data' in first_run:
                                        node_output = first_run['data']
                                        if 'main' in node_output and node_output['main']:
                                            items = node_output['main'][0] if node_output['main'] else []
                                            if items and len(items) > 0:
                                                print(f"  Output items: {len(items)}")
                                                first_item = items[0]
                                                if 'json' in first_item:
                                                    print(f"  JSON data keys: {list(first_item['json'].keys())[:10]}")

                                                    # Look for message fields
                                                    json_data = first_item['json']
                                                    for key in ['message', 'text', 'content', 'body', 'chatInput', 'query']:
                                                        if key in json_data:
                                                            value = str(json_data[key])[:100]
                                                            print(f"  → Found '{key}': {value}...")
                                    break

                # Also check for workflow static data
                if 'workflowData' in data:
                    workflow_data = data['workflowData']
                    if 'nodes' in workflow_data:
                        print(f"\nWorkflow has {len(workflow_data['nodes'])} nodes")

                        # Check node types
                        node_types = set()
                        for node in workflow_data['nodes']:
                            if 'type' in node:
                                node_types.add(node['type'])
                        print(f"Node types: {list(node_types)[:10]}")
        else:
            print("❌ No executions with data found")

        print("\n" + "=" * 80)

        # 3. Check for webhook executions
        print("\n🔗 WEBHOOK EXECUTIONS:")
        print("-" * 40)

        webhook_query = """
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT "workflowId") as unique_workflows
            FROM n8n.execution_entity
            WHERE mode = 'webhook'
                AND data IS NOT NULL;
        """

        webhook_stats = await conn.fetchrow(webhook_query)
        print(f"Total webhook executions: {webhook_stats['total']}")
        print(f"Unique workflows with webhooks: {webhook_stats['unique_workflows']}")

        # Close connection
        await conn.close()
        print("\n✅ Analysis complete!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(explore_n8n_data())