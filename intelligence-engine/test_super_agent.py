#!/usr/bin/env python3
"""
SUPER TEST AGENT - Verifica COMPLETA del sistema
Usa GPT-4o-mini con 10M tokens GRATIS!
"""

import os
import httpx
import json
import time
from datetime import datetime

print("\n" + "="*60)
print("🤖 SUPER TEST AGENT - VERIFICA COMPLETA SISTEMA")
print("="*60)

# Configurazione
BASE_URL = "http://localhost:8000"
TEST_MODEL = "gpt-4o-mini"  # 10M tokens GRATIS!

def test_connection(name, test_func):
    """Helper per testare connessioni"""
    print(f"\n🔍 Testing {name}...")
    try:
        result = test_func()
        print(f"   ✅ {name}: {result}")
        return True
    except Exception as e:
        print(f"   ❌ {name}: {str(e)[:100]}")
        return False

print(f"\n📊 Modello selezionato: {TEST_MODEL}")
print("   Token limit: 10,000,000 (10M) GRATIS")
print("   Provider: OpenAI")

# Step 1: Verifica che il modello sia disponibile
print("\n" + "-"*40)
print("STEP 1: Verifica disponibilità modello")
print("-"*40)

try:
    response = httpx.get(f"{BASE_URL}/api/models/list")
    models = response.json()

    if TEST_MODEL in models['models']:
        model_info = models['models'][TEST_MODEL]
        print(f"✅ Modello {TEST_MODEL} trovato!")
        print(f"   Description: {model_info['description']}")
        print(f"   Enabled: {model_info['enabled']}")
        print(f"   Loaded: {model_info['loaded']}")
    else:
        print(f"❌ Modello {TEST_MODEL} non configurato!")
except Exception as e:
    print(f"❌ Errore: {e}")

# Step 2: Test connessioni Stack
print("\n" + "-"*40)
print("STEP 2: Test connessioni Stack")
print("-"*40)

# Test diretto dal container
os.system(f"""docker exec intelligence-v2 python3 -c "
import psycopg2
import redis
import httpx
import os

print('Testing stack connections...')

# 1. PostgreSQL
try:
    conn = psycopg2.connect(
        host='host.docker.internal',
        port=5432,
        database='pilotpros_db',
        user='pilotpros_user',
        password='pilotpros_secure_pass_2025'
    )
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM information_schema.tables')
    count = cursor.fetchone()[0]
    print(f'✅ PostgreSQL: Connected ({count} tables found)')

    # Test write/read
    cursor.execute(\\\"\\\"\\\"
        CREATE TABLE IF NOT EXISTS test_agent (
            id SERIAL PRIMARY KEY,
            message TEXT,
            timestamp TIMESTAMP DEFAULT NOW()
        )
    \\\"\\\"\\\")
    cursor.execute(\\\"INSERT INTO test_agent (message) VALUES ('Test from Super Agent')\\\")
    conn.commit()

    cursor.execute('SELECT COUNT(*) FROM test_agent')
    test_count = cursor.fetchone()[0]
    print(f'   → Write/Read test: {test_count} records')

    cursor.close()
    conn.close()
except Exception as e:
    print(f'❌ PostgreSQL: {e}')

# 2. Redis
try:
    r = redis.Redis(host='host.docker.internal', port=6379, decode_responses=True)
    r.ping()

    # Test write/read
    test_key = f'test_agent_{datetime.now().isoformat()}'
    r.set(test_key, 'Super Agent Test Value', ex=60)
    value = r.get(test_key)

    print(f'✅ Redis: Connected (test value: {value})')

    # Test cache operations
    r.lpush('agent_logs', f'Test at {datetime.now()}')
    log_count = r.llen('agent_logs')
    print(f'   → Cache operations: {log_count} log entries')

except Exception as e:
    print(f'❌ Redis: {e}')

# 3. n8n Automation
try:
    n8n_url = os.getenv('N8N_URL', 'http://automation-engine-dev:5678')
    response = httpx.get(f'{n8n_url}/healthz', timeout=2)
    if response.status_code == 200:
        print(f'✅ n8n: Connected at {n8n_url}')
    else:
        print(f'⚠️  n8n: Status {response.status_code}')
except Exception as e:
    print(f'❌ n8n: Not reachable - {str(e)[:50]}')

# 4. Backend API
try:
    backend_url = 'http://backend-dev:3001'
    response = httpx.get(f'{backend_url}/api/health', timeout=2)
    if response.status_code == 200:
        print(f'✅ Backend API: Connected at {backend_url}')
    else:
        print(f'⚠️  Backend: Status {response.status_code}')
except Exception as e:
    print(f'❌ Backend: Not reachable - {str(e)[:50]}')
" 2>&1""")

# Step 3: Test LangSmith Tracing
print("\n" + "-"*40)
print("STEP 3: LangSmith Tracing")
print("-"*40)

