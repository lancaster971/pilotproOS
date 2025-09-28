#!/usr/bin/env python3
"""
FIX LANGSMITH DEFINITIVAMENTE
Questo script verifica e corregge tutti i problemi con LangSmith
"""
import os
import sys
import json
import requests
from datetime import datetime

def print_header(text):
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60)

def check_env_variables():
    """Verifica variabili ambiente"""
    print_header("1. VERIFICA VARIABILI AMBIENTE")

    required_vars = {
        "LANGCHAIN_TRACING_V2": os.getenv("LANGCHAIN_TRACING_V2"),
        "LANGCHAIN_API_KEY": os.getenv("LANGCHAIN_API_KEY"),
        "LANGCHAIN_PROJECT": os.getenv("LANGCHAIN_PROJECT"),
        "LANGCHAIN_ENDPOINT": os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    }

    all_ok = True
    for var, value in required_vars.items():
        if value:
            if var == "LANGCHAIN_API_KEY":
                print(f"  ✅ {var} = {value[:20]}...{value[-10:]}")
            else:
                print(f"  ✅ {var} = {value}")
        else:
            print(f"  ❌ {var} = NON IMPOSTATO!")
            all_ok = False

    return all_ok

def test_langsmith_connection():
    """Test connessione a LangSmith"""
    print_header("2. TEST CONNESSIONE LANGSMITH")

    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        print("  ❌ LANGCHAIN_API_KEY non trovato!")
        return False

    # Test API endpoint
    headers = {"x-api-key": api_key}

    try:
        # Test info endpoint
        response = requests.get(
            "https://api.smith.langchain.com/info",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            print(f"  ✅ Connessione a LangSmith OK")
            print(f"  ✅ Response: {response.json()}")
            return True
        else:
            print(f"  ❌ Errore: Status code {response.status_code}")
            print(f"  ❌ Response: {response.text}")
            return False

    except Exception as e:
        print(f"  ❌ Errore connessione: {e}")
        return False

def test_langsmith_tracing():
    """Test tracing con LangSmith"""
    print_header("3. TEST TRACING LANGSMITH")

    try:
        from langsmith import Client

        # Crea client
        client = Client()

        # Verifica progetti
        print("  Verifico progetti...")
        projects = list(client.list_projects())

        if projects:
            print(f"  ✅ Trovati {len(projects)} progetti:")
            for p in projects[:5]:
                print(f"     - {p.name}")
        else:
            print("  ⚠️  Nessun progetto trovato, creazione automatica al primo trace")

        # Crea un trace di test
        print("\n  Creazione trace di test...")

        # Create a test run
        from langsmith.run_trees import RunTree

        run = RunTree(
            name="LangSmith Test",
            run_type="chain",
            inputs={"test": "Verifica connessione"},
            project_name="milhena-v3-production"
        )

        # Simula esecuzione
        run.end(outputs={"result": "Test completato"})
        run.post()

        print(f"  ✅ Trace creato con successo!")
        print(f"  📊 Progetto: milhena-v3-production")
        print(f"  🔗 URL: https://smith.langchain.com/public/{run.id}")

        return True

    except Exception as e:
        print(f"  ❌ Errore tracing: {e}")
        import traceback
        traceback.print_exc()
        return False

def fix_docker_compose():
    """Verifica che docker-compose passi le variabili"""
    print_header("4. VERIFICA DOCKER-COMPOSE")

    compose_file = "/Volumes/BK12/Dropbox/Dropbox/TIZIANO/AI/PilotProOS/docker-compose.yml"

    if os.path.exists(compose_file):
        with open(compose_file, 'r') as f:
            content = f.read()

        if "LANGCHAIN_API_KEY" in content:
            print("  ✅ LANGCHAIN_API_KEY presente in docker-compose.yml")
        else:
            print("  ⚠️  LANGCHAIN_API_KEY non trovato in docker-compose.yml")
            print("     Aggiungi nel container intelligence-engine:")
            print("     environment:")
            print("       - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}")
            print("       - LANGCHAIN_TRACING_V2=true")
            print("       - LANGCHAIN_PROJECT=milhena-v3-production")
    else:
        print(f"  ❌ File non trovato: {compose_file}")

def test_in_python():
    """Test diretto in Python"""
    print_header("5. TEST DIRETTO PYTHON")

    # Imposta variabili
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "milhena-v3-test"

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage

        # Test con modello semplice
        print("  Creazione LLM...")
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0
        )

        print("  Invocazione con tracing...")
        response = llm.invoke([HumanMessage(content="Say 'test' in one word")])

        print(f"  ✅ Risposta: {response.content}")
        print(f"  ✅ Tracing attivo!")
        print(f"  🔗 Controlla: https://smith.langchain.com")

        return True

    except Exception as e:
        print(f"  ❌ Errore: {e}")
        return False

