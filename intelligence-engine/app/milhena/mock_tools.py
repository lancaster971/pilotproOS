"""
Mock Tools for Testing Milhena v3.2 Without Real Database

Usage:
    export USE_MOCK_DATA=true
    ./graph

This module provides realistic fake data for testing the flattened ReAct agent
without requiring a PostgreSQL database with n8n workflows.
"""

import os
from typing import Dict, List

MOCK_ENABLED = os.getenv("USE_MOCK_DATA", "false").lower() == "true"


def get_mock_workflows() -> str:
    """Mock: Lista tutti i workflow"""
    return """📋 Processi Attivi (MOCK DATA):

1. **Gestione Ordini Clienti** (ID: wf-001)
   - Stato: Attivo
   - Esecuzioni oggi: 145
   - Success rate: 98%

2. **Sincronizzazione Magazzino** (ID: wf-002)
   - Stato: Attivo
   - Esecuzioni oggi: 89
   - Success rate: 100%

3. **Invio Email Marketing** (ID: wf-003)
   - Stato: Paused
   - Ultima esecuzione: 2 giorni fa

4. **Elaborazione Fatture** (ID: wf-004)
   - Stato: Attivo
   - Esecuzioni oggi: 67
   - Success rate: 95%

5. **GRAB INFO SUPPLIER FROM ORDINI** (ID: wf-005)
   - Stato: Attivo
   - Esecuzioni oggi: 12
   - Success rate: 0% (ERRORI!)
"""


def get_mock_errors() -> str:
    """Mock: Errori ultimi 7 giorni"""
    return """⚠️ Errori Ultimi 7 Giorni (MOCK):

**GRAB INFO SUPPLIER FROM ORDINI**:
- 5 errori consecutivi
- Ultimo: oggi alle 14:32
- Tipo: Connessione database fallita
- Success rate: 0%

**Gestione Ordini Clienti**:
- 3 errori (timeout API pagamenti)
- Success rate: 98%

**Elaborazione Fatture**:
- 1 errore (file PDF corrotto)
- Success rate: 95%

**Sincronizzazione Magazzino**:
- 0 errori
- Success rate: 100%
"""


def get_mock_workflow_details(workflow_name: str) -> str:
    """Mock: Dettagli specifici workflow"""
    workflows_details = {
        "grab info supplier": """📊 Dettagli GRAB INFO SUPPLIER FROM ORDINI (MOCK):

**Performance**:
- Success rate: 0% (ultimi 7 giorni)
- Tempo medio: 2min 30sec
- Trend: ↓ Peggioramento (5 fallimenti consecutivi)

**Ultima Esecuzione**:
- Data: Oggi 14:32
- Stato: FALLITA
- Errore: "Connection timeout to Excel DB1"
- Durata: 2min 28sec (interrotta)

**Nodo Problematico**:
- Nome: "Excel DB1"
- Tipo: Database Query
- Dettaglio: Credenziali scadute o database non raggiungibile

**Statistiche**:
- Totale esecuzioni: 12 oggi
- Fallimenti: 12 (100%)
- Pattern: Fallisce sempre a 2:30 dall'avvio
""",
        "gestione ordini": """📊 Dettagli Gestione Ordini Clienti (MOCK):

**Performance**:
- Success rate: 98%
- Tempo medio: 45 secondi
- Trend: ↑ Stabile

**Ultima Esecuzione**:
- Data: Oggi 15:10
- Stato: SUCCESSO
- Durata: 42 secondi

**Statistiche**:
- Totale esecuzioni oggi: 145
- Successi: 142
- Fallimenti: 3 (timeout API)
""",
        "default": f"""📊 Dettagli {workflow_name} (MOCK):

Workflow trovato ma dati limitati.
Usa get_all_errors_summary per vedere errori generali.
"""
    }

    # Match workflow name (case-insensitive)
    for key, details in workflows_details.items():
        if key in workflow_name.lower():
            return details

    return workflows_details["default"]


def get_mock_statistics() -> str:
    """Mock: Statistiche complete sistema"""
    return """📈 Statistiche Sistema (MOCK DATA):

**Oggi**:
- Processi totali: 5
- Processi attivi: 4
- Esecuzioni totali: 313
- Success rate: 92%

**Performance**:
- Tempo medio elaborazione: 1min 15sec
- Disponibilità sistema: 99.9%
- Uptime: 27 giorni

**Top Processi (esecuzioni)**:
1. Gestione Ordini: 145
2. Sincronizzazione Magazzino: 89
3. Elaborazione Fatture: 67
4. GRAB INFO SUPPLIER: 12 (tutti falliti)

**Problemi Attivi**:
- ⚠️ GRAB INFO SUPPLIER: 5 fallimenti consecutivi (CRITICO)
- ⚠️ Gestione Ordini: 3 timeout sporadici
"""


def get_mock_executions_by_date(date: str) -> str:
    """Mock: Esecuzioni per data specifica"""
    return f"""📅 Esecuzioni del {date} (MOCK):

1. **Gestione Ordini Clienti** (08:00) - SUCCESSO (45s)
2. **Sincronizzazione Magazzino** (08:15) - SUCCESSO (1m 10s)
3. **GRAB INFO SUPPLIER** (09:00) - FALLITO (2m 30s)
4. **Elaborazione Fatture** (09:30) - SUCCESSO (3m 15s)
5. **Gestione Ordini Clienti** (10:00) - SUCCESSO (42s)
...

Totale esecuzioni: 313
Successi: 288 (92%)
Fallimenti: 25 (8%)
"""


# Export mock functions with same signature as real tools
MOCK_TOOLS = {
    "get_workflows_tool": get_mock_workflows,
    "get_all_errors_summary_tool": get_mock_errors,
    "get_workflow_details_tool": get_mock_workflow_details,
    "get_full_database_dump": get_mock_statistics,
    "get_executions_by_date_tool": get_mock_executions_by_date,
}


def is_mock_enabled() -> bool:
    """Check if mock data is enabled via environment variable"""
    return MOCK_ENABLED


def get_mock_info() -> str:
    """Return mock data status message"""
    if MOCK_ENABLED:
        return "✅ MOCK DATA ENABLED - Using fake data for testing"
    else:
        return "❌ MOCK DATA DISABLED - Using real PostgreSQL database"
