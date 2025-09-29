#!/usr/bin/env python3
"""
Explore N8N Schema to find where execution data is stored
"""

import asyncio
import asyncpg

async def explore_schema():
    DATABASE_URL = 'postgresql://pilotpros_user:pilotpros_secure_pass_2025@postgres-dev:5432/pilotpros_db'

    print("🔍 Exploring N8N Schema\n")

    conn = await asyncpg.connect(DATABASE_URL)

    # 1. List all tables in n8n schema
    print("📊 TABLES IN N8N SCHEMA:")
    print("-" * 40)

    tables_query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'n8n'
        ORDER BY table_name;
    """

    tables = await conn.fetch(tables_query)
    for table in tables:
        print(f"  • {table['table_name']}")

        # Check if execution_data table exists
        if 'execution' in table['table_name'].lower() and 'entity' not in table['table_name'].lower():
            print(f"    → Found potential data table: {table['table_name']}")

    # 2. Check for execution_data table
    print("\n📦 LOOKING FOR EXECUTION DATA STORAGE:")
    print("-" * 40)

    # Check if execution_data exists
    exec_data_query = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'n8n'
        AND table_name = 'execution_data'
        ORDER BY ordinal_position;
    """

    exec_data_cols = await conn.fetch(exec_data_query)
    if exec_data_cols:
        print("✅ Found execution_data table!")
        for col in exec_data_cols:
            print(f"  • {col['column_name']}: {col['data_type']}")
            if col['column_name'] == 'data':
                print(f"    → This is the JSON data field!")
    else:
        print("❌ No execution_data table found")

    # 3. Check workflow_entity structure
    print("\n📋 WORKFLOW_ENTITY STRUCTURE:")
    print("-" * 40)

    wf_query = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'n8n'
        AND table_name = 'workflow_entity'
        LIMIT 10;
    """

    wf_cols = await conn.fetch(wf_query)
    for col in wf_cols:
        print(f"  • {col['column_name']}: {col['data_type']}")

    # 4. Sample workflow to see if executions are stored elsewhere
    print("\n🔍 SAMPLE WORKFLOW:")
    print("-" * 40)

    sample_wf = """
        SELECT id, name, active, "createdAt"
        FROM n8n.workflow_entity
        LIMIT 3;
    """

    workflows = await conn.fetch(sample_wf)
    for wf in workflows:
        print(f"  • {wf['name']} (ID: {wf['id']}, Active: {wf['active']})")

    # 5. Check if there's a relationship between tables
    print("\n🔗 CHECKING RELATIONSHIPS:")
    print("-" * 40)

    # Try to find execution data
    test_query = """
        SELECT
            e.id,
            e."workflowId",
            e.status,
            COUNT(d.*) as data_records
        FROM n8n.execution_entity e
        LEFT JOIN n8n.execution_data d ON d."executionId" = e.id
        WHERE e."stoppedAt" IS NOT NULL
        GROUP BY e.id, e."workflowId", e.status
        LIMIT 5;
    """

    try:
        results = await conn.fetch(test_query)
        if results:
            print("✅ Found execution_data relationship!")
            for r in results:
                print(f"  Execution {r['id']}: {r['data_records']} data records")
    except Exception as e:
        print(f"  ❌ No execution_data relationship: {e}")

    await conn.close()
    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    asyncio.run(explore_schema())