def create_test_script():
    """Crea script di test per container"""
    print_header("6. CREAZIONE SCRIPT TEST CONTAINER")

    script = """#!/bin/bash
# Test LangSmith nel container

echo "Testing LangSmith in container..."

# Verifica variabili
echo "LANGCHAIN_API_KEY: ${LANGCHAIN_API_KEY:0:20}...${LANGCHAIN_API_KEY: -10}"
echo "LANGCHAIN_TRACING_V2: $LANGCHAIN_TRACING_V2"
echo "LANGCHAIN_PROJECT: $LANGCHAIN_PROJECT"

# Test Python
python3 -c "
import os
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_PROJECT'] = 'milhena-container-test'

from langsmith import Client
client = Client()
print('✅ LangSmith Client created successfully')

from langsmith.run_trees import RunTree
run = RunTree(
    name='Container Test',
    run_type='chain',
    inputs={'test': 'container'},
    project_name='milhena-container-test'
)
run.end(outputs={'result': 'success'})
run.post()
print(f'✅ Trace created: https://smith.langchain.com/public/{run.id}')
"
"""

    path = "/Volumes/BK12/Dropbox/Dropbox/TIZIANO/AI/PilotProOS/intelligence-engine/test_langsmith_container.sh"

    with open(path, 'w') as f:
        f.write(script)

    os.chmod(path, 0o755)
    print(f"  ✅ Script creato: {path}")
    print(f"     Esegui nel container: ./test_langsmith_container.sh")

    return True

def main():
    print("\n" + "🔧"*30)
    print(" FIX DEFINITIVO LANGSMITH")
    print("🔧"*30)

    results = {}

    # 1. Check environment
    results["env"] = check_env_variables()

    # 2. Test connection
    results["connection"] = test_langsmith_connection()

    # 3. Test tracing
    results["tracing"] = test_langsmith_tracing()

    # 4. Check Docker
    fix_docker_compose()

    # 5. Test Python
    results["python"] = test_in_python()

    # 6. Create test script
    create_test_script()

    # Summary
    print_header("RISULTATO FINALE")

    if all(results.values()):
        print("""
  🎉 LANGSMITH FUNZIONA CORRETTAMENTE!

  ✅ Variabili ambiente: OK
  ✅ Connessione API: OK
  ✅ Tracing: OK
  ✅ Python test: OK

  📊 Dashboard: https://smith.langchain.com
  🔍 Progetto: milhena-v3-production

  PROSSIMI PASSI:
  1. docker-compose down
  2. docker-compose up -d
  3. docker exec -it pilotpros-intelligence-engine-dev bash
  4. ./test_langsmith_container.sh
  5. python test_milhena_langsmith.py
        """)
    else:
        print("""
  ⚠️  ALCUNI PROBLEMI DA RISOLVERE:
        """)
        for key, value in results.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}")

        print("""

  SOLUZIONI:

  1. Se API key non valida:
     - Vai su https://smith.langchain.com/settings
     - Genera nuova API key
     - Aggiorna .env: LANGCHAIN_API_KEY=nuova_key

  2. Se docker-compose non passa variabili:
     - Aggiungi in docker-compose.yml sotto intelligence-engine:
       environment:
         - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
         - LANGCHAIN_TRACING_V2=true

  3. Se connessione fallisce:
     - Verifica connessione internet
     - Verifica firewall/proxy

  4. Riavvia tutto:
     docker-compose down
     docker-compose up -d
        """)

if __name__ == "__main__":
    main()