os.system("""docker exec intelligence-v2 python3 -c "
import os

tracing = os.getenv('LANGCHAIN_TRACING_V2', '')
api_key = os.getenv('LANGCHAIN_API_KEY', '')
project = os.getenv('LANGCHAIN_PROJECT', '')

if tracing == 'true' and api_key:
    print(f'✅ LangSmith ACTIVE')
    print(f'   Project: {project}')
    print(f'   API Key: {api_key[:20]}...')
    print(f'   Dashboard: https://smith.langchain.com/o/a3dd14cc-afa9-5d2b-a118-03bdc03f11d8/projects/p/{project}')
else:
    print('❌ LangSmith NOT active')
" """)

# Step 4: Test Agent con Tool Calling
print("\n" + "-"*40)
print("STEP 4: Test Agent Execution")
print("-"*40)

print("\n🤖 Creando agent di test con tools...")

# Prepara la richiesta per l'agent
agent_request = {
    "message": "Test all system components and report status",
    "model_id": TEST_MODEL,
    "test_stack": True,
    "test_langsmith": True
}

try:
    print(f"📤 Inviando richiesta all'agent...")
    print(f"   Model: {TEST_MODEL}")
    print(f"   Message: {agent_request['message']}")

    # Se abbiamo configurato il test agent endpoint
    response = httpx.post(
        f"{BASE_URL}/api/test/agent",
        json=agent_request,
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ AGENT EXECUTION SUCCESS!")
        print(f"   Model used: {result.get('model_used', 'unknown')}")
        print(f"   Response time: {result.get('performance', {}).get('response_time_ms', 0)}ms")

        print(f"\n📊 Stack Status:")
        for component, status in result.get('stack_status', {}).items():
            print(f"   {component}: {status}")

        print(f"\n🔍 LangSmith Status:")
        langsmith = result.get('langsmith_status', {})
        print(f"   {langsmith.get('details', 'No details')}")

        print(f"\n💬 Agent Response:")
        print(f"   {result.get('response', 'No response')[:200]}...")

    elif response.status_code == 404:
        print("⚠️  Agent endpoint not found - trying simple chat...")

        # Fallback to simple chat
        chat_response = httpx.post(
            f"{BASE_URL}/api/chat",
            json={"message": "Hello, test the system", "model_id": TEST_MODEL},
            timeout=10
        )

        if chat_response.status_code == 200:
            result = chat_response.json()
            print(f"✅ Chat endpoint works!")
            print(f"   Response: {result.get('response', '')[:100]}...")
        else:
            print(f"❌ Chat failed: {chat_response.status_code}")
            print(f"   Error: {chat_response.text[:200]}")

    else:
        print(f"❌ Agent test failed: {response.status_code}")
        print(f"   Error: {response.text[:200]}")

except httpx.ConnectError:
    print("❌ Cannot connect to Intelligence Engine")
except httpx.TimeoutException:
    print("⚠️  Request timeout - agent might be processing")
except Exception as e:
    print(f"❌ Error: {e}")

# Step 5: Performance Metrics
print("\n" + "-"*40)
print("STEP 5: Performance Metrics")
print("-"*40)

try:
    response = httpx.get(f"{BASE_URL}/api/stats")
    if response.status_code == 200:
        stats = response.json()

        if stats.get('stats'):
            print("✅ Performance tracking active!")

            # Mostra statistiche per modello
            for model_id, model_stats in stats['stats'].items():
                print(f"\n📊 {model_id}:")
                print(f"   Calls: {model_stats.get('calls', 0)}")
                print(f"   Success rate: {model_stats.get('success_rate', 0)}%")
                print(f"   Avg response: {model_stats.get('response_time', {}).get('avg', 0)}ms")
                print(f"   Total cost: ${model_stats.get('cost', {}).get('total', 0)}")
        else:
            print("ℹ️  No performance data yet (normal for fresh start)")

        # Raccomandazioni
        recs = stats.get('recommendations', {})
        if recs.get('suggested_chain'):
            print(f"\n🎯 Recommended model chain: {recs['suggested_chain']}")

except Exception as e:
    print(f"⚠️  Stats not available: {e}")

# REPORT FINALE
print("\n" + "="*60)
print("📊 REPORT FINALE SUPER TEST AGENT")
print("="*60)

# Raccogli status finale
os.system("""docker exec intelligence-v2 python3 -c "
print('')
print('🔧 SYSTEM STATUS SUMMARY:')
print('-' * 30)

# Check API keys
import os
keys_status = {
    'OPENAI': '✅' if os.getenv('OPENAI_API_KEY') else '❌ Missing',
    'GROQ': '✅' if os.getenv('GROQ_API_KEY') else '❌ Missing',
    'GOOGLE': '✅' if os.getenv('GOOGLE_API_KEY') else '❌ Missing',
    'ANTHROPIC': '✅' if os.getenv('ANTHROPIC_API_KEY') else '❌ Missing',
    'LANGSMITH': '✅' if os.getenv('LANGCHAIN_API_KEY') else '❌ Missing'
}

for provider, status in keys_status.items():
    print(f'{provider}: {status}')

print('')
print('📝 NEXT STEPS:')
if '❌' in str(keys_status.values()):
    print('1. Add missing API keys to .env file')
    print('2. Restart container: docker restart intelligence-v2')
    print('3. Run this test again')
else:
    print('✅ All API keys configured!')
    print('🚀 System ready for production use!')
" """)

print("\n" + "="*60)
print("✨ TEST COMPLETATO!")
print("="*60)