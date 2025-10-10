"""
PilotPro Tools for v3.1 Intelligence Engine
Business-critical tools for n8n workflow data extraction and analytics
Subset of business_tools.py (7 base tools)
"""

import os
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from langsmith import traceable
import json
import logging
import httpx
import re

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE CONNECTION HELPER
# ============================================================================

def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres-dev"),
        port=5432,
        dbname="pilotpros_db",
        user="pilotpros_user",
        password="pilotpros_secure_pass_2025"
    )

# ============================================================================
# HTTP CLIENT HELPER - Call PilotProOS Backend APIs
# ============================================================================

async def call_backend_api(endpoint: str, timeout: float = 10.0) -> dict:
    """
    Call PilotProOS backend API from Intelligence Engine.
    Uses service-to-service authentication with shared secret.

    Args:
        endpoint: API path (e.g., "/api/business/top-performers")
        timeout: Request timeout in seconds

    Returns:
        JSON response from backend
    """
    backend_url = os.getenv("BACKEND_URL", "http://pilotpros-backend-dev:3001")
    service_token = os.getenv("SERVICE_AUTH_TOKEN", "intelligence-engine-service-token-2025")

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            headers = {
                "X-Service-Auth": service_token,
                "Content-Type": "application/json"
            }
            response = await client.get(f"{backend_url}{endpoint}", headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        logger.error(f"Backend API timeout: {endpoint}")
        return {"error": "timeout", "endpoint": endpoint}
    except httpx.HTTPStatusError as e:
        logger.error(f"Backend API error {e.response.status_code}: {endpoint}")
        return {"error": f"http_{e.response.status_code}", "endpoint": endpoint}
    except Exception as e:
        logger.error(f"Backend API exception: {endpoint} - {e}")
        return {"error": str(e), "endpoint": endpoint}

# ============================================================================
# 13 TOOLS MIGRATED FROM v3.0 business_tools.py
# ============================================================================

# TOOL 1: get_workflows_tool
@tool
@traceable(name="MilhenaWorkflows", run_type="tool")
def get_workflows_tool(query_type: str = "active") -> str:
    """
    Get BASIC workflow list (names only, NO statistics/metrics).

    USE THIS ONLY for simple lists like:
    - "quali workflow esistono?"
    - "mostra i workflow attivi"
    - "lista processi"

    DO NOT use for statistics/metrics - use get_full_database_dump instead!

    Args:
        query_type: "active", "inactive", "all", "top_used", "complex", "recent", "errors"

    Returns:
        Workflow names list (NO execution stats, NO performance data)
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if query_type == "active":
            cur.execute("""
                SELECT name, "triggerCount", "createdAt"
                FROM n8n.workflow_entity
                WHERE active = true
                ORDER BY name
            """)
            results = cur.fetchall()
            workflows = [f"- {r[0]} (Trigger: {r[1]}, Creato: {r[2].strftime('%d/%m/%Y')})" for r in results]
            response = f"**Processi Attivi: {len(results)}**\n" + "\n".join(workflows) if workflows else "Nessun processo attivo"

        elif query_type == "inactive":
            cur.execute("""
                SELECT name, "updatedAt"
                FROM n8n.workflow_entity
                WHERE active = false
                ORDER BY "updatedAt" DESC
                LIMIT 10
            """)
            results = cur.fetchall()
            workflows = [f"- {r[0]} (Ultimo aggiornamento: {r[1].strftime('%d/%m/%Y')})" for r in results]
            response = f"**Processi Inattivi:**\n" + "\n".join(workflows) if workflows else "Tutti i processi sono attivi"

        elif query_type == "top_used":
            cur.execute("""
                SELECT we.name, COUNT(ee.id) as exec_count,
                       MAX(ee."startedAt") as last_run
                FROM n8n.workflow_entity we
                LEFT JOIN n8n.execution_entity ee ON we.id = ee."workflowId"
                GROUP BY we.id, we.name
                HAVING COUNT(ee.id) > 0
                ORDER BY exec_count DESC
                LIMIT 5
            """)
            results = cur.fetchall()
            workflows = []
            for r in results:
                last_run = r[2].strftime('%d/%m %H:%M') if r[2] else "Mai"
                workflows.append(f"- {r[0]}: {r[1]} esecuzioni (Ultima: {last_run})")
            response = "**Top 5 Processi più utilizzati:**\n" + "\n".join(workflows)

        elif query_type == "complex":
            cur.execute("""
                SELECT name, JSON_ARRAY_LENGTH(nodes) as node_count
                FROM n8n.workflow_entity
                ORDER BY JSON_ARRAY_LENGTH(nodes) DESC
                LIMIT 5
            """)
            results = cur.fetchall()
            workflows = [f"- {r[0]}: {r[1]} passaggi" for r in results]
            response = "**Processi più complessi:**\n" + "\n".join(workflows)

        elif query_type == "recent":
            cur.execute("""
                SELECT name, "updatedAt", active
                FROM n8n.workflow_entity
                ORDER BY "updatedAt" DESC
                LIMIT 5
            """)
            results = cur.fetchall()
            workflows = []
            for r in results:
                status = "Attivo" if r[2] else "Inattivo"
                workflows.append(f"- {r[0]} ({status}) - Aggiornato: {r[1].strftime('%d/%m %H:%M')}")
            response = "**Processi modificati di recente:**\n" + "\n".join(workflows)

        elif query_type == "errors":
            cur.execute("""
                SELECT we.name, COUNT(ee.id) as error_count,
                       MAX(ee."startedAt") as last_error
                FROM n8n.workflow_entity we
                JOIN n8n.execution_entity ee ON we.id = ee."workflowId"
                WHERE ee.status = 'error'
                GROUP BY we.id, we.name
                ORDER BY error_count DESC
                LIMIT 5
            """)
            results = cur.fetchall()
            if results:
                workflows = []
                for r in results:
                    last_error = r[2].strftime('%d/%m %H:%M') if r[2] else "N/A"
                    workflows.append(f"- {r[0]}: {r[1]} errori (Ultimo: {last_error})")
                response = "**Processi con più errori:**\n" + "\n".join(workflows)
            else:
                response = "Nessun processo con errori recenti"

        else:  # all
            cur.execute("""
                SELECT COUNT(*),
                       COUNT(CASE WHEN active = true THEN 1 END) as active,
                       COUNT(CASE WHEN active = false THEN 1 END) as inactive
                FROM n8n.workflow_entity
            """)
            result = cur.fetchone()
            response = f"""**Riepilogo Processi:**
- Totali: {result[0]}
- Attivi: {result[1]}
- Inattivi: {result[2]}
- Tasso attivazione: {(result[1]/result[0]*100 if result[0] > 0 else 0):.1f}%"""

        conn.close()
        return response

    except Exception as e:
        return f"Errore accesso processi: {str(e)}"


# TOOL 2: get_all_errors_summary_tool
@tool
@traceable(name="MilhenaAllErrors", run_type="tool")
def get_all_errors_summary_tool(hours: int = 24) -> str:
    """
    Get summary of ALL workflows that had errors (no details, just list).

    Use this when user asks general questions:
    - "che errori abbiamo oggi?"
    - "quali processi hanno avuto problemi?"
    - "ci sono errori?"

    Returns: List of workflow names with error counts
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        time_cutoff = datetime.now() - timedelta(hours=hours)

        # All workflows with errors
        cur.execute("""
            SELECT
                we.name,
                COUNT(*) as error_count,
                MAX(ee."startedAt") as last_error
            FROM n8n.execution_entity ee
            JOIN n8n.workflow_entity we ON ee."workflowId" = we.id
            WHERE ee.status = 'error'
              AND ee."startedAt" >= %s
            GROUP BY we.name
            ORDER BY error_count DESC
            LIMIT 10
        """, (time_cutoff,))

        errors = cur.fetchall()

        if not errors:
            return f"[OK] Nessun errore rilevato nelle ultime {hours} ore. Sistema operativo."

        # SMART RESPONSE: Se c'è UN SOLO errore, mostra subito i dettagli!
        if len(errors) == 1:
            workflow_name = errors[0][0]

            # Ottieni dettagli errore inline (non possiamo chiamare altro @tool)
            cur.execute("""
                SELECT
                    we.name,
                    ee."startedAt",
                    ee."stoppedAt",
                    ee.status,
                    ee.id,
                    ed.data
                FROM n8n.execution_entity ee
                JOIN n8n.workflow_entity we ON ee."workflowId" = we.id
                LEFT JOIN n8n.execution_data ed ON ed."executionId" = ee.id
                WHERE LOWER(we.name) LIKE LOWER(%s)
                  AND ee.status = 'error'
                  AND ee."startedAt" >= %s
                ORDER BY ee."startedAt" DESC
                LIMIT 5
            """, (f"%{workflow_name}%", time_cutoff))

            error_details = cur.fetchall()

            if error_details:
                # Mostra dettagli completi (riusa la logica del tool dettagliato)
                response = f"[ERRORE] **Errore in '{workflow_name}'**:\n\n"

                for idx, (name, started, stopped, status, exec_id, error_data) in enumerate(error_details[:1], 1):  # Solo il primo
                    duration = (stopped - started).total_seconds() if stopped else 0
                    response += f"**Errore del {started.strftime('%d/%m/%Y alle %H:%M')}** (durata: {duration:.0f}s)\n"

                    if error_data:
                        try:
                            # Decompressione errore (inline)
                            data = json.loads(error_data)

                            def decompress(obj, array):
                                if isinstance(obj, dict):
                                    return {k: decompress(v, array) for k, v in obj.items()}
                                elif isinstance(obj, list):
                                    return [decompress(item, array) for item in obj]
                                elif isinstance(obj, str) and obj.isdigit():
                                    idx = int(obj)
                                    if 0 <= idx < len(array):
                                        return decompress(array[idx], array)
                                return obj

                            decompressed = decompress(data[0], data)
                            result_data = decompressed.get('resultData', {})
                            error_obj = result_data.get('error', {})

                            error_msg = error_obj.get('message', 'Errore sconosciuto')
                            node_name = error_obj.get('node', {}).get('name', 'N/A')

                            response += f"[!] **Passaggio fallito:** {node_name}\n"

                            # Trova spiegazione (pattern matching inline)
                            if 'unable to sign without access token' in error_msg.lower():
                                response += "\n[CAUSA] Le credenziali di accesso al file esterno (Google Sheets/Excel) sono scadute o mancanti."
                                response += "\n[SOLUZIONE] Contatta IT per riautorizzare l'accesso al file. Servirà riconnettere l'account Google/Microsoft."
                            elif 'timeout' in error_msg.lower() or 'ETIMEDOUT' in error_msg:
                                response += "\n[CAUSA] Il servizio esterno non ha risposto in tempo."
                                response += "\n[SOLUZIONE] Riprova tra 5 minuti. Se persiste, contatta IT."
                            elif '401' in error_msg or 'unauthorized' in error_msg.lower():
                                response += "\n[CAUSA] Credenziali non valide o scadute."
                                response += "\n[SOLUZIONE] Contatta IT per aggiornare le credenziali."
                            elif '403' in error_msg or 'forbidden' in error_msg.lower():
                                response += "\n[CAUSA] Permessi insufficienti."
                                response += "\n[SOLUZIONE] Contatta IT per richiedere i permessi necessari."
                            elif '429' in error_msg or 'rate limit' in error_msg.lower():
                                response += "\n[CAUSA] Troppo richieste. Limite raggiunto."
                                response += "\n[SOLUZIONE] Attendi 1 ora prima di riprovare."
                            elif 'ECONNREFUSED' in error_msg:
                                response += "\n[CAUSA] Impossibile connettersi al servizio esterno."
                                response += "\n[SOLUZIONE] Contatta IT per verificare lo stato del servizio."
                            else:
                                response += f"\n[INFO] {error_msg}"
                                response += "\n[SOLUZIONE] Contatta IT con questo messaggio e l'orario dell'errore."

                        except Exception as e:
                            logger.error(f"Error parsing error data: {e}")
                            response += "[AVVISO] Dettagli errore non disponibili"
                    else:
                        response += "[AVVISO] Dettagli errore non disponibili"

                cur.close()
                conn.close()
                return response

        # Se ci sono MULTIPLI errori, mostra solo la lista
        response = f"[ERRORE] **Processi con errori** (ultime {hours}h):\n\n"

        for i, (name, count, last_error) in enumerate(errors, 1):
            severity = "[!!!]" if count >= 5 else "[!!]" if count >= 2 else "[!]"
            response += f"{severity} **{name}**\n"
            response += f"   Errori: {count} | Ultimo: {last_error.strftime('%d/%m %H:%M')}\n\n"

        response += f"**Totale processi con errori:** {len(errors)}\n\n"

        # Suggerisci di chiedere dettagli
        response += "[SUGGERIMENTO] Per vedere i dettagli di un errore specifico, chiedi: \"spiegami l'errore di [nome processo]\""

        # Critical alert
        critical = [e for e in errors if e[1] >= 5]
        if critical:
            response += f"\n\n[CRITICO] {len(critical)} processi con errori multipli. Contatta IT urgentemente."

        cur.close()
        conn.close()

        return response

    except Exception as e:
        return f"Errore recupero lista errori: {str(e)}"


# TOOL 3: get_error_details_tool
@tool
@traceable(name="MilhenaErrorDetails", run_type="tool")
def get_error_details_tool(workflow_name: str, hours: int = 24) -> str:
    """
    Get DETAILED error explanation with cause, failed step, and solution for a SPECIFIC workflow.

    IMPORTANT: workflow_name is REQUIRED! If user mentions a workflow name in previous messages,
    extract it from conversation history.

    Use this when user asks:
    - "che errore ha il processo X?" → workflow_name="X"
    - "spiegami l'errore di X" → workflow_name="X"
    - "perché è fallito X?" → workflow_name="X"
    - "che tipo di errore è?" (follow-up to previous error message) → extract name from history

    Args:
        workflow_name: REQUIRED - Name of workflow to analyze (extract from user query or history)
        hours: Time range in hours (default: last 24 hours)

    Returns:
        Detailed error with: timestamp, failed node/step name, error cause in business terms, solution
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        time_cutoff = datetime.now() - timedelta(hours=hours)

        # Errors for specific workflow WITH error data
        cur.execute("""
            SELECT
                we.name,
                ee."startedAt",
                ee."stoppedAt",
                ee.status,
                ee.id,
                ed.data
            FROM n8n.execution_entity ee
            JOIN n8n.workflow_entity we ON ee."workflowId" = we.id
            LEFT JOIN n8n.execution_data ed ON ed."executionId" = ee.id
            WHERE LOWER(we.name) LIKE LOWER(%s)
              AND ee.status = 'error'
              AND ee."startedAt" >= %s
            ORDER BY ee."startedAt" DESC
            LIMIT 10
        """, (f"%{workflow_name}%", time_cutoff))

        errors = cur.fetchall()

        if not errors:
            return f"Nessun errore trovato per il processo '{workflow_name}' nelle ultime {hours} ore."

        workflow_full_name = errors[0][0]

        response = f"[ERRORE] **Errori per '{workflow_full_name}'** (ultime {hours}h):\n\n"

        # AUTO-ENRICHMENT: Aggiungi statistiche workflow per context completo
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE ee.status = 'success') as successes,
                COUNT(*) FILTER (WHERE ee.status = 'error') as errors_count,
                COUNT(*) as total_execs,
                AVG(EXTRACT(EPOCH FROM (ee."stoppedAt" - ee."startedAt"))) as avg_duration
            FROM n8n.execution_entity ee
            JOIN n8n.workflow_entity we ON ee."workflowId" = we.id
            WHERE LOWER(we.name) LIKE LOWER(%s)
              AND ee."startedAt" >= %s
        """, (f"%{workflow_name}%", time_cutoff))

        stats = cur.fetchone()
        if stats and stats[2] > 0:
            success_rate = (stats[0] / stats[2] * 100) if stats[2] > 0 else 0
            response += f"**📊 Context Performance** (ultime {hours}h):\n"
            response += f"  • Esecuzioni totali: {stats[2]}\n"
            response += f"  • Successi: {stats[0]} | Errori: {stats[1]}\n"
            response += f"  • Success Rate: {success_rate:.1f}%\n"
            response += f"  • Durata media: {stats[3]:.1f}s\n\n"

        response += f"**🔍 Dettaglio Errori:**\n\n"

        # Helper function to decompress n8n error data
        def decompress_error_data(data_str):
            """Decomprime il formato JSON indicizzato di n8n"""
            try:
                data = json.loads(data_str)

                def decompress(obj, array):
                    if isinstance(obj, dict):
                        return {k: decompress(v, array) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [decompress(item, array) for item in obj]
                    elif isinstance(obj, str) and obj.isdigit():
                        idx = int(obj)
                        if 0 <= idx < len(array):
                            return decompress(array[idx], array)
                    return obj

                decompressed = decompress(data[0], data)
                result_data = decompressed.get('resultData', {})
                error = result_data.get('error', {})

                return {
                    'message': error.get('message', 'Errore sconosciuto'),
                    'node': error.get('node', {}).get('name', 'N/A'),
                    'type': error.get('name', 'N/A')
                }
            except Exception as e:
                logger.error(f"Error decompressing error data: {e}")
                return None

        # Helper function to explain error in business terms
        def explain_error(error_msg, node_name):
            """Spiega l'errore in linguaggio business con soluzione"""
            explanations = {
                # OAuth / Autenticazione
                'Unable to sign without access token': {
                    'reason': 'Le credenziali di accesso al file esterno (Google Sheets/Excel) sono scadute o mancanti.',
                    'solution': 'Contatta IT per riautorizzare l\'accesso al file. Servirà riconnettere l\'account Google/Microsoft.'
                },
                'authentication': {
                    'reason': 'Problema di autenticazione con servizio esterno.',
                    'solution': 'Contatta IT per verificare credenziali e permessi di accesso.'
                },
                'invalid credentials': {
                    'reason': 'Le credenziali di accesso non sono corrette o sono scadute.',
                    'solution': 'Contatta IT per aggiornare le credenziali di accesso al servizio.'
                },
                'unauthorized': {
                    'reason': 'Accesso negato al servizio esterno. Credenziali mancanti o non valide.',
                    'solution': 'Contatta IT per verificare i permessi e le credenziali dell\'account.'
                },

                # Timeout / Connessione
                'timeout': {
                    'reason': 'Il sistema esterno non ha risposto in tempo.',
                    'solution': 'Riprova tra qualche minuto. Se persiste, contatta IT per verificare la connessione.'
                },
                'ETIMEDOUT': {
                    'reason': 'Tempo di attesa scaduto durante la connessione al servizio esterno.',
                    'solution': 'Il servizio esterno è lento o non disponibile. Riprova tra 5 minuti.'
                },
                'ECONNREFUSED': {
                    'reason': 'Impossibile connettersi al servizio esterno. Il servizio potrebbe essere offline.',
                    'solution': 'Contatta IT per verificare lo stato del servizio esterno.'
                },
                'network error': {
                    'reason': 'Problema di connessione di rete con il servizio esterno.',
                    'solution': 'Verifica la connessione internet. Se il problema persiste, contatta IT.'
                },

                # Permessi / Rate Limit
                'permission': {
                    'reason': 'Permessi insufficienti per accedere alla risorsa.',
                    'solution': 'Contatta IT per verificare i permessi dell\'account sul servizio esterno.'
                },
                'forbidden': {
                    'reason': 'Accesso negato alla risorsa. I permessi sono insufficienti.',
                    'solution': 'Contatta IT per richiedere i permessi necessari sul file o servizio.'
                },
                'rate limit': {
                    'reason': 'Raggiunto il limite di richieste consentite dal servizio esterno.',
                    'solution': 'Attendi 1 ora prima di riprovare. Se urgente, contatta IT per aumentare i limiti.'
                },
                'too many requests': {
                    'reason': 'Troppe richieste inviate al servizio esterno in breve tempo.',
                    'solution': 'Attendi 30 minuti prima di riprovare l\'elaborazione.'
                },

                # Dati / Formato
                'not found': {
                    'reason': 'Il file o la risorsa richiesta non esiste o è stata spostata.',
                    'solution': 'Verifica che il file esista nella posizione corretta. Contatta IT se non lo trovi.'
                },
                'invalid format': {
                    'reason': 'Il formato dei dati ricevuti non è quello atteso dal sistema.',
                    'solution': 'Contatta IT per verificare la struttura del file o dei dati di input.'
                },
                'required parameter': {
                    'reason': 'Mancano informazioni obbligatorie per completare l\'elaborazione.',
                    'solution': 'Contatta IT specificando quale elaborazione è fallita. Potrebbero servire dati aggiuntivi.'
                },
                'invalid json': {
                    'reason': 'I dati ricevuti dal servizio esterno sono malformati.',
                    'solution': 'Errore tecnico del servizio esterno. Contatta IT per una verifica approfondita.'
                },

                # Email / SMTP
                'SMTP': {
                    'reason': 'Impossibile inviare l\'email. Problema con il server di posta.',
                    'solution': 'Contatta IT per verificare la configurazione del server email.'
                },
                'invalid recipient': {
                    'reason': 'Uno o più destinatari email non sono validi.',
                    'solution': 'Verifica gli indirizzi email dei destinatari. Contatta IT se il problema persiste.'
                },

                # Database / Storage
                'duplicate': {
                    'reason': 'Il record esiste già nel sistema. Impossibile creare duplicati.',
                    'solution': 'Verifica che il dato non sia già presente. Se è corretto, contatta IT.'
                },
                'constraint violation': {
                    'reason': 'Violazione delle regole di integrità dei dati.',
                    'solution': 'I dati non rispettano i vincoli definiti. Contatta IT per una verifica.'
                },

                # API / Servizi esterni
                'API key': {
                    'reason': 'La chiave di accesso al servizio esterno non è valida o è scaduta.',
                    'solution': 'Contatta IT per rinnovare la chiave di accesso al servizio.'
                },
                'quota exceeded': {
                    'reason': 'Superato il limite di utilizzo del servizio esterno per il mese corrente.',
                    'solution': 'Contatta IT per aumentare la quota o attendere il rinnovo mensile.'
                },
                'service unavailable': {
                    'reason': 'Il servizio esterno è temporaneamente non disponibile.',
                    'solution': 'Riprova tra 15 minuti. Se persiste, contatta IT per verifiche.'
                },

                # HTTP Status Codes
                '400': {
                    'reason': 'La richiesta inviata contiene dati non validi o incompleti.',
                    'solution': 'Contatta IT con l\'orario dell\'errore. Potrebbero servire correzioni alla configurazione.'
                },
                '401': {
                    'reason': 'Credenziali non valide o scadute per accedere al servizio.',
                    'solution': 'Contatta IT per aggiornare le credenziali di autenticazione.'
                },
                '403': {
                    'reason': 'Accesso negato. L\'account non ha i permessi necessari.',
                    'solution': 'Contatta IT per richiedere i permessi mancanti sull\'account.'
                },
                '404': {
                    'reason': 'La risorsa richiesta non esiste o è stata rimossa.',
                    'solution': 'Verifica che il file/dato esista. Contatta IT se il problema persiste.'
                },
                '429': {
                    'reason': 'Troppe richieste inviate. Limite del servizio esterno raggiunto.',
                    'solution': 'Attendi 1 ora prima di riprovare. Contatta IT se urgente per aumentare i limiti.'
                },
                '500': {
                    'reason': 'Errore interno del servizio esterno.',
                    'solution': 'Il problema è sul servizio esterno. Riprova tra 30 minuti. Se persiste, contatta IT.'
                },
                '502': {
                    'reason': 'Errore di comunicazione tra servizi. Gateway non raggiungibile.',
                    'solution': 'Problema temporaneo del servizio esterno. Riprova tra 10 minuti.'
                },
                '503': {
                    'reason': 'Servizio esterno temporaneamente in manutenzione.',
                    'solution': 'Riprova tra 20 minuti. Se urgente, verifica lo stato del servizio esterno.'
                },

                # Errori specifici servizi comuni
                'ENOTFOUND': {
                    'reason': 'Impossibile trovare l\'indirizzo del servizio esterno.',
                    'solution': 'Verifica connessione internet. Se funziona, contatta IT per verificare la configurazione.'
                },
                'certificate': {
                    'reason': 'Problema con il certificato di sicurezza del servizio esterno.',
                    'solution': 'Errore di sicurezza della connessione. Contatta IT per verificare i certificati.'
                },
                'SSL': {
                    'reason': 'Errore nella connessione sicura (SSL/TLS) al servizio.',
                    'solution': 'Problema di sicurezza della connessione. Contatta IT immediatamente.'
                },
                'refresh token': {
                    'reason': 'Il token di accesso è scaduto e il rinnovo automatico è fallito.',
                    'solution': 'Contatta IT per riautenticare l\'account e rinnovare i permessi.'
                },
                'webhook': {
                    'reason': 'Il punto di ricezione dati automatico non è raggiungibile o configurato correttamente.',
                    'solution': 'Contatta IT per verificare la configurazione del punto di ricezione dati.'
                },
                'execution': {
                    'reason': 'Errore generico durante l\'elaborazione del processo.',
                    'solution': 'Contatta IT specificando l\'orario esatto dell\'errore per una diagnosi dettagliata.'
                }
            }

            # Cerca spiegazione
            for key, expl in explanations.items():
                if key.lower() in error_msg.lower():
                    return f"\n   [CAUSA] {expl['reason']}\n   [SOLUZIONE] {expl['solution']}"

            return f"\n   [INFO] {error_msg}\n   [SOLUZIONE] Contatta IT con questo messaggio e l'orario dell'errore."

        for i, (name, started, stopped, status, exec_id, error_data) in enumerate(errors, 1):
            duration = (stopped - started).total_seconds() if stopped else 0
            response += f"**{i}. Errore del {started.strftime('%d/%m/%Y alle %H:%M')}** (durata: {duration:.0f}s)\n"

            # Estrai e spiega errore
            if error_data:
                error_info = decompress_error_data(error_data)
                if error_info:
                    response += f"   [!] **Passaggio fallito:** {error_info['node']}\n"
                    response += explain_error(error_info['message'], error_info['node'])
                else:
                    response += "   [AVVISO] Dettagli errore non disponibili"
            else:
                response += "   [AVVISO] Dettagli errore non disponibili"

            response += "\n\n"

        response += f"**Totale errori:** {len(errors)}"

        if len(errors) >= 3:
            response += "\n\n[ATTENZIONE] Errori ripetuti rilevati. Contatta il reparto IT urgentemente con questi dettagli."

        conn.close()
        return response

    except Exception as e:
        return f"Errore recupero dettagli errore: {str(e)}"


# TOOL 4: get_executions_by_date_tool
@tool
@traceable(name="MilhenaExecutionsList", run_type="tool")
def get_executions_by_date_tool(date: str, workflow_name: Optional[str] = None) -> str:
    """
    Get detailed list of ALL executions for a specific date.

    Use this when user asks for:
    - "tutte le esecuzioni del DD/MM/YY"
    - "dammi le esecuzioni di oggi/ieri/data"
    - "cosa è stato eseguito il DD/MM"
    - "elenco esecuzioni del DD/MM"

    Args:
        date: Date in format DD/MM/YYYY or DD/MM/YY (e.g., "29/09/25", "01/10/2025")
        workflow_name: Optional - filter by workflow name

    Returns:
        Detailed list with: processo name, execution time, status, duration
    """
    try:
        # Parse date (support DD/MM/YY, DD/MM/YYYY, YYYY-MM-DD, and "oggi"/"ieri")

        # Handle special keywords
        if date.lower() in ["oggi", "today"]:
            pg_date = datetime.now().strftime("%Y-%m-%d")
        elif date.lower() in ["ieri", "yesterday"]:
            pg_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        # Check if ISO format (YYYY-MM-DD)
        elif '-' in date and len(date.split('-')) == 3:
            parts = date.split('-')
            if len(parts[0]) == 4:  # Year first (ISO format)
                pg_date = date  # Already in PostgreSQL format
            else:
                return f"[AVVISO] Formato data non valido. Usa DD/MM/YYYY o YYYY-MM-DD (es: 03/10/2025 o 2025-10-03)"
        # Italian format DD/MM/YY or DD/MM/YYYY
        elif '/' in date:
            date_parts = date.split('/')
            if len(date_parts) == 3:
                day, month, year = date_parts
                # Convert 2-digit year to 4-digit
                if len(year) == 2:
                    year = f"20{year}"
                pg_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            else:
                return f"[AVVISO] Formato data non valido. Usa DD/MM/YYYY o YYYY-MM-DD (es: 03/10/2025 o 2025-10-03)"
        else:
            return f"[AVVISO] Formato data non valido. Usa DD/MM/YYYY o YYYY-MM-DD (es: 03/10/2025 o 2025-10-03)"

        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to get ALL executions for the date
        query = """
            SELECT
                w.name,
                TO_CHAR(e."startedAt", 'HH24:MI:SS') as execution_time,
                e.status,
                EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt")) as duration_seconds
            FROM n8n.execution_entity e
            JOIN n8n.workflow_entity w ON e."workflowId" = w.id
            WHERE DATE(e."startedAt") = %s
        """

        params = [pg_date]

        if workflow_name:
            query += " AND w.name ILIKE %s"
            params.append(f"%{workflow_name}%")

        query += " ORDER BY e.\"startedAt\" DESC"

        cursor.execute(query, params)
        executions = cursor.fetchall()

        cursor.close()
        conn.close()

        if not executions:
            return f"Nessuna esecuzione trovata per il {date}"

        # Format response with ALL executions listed
        response = f"**Esecuzioni del {date}** (Totale: {len(executions)})\n\n"

        for idx, (name, exec_time, status, duration) in enumerate(executions, 1):
            status_icon = "[OK]" if status == "success" else "[ERR]"
            duration_str = f"{int(duration)}s" if duration else "N/A"

            response += f"{idx}. {status_icon} **{name}**\n"
            response += f"   • Orario: {exec_time}\n"
            response += f"   • Stato: {status}\n"
            response += f"   • Durata: {duration_str}\n\n"

        return response

    except Exception as e:
        logger.error(f"Error getting executions by date: {e}")
        return f"[ERRORE] Impossibile recuperare esecuzioni per {date}: {str(e)}"


# TOOL 5: search_knowledge_base_tool
@tool
@traceable(name="MilhenaKnowledgeBase", run_type="tool")
async def search_knowledge_base_tool(query: str, top_k: int = 3) -> str:
    """
    Search knowledge base for DOCUMENTATION, HOW-TO, PROCEDURES (NOT for workflow stats!).

    **DO NOT USE** for workflow/process statistics or details!
    Use get_workflow_details_tool or get_full_database_dump instead!

    Use this ONLY for:
    - "come funziona X?" (how does X work - conceptual)
    - "how do I...?"
    - Documentation/procedures
    - When database tools return no data

    **NEVER use for:**
    - "info su workflow X" → use get_workflow_details_tool
    - "statistiche X" → use get_full_database_dump
    - "dettagli processo Y" → use get_workflow_details_tool

    Args:
        query: Search query (conceptual questions, procedures, documentation)
        top_k: Number of results to return (default 3)

    Returns:
        Documentation from knowledge base (NOT execution stats)
    """
    try:
        from app.rag import get_rag_system

        rag = get_rag_system()
        results = await rag.search(query=query, top_k=top_k)

        if not results or len(results) == 0:
            return "Nessuna informazione trovata nella knowledge base. Contatta il reparto IT per maggiori dettagli."

        # Format results business-friendly
        response = "📚 **Informazioni dalla Knowledge Base:**\n\n"

        for i, result in enumerate(results, 1):
            content = result.get("content", "")
            metadata = result.get("metadata", {})
            score = result.get("relevance_score", 0)

            # Only show highly relevant results (score > 0.5)
            if score < 0.5:
                continue

            # Extract title and category
            title = metadata.get("title", "Informazione")
            category = metadata.get("category", "")

            response += f"**{i}. {title}**\n"
            if category:
                response += f"*Categoria: {category}*\n\n"
            response += f"{content}\n\n"
            response += "---\n\n"

        if response == "📚 **Informazioni dalla Knowledge Base:**\n\n":
            return "Nessun risultato rilevante trovato. Per informazioni specifiche, contatta il reparto IT."

        return response

    except Exception as e:
        return f"Errore ricerca knowledge base. Contatta IT per assistenza. (Dettaglio tecnico: {str(e)})"


# TOOL 6: get_node_execution_details_tool
@tool
@traceable(name="MilhenaNodeDetails", run_type="tool")
def get_node_execution_details_tool(
    workflow_name: str,
    node_name: str,
    date: str = "oggi"
) -> str:
    """
    Estrae dati di esecuzione di un NODO SPECIFICO di un workflow.

    Use cases:
    - "output del nodo Rispondi a mittente"
    - "cosa ha fatto il nodo X?"
    - "input ricevuto dal trigger"
    - "che dati ha prodotto il nodo Y?"

    Args:
        workflow_name: Nome del workflow (es: "ChatOne", "CHATBOT COMMERCIALE")
        node_name: Nome esatto del nodo (es: "Rispondi a mittente", "Ricezione Mail")
        date: Data esecuzione (DD/MM/YYYY, YYYY-MM-DD, "oggi", "ieri")

    Returns:
        Input/output del nodo specifico con timestamp e parametri
    """
    try:
        # Parse date
        if date.lower() in ["oggi", "today"]:
            pg_date = datetime.now().strftime("%Y-%m-%d")
        elif date.lower() in ["ieri", "yesterday"]:
            pg_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        elif '-' in date:
            pg_date = date  # ISO format
        elif '/' in date:
            parts = date.split('/')
            if len(parts) == 3:
                day, month, year = parts
                if len(year) == 2:
                    year = f"20{year}"
                pg_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            else:
                return "[ERRORE] Formato data non valido. Usa DD/MM/YYYY o YYYY-MM-DD"
        else:
            return "[ERRORE] Formato data non valido. Usa DD/MM/YYYY o YYYY-MM-DD"

        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to get execution data with node outputs
        query = """
            SELECT
                ee.id as execution_id,
                w.name as workflow_name,
                TO_CHAR(ee."startedAt", 'DD/MM/YYYY HH24:MI:SS') as started_at,
                ee.status,
                ed.data::jsonb -> 'resultData' -> 'runData' -> %s as node_data
            FROM n8n.execution_entity ee
            JOIN n8n.workflow_entity w ON ee."workflowId" = w.id
            JOIN n8n.execution_data ed ON ed."executionId" = ee.id
            WHERE w.name ILIKE %s
              AND DATE(ee."startedAt") = %s
              AND ed.data::jsonb -> 'resultData' -> 'runData' -> %s IS NOT NULL
            ORDER BY ee."startedAt" DESC
            LIMIT 5
        """

        cursor.execute(query, [node_name, f"%{workflow_name}%", pg_date, node_name])
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        if not results:
            return f"[INFO] Nessuna esecuzione trovata per il nodo '{node_name}' nel workflow '{workflow_name}' in data {date}."

        response = f"**Dettagli Nodo: {node_name}** ({workflow_name})\n\n"

        for exec_id, wf_name, started, status, node_data in results:
            response += f"**Esecuzione {exec_id}** - {started}\n"
            response += f"Stato: {status}\n\n"

            # Extract node execution data (first run)
            if node_data and len(node_data) > 0:
                first_run = node_data[0]

                # Input data
                if first_run.get('data', {}).get('main'):
                    main_data = first_run['data']['main'][0]
                    if main_data and len(main_data) > 0:
                        output_json = main_data[0].get('json', {})

                        # Format key fields
                        response += "**Output del nodo:**\n"
                        for key, value in list(output_json.items())[:10]:  # Limit to 10 fields
                            if isinstance(value, str) and len(value) > 200:
                                value = value[:200] + "..."
                            response += f"  • {key}: {value}\n"

                        response += "\n"

            response += "---\n\n"

        return response

    except Exception as e:
        logger.error(f"Error getting node execution details: {e}")
        return f"[ERRORE] Impossibile recuperare dettagli nodo: {str(e)}"


# TOOL 7: get_chatone_email_details_tool
@tool
@traceable(name="MilhenaChatOneEmails", run_type="tool")
def get_chatone_email_details_tool(date: str = "oggi", limit: int = 5) -> str:
    """
    Mostra email ricevute e risposte inviate dal workflow ChatOne (email automation bot).

    Use cases:
    - "che risposta ha dato il chatbot alla mail?"
    - "email ricevute oggi"
    - "ultima conversazione email"
    - "cosa ha risposto il bot?"

    Args:
        date: Data esecuzione (DD/MM/YYYY, YYYY-MM-DD, "oggi", "ieri")
        limit: Numero massimo di conversazioni da mostrare (default 5)

    Returns:
        Lista conversazioni: email ricevuta + risposta inviata
    """
    try:
        # Parse date
        if date.lower() in ["oggi", "today"]:
            pg_date = datetime.now().strftime("%Y-%m-%d")
        elif date.lower() in ["ieri", "yesterday"]:
            pg_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        elif '-' in date:
            pg_date = date
        elif '/' in date:
            parts = date.split('/')
            if len(parts) == 3:
                day, month, year = parts
                if len(year) == 2:
                    year = f"20{year}"
                pg_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            else:
                return "[ERRORE] Formato data non valido"
        else:
            return "[ERRORE] Formato data non valido"

        conn = get_db_connection()
        cursor = conn.cursor()

        # Query ChatOne workflow executions with email nodes data
        query = """
            SELECT
                ee.id,
                TO_CHAR(ee."startedAt", 'DD/MM/YYYY HH24:MI') as started,
                ed.data::jsonb -> 'resultData' -> 'runData' -> 'Ricezione Mail' -> 0 -> 'data' -> 'main' -> 0 -> 0 -> 'json' as email_received,
                ed.data::jsonb -> 'resultData' -> 'runData' -> 'Rispondi a mittente' -> 0 -> 'data' -> 'main' -> 0 -> 0 -> 'json' as email_reply
            FROM n8n.execution_entity ee
            JOIN n8n.workflow_entity w ON ee."workflowId" = w.id
            JOIN n8n.execution_data ed ON ed."executionId" = ee.id
            WHERE w.name = 'ChatOne'
              AND DATE(ee."startedAt") = %s
              AND ed.data::jsonb -> 'resultData' -> 'runData' -> 'Ricezione Mail' IS NOT NULL
            ORDER BY ee."startedAt" DESC
            LIMIT %s
        """

        cursor.execute(query, [pg_date, limit])
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        if not results:
            return f"[INFO] Nessuna email gestita da ChatOne in data {date}."

        response = f"**📧 Conversazioni Email ChatOne** ({date})\n\n"

        for exec_id, started, email_in, email_out in results:
            response += f"**Conversazione del {started}**\n\n"

            # Email ricevuta
            if email_in:
                sender = email_in.get('from', {})
                if isinstance(sender, dict):
                    sender_email = sender.get('emailAddress', {}).get('address', 'N/A')
                else:
                    sender_email = str(sender)

                subject = email_in.get('subject', 'N/A')
                body = email_in.get('bodyPreview', email_in.get('body', {}).get('content', 'N/A'))

                if isinstance(body, str) and len(body) > 150:
                    body = body[:150] + "..."

                response += f"📨 **Email ricevuta:**\n"
                response += f"  • Da: {sender_email}\n"
                response += f"  • Oggetto: {subject}\n"
                response += f"  • Contenuto: {body}\n\n"

            # Risposta inviata
            if email_out:
                reply_message = email_out.get('message', 'N/A')
                if isinstance(reply_message, str) and len(reply_message) > 200:
                    # Remove HTML tags for readability
                    reply_clean = re.sub(r'<[^>]+>', '', reply_message)
                    reply_clean = reply_clean[:200] + "..."
                else:
                    reply_clean = reply_message

                response += f"🤖 **Risposta bot:**\n"
                response += f"  {reply_clean}\n\n"

            response += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

        return response

    except Exception as e:
        logger.error(f"Error getting ChatOne email details: {e}")
        return f"[ERRORE] Impossibile recuperare conversazioni email: {str(e)}"


# TOOL 8: get_live_events_tool
@tool
@traceable(name="MilhenaLiveEvents", run_type="tool")
async def get_live_events_tool() -> str:
    """
    Eventi in tempo reale (esecuzioni attive, errori, completamenti).

    Use cases:
    - "cosa sta succedendo ora"
    - "eventi live"
    - "attività in tempo reale"
    - "cosa sta girando"

    Returns:
        Live events stream con timestamp
    """
    try:
        data = await call_backend_api("/api/business/live-events")

        if "error" in data:
            return "[ERRORE] Impossibile recuperare live events dal backend."

        events = data.get("events", [])

        if not events:
            return "[INFO] Nessun evento live al momento. Sistema in standby."

        response = "**🔴 Eventi Live**\n\n"

        for idx, event in enumerate(events[:15], 1):
            event_type = event.get('type', 'N/A')
            workflow_name = event.get('workflowName', 'N/A')
            timestamp = event.get('timestamp', 'N/A')

            emoji = "▶️" if event_type == "started" else "✅" if event_type == "success" else "❌"

            response += f"{idx}. {emoji} {workflow_name} - {event_type}\n"
            response += f"   {timestamp}\n"

        return response

    except Exception as e:
        logger.error(f"Error getting live events: {e}")
        return f"[ERRORE] Impossibile recuperare live events: {str(e)}"


# TOOL 9: get_raw_modal_data_tool
@tool
@traceable(name="MilhenaRawModalData", run_type="tool")
async def get_raw_modal_data_tool(workflow_id: str, execution_id: int = None) -> str:
    """
    Raw data per modal Timeline: NODE-LEVEL data completi con business intelligence.

    QUESTO È IL TOOL PIÙ POTENTE per dettagli node-by-node!

    Use cases:
    - "dettagli completi esecuzione [WORKFLOW]"
    - "node-by-node breakdown [WORKFLOW]"
    - "cosa ha fatto ogni nodo"
    - "timeline dettagliata [WORKFLOW]"

    Args:
        workflow_id: ID workflow
        execution_id: ID esecuzione specifica (opzionale, default=latest)

    Returns:
        Business nodes con input/output, AI summaries, email details, order data
    """
    try:
        url = f"/api/business/raw-data-for-modal/{workflow_id}"
        if execution_id:
            url += f"?executionId={execution_id}"

        data = await call_backend_api(url)

        if "error" in data:
            return f"[ERRORE] Impossibile recuperare raw modal data per workflow {workflow_id}."

        result = data.get("data", {})
        business_nodes = result.get("businessNodes", [])
        workflow = result.get("workflow", {})

        response = f"**🔬 Timeline Dettagliata: {workflow.get('name', 'N/A')}**\n\n"

        if not business_nodes:
            return f"[INFO] Nessun nodo business configurato per questo workflow. Aggiungi note 'show-1', 'show-2' ai nodi in n8n."

        for idx, node in enumerate(business_nodes, 1):
            node_name = node.get('businessName') or node.get('name', 'N/A')
            node_type = node.get('nodeType', 'N/A')
            status = node.get('status', 'unknown')

            status_emoji = "✅" if status == "success" else "❌" if status == "error" else "⚙️"

            response += f"{idx}. {status_emoji} **{node_name}**\n"
            response += f"   Tipo: {node_type}\n"

            # Extract business data
            data_obj = node.get('data', {})

            # Email data
            if data_obj.get('emailSender'):
                response += f"   📧 Email da: {data_obj.get('emailSender')}\n"
                response += f"   📝 Oggetto: {data_obj.get('emailSubject', 'N/A')[:60]}\n"

            # AI response
            if data_obj.get('aiResponse'):
                ai_resp = data_obj.get('aiResponse')[:100]
                response += f"   🤖 AI: {ai_resp}...\n"

            # Order data
            if data_obj.get('orderId'):
                response += f"   📦 Order: {data_obj.get('orderId')}\n"

            response += "\n"

        return response

    except Exception as e:
        logger.error(f"Error getting raw modal data: {e}")
        return f"[ERRORE] Impossibile recuperare raw modal data: {str(e)}"


# TOOL 10: get_workflow_cards_tool
@tool
@traceable(name="MilhenaWorkflowCards", run_type="tool")
async def get_workflow_cards_tool() -> str:
    """
    Card overview di TUTTI i workflow con metriche essenziali.

    Use cases:
    - "overview tutti i workflow"
    - "card riepilogo processi"
    - "vista generale workflow"

    Returns:
        Lista card con: nome, status, esecuzioni, success rate per ogni workflow
    """
    try:
        data = await call_backend_api("/api/business/workflow-cards")

        if "error" in data:
            return "[ERRORE] Impossibile recuperare workflow cards dal backend."

        cards = data.get("cards", [])

        if not cards:
            return "[INFO] Nessun workflow trovato."

        response = "**🗂️ Workflow Cards** (overview completo)\n\n"

        for idx, card in enumerate(cards[:15], 1):  # Limit 15
            name = card.get('name', 'N/A')
            active = card.get('active', False)
            execs = card.get('executionCount', 0)
            success_rate = card.get('successRate', 0)

            status_emoji = "🟢" if active else "⚪"

            response += f"{idx}. {status_emoji} **{name}**\n"
            response += f"   Esecuzioni: {execs} | Success: {success_rate}%\n"

        return response

    except Exception as e:
        logger.error(f"Error getting workflow cards: {e}")
        return f"[ERRORE] Impossibile recuperare workflow cards: {str(e)}"


# TOOL 11: smart_analytics_query_tool
@tool
@traceable(name="MilhenaSmartAnalytics", run_type="tool")
async def smart_analytics_query_tool(
    metric_type: str = "statistics",
    period_days: int = 7
) -> str:
    """
    Smart Analytics Query - Consolida 9 tool analytics in UNO.

    Use cases:
    - "statistiche sistema" → metric_type="statistics"
    - "top performers" → metric_type="top_performers"
    - "trend giornaliero" → metric_type="daily_trend"
    - "orari picco" → metric_type="hourly"
    - "analytics completo" → metric_type="overview"
    - "salute integrazioni" → metric_type="integration_health"
    - "insights automazioni" → metric_type="automation"

    Args:
        metric_type: Tipo metrica richiesta
          - "statistics": KPI core sistema (default)
          - "overview": Analytics overview con trend
          - "top_performers": Top 5 workflow migliori
          - "hourly": Distribuzione oraria 24h
          - "daily_trend": Trend giornaliero N giorni
          - "automation": Automation insights (growth, rate)
          - "integration_health": Health integrazioni
          - "performance": Performance metrics dettagliati
        period_days: Periodo analisi in giorni (7 o 30)

    Returns:
        Metriche richieste formattate per business user
    """
    try:
        # Route to appropriate backend API based on metric_type
        if metric_type == "statistics":
            data = await call_backend_api("/api/business/statistics")
            if "error" in data:
                return "[ERRORE] Impossibile recuperare statistiche."
            stats = data.get("data", {})
            return f"""📈 Statistiche Sistema

• Processi totali: {stats.get('totalProcesses', 0)}
• Processi attivi: {stats.get('activeProcesses', 0)}
• Esecuzioni totali: {stats.get('totalExecutions', 0)}
• Success rate: {stats.get('successRate', 0)}%
• Tempo elaborazione medio: {stats.get('avgProcessingTime', 0)}ms"""

        elif metric_type == "overview":
            data = await call_backend_api("/api/business/analytics")
            if "error" in data:
                return "[ERRORE] Impossibile recuperare analytics overview."
            overview = data.get("overview", {})
            return f"""📊 Analytics Sistema Completo

Processi: {overview.get('totalProcesses', 0)} totali, {overview.get('activeProcesses', 0)} attivi
Esecuzioni: {overview.get('totalExecutions', 0)} totali, {overview.get('successRate', 0)}% successo
Durata media: {overview.get('avgDurationSeconds', 0)}s"""

        elif metric_type == "top_performers":
            data = await call_backend_api("/api/business/top-performers")
            if "error" in data:
                return "[ERRORE] Impossibile recuperare top performers."
            performers = data.get("data", [])
            response = "🏆 Top 5 Workflow Performanti\n\n"
            for idx, perf in enumerate(performers[:5], 1):
                response += f"{idx}. {perf.get('process_name')} - {perf.get('success_rate')}% ({perf.get('execution_count')} exec)\n"
            return response

        elif metric_type == "hourly":
            data = await call_backend_api("/api/business/hourly-analytics")
            insights = data.get("insights", {})
            return f"""⏰ Distribuzione Oraria

Picco: ore {insights.get('peakHour', 0)}:00 ({insights.get('peakValue', 0)} exec)
Calmo: ore {insights.get('quietHour', 0)}:00
Media oraria: {insights.get('avgHourlyLoad', 0)} exec/h"""

        elif metric_type == "daily_trend":
            data = await call_backend_api("/api/business/daily-trend")
            daily_stats = data.get("dailyStats", [])[-period_days:]
            total = sum(d.get('executions', 0) for d in daily_stats)
            success = sum(d.get('successes', 0) for d in daily_stats)
            return f"""📈 Trend Ultimi {period_days} Giorni

Esecuzioni totali: {total}
Successi: {success}
Errori: {total-success}"""

        elif metric_type == "automation":
            data = await call_backend_api("/api/business/automation-insights")
            return f"""🤖 Automation Insights

Processi: {data.get('totalProcesses', 0)} totali, {data.get('activeProcesses', 0)} attivi
Success rate: {data.get('successRate', 0):.1f}%
Crescita settimanale: {data.get('weeklyGrowth', 0):+.1f}%"""

        elif metric_type == "integration_health":
            data = await call_backend_api("/api/business/integration-health")
            return f"""🟢 Salute Integrazioni

Status: {data.get('status', 'N/A').upper()}
Uptime: {data.get('uptime', 0):.1f}%
Connessioni: {data.get('healthyConnections', 0)}/{data.get('totalConnections', 0)}"""

        elif metric_type == "performance":
            data = await call_backend_api("/api/business/performance-metrics")
            return f"⚡ Performance Metrics\n\n{json.dumps(data, indent=2, ensure_ascii=False)[:500]}"

        else:
            return f"[ERRORE] metric_type '{metric_type}' non valido. Usa: statistics, overview, top_performers, hourly, daily_trend, automation, integration_health, performance"

    except Exception as e:
        logger.error(f"Error in smart analytics query: {e}")
        return f"[ERRORE] Impossibile recuperare analytics: {str(e)}"


# TOOL 12: smart_workflow_query_tool
@tool
@traceable(name="MilhenaSmartWorkflow", run_type="tool")
async def smart_workflow_query_tool(
    workflow_id: str,
    detail_level: str = "dashboard"
) -> str:
    """
    Smart Workflow Query - Consolida 3 tool workflow details in UNO.

    Use cases:
    - "info su ChatOne" → detail_level="basic"
    - "dashboard ChatOne" → detail_level="dashboard" (include recentActivity!)
    - "statistiche complete ChatOne" → detail_level="full_stats"

    Args:
        workflow_id: ID workflow (es: "iZnBHM7mDFS2wW0u") o nome (es: "ChatOne")
        detail_level: Livello dettaglio richiesto
          - "basic": Status, errori recenti, performance base
          - "dashboard": Dashboard completo + recentActivity (EMAIL, AI responses)
          - "full_stats": Statistiche complete 30gg (KPIs, trend, durations)

    Returns:
        Dettagli workflow al livello richiesto
    """
    try:
        # Call appropriate backend API based on detail_level
        if detail_level == "basic":
            # Use DB query for basic info
            return get_workflow_details_tool(workflow_name=workflow_id)

        elif detail_level == "dashboard":
            # Use dashboard API (has recentActivity!)
            data = await call_backend_api(f"/api/business/dashboard/{workflow_id}")
            if "error" in data:
                return f"[ERRORE] Impossibile recuperare dashboard workflow."

            workflow = data.get("workflow", {})
            recent = data.get("recentActivity", [])

            response = f"""📊 Dashboard: {workflow.get('name', 'N/A')}

Status: {'Attivo' if workflow.get('active') else 'Inattivo'}
Complessità: {workflow.get('nodeCount', 0)} passaggi

🔔 Attività Recenti ({len(recent)} eventi):
"""
            for idx, act in enumerate(recent[:5], 1):
                response += f"{idx}. [{act.get('type')}] {act.get('summary', '')[:80]}\n"
            return response

        elif detail_level == "full_stats":
            # Use full-stats API
            data = await call_backend_api(f"/api/business/workflow/{workflow_id}/full-stats?days=30")
            if "error" in data:
                return f"[ERRORE] Impossibile recuperare full stats workflow."

            kpis = data.get("kpis", {})
            return f"""📈 Statistiche Complete (30 giorni)

Esecuzioni: {kpis.get('totalExecutions', 0)} totali
Successi: {kpis.get('successfulExecutions', 0)} ({kpis.get('successRate', 0)}%)
Errori: {kpis.get('failedExecutions', 0)}
Tempo medio: {kpis.get('avgRunTime', 0)}ms
Ultime 24h: {kpis.get('last24hExecutions', 0)} esecuzioni"""

        else:
            return f"[ERRORE] detail_level '{detail_level}' non valido. Usa: basic, dashboard, full_stats"

    except Exception as e:
        logger.error(f"Error in smart workflow query: {e}")
        return f"[ERRORE] Impossibile recuperare dati workflow: {str(e)}"


# TOOL 13: smart_executions_query_tool
@tool
@traceable(name="MilhenaSmartExecutions", run_type="tool")
async def smart_executions_query_tool(
    scope: str = "recent_all",
    target: str = None,
    limit: int = 20
) -> str:
    """
    Smart Executions Query - Consolida 4 tool executions in UNO.

    Use cases:
    - "ultime esecuzioni" → scope="recent_all"
    - "esecuzioni di oggi" → scope="by_date", target="2025-10-03"
    - "esecuzioni ChatOne" → scope="by_workflow", target="iZnBHM7mDFS2wW0u"
    - "status esecuzione 123" → scope="specific", target="123"

    Args:
        scope: Tipo query esecuzioni
          - "recent_all": Ultime N esecuzioni (cross-workflow)
          - "by_date": Esecuzioni per data specifica
          - "by_workflow": Esecuzioni di workflow specifico
          - "specific": Status esecuzione singola
        target: Valore filtro (date | workflow_id | execution_id)
        limit: Numero risultati (default 20)

    Returns:
        Lista esecuzioni o status specifico
    """
    try:
        if scope == "recent_all":
            # Call backend API for recent executions
            data = await call_backend_api(f"/api/business/executions?limit={limit}")
            if "error" in data:
                return "[ERRORE] Impossibile recuperare esecuzioni."

            executions = data.get("data", [])
            if not executions:
                return "[INFO] Nessuna esecuzione recente."

            response = f"🔄 Ultime {len(executions)} Esecuzioni\n\n"
            for idx, exe in enumerate(executions[:limit], 1):
                status_emoji = "✅" if exe.get('status') == "success" else "❌"
                response += f"{idx}. {status_emoji} {exe.get('workflowName', 'N/A')} - {exe.get('status')}\n"
            return response

        elif scope == "by_date":
            if not target:
                return "[ERRORE] Specifica target=date per scope='by_date'"
            # Use DB query for date-specific
            return get_executions_by_date_tool(date=target)

        elif scope == "by_workflow":
            if not target:
                return "[ERRORE] Specifica target=workflow_id per scope='by_workflow'"
            # Call backend API
            data = await call_backend_api(f"/api/business/process-executions/{target}?limit={limit}")
            if "error" in data:
                return f"[ERRORE] Impossibile recuperare executions workflow."

            executions = data.get("data", [])
            response = f"🔄 Esecuzioni Workflow ({len(executions)})\n\n"
            for idx, exe in enumerate(executions, 1):
                response += f"{idx}. {exe.get('status')} - {exe.get('startedAt', '')[:16]}\n"
            return response

        elif scope == "specific":
            if not target:
                return "[ERRORE] Specifica target=execution_id per scope='specific'"
            # Call backend API
            data = await call_backend_api(f"/api/business/execution-status/{target}")
            if "error" in data:
                return f"[ERRORE] Impossibile recuperare execution status."

            exe = data.get("data", {})
            return f"""🔍 Execution {target}

Workflow: {exe.get('workflowName', 'N/A')}
Status: {exe.get('status', 'N/A')}
Started: {exe.get('startedAt', 'N/A')[:19]}
Duration: {exe.get('duration', 0)}ms"""

        else:
            return f"[ERRORE] scope '{scope}' non valido. Usa: recent_all, by_date, by_workflow, specific"

    except Exception as e:
        logger.error(f"Error in smart executions query: {e}")
        return f"[ERRORE] Impossibile recuperare executions: {str(e)}"


# ============================================================================
# HELPER TOOL - Referenced by smart_workflow_query_tool
# ============================================================================

@tool
@traceable(name="MilhenaWorkflowDetails", run_type="tool")
def get_workflow_details_tool(workflow_name: str) -> str:
    """
    Get COMPLETE detailed information about a specific workflow/process.

    **USE THIS when user asks about a specific workflow/process by name:**
    - "info su ChatOne"
    - "dettagli workflow X"
    - "com'è andato il processo Y"
    - "statistiche di Z"

    Returns COMPLETE data:
    - Basic info (stato, complessità, date)
    - Execution statistics (totali, successi, errori, percentuali)
    - Performance metrics (durata media/min/max)
    - Trend ultimi 7 giorni (esecuzioni giornaliere)
    - Ultime 10 esecuzioni dettagliate

    Args:
        workflow_name: Name of the workflow (can be partial, will use LIKE match)

    Returns:
        Complete workflow details with performance, trends, and execution history
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get workflow basic info
        cur.execute("""
            SELECT
                we.id,
                we.name,
                we.active,
                we."createdAt",
                we."updatedAt",
                we."triggerCount",
                JSON_ARRAY_LENGTH(we.nodes) as node_count
            FROM n8n.workflow_entity we
            WHERE LOWER(we.name) LIKE LOWER(%s)
            LIMIT 1
        """, (f"%{workflow_name}%",))

        workflow = cur.fetchone()

        if not workflow:
            return f"Processo '{workflow_name}' non trovato. Verifica il nome o contatta IT."

        wf_id, name, active, created, updated, trigger_count, node_count = workflow

        # Get execution stats
        cur.execute("""
            SELECT
                COUNT(*) as total_executions,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
                COUNT(CASE WHEN status = 'error' THEN 1 END) as failed,
                MAX("startedAt") as last_execution,
                MAX(CASE WHEN status = 'success' THEN "startedAt" END) as last_success,
                MAX(CASE WHEN status = 'error' THEN "startedAt" END) as last_error
            FROM n8n.execution_entity
            WHERE "workflowId" = %s
        """, (wf_id,))

        stats = cur.fetchone()
        total_exec, successful, failed, last_exec, last_success, last_error = stats

        # Build response
        status_emoji = "[ATTIVO]" if active else "[PAUSA]"
        status_text = "Attivo" if active else "Inattivo"

        response = f"""**{status_emoji} Processo: {name}**

**Stato:** {status_text}
**Complessità:** {node_count} passaggi
**Creato:** {created.strftime('%d/%m/%Y alle %H:%M')}
**Ultimo aggiornamento:** {updated.strftime('%d/%m/%Y alle %H:%M')}

**[STATISTICHE ESECUZIONI]**
- Totali: {total_exec or 0}
- Successo: {successful or 0} ({(successful/total_exec*100 if total_exec else 0):.1f}%)
- Errori: {failed or 0} ({(failed/total_exec*100 if total_exec else 0):.1f}%)
"""

        if last_exec:
            response += f"\n**[i] Ultima Esecuzione:** {last_exec.strftime('%d/%m/%Y alle %H:%M')}"

        if last_success:
            response += f"\n**[OK] Ultimo Successo:** {last_success.strftime('%d/%m/%Y alle %H:%M')}"

        if last_error:
            response += f"\n**[ERRORE] Ultimo Errore:** {last_error.strftime('%d/%m/%Y alle %H:%M')}"

        if not last_exec:
            response += "\n\n[AVVISO] Questo processo non è mai stato eseguito."

        # AGGIUNGI DETTAGLI AVANZATI

        # 1. DURATA MEDIA E TREND
        cur.execute("""
            SELECT
                AVG(EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt"))) as avg_duration,
                MIN(EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt"))) as min_duration,
                MAX(EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt"))) as max_duration
            FROM n8n.execution_entity
            WHERE "workflowId" = %s
            AND "stoppedAt" IS NOT NULL
        """, (wf_id,))

        duration_stats = cur.fetchone()
        if duration_stats and duration_stats[0]:
            avg_dur, min_dur, max_dur = duration_stats
            response += f"\n\n**[PERFORMANCE]**"
            response += f"\n- Durata media: {avg_dur:.1f}s"
            response += f"\n- Durata min/max: {min_dur:.1f}s / {max_dur:.1f}s"

        # 2. TREND ULTIMI 7 GIORNI
        cur.execute("""
            SELECT
                DATE("startedAt") as day,
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as success
            FROM n8n.execution_entity
            WHERE "workflowId" = %s
            AND "startedAt" >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE("startedAt")
            ORDER BY day DESC
            LIMIT 7
        """, (wf_id,))

        daily_trend = cur.fetchall()
        if daily_trend:
            response += f"\n\n**[TREND ULTIMI 7 GIORNI]**"
            for day, total, success in daily_trend:
                rate = (success/total*100) if total > 0 else 0
                response += f"\n- {day.strftime('%d/%m')}: {total} esec, {rate:.0f}% successo"

        # 3. ULTIME 10 ESECUZIONI DETTAGLIATE
        cur.execute("""
            SELECT
                "startedAt",
                "stoppedAt",
                status,
                EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt")) as duration
            FROM n8n.execution_entity
            WHERE "workflowId" = %s
            ORDER BY "startedAt" DESC
            LIMIT 10
        """, (wf_id,))

        recent_execs = cur.fetchall()
        if recent_execs:
            response += f"\n\n**[ULTIME 10 ESECUZIONI]**"
            for started, stopped, status, duration in recent_execs:
                status_icon = "[OK]" if status == "success" else "[ERR]"
                dur_str = f"{duration:.0f}s" if duration else "N/A"
                response += f"\n{status_icon} {started.strftime('%d/%m %H:%M')} - {dur_str}"

        conn.close()
        return response

    except Exception as e:
        return f"Errore recupero dettagli processo: {str(e)}"
