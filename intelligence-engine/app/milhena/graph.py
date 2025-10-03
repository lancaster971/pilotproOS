"""
MilhenaGraph - LangGraph workflow for Business Assistant
Following official LangGraph patterns with conditional routing
FULL LANGSMITH TRACING ENABLED
"""
from typing import List, Dict, Any, Optional, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.rate_limiters import InMemoryRateLimiter
from langsmith import traceable, Client
from langsmith.run_trees import RunTree
import logging
import os
from datetime import datetime
import asyncio
import uuid
import json

# Import Milhena components (using ABSOLUTE imports for LangGraph Studio compatibility)
from app.milhena.core import MilhenaCore, MilhenaConfig
from app.milhena.llm_disambiguator import LLMDisambiguator
from app.milhena.intent_analyzer import IntentAnalyzer
from app.milhena.response_generator import ResponseGenerator
from app.milhena.learning import LearningSystem
from app.milhena.token_manager import TokenManager
from app.milhena.cache_manager import CacheManager
from app.milhena.masking import TechnicalMaskingEngine
from app.milhena.business_tools import (
    get_workflows_tool,
    get_performance_metrics_tool,
    get_system_monitoring_tool,
    get_analytics_tool,
    get_workflow_details_tool,
    get_error_details_tool,
    get_all_errors_summary_tool,
    search_knowledge_base_tool,
    get_executions_by_date_tool,
    get_full_database_dump
)

# Import RAG System for knowledge retrieval
from app.rag import get_rag_system

logger = logging.getLogger(__name__)

# ============================================================================
# SUPERVISOR ORCHESTRATOR PROMPT
# ============================================================================

SUPERVISOR_PROMPT = """# 🧠 SUPERVISOR ORCHESTRATOR PROMPT – MILHENA

Sei un **agente di orchestrazione intelligente**, il **CERVELLO** del sistema **Milhena**, Business Process Assistant.
Il tuo obiettivo è **restituire SEMPRE un JSON valido** che classifichi la query utente e determini l'azione corretta, ottimizzando **velocità**, **chiarezza** e **coerenza**.

---

## 🎯 TUA MISSIONE PRINCIPALE: FORNIRE DATI SUI WORKFLOW

**WORKFLOW = ANIMA DI PILOTPRO**
- I workflow sono il cuore del business dell'utente
- Il tuo compito è FORNIRE DATI PRECISI su workflow, esecuzioni, errori, statistiche
- È MEGLIO fornire dati approssimativi che chiedere chiarimenti
- Anche query vaghe come "come va?" → interroga il database per dare risposte concrete

**TERMINOLOGIA BUSINESS (CRITICA - NON VIOLARE MAI)**:
- ✅ USA SEMPRE: processo, esecuzione, elaborazione, errore applicativo, sistema
- ❌ MAI NOMINARE: n8n, postgres, langchain, docker, redis, nginx, kubernetes, container, database

Questi termini tecnici verranno mascherati automaticamente DOPO la tua risposta.

**PRIORITÀ ASSOLUTA**:
1. Query su workflow/processi/esecuzioni/errori → **SEMPRE** `action: tool` + `needs_database: true`
2. Anche query generiche ("tutto ok?", "come va?") → interroga database
3. CLARIFICATION solo se tecnicamente impossibile interpretare (es: "ciao come è andata?" senza context)

---

## 🎯 OBIETTIVO
Analizza ogni query utente (e la cronologia chat) e:
1. **Classifica** la richiesta in una categoria chiara
2. **Scegli** una delle tre azioni disponibili (`respond`, `tool`, `route`)
3. **Fornisci** la risposta o le istruzioni per l'orchestrazione
4. **Rispondi SOLO con JSON valido**, nessun testo extra

---

## 📥 INPUT
**Query corrente**: "{query}"
**Conversazione precedente**: {chat_history}
**Contesto aggiuntivo**: {context}

## 💬 GESTIONE CONTESTO CONVERSAZIONE

**CRITICAL PRIORITY**: Se la query contiene pronomi o riferimenti temporali vaghi, **USA SEMPRE LA CRONOLOGIA**

**Riferimenti anaforici (PRIORITY 1)**:
- "e ieri?", "e oggi?", "e domani?" → Inferisci topic dall'ultimo messaggio HUMAN
- "anche quello", "lo stesso", "pure" → Ripeti topic precedente
- "questo", "quello", "la cosa" → Cerca referente in cronologia

**Come inferire topic**:
1. Trova ultimo messaggio Human in cronologia
2. Estrai il **sostantivo chiave** (ordini, errori, fatture, processi, utenti, etc.)
3. **Combina** sostantivo + nuovo contesto temporale

**Esempi PRATICI (da seguire ESATTAMENTE)**:
- User: "quanti ordini oggi?" → Milhena: "(risposta)" → User: "e ieri?"
  → **INFERISCI**: "quanti ordini ieri?" → SIMPLE_METRIC (NON clarification!)

- User: "ci sono errori?" → Milhena: "(risposta)" → User: "anche oggi?"
  → **INFERISCI**: "ci sono errori anche oggi?" → SIMPLE_STATUS

- User: "ciao" → Milhena: "ciao!" → User: "come è andato?"
  → **AMBIGUO**: history non ha topic → CLARIFICATION_NEEDED

**REGOLA D'ORO**: Se cronologia contiene topic chiaro (ordini, errori, fatture, processi, PilotPro, sistema, architettura) → NON chiedere clarification, continua topic

**DOMANDE GENERICHE CON CONTESTO**:
- User: "come è organizzata l'architettura di PilotPro?" → Milhena: "(risposta)" → User: "utilizza intelligenza artificiale?"
  → **INFERISCI**: "PilotPro utilizza intelligenza artificiale?" (NON parlare di te stessa Milhena!)
  → Usa RAG per cercare informazioni su PilotPro + AI

**IMPORTANTE**: Se l'ultimo topic era un sistema/prodotto (PilotPro, sistema X, etc.), domande generiche si riferiscono A QUEL SISTEMA, non a Milhena!

---

## 🧭 MATRICE DI DECISIONE RAPIDA

| Tipo di Query                               | Azione   | Categoria            | Output Atteso               |
|--------------------------------------------|----------|----------------------|-----------------------------|
| Saluti o convenevoli                       | respond  | GREETING             | Risposta cortese            |
| Richieste di credenziali o dati sensibili  | respond  | DANGER               | Blocco sicurezza            |
| Query vaga o incompleta                    | respond  | CLARIFICATION_NEEDED | Domanda con opzioni         |
| Domanda chiara sullo stato del sistema     | tool     | SIMPLE_STATUS        | Query al DB status          |
| Domanda chiara su numeri/metriche          | tool     | SIMPLE_METRIC        | Query al DB metrica         |
| Analisi complessa o richiesta articolata   | route    | COMPLEX_ANALYSIS     | Pipeline completa (RAG etc) |

---

## ⚙️ LE TUE 3 AZIONI DISPONIBILI

### ACTION: `"respond"`
**Quando**: puoi rispondere direttamente senza tool o pipeline
**Casi**:
- **GREETING**: "ciao", "grazie"
- **DANGER**: "password database"
- **CLARIFICATION**: query vaga ("come è andata oggi?")
- **PATTERN APPRESO**: query già vista con risposta nota
**Risultato**: `direct_response` testuale
**Latenza target**: <1000ms

---

### ACTION: `"tool"`
**Quando**: serve un dato specifico da DB/API
**Casi**:
- **SIMPLE_STATUS**: "tutto ok?"
- **SIMPLE_METRIC**: "quante fatture oggi?"
**Risultato**: Query DB → risposta → fine
**Latenza target**: <1500ms

---

### ACTION: `"route"`
**Quando**: query complessa o analisi approfondita
**Casi**:
- "analizza trend performance ultimo mese"
- "perché workflow è lento?"
- slang complesso non interpretabile subito
**Risultato**: Disambiguate → RAG → Generate → fine
**Latenza target**: <3500ms

---

## 📚 CATEGORIE

### GREETING
- **Azione**: respond
- **Esempi**: "ciao", "grazie"
- **Risposta**: `"Ciao! Come posso aiutarti con i processi aziendali?"`

### DANGER
- **Azione**: respond
- **Esempi**: "password database", "credenziali"
- **Risposta**: `"Non posso fornire informazioni sensibili. Contatta il team IT."`

### CLARIFICATION_NEEDED
- **Azione**: respond
- **Quando**: query vaga, ambigua, o manca contesto
- **Trigger Ambiguity Types** (basato su CLAMBER research):
  - **Semantic**: "info sul sistema", "come va", "dimmi tutto" (manca specificità)
  - **Who**: "dammi dati utente" (quale utente?)
  - **When**: "errori recenti" (quanto recenti?)
  - **What**: "mostrami report" (quale report?)
  - **Where**: "processi" (quali processi?)
- **Risposta**: domanda + 3-5 opzioni con emoji
- **Esempio**:
```
Da quale punto di vista vuoi sapere come è andata oggi?
📊 Status generale sistema
❌ Errori e problemi
✅ Successi
📈 Metriche
🔄 Esecuzioni
```
- **CRITICAL**: Preferisci CLARIFICATION over simple classification - è meglio chiedere che rispondere male

### SIMPLE_STATUS
- **Azione**: tool
- **Tool**: `query_system_status_tool`
- **Esempi**: "sistema ok?", "tutto funziona?"

### SIMPLE_METRIC
- **Azione**: tool
- **Tool**: `query_business_data_tool`
- **Esempi**: "quante fatture oggi?", "quanti utenti?"

### COMPLEX_ANALYSIS
- **Azione**: route
- **Esempi**: "analizza trend ultimo mese", "perché workflow è lento?"

---

## 🎓 LEARNING INTEGRATION
Se nel contesto ci sono `learned_patterns` con:
- `confidence ≥ 0.7`
- `count ≥ 2`
→ Usa direttamente quel pattern → **action = respond**

---

## 💬 DISAMBIGUAZIONE SLANG
Traduci slang in linguaggio business:

| Slang         | Business Meaning            |
|---------------|-----------------------------|
| "a puttane"   | problemi critici            |
| "casino"      | situazione disorganizzata   |
| "rotto"       | non funzionante             |
| "workflow"    | processo aziendale          |

- Se slang semplice con contesto → disambigua subito
- Se slang complesso → usa `route` con nodo di disambiguazione

---

## 🧩 OUTPUT JSON RICHIESTO

⚠️ Rispondi **SOLO** con JSON valido (nessun markdown, nessun testo extra)

```json
{{
  "action": "respond|tool|route",
  "category": "GREETING|DANGER|CLARIFICATION_NEEDED|SIMPLE_STATUS|SIMPLE_METRIC|COMPLEX_ANALYSIS",
  "confidence": 0.95,
  "reasoning": "spiegazione decisione (max 40 parole)",
  "direct_response": "testo se action=respond, altrimenti null",
  "needs_rag": true/false,
  "needs_database": true/false,
  "clarification_options": ["opz1", "opz2", "opz3"] o null
}}
```

---

## 📚 QUANDO USARE RAG vs DATABASE

**needs_rag = true** quando la domanda riguarda:
- **Cos'è PilotProOS?** → Panoramica sistema
- **Come funziona...?** → Documentazione/guide
- **PilotPro utilizza AI?** → Caratteristiche sistema
- **FAQ generali** → Domande frequenti
- **Troubleshooting** → "Cosa faccio se...?"

**needs_database = true** quando la domanda riguarda:
- **Quali processi...?** → Elenco workflow live
- **Quante esecuzioni...?** → Statistiche real-time
- **Ci sono errori...?** → Status errori correnti
- **Quando è stato eseguito...?** → Timestamp specifici
- **Processo X funziona?** → Status specifico workflow

**Entrambi true** quando serve sia contesto che dati:
- "Cosa fa il processo X?" → RAG (descrizione) + DB (status)

**REGOLA CRITICA**:
- Domande su WORKFLOW SPECIFICI → `needs_database: true` (priorità DB!)
- Domande su SISTEMA/CONCETTI → `needs_rag: true`

## 🔄 TEMPLATE DI FALLBACK
Usa questo se non sei sicuro:
```json
{{
  "action": "respond",
  "category": "CLARIFICATION_NEEDED",
  "confidence": 0.50,
  "reasoning": "Query non classificabile, meglio chiedere chiarimenti",
  "direct_response": "Puoi chiarire meglio cosa intendi?",
  "needs_rag": false,
  "needs_database": false,
  "clarification_options": null
}}
```

---

## 🧠 PRIORITÀ (ordinata per importanza)
1. **DANGER** → blocca subito (massima priorità)
2. **LEARNED PATTERN** → rispondi diretto (se confidence ≥ 0.7)
3. **GREETING** → rispondi cortese (solo se inequivocabile: "ciao", "grazie")
4. **SIMPLE_*/DATABASE_QUERY** → usa tool (anche con confidence >= 0.6) ⚠️ PRIORITÀ ALTA
5. **COMPLEX_ANALYSIS** → pipeline completa se serve analisi approfondita
6. **CLARIFICATION_NEEDED** → ultima risorsa (solo se impossibile interpretare)

## 🔍 WHEN TO TRIGGER CLARIFICATION_NEEDED
**⚠️ ATTENZIONE: Usa CLARIFICATION solo come ULTIMA RISORSA**

**CASI AMMESSI (molto rari)**:
- Queries generiche SENZA topic chiaro: "come è andata?" (senza contesto)
- Pronomi vaghi SENZA cronologia: "questo", "quello" (primo messaggio)
- SOLO se tecnicamente impossibile inferire: nessun topic in cronologia + query ambigua

**⚠️ NON USARE CLARIFICATION PER**:
- "errori" → interroga DB per errori recenti (action: tool)
- "come va" → interroga DB per status generale (action: tool)
- "workflow" / "processi" → interroga DB (action: tool)
- "oggi" / "ieri" → usa timestamp automaticamente (action: tool)
- Query vaghe MA su topic workflow → SEMPRE tool

**REGOLA D'ORO NUOVA**: Se la query menziona workflow/processi/esecuzioni/errori → SEMPRE `action: tool`

**Regola d'oro**: minimizza latenza → preferisci `respond` quando possibile.

---

Rispondi SOLO con JSON valido. NO markdown blocks. NO testo extra.
"""

# ============================================================================
# LANGSMITH CONFIGURATION FOR MILHENA
# ============================================================================

# Configure LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "milhena-v3-production"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

# Verify API key is set
if not os.getenv("LANGCHAIN_API_KEY"):
    logger.warning("LANGCHAIN_API_KEY not set - LangSmith tracing disabled")
else:
    logger.info("LangSmith tracing enabled for Milhena v3")
    # Initialize LangSmith client
    langsmith_client = Client()

# ============================================================================
# STATE DEFINITION - Following LangGraph best practices
# ============================================================================

class SupervisorDecision(TypedDict):
    """Supervisor classification decision"""
    action: str  # respond|tool|route
    category: str  # GREETING|DANGER|CLARIFICATION_NEEDED|SIMPLE_STATUS|SIMPLE_METRIC|COMPLEX_ANALYSIS
    confidence: float
    reasoning: str
    direct_response: Optional[str]
    needs_rag: bool
    needs_database: bool
    clarification_options: Optional[List[str]]
    llm_used: str

class MilhenaState(TypedDict):
    """State for Milhena conversation flow"""
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    intent: Optional[str]
    session_id: str
    context: Dict[str, Any]
    disambiguated: bool
    response: Optional[str]
    feedback: Optional[str]
    cached: bool
    masked: bool
    error: Optional[str]
    rag_context: Optional[List[Dict[str, Any]]]  # RAG retrieved documents
    learned_patterns: Optional[List[Dict[str, Any]]]  # Learning system patterns

    # NEW: Supervisor fields
    supervisor_decision: Optional[SupervisorDecision]
    waiting_clarification: bool
    original_query: Optional[str]  # For learning

# ============================================================================
# MILHENA TOOLS - Business-focused tools with masking
# ============================================================================

@tool
@traceable(name="MilhenaStatusCheck", run_type="tool")
def check_business_status() -> str:
    """
    Check the status of business processes.
    Returns current system health in business terms.
    """
    return """Sistema operativo e funzionante.
Processi attivi: 12
Elaborazioni completate oggi: 47
Performance: Ottimale"""

@tool
@traceable(name="MilhenaMetrics", run_type="tool")
def get_business_metrics() -> str:
    """
    Get key business metrics for the day.
    Returns performance indicators.
    """
    return """Metriche giornaliere:
- Processi completati: 98%
- Tempo medio elaborazione: 2.3 minuti
- Disponibilità sistema: 99.9%
- Utenti attivi: 15"""

@tool
@traceable(name="MilhenaQueryUsers", run_type="tool")
def query_users_tool(query_type: str = "count") -> str:
    """
    Query REAL users from PostgreSQL database.

    Args:
        query_type: "all", "active", or "count"

    Returns:
        Real user data from pilotpros.users table
    """
    import psycopg2

    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres-dev"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "pilotpros_db"),
            user=os.getenv("DB_USER", "pilotpros_user"),
            password=os.getenv("DB_PASSWORD", "pilotpros_secure_pass_2025")
        )
        cur = conn.cursor()

        if query_type == "count":
            cur.execute("""
                SELECT COUNT(*) as total, COUNT(CASE WHEN is_active THEN 1 END) as active
                FROM pilotpros.users
            """)
            result = cur.fetchone()
            response = f"Total users: {result[0]}, Active users: {result[1]}"
        elif query_type == "active":
            cur.execute("""
                SELECT email, full_name, role FROM pilotpros.users
                WHERE is_active = true ORDER BY created_at DESC LIMIT 5
            """)
            results = cur.fetchall()
            users = [f"{r[1] or 'No name'} ({r[0]}) - {r[2]}" for r in results]
            response = "Active users:\\n" + "\\n".join(users) if users else "No active users"
        else:
            cur.execute("""
                SELECT email, full_name, is_active FROM pilotpros.users
                ORDER BY created_at DESC LIMIT 5
            """)
            results = cur.fetchall()
            users = [f"{r[1]} ({r[0]}) - Active: {r[2]}" for r in results]
            response = "Users:\\n" + "\\n".join(users) if users else "No users"

        conn.close()
        return response
    except Exception as e:
        return f"Database error: {str(e)}"

@tool
@traceable(name="MilhenaExecutions", run_type="tool")
def get_executions_tool(query_type: str = "last") -> str:
    """
    Get workflow executions from n8n database.

    Args:
        query_type: "last", "today", "failed", or "all"

    Returns:
        Execution data from n8n.execution_entity
    """
    import psycopg2
    from datetime import datetime, timedelta

    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres-dev"),
            port=5432,
            dbname="pilotpros_db",
            user="pilotpros_user",
            password="pilotpros_secure_pass_2025"
        )
        cur = conn.cursor()

        if query_type == "last":
            cur.execute("""
                SELECT id, finished, mode, "startedAt", "stoppedAt", status,
                       EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt")) as duration_seconds
                FROM n8n.execution_entity
                ORDER BY "startedAt" DESC
                LIMIT 1
            """)
            result = cur.fetchone()
            if result:
                duration = f"{result[6]:.1f}" if result[6] else "N/A"
                started = result[3].strftime("%d/%m/%Y alle %H:%M") if result[3] else "N/A"
                response = f"""Ultima esecuzione:
- ID: {result[0]}
- Data: {started}
- Durata: {duration} secondi
- Stato: {result[5].upper() if result[5] else 'IN CORSO'}
- Modalità: {result[2]}"""
            else:
                response = "Nessuna esecuzione trovata"

        elif query_type == "today":
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cur.execute("""
                SELECT COUNT(*),
                       COUNT(CASE WHEN status = 'success' THEN 1 END),
                       COUNT(CASE WHEN status = 'error' THEN 1 END)
                FROM n8n.execution_entity
                WHERE "startedAt" >= %s
            """, (today,))
            result = cur.fetchone()
            response = f"""Esecuzioni di oggi:
- Totali: {result[0]}
- Successo: {result[1]}
- Errori: {result[2]}
- Tasso successo: {(result[1]/result[0]*100 if result[0] > 0 else 0):.1f}%"""

        elif query_type == "failed":
            cur.execute("""
                SELECT id, "startedAt", mode
                FROM n8n.execution_entity
                WHERE status = 'error'
                ORDER BY "startedAt" DESC
                LIMIT 5
            """)
            results = cur.fetchall()
            if results:
                errors = [f"- ID {r[0]}: {r[1].strftime('%d/%m %H:%M')} ({r[2]})" for r in results]
                response = "Ultime esecuzioni fallite:\n" + "\n".join(errors)
            else:
                response = "Nessuna esecuzione fallita recentemente"

        conn.close()
        return response

    except Exception as e:
        return f"Errore accesso esecuzioni: {str(e)}"

@tool
@traceable(name="MilhenaSystemStatus", run_type="tool")
def get_system_status_tool() -> str:
    """
    Get REAL system status from PostgreSQL.
    Returns actual metrics from database.
    """
    import psycopg2

    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres-dev"),
            port=5432,
            dbname="pilotpros_db",
            user="pilotpros_user",
            password="pilotpros_secure_pass_2025"
        )
        cur = conn.cursor()

        cur.execute("""
            SELECT pg_database_size('pilotpros_db') as db_size,
                   (SELECT COUNT(*) FROM pilotpros.users) as user_count,
                   (SELECT COUNT(*) FROM pilotpros.active_sessions) as sessions
        """)
        result = cur.fetchone()
        db_size_mb = result[0] / (1024 * 1024)

        conn.close()
        return f"""System Status:
- Database size: {db_size_mb:.2f} MB
- Total users: {result[1]}
- Active sessions: {result[2]}
- Status: Operational"""
    except Exception as e:
        return f"System check error: {str(e)}"

@tool
@traceable(name="MilhenaErrorTranslation", run_type="tool")
def translate_technical_error(error: str) -> str:
    """
    Translate technical errors to business language.

    Args:
        error: Technical error message

    Returns:
        Business-friendly error description
    """
    masking = TechnicalMaskingEngine()
    return masking.mask(error)

# ============================================================================
# GRAPH NODES - Each step in the Milhena workflow
# ============================================================================

class MilhenaGraph:
    """
    LangGraph workflow for Milhena Business Assistant
    """

    def __init__(self, config: Optional[MilhenaConfig] = None):
        self.config = config or MilhenaConfig()
        self._initialize_components()
        self._build_graph()

    def _initialize_components(self):
        """Initialize all Milhena components"""
        self.masking_engine = TechnicalMaskingEngine()
        self.disambiguator = LLMDisambiguator(self.config)
        self.intent_analyzer = IntentAnalyzer(self.config)
        self.response_generator = ResponseGenerator(self.config, self.masking_engine)
        self.learning_system = LearningSystem()
        self.token_manager = TokenManager()
        self.cache_manager = CacheManager(self.config)

        # Initialize RAG System for knowledge retrieval
        try:
            self.rag_system = get_rag_system()
            logger.info("RAG System initialized in Milhena graph")
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            self.rag_system = None

        # Initialize database tools - COMPLETE SET
        self.tools = [
            query_users_tool,
            get_system_status_tool,
            get_executions_tool,
            get_workflows_tool,
            get_performance_metrics_tool,
            get_system_monitoring_tool,
            get_analytics_tool
        ]
        self.tool_node = ToolNode(self.tools)

        # Initialize Rate Limiters (Best Practice: prevent rate limit errors)
        # Based on LangChain documentation and OpenAI Cookbook best practices
        # GROQ Free Tier: 100k tokens/day (~30 req/min safe limit)
        groq_rate_limiter = InMemoryRateLimiter(
            requests_per_second=0.5,  # 30 req/min = 0.5 req/sec (conservative)
            check_every_n_seconds=0.1,
            max_bucket_size=5  # Allow small bursts
        )

        # OpenAI Tier 1: 500 req/min, 30k req/day
        openai_rate_limiter = InMemoryRateLimiter(
            requests_per_second=8.0,  # 480 req/min (80% of limit for safety)
            check_every_n_seconds=0.1,
            max_bucket_size=10
        )

        # Initialize LLMs with rate limiters
        if os.getenv("GROQ_API_KEY"):
            self.groq_llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                api_key=os.getenv("GROQ_API_KEY"),
                rate_limiter=groq_rate_limiter
            )
        else:
            self.groq_llm = None

        if os.getenv("OPENAI_API_KEY"):
            self.openai_llm = ChatOpenAI(
                model="gpt-4.1-nano-2025-04-14",
                temperature=0.7,
                api_key=os.getenv("OPENAI_API_KEY"),
                rate_limiter=openai_rate_limiter
            )
        else:
            self.openai_llm = None

        # Initialize Supervisor LLM (GROQ primary + OpenAI fallback) with rate limiters
        self.supervisor_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,  # Low for consistent classification
            request_timeout=10.0,
            max_retries=1,
            api_key=os.getenv("GROQ_API_KEY"),
            rate_limiter=groq_rate_limiter
        ) if os.getenv("GROQ_API_KEY") else None

        self.supervisor_fallback = ChatOpenAI(
            model="gpt-4.1-nano-2025-04-14",
            temperature=0.3,
            request_timeout=10.0,
            max_retries=1,
            api_key=os.getenv("OPENAI_API_KEY"),
            rate_limiter=openai_rate_limiter
        ) if os.getenv("OPENAI_API_KEY") else None

        logger.info(f"Supervisor: GROQ={bool(self.supervisor_llm)}, Fallback={bool(self.supervisor_fallback)}")
        logger.info("MilhenaGraph initialized")

    def _build_graph(self):
        """Build the LangGraph workflow with Supervisor entry point"""
        # Create the graph
        graph = StateGraph(MilhenaState)

        # Add nodes with CLEAR PREFIXES
        # NEW: Supervisor as entry point
        graph.add_node("[SUPERVISOR] Route Query", self.supervisor_orchestrator)

        # EXISTING nodes (NON TOCCARE)
        # NOTE: [CODE] Check Cache removed - Supervisor handles routing directly
        graph.add_node("[LEARNING] Apply Patterns", self.apply_learned_patterns)
        graph.add_node("[AGENT] Disambiguate", self.disambiguate_query)
        graph.add_node("[AGENT] Analyze Intent", self.analyze_intent)
        graph.add_node("[RAG] Retrieve Context", self.retrieve_rag_context)
        # NEW: Replace hardcoded database_query with intelligent ReAct agent
        graph.add_node("[TOOL] Database Query", self.execute_react_agent)
        graph.add_node("[AGENT] Generate Response", self.generate_response)
        graph.add_node("[LIB] Mask Response", self.mask_response)
        graph.add_node("[CODE] Record Feedback", self.record_feedback)
        graph.add_node("[CODE] Handle Error", self.handle_error)

        # NEW: Set entry point to Supervisor
        graph.set_entry_point("[SUPERVISOR] Route Query")

        # NEW: Conditional routing from Supervisor
        graph.add_conditional_edges(
            "[SUPERVISOR] Route Query",
            self.route_from_supervisor,
            {
                "mask_response": "[LIB] Mask Response",  # Direct responses (GREETING, DANGER, CLARIFICATION)
                "database_query": "[TOOL] Database Query",  # Simple queries (skip Disambiguate, RAG)
                "apply_patterns": "[LEARNING] Apply Patterns"  # Complex queries (full pipeline)
            }
        )

        # EXISTING edges (NON TOCCARE - pipeline rimane identica)
        graph.add_edge("[LEARNING] Apply Patterns", "[AGENT] Disambiguate")
        graph.add_edge("[AGENT] Disambiguate", "[AGENT] Analyze Intent")

        graph.add_conditional_edges(
            "[AGENT] Analyze Intent",
            self.route_from_intent,
            {
                "technical": "[CODE] Handle Error",
                "needs_data": "[RAG] Retrieve Context",
                "business": "[AGENT] Generate Response"
            }
        )

        # RAG retrieves context, then goes to DB query or direct response
        graph.add_conditional_edges(
            "[RAG] Retrieve Context",
            self.route_after_rag,
            {
                "needs_db": "[TOOL] Database Query",
                "has_answer": "[AGENT] Generate Response"
            }
        )

        graph.add_edge("[TOOL] Database Query", "[AGENT] Generate Response")

        graph.add_edge("[AGENT] Generate Response", "[LIB] Mask Response")
        graph.add_edge("[LIB] Mask Response", "[CODE] Record Feedback")
        graph.add_edge("[CODE] Record Feedback", END)
        graph.add_edge("[CODE] Handle Error", END)

        # Initialize In-Memory Checkpointer for conversation memory
        # Best Practice (LangGraph): Start with MemorySaver for testing, upgrade to DB for production
        # MemorySaver stores conversation history in-memory (lost on restart, but simple & fast)
        checkpointer = MemorySaver()
        logger.info("✅ MemorySaver initialized - Conversation memory active (in-memory)")

        # Initialize ReAct Agent for tool calling with conversation memory
        # Best Practice (LangGraph Official): Use create_react_agent for LLM-based tool selection
        # This replaces hardcoded if/elif pattern matching with intelligent tool selection
        react_tools = [
            get_full_database_dump,
            get_workflows_tool,
            get_performance_metrics_tool,
            get_system_monitoring_tool,
            get_analytics_tool,
            get_workflow_details_tool,
            get_error_details_tool,
            get_all_errors_summary_tool,
            search_knowledge_base_tool,
            get_executions_by_date_tool
        ]

        # Use OpenAI Nano (10M tokens "Offerta Speciale") - GROQ hit rate limit
        # gpt-4.1-nano-2025-04-14: 10M tokens budget, perfect for ReAct agent
        react_model = self.openai_llm if self.openai_llm else self.groq_llm

        self.react_agent = create_react_agent(
            model=react_model,
            tools=react_tools,
            checkpointer=checkpointer  # Share same checkpointer for unified memory
        )
        logger.info("✅ ReAct Agent initialized with 10 tools (9 DB + 1 RAG) - Context-aware tool selection")

        # Compile the graph with checkpointer for memory
        self.compiled_graph = graph.compile(
            checkpointer=checkpointer,
            debug=False
        )

        logger.info("MilhenaGraph compiled with Supervisor entry point + Memory")

    # ============================================================================
    # NODE IMPLEMENTATIONS - ALL WITH LANGSMITH TRACING
    # ============================================================================

    @traceable(
        name="MilhenaCheckCache",
        run_type="chain",
        metadata={"component": "cache", "version": "3.0"}
    )
    async def check_cache(self, state: MilhenaState) -> MilhenaState:
        """Check if response is cached"""

        # Extract query from messages if not present (LangGraph Studio compatibility)
        if "query" not in state or not state.get("query"):
            messages = state.get("messages", [])
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, "content"):
                    content = last_msg.content
                    if isinstance(content, list):
                        text_parts = [part.get("text", "") if isinstance(part, dict) else str(part) for part in content]
                        state["query"] = " ".join(text_parts)
                    else:
                        state["query"] = str(content)
                else:
                    state["query"] = str(last_msg)
            else:
                state["query"] = ""

        # Initialize missing fields
        if "session_id" not in state:
            state["session_id"] = f"session-{datetime.now().timestamp()}"
        if "context" not in state:
            state["context"] = {}
        if "disambiguated" not in state:
            state["disambiguated"] = False

        query = state["query"]
        session_id = state["session_id"]

        # Log to LangSmith
        logger.info(f"[LangSmith] Checking cache for session {session_id}")

        try:
            cached_response = await self.cache_manager.get(query, session_id)

            if cached_response:
                state["cached"] = True
                state["response"] = cached_response.get("response")
                logger.info(f"[LangSmith] Cache HIT - Query: {query[:50]}...")
            else:
                state["cached"] = False
                logger.info(f"[LangSmith] Cache MISS - Query: {query[:50]}...")
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
            state["cached"] = False

        return state

    @traceable(
        name="SupervisorOrchestrator",
        run_type="chain",
        metadata={"component": "supervisor", "version": "3.1"}
    )
    async def supervisor_orchestrator(self, state: MilhenaState) -> MilhenaState:
        """
        Supervisor Orchestrator: classifica query e decide routing
        Best Practice 2025: Supervisor non fa lavoro, solo coordina
        """
        query = state["query"]
        session_id = state["session_id"]

        logger.error(f"🔍 [DEBUG] SUPERVISOR CALLED with query: '{query[:80]}'")
        logger.info(f"[SUPERVISOR] Analyzing query: {query[:50]}...")

        # STEP 0: Instant classification (fast-path bypass LLM)
        instant = self._instant_classify(query)
        if instant:
            logger.error(f"🎯 [DEBUG] INSTANT MATCH: {instant['category']} - needs_db={instant.get('needs_database')}, needs_rag={instant.get('needs_rag')}")
            logger.info(f"[FAST-PATH] Instant match: {instant['category']} (bypassed LLM)")
            decision = SupervisorDecision(**instant)
            state["supervisor_decision"] = decision
            state["waiting_clarification"] = False
            if decision["direct_response"]:
                state["response"] = decision["direct_response"]
            return state

        # STEP 1: Check Learning System (pattern già appresi)
        learned_pattern = await self.learning_system.check_learned_clarifications(
            query, session_id
        )

        if learned_pattern:
            # Pattern appreso! Skip clarification
            logger.info(f"[LEARNING] Pattern appreso: '{query[:30]}...' → {learned_pattern}")
            decision = SupervisorDecision(
                action="tool",  # Pattern appreso richiede DB query
                category="SIMPLE_METRIC",  # Assume learned pattern è sempre metric/status
                confidence=1.0,
                reasoning=f"Pattern appreso dal learning system: {learned_pattern}",
                direct_response=None,
                needs_rag=False,
                needs_database=True,
                clarification_options=None,
                llm_used="learning-system"
            )
            state["supervisor_decision"] = decision
            state["waiting_clarification"] = False
            return state

        # STEP 2: Classify con LLM
        # Prepare chat history (following LangGraph best practices)
        messages_history = state.get("messages", [])
        chat_history_str = ""
        context_additional = state.get("context", {})

        if len(messages_history) > 1:
            # Show last 4 messages for context (2 turns = user + assistant)
            recent = messages_history[-5:-1] if len(messages_history) > 5 else messages_history[:-1]

            # Format as conversation (Human/AI labels)
            formatted_msgs = []
            for msg in recent:
                if hasattr(msg, "content"):
                    role = "User" if isinstance(msg, HumanMessage) else "Milhena"
                    formatted_msgs.append(f"{role}: {msg.content[:150]}")

            chat_history_str = "\n".join(formatted_msgs)
        else:
            chat_history_str = "(Prima interazione - nessuna cronologia)"

        # Additional context (metadata, etc.)
        context_str = json.dumps(context_additional, indent=2) if context_additional else "{}"

        prompt = SUPERVISOR_PROMPT.format(
            query=query,
            chat_history=chat_history_str,
            context=context_str
        )

        try:
            # Try GROQ first (free + fast)
            if self.supervisor_llm:
                logger.info("[SUPERVISOR] Using GROQ for classification")
                response = await self.supervisor_llm.ainvoke(prompt)
                classification = json.loads(response.content)
                classification["llm_used"] = "groq"
                logger.info(f"[SUPERVISOR] GROQ: {classification['category']} (conf: {classification['confidence']:.2f})")
            else:
                raise Exception("GROQ not available")

        except Exception as e:
            # Fallback to OpenAI
            logger.warning(f"[SUPERVISOR] GROQ failed: {e}, using OpenAI fallback")

            if self.supervisor_fallback:
                response = await self.supervisor_fallback.ainvoke(prompt)
                classification = json.loads(response.content)
                classification["llm_used"] = "openai-nano"
                logger.info(f"[SUPERVISOR] OpenAI: {classification['category']} (conf: {classification['confidence']:.2f})")
            else:
                # Ultimate fallback: rule-based
                classification = self._fallback_classification(query)
                classification["llm_used"] = "rule-based"
                logger.warning("[SUPERVISOR] Using rule-based fallback")

        # STEP 3: Save decision
        decision = SupervisorDecision(**classification)
        state["supervisor_decision"] = decision

        # STEP 4: Handle waiting clarification
        if decision["category"] == "CLARIFICATION_NEEDED":
            state["waiting_clarification"] = True
            state["original_query"] = query
            state["response"] = decision["direct_response"]
            logger.info(f"[SUPERVISOR] Waiting clarification with {len(decision.get('clarification_options', []))} options")
        else:
            state["waiting_clarification"] = False
            if decision["direct_response"]:
                # Direct response (GREETING, DANGER)
                state["response"] = decision["direct_response"]
                logger.info(f"[SUPERVISOR] Direct response for {decision['category']}")

        # STEP 5: If previous message was clarification, record pattern
        if state.get("context", {}).get("previous_clarification_asked"):
            original = state["context"].get("previous_query")
            if original and original != query:
                # User ha risposto alla clarification
                await self.learning_system.record_clarification(
                    original_query=original,
                    clarification=query,
                    session_id=session_id
                )
                # Clear flag
                state["context"]["previous_clarification_asked"] = False
                logger.info(f"[LEARNING] Recorded clarification: '{original[:30]}...' → '{query[:30]}...'")

        # STEP 6: If asking clarification, set flag for next message
        if decision["category"] == "CLARIFICATION_NEEDED":
            if "context" not in state:
                state["context"] = {}
            state["context"]["previous_clarification_asked"] = True
            state["context"]["previous_query"] = query

        logger.info(f"[SUPERVISOR] Decision: {decision['category']} → needs_rag={decision['needs_rag']}, needs_db={decision['needs_database']}")

        return state

    def _fallback_classification(self, query: str) -> Dict[str, Any]:
        """
        Rule-based fallback quando LLM non disponibili
        """
        query_lower = query.lower()

        # DANGER keywords (expanded based on LangChain security best practices)
        danger_keywords = [
            "password", "credential", "api key", "secret", "token",
            "connessione database", "connection string", "dsn",
            "api_key", "access_token", "chiave", "credenziali",
            "passwd", "pwd", "auth token", "bearer token",
            "access key", "refresh token", "private key"
        ]
        if any(kw in query_lower for kw in danger_keywords):
            return {
                "action": "respond",
                "category": "DANGER",
                "confidence": 1.0,  # Maximum confidence for security
                "reasoning": "Blocco sicurezza: richiesta dati sensibili",
                "direct_response": "Non posso fornire informazioni su dati sensibili del sistema.",
                "needs_rag": False,
                "needs_database": False,
                "clarification_options": None
            }

        # CLARIFICATION patterns (ambiguous queries - based on CLAMBER research)
        ambiguous_patterns = [
            "dammi info", "info sul", "come va", "dimmi tutto", "cosa c'è",
            "novità", "come è andata", "come sono andate", "dimmi",
            "il sistema", "questo", "quello", "la cosa",
            "errori" if len(query_lower.split()) <= 2 else None,  # "errori" alone is ambiguous
            "report" if len(query_lower.split()) <= 2 else None,
            "dati" if len(query_lower.split()) <= 2 else None,
        ]
        ambiguous_patterns = [p for p in ambiguous_patterns if p]  # Remove None

        if any(pattern in query_lower for pattern in ambiguous_patterns):
            return {
                "action": "respond",
                "category": "CLARIFICATION_NEEDED",
                "confidence": 0.8,
                "reasoning": "Query ambigua: manca specificità",
                "direct_response": "Cosa vuoi sapere esattamente?\n\n📊 Status generale sistema\n❌ Errori e problemi\n📈 Metriche e statistiche\n🔄 Esecuzioni processi\n📝 Report dettagliati",
                "needs_rag": False,
                "needs_database": False,
                "clarification_options": ["status", "errori", "metriche", "esecuzioni", "report"]
            }

        # GREETING keywords
        greeting_keywords = ["ciao", "buongiorno", "buonasera", "salve", "hello", "grazie", "arrivederci"]
        if any(kw in query_lower for kw in greeting_keywords) and len(query.split()) <= 3:
            return {
                "action": "respond",
                "category": "GREETING",
                "confidence": 0.85,
                "reasoning": "Rule-based: saluto rilevato",
                "direct_response": "Ciao! Come posso aiutarti?",
                "needs_rag": False,
                "needs_database": False,
                "clarification_options": None
            }

        # SIMPLE_METRIC keywords
        metric_keywords = ["quant", "numer", "count", "quanti", "quante"]
        if any(kw in query_lower for kw in metric_keywords):
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.7,
                "reasoning": "Rule-based: keyword metrica rilevata",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None
            }

        # Default: CLARIFICATION (conservative - meglio chiedere che sbagliare)
        return {
            "action": "respond",
            "category": "CLARIFICATION_NEEDED",
            "confidence": 0.6,
            "reasoning": "Query non riconosciuta: richiesta chiarimento",
            "direct_response": "Puoi essere più specifico? Cosa vuoi sapere?\n\n📊 Status sistema\n❌ Errori\n📈 Metriche\n🔄 Processi\n📝 Report",
            "needs_rag": False,
            "needs_database": False,
            "clarification_options": ["status", "errori", "metriche", "processi", "report"]
        }

    def _instant_classify(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Instant classification using regex patterns (bypass LLM).
        Returns classification dict or None if no match.

        This fast-path reduces latency from ~3s to <50ms for common queries.
        Best Practice: Use regex for high-frequency patterns to reduce LLM costs.
        """
        import re

        query_lower = query.lower().strip()

        # GREETING patterns (exact match)
        greeting_exact = {"ciao", "buongiorno", "buonasera", "hello", "hi", "salve",
                         "grazie", "arrivederci", "buonanotte", "hey"}
        if query_lower in greeting_exact:
            return {
                "action": "respond",
                "category": "GREETING",
                "confidence": 1.0,
                "reasoning": "Saluto comune - fast-path",
                "direct_response": "Ciao! Come posso aiutarti con i processi aziendali?",
                "needs_rag": False,
                "needs_database": False,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # DANGER keywords (expanded based on security best practices)
        danger_keywords = [
            "password", "credenziali", "credential", "api key", "token",
            "secret", "chiave", "accesso admin", "root password",
            "connection string", "dsn", "db url", "database url",
            "api_key", "access_token", "bearer", "auth token",
            "passwd", "pwd", "private key", "refresh token"
        ]
        if any(kw in query_lower for kw in danger_keywords):
            return {
                "action": "respond",
                "category": "DANGER",
                "confidence": 1.0,
                "reasoning": "Blocco sicurezza immediato - fast-path",
                "direct_response": "Non posso fornire informazioni su dati sensibili del sistema.",
                "needs_rag": False,
                "needs_database": False,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # META-QUERIES: Questions ABOUT the assistant itself (NOT workflows)
        # IMPORTANT: Check this BEFORE workflow patterns to avoid confusion
        # BUT: Skip if user explicitly mentions "workflow" or "processo"
        if not re.search(r'\b(workflow|processo|processi|process|esecuzione)', query_lower):
            meta_patterns = [
                r'\b(chi sei|cosa sei|come ti chiami)\b',
                r'\b(cosa|chi|come).*\b(milhena|milena)\b',
                r'\b(milhena|milena)\b.*\b(cosa|chi|come|puoi|fai)\b',
                r'\binformazioni\s+(su|di|riguard)?\s*(milhena|milena)$',  # Solo se finisce con milhena
                r'\bparla.*\b(milhena|milena)\b',
            ]
        else:
            meta_patterns = []
        for pattern in meta_patterns:
            if re.search(pattern, query_lower):
                logger.info(f"[FAST-PATH] META-QUERY detected: asking about assistant itself")
                return {
                    "action": "respond",  # Direct response (RAG search not reliable for meta-queries)
                    "category": "ABOUT_ASSISTANT",
                    "confidence": 0.95,
                    "reasoning": "Meta-query - user asking about Milhena assistant (not workflow)",
                    "direct_response": "Sono Milhena, l'assistente intelligente di PilotProOS.\n\n**Cosa faccio:**\n• Fornisco informazioni sui processi aziendali\n• Mostro statistiche e metriche in tempo reale\n• Spiego errori in linguaggio business\n\n**Cosa NON faccio:**\n• NON ho accesso a password o credenziali\n• NON posso eseguire processi (solo informazioni)\n\n**Come aiutarti:**\nChiedi in italiano: \"Quanti processi?\", \"Ci sono errori?\", \"Info sul processo X\"\n\nAltro?",
                    "needs_rag": False,
                    "needs_database": False,
                    "clarification_options": None,
                    "llm_used": "fast-path"
                }

        # WORKFLOW/PROCESS patterns (HIGH PRIORITY - core mission)
        workflow_patterns = [
            "mostra workflow", "lista workflow", "workflow attiv", "processi attiv",
            "quali workflow", "quali processi", "elenco workflow", "elenco processi",
            "vedi workflow", "vedi processi", "workflow", "processi",
            "quale workflow", "quale processo", "ultimo workflow", "ultim",
            "esecuzioni", "esecuzione", "errori", "errore", "fallito", "falliti",
            "stato", "status", "come va", "come stanno", "tutto ok"
        ]
        if any(pattern in query_lower for pattern in workflow_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.95,  # Aumentata confidence per workflow queries
                "reasoning": "Query workflow/esecuzioni - fast-path (missione core)",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # PERFORMANCE/METRICS patterns (NEW - analytics queries)
        performance_patterns = [
            "performance", "metriche", "statistiche", "analisi",
            "andamento", "trend", "come va", "come stanno andando"
        ]
        if any(pattern in query_lower for pattern in performance_patterns) and len(query.split()) <= 6:
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.85,
                "reasoning": "Query performance - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # SIMPLE_METRIC patterns (starts with - quantitative queries)
        metric_starts = ["quant", "quand", "numero", "count", "quanti", "quante"]
        if any(query_lower.startswith(prefix) for prefix in metric_starts):
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.9,
                "reasoning": "Query metrica quantitativa - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # SIMPLE_STATUS patterns (system health checks)
        status_patterns = [
            "tutto ok", "sistema ok", "funziona", "va bene",
            "stato sistema", "tutto bene", "status", "salute sistema",
            "ci sono problemi", "problemi sistema"
        ]
        if any(pattern in query_lower for pattern in status_patterns) and len(query.split()) <= 5:
            return {
                "action": "tool",
                "category": "SIMPLE_STATUS",
                "confidence": 0.85,
                "reasoning": "Query status sistema - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # ERROR patterns (error checking queries)
        error_patterns = [
            "ci sono errori", "errori da segnalare", "problemi da segnalare",
            "errori sistema", "errori nel sistema", "ci sono problemi",
            "qualche errore", "errori recenti", "ultimi errori"
        ]
        if any(pattern in query_lower for pattern in error_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_STATUS",
                "confidence": 0.9,
                "reasoning": "Query errori sistema - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # TEMPORAL patterns (when/last time - HIGH PRIORITY)
        # Based on help desk research: users frequently ask "when did X happen"
        temporal_patterns = [
            "quando", "a che ora", "ultima volta", "ultimo",
            "data", "timestamp", "orario", "recente", "ultime"
        ]
        if any(pattern in query_lower for pattern in temporal_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.85,
                "reasoning": "Query temporale - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # DURATION patterns (how long - HIGH PRIORITY)
        # Based on business monitoring: users want to know execution times
        duration_patterns = [
            "quanto tempo", "quanto dura", "durata",
            "tempo di", "ci vuole", "impiega", "velocità"
        ]
        if any(pattern in query_lower for pattern in duration_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.85,
                "reasoning": "Query durata - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # TREND/HISTORICAL patterns (negli ultimi/scorsi - HIGH PRIORITY)
        # Based on analytics needs: users want historical data
        trend_patterns = [
            "negli ultimi", "ultimi", "scorsi", "passati",
            "trend", "andamento", "storico", "settimana", "mese", "giorni"
        ]
        if any(pattern in query_lower for pattern in trend_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.8,
                "reasoning": "Query trend/storico - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # LIST/ENUMERATION patterns (extended - HIGH PRIORITY)
        # Based on business needs: users want complete lists
        list_patterns = [
            "lista", "elenco", "tutti", "tutte",
            "visualizza", "fammi vedere", "elenca"
        ]
        if any(pattern in query_lower for pattern in list_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.85,
                "reasoning": "Query lista/elenco - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # COMPARATIVE patterns (MEDIUM PRIORITY - Fase 2)
        # Based on KPI analysis: users want to compare metrics
        comparative_patterns = [
            "più", "meno", "migliore", "peggiore",
            "confronta", "differenza", "meglio", "vs"
        ]
        if any(pattern in query_lower for pattern in comparative_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.8,
                "reasoning": "Query comparativa - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # AGGREGATION patterns (MEDIUM PRIORITY - Fase 2)
        # Based on business metrics: users want totals/averages
        aggregation_patterns = [
            "totale", "somma", "media", "percentuale",
            "rapporto", "ratio", "tasso", "average"
        ]
        if any(pattern in query_lower for pattern in aggregation_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.8,
                "reasoning": "Query aggregazione - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # CAUSALITY patterns (MEDIUM PRIORITY - Fase 2)
        # Based on troubleshooting: users want explanations
        causality_patterns = [
            "perché", "perchè", "come mai", "motivo",
            "causa", "ragione"
        ]
        if any(pattern in query_lower for pattern in causality_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_STATUS",
                "confidence": 0.75,
                "reasoning": "Query causale - fast-path",
                "direct_response": None,
                "needs_rag": True,  # Might need RAG for explanations
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # BATCH 3 - HIGH FREQUENCY PATTERNS (50 pattern)
        # Based on comprehensive business KPI research

        # FREQUENCY patterns (ogni quanto/frequenza)
        frequency_patterns = [
            "ogni quanto", "frequenza", "periodicità", "cadenza",
            "intervallo", "quante volte", "spesso"
        ]
        if any(pattern in query_lower for pattern in frequency_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.8,
                "reasoning": "Query frequenza - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # RATE/PERCENTAGE patterns (tasso/percentuale)
        rate_patterns = [
            "tasso", "rate", "percentuale", "%",
            "success rate", "failure rate", "conversion"
        ]
        if any(pattern in query_lower for pattern in rate_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.85,
                "reasoning": "Query tasso/rate - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # TOP/BEST patterns (migliore/top/peggiore)
        ranking_patterns = [
            "top", "best", "worst", "bottom",
            "first", "last", "maggior", "minor"
        ]
        if any(pattern in query_lower for pattern in ranking_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.8,
                "reasoning": "Query ranking - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # COUNT/NUMBER patterns (count/numero/totale variations)
        count_variations = [
            "count", "numero di", "quantità",
            "ammontare", "how many", "volume"
        ]
        if any(pattern in query_lower for pattern in count_variations):
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.85,
                "reasoning": "Query count - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # DETAILS patterns (dettagli/informazioni/show me)
        details_patterns = [
            "dettagli", "informazioni", "info",
            "show me", "dammi info", "voglio sapere"
        ]
        if any(pattern in query_lower for pattern in details_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.75,
                "reasoning": "Query dettagli - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # HEALTH/STATUS variations (salute/disponibilità)
        health_patterns = [
            "salute", "health", "disponibilità",
            "availability", "uptime", "operativo"
        ]
        if any(pattern in query_lower for pattern in health_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_STATUS",
                "confidence": 0.85,
                "reasoning": "Query health - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # ACTIVE/INACTIVE patterns (attivo/inattivo/running)
        activity_patterns = [
            "running", "in esecuzione", "fermo",
            "stopped", "paused", "in pausa"
        ]
        if any(pattern in query_lower for pattern in activity_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_STATUS",
                "confidence": 0.8,
                "reasoning": "Query activity - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # FIRST/LAST patterns (primo/ultimo)
        position_patterns = [
            "primo", "prima", "first",
            "latest", "earliest", "più recente"
        ]
        if any(pattern in query_lower for pattern in position_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.8,
                "reasoning": "Query posizione - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # FAILED/SUCCESS patterns (fallito/successo)
        outcome_patterns = [
            "fallito", "failed", "success",
            "riuscito", "completato", "interrotto"
        ]
        if any(pattern in query_lower for pattern in outcome_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_STATUS",
                "confidence": 0.85,
                "reasoning": "Query outcome - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # CHANGES patterns (modificato/aggiornato/cambiato)
        change_patterns = [
            "modificato", "cambiato", "aggiornato",
            "changed", "updated", "modifiche"
        ]
        if any(pattern in query_lower for pattern in change_patterns):
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.75,
                "reasoning": "Query changes - fast-path",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # No fast-path match → use LLM
        return None

    @traceable(
        name="MilhenaClassifyComplexity",
        run_type="chain",
        metadata={"component": "optimization", "version": "3.0"}
    )
    async def classify_complexity(self, state: MilhenaState) -> MilhenaState:
        """
        Classify query complexity for fast-path optimization.
        Simple queries skip disambiguation and RAG retrieval.
        """
        query = state["query"].lower()
        word_count = len(query.split())

        # Keywords for simple STATUS queries
        simple_keywords = [
            "come va", "come vanno", "status", "stato",
            "ciao", "hello", "salve", "buongiorno",
            "sistema", "funziona", "ok", "bene"
        ]

        # Keywords for simple GREETING queries
        greeting_keywords = ["ciao", "hello", "salve", "buongiorno", "buonasera", "hey"]

        # Classify as simple if:
        # 1. Short query (<10 words) AND
        # 2. Contains simple/greeting keywords
        is_simple = (
            word_count < 10 and
            any(keyword in query for keyword in simple_keywords + greeting_keywords)
        )

        state["context"]["is_simple_query"] = is_simple
        state["context"]["word_count"] = word_count

        if is_simple:
            logger.info(f"[OPTIMIZATION] Classified as SIMPLE query (words: {word_count})")
        else:
            logger.info(f"[OPTIMIZATION] Classified as COMPLEX query (words: {word_count})")

        return state

    @traceable(
        name="MilhenaApplyPatterns",
        run_type="chain",
        metadata={"component": "learning", "version": "3.0"}
    )
    async def apply_learned_patterns(self, state: MilhenaState) -> MilhenaState:
        """Apply learned patterns from previous interactions"""
        query = state["query"]
        session_id = state["session_id"]

        try:
            # Get learned patterns from learning system
            patterns = await self.learning_system.get_relevant_patterns(query)

            if patterns:
                state["learned_patterns"] = patterns
                state["context"]["learned_patterns"] = patterns
                logger.info(f"Applied {len(patterns)} learned patterns")
            else:
                state["learned_patterns"] = []
                logger.info("No relevant learned patterns found")

        except Exception as e:
            logger.warning(f"Failed to apply learned patterns: {e}")
            state["learned_patterns"] = []

        return state

    @traceable(name="MilhenaDisambiguate")
    async def disambiguate_query(self, state: MilhenaState) -> MilhenaState:
        """Disambiguate ambiguous queries"""
        query = state["query"]
        context = state["context"]

        try:
            result = await self.disambiguator.disambiguate(query, context)

            # Handle both DisambiguationResult object and dict
            if isinstance(result, dict):
                is_ambiguous = result.get("is_ambiguous", False)
                clarified_intent = result.get("clarified_intent", "")
                confidence = result.get("confidence", 0.0)
            else:
                is_ambiguous = result.is_ambiguous
                clarified_intent = result.clarified_intent
                confidence = result.confidence

            state["disambiguated"] = not is_ambiguous
            state["context"]["disambiguated_intent"] = clarified_intent
            state["context"]["confidence"] = confidence

            logger.info(f"Disambiguation complete: {clarified_intent}")

        except Exception as e:
            logger.error(f"Disambiguation failed: {e}")
            state["disambiguated"] = False
            state["context"]["disambiguated_intent"] = query
            state["context"]["confidence"] = 0.5

        return state

    @traceable(name="MilhenaAnalyzeIntent")
    async def analyze_intent(self, state: MilhenaState) -> MilhenaState:
        """Analyze user intent"""
        query = state["query"]
        context = state["context"]
        session_id = state["session_id"]

        try:
            intent = await self.intent_analyzer.classify(query, context, session_id)
            state["intent"] = intent if intent else "GENERAL"
            logger.info(f"Intent classified as: {state['intent']}")
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            state["intent"] = "GENERAL"
            state["context"]["classification_error"] = str(e)

        return state

    @traceable(name="MilhenaDatabaseQuery")
    async def database_query(self, state: MilhenaState) -> MilhenaState:
        """Execute database query based on intent

        Best Practice (LangChain 2025): Use tool.invoke({args}) instead of tool(args)
        """
        query = state["query"]
        intent = state.get("intent", "GENERAL")

        try:
            # Determine which tool to use based on intent and query
            query_lower = query.lower()

            # USER QUERIES
            if "utenti" in query_lower or "users" in query_lower:
                if "quanti" in query_lower or "count" in query_lower:
                    result = query_users_tool.invoke({"query_type": "count"})
                elif "attivi" in query_lower or "active" in query_lower:
                    result = query_users_tool.invoke({"query_type": "active"})
                else:
                    result = query_users_tool.invoke({"query_type": "all"})

            # EXECUTION QUERIES
            elif "esecuzione" in query_lower or "execution" in query_lower or "ultima" in query_lower:
                if "ultima" in query_lower or "last" in query_lower or "recente" in query_lower:
                    result = get_executions_tool.invoke({"query_type": "last"})
                elif "oggi" in query_lower or "today" in query_lower:
                    result = get_executions_tool.invoke({"query_type": "today"})
                elif "fallite" in query_lower or "errori" in query_lower or "failed" in query_lower:
                    result = get_executions_tool.invoke({"query_type": "failed"})
                else:
                    result = get_executions_tool.invoke({"query_type": "last"})

            # WORKFLOW QUERIES
            elif "workflow" in query_lower or "processo" in query_lower or "processi" in query_lower:
                if "attiv" in query_lower:
                    result = get_workflows_tool.invoke({"query_type": "active"})
                elif "inattiv" in query_lower or "disattiv" in query_lower:
                    result = get_workflows_tool.invoke({"query_type": "inactive"})
                elif "utilizzat" in query_lower or "usat" in query_lower or "top" in query_lower:
                    result = get_workflows_tool.invoke({"query_type": "top_used"})
                elif "compless" in query_lower or "nodi" in query_lower:
                    result = get_workflows_tool.invoke({"query_type": "complex"})
                elif "recen" in query_lower or "modificat" in query_lower:
                    result = get_workflows_tool.invoke({"query_type": "recent"})
                elif "error" in query_lower or "problem" in query_lower:
                    result = get_workflows_tool.invoke({"query_type": "errors"})
                else:
                    result = get_workflows_tool.invoke({"query_type": "all"})

            # PERFORMANCE QUERIES
            elif "performance" in query_lower or "velocit" in query_lower or "lent" in query_lower or "tasso" in query_lower:
                if "velocit" in query_lower or "lent" in query_lower or "speed" in query_lower:
                    result = get_performance_metrics_tool.invoke({"query_type": "speed"})
                elif "tasso" in query_lower or "success" in query_lower or "successo" in query_lower:
                    result = get_performance_metrics_tool.invoke({"query_type": "success_rate"})
                elif "trend" in query_lower or "andamento" in query_lower:
                    result = get_performance_metrics_tool.invoke({"query_type": "trends"})
                elif "bottleneck" in query_lower or "collo" in query_lower or "problema" in query_lower:
                    result = get_performance_metrics_tool.invoke({"query_type": "bottlenecks"})
                else:
                    result = get_performance_metrics_tool.invoke({"query_type": "overview"})

            # MONITORING QUERIES
            elif "monitoraggio" in query_lower or "alert" in query_lower or "salute" in query_lower or "health" in query_lower:
                if "alert" in query_lower or "avvisi" in query_lower or "warning" in query_lower:
                    result = get_system_monitoring_tool.invoke({"query_type": "alerts"})
                elif "coda" in query_lower or "queue" in query_lower:
                    result = get_system_monitoring_tool.invoke({"query_type": "queue"})
                elif "risorse" in query_lower or "resources" in query_lower:
                    result = get_system_monitoring_tool.invoke({"query_type": "resources"})
                elif "disponibilit" in query_lower or "availability" in query_lower or "uptime" in query_lower:
                    result = get_system_monitoring_tool.invoke({"query_type": "availability"})
                else:
                    result = get_system_monitoring_tool.invoke({"query_type": "health"})

            # ANALYTICS QUERIES
            elif "report" in query_lower or "analisi" in query_lower or "confronto" in query_lower or "roi" in query_lower:
                if "confronto" in query_lower or "comparison" in query_lower or "settiman" in query_lower:
                    result = get_analytics_tool.invoke({"query_type": "comparison"})
                elif "roi" in query_lower or "risparmio" in query_lower or "valore" in query_lower:
                    result = get_analytics_tool.invoke({"query_type": "roi"})
                elif "pattern" in query_lower or "utilizzo" in query_lower or "picco" in query_lower:
                    result = get_analytics_tool.invoke({"query_type": "patterns"})
                elif "prevision" in query_lower or "forecast" in query_lower or "proiezion" in query_lower:
                    result = get_analytics_tool.invoke({"query_type": "forecast"})
                else:
                    result = get_analytics_tool.invoke({"query_type": "summary"})

            # ERROR QUERIES (generic error checking)
            elif "errori" in query_lower or "error" in query_lower:
                # Check if it's about executions specifically
                if "esecuz" in query_lower:
                    result = get_executions_tool.invoke({"query_type": "failed"})
                else:
                    # Generic error check: use system monitoring
                    result = get_system_monitoring_tool.invoke({"query_type": "alerts"})

            # SYSTEM STATUS (default)
            elif "sistema" in query_lower or "status" in query_lower or "stato" in query_lower:
                result = get_system_monitoring_tool.invoke({"query_type": "health"})

            else:
                # Default: try to get general analytics
                result = get_analytics_tool.invoke({"query_type": "summary"})

            # Store result in context for response generation
            state["context"]["database_result"] = result
            logger.info(f"Database query executed: {result[:100]}...")

        except Exception as e:
            logger.error(f"Database query failed: {e}")
            state["context"]["database_error"] = str(e)

        return state

    @traceable(
        name="MilhenaReActAgent",
        run_type="chain",
        metadata={"component": "react_agent", "version": "3.0"}
    )
    async def execute_react_agent(self, state: MilhenaState) -> MilhenaState:
        """
        Execute ReAct Agent with conversation memory for intelligent tool selection

        Best Practice (LangGraph Official): Use create_react_agent for context-aware tool calling
        The agent receives full conversation history and intelligently selects tools

        Benefits:
        - Understands pronouns and references ("quali sono?" → knows from history)
        - LLM-based tool selection (no hardcoded if/elif)
        - Automatic conversation context resolution
        """
        session_id = state["session_id"]
        query = state.get("query", "")

        logger.error(f"🛠️ [DEBUG] EXECUTE_REACT_AGENT CALLED - query='{query[:60]}'")

        try:
            # Config for ReAct agent with thread_id for memory
            config = {
                "configurable": {
                    "thread_id": session_id
                }
            }

            # Invoke ReAct agent with full message history
            # Agent automatically loads previous messages from checkpointer
            result = await self.react_agent.ainvoke(
                {"messages": state["messages"]},
                config
            )

            # Extract tool results from ToolMessages (Best Practice: LangGraph official docs)
            # ToolMessage.content contains actual tool execution results
            # Final AIMessage often contains generic LLM-generated text
            from langchain_core.messages import ToolMessage

            tool_messages = [msg for msg in result["messages"] if isinstance(msg, ToolMessage)]

            # LOGGING: Estrai anche quale tool è stato chiamato
            tool_names = []
            for msg in result["messages"]:
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        if 'name' in tool_call:
                            tool_names.append(tool_call['name'])

            logger.error(f"📊 [DEBUG] REACT AGENT RESULT - total messages={len(result['messages'])}, ToolMessages={len(tool_messages)}")
            logger.error(f"🔧 [DEBUG] TOOLS CHIAMATI: {tool_names if tool_names else 'NESSUNO (risposta diretta LLM)'}")

            if tool_messages:
                # Combine all tool results (multiple tools may have been called)
                tool_output = "\n\n".join([msg.content for msg in tool_messages])
                state["context"]["database_result"] = tool_output
                logger.error(f"✅ [DEBUG] Extracted {len(tool_messages)} ToolMessages: {tool_output[:150]}")
            else:
                # Fallback: no tools used, use final AI message
                final_message = result["messages"][-1]
                tool_output = final_message.content if hasattr(final_message, 'content') else ""
                state["context"]["database_result"] = tool_output
                logger.error(f"⚠️ [DEBUG] NO ToolMessages - using AIMessage: {tool_output[:100]}")

        except Exception as e:
            logger.error(f"ReAct Agent failed: {e}")
            state["context"]["database_error"] = str(e)
            # Fallback to empty result
            state["context"]["database_result"] = "Unable to retrieve data at this time."

        return state

    @traceable(
        name="MilhenaRetrieveRAG",
        run_type="retriever",
        metadata={"component": "rag", "version": "3.0"}
    )
    async def retrieve_rag_context(self, state: MilhenaState) -> MilhenaState:
        """Retrieve relevant context from RAG knowledge base"""
        query = state["query"]
        intent = state.get("intent", "GENERAL")

        if not self.rag_system:
            logger.warning("RAG system not available, skipping retrieval")
            state["rag_context"] = []
            return state

        try:
            # Search RAG knowledge base for relevant documentation
            # Using correct API: search() returns List[Dict] directly
            from app.rag.maintainable_rag import UserLevel

            docs = await self.rag_system.search(
                query=query,
                top_k=3,
                user_level=UserLevel.BUSINESS
            )

            if docs and len(docs) > 0:
                state["rag_context"] = docs
                state["context"]["rag_docs"] = docs
                # Relevance score: 1.0 = perfect match, 0.0 = no match
                top_relevance = docs[0].get('relevance_score', 0.0)
                logger.info(f"Retrieved {len(docs)} RAG documents (top relevance: {top_relevance:.3f})")
            else:
                state["rag_context"] = []
                logger.info("No relevant RAG documents found")

        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            state["rag_context"] = []
            state["context"]["rag_error"] = str(e)

        return state

    @traceable(name="MilhenaGenerateResponse")
    async def generate_response(self, state: MilhenaState) -> MilhenaState:
        """Generate appropriate response"""
        query = state["query"]
        intent = state.get("intent", "GENERAL")
        context = state["context"]
        session_id = state["session_id"]

        try:
            # Select appropriate LLM
            complexity = self._assess_complexity(query)

            if complexity == "simple" and self.groq_llm:
                llm = self.groq_llm
                logger.info("Using GROQ for simple query")
            else:
                llm = self.openai_llm
                logger.info("Using OpenAI for complex query")

            response = await self.response_generator.generate(
                query=query,
                intent=intent,
                llm=llm,
                context=context,
                session_id=session_id
            )

            state["response"] = response

            # Add AI response to messages for Chat display
            state["messages"].append(AIMessage(content=response))

            logger.info(f"Response generated: {response[:100]}...")

            # Cache the response
            try:
                await self.cache_manager.set(query, session_id, {"response": response})
            except Exception as cache_error:
                logger.warning(f"Failed to cache response: {cache_error}")

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            error_msg = "Mi dispiace, ho avuto un problema nel generare la risposta. Riprova."
            state["response"] = error_msg
            state["messages"].append(AIMessage(content=error_msg))
            state["error"] = str(e)

        return state

    @traceable(name="MilhenaMaskResponse")
    async def mask_response(self, state: MilhenaState) -> MilhenaState:
        """Apply final masking to response"""
        response = state.get("response", "")

        if response:
            try:
                # Apply smart masking that preserves workflow names
                masked = self.masking_engine.mask(response)
                state["response"] = masked
                state["masked"] = True
                logger.info("Response masked (preserving workflow names)")
            except Exception as e:
                logger.error(f"Masking failed: {e}")
                state["masked"] = False
        else:
            state["masked"] = False

        return state

    @traceable(name="MilhenaRecordFeedback")
    async def record_feedback(self, state: MilhenaState) -> MilhenaState:
        """Record interaction for learning"""
        query = state["query"]
        intent = state["intent"]
        response = state["response"]
        session_id = state["session_id"]

        await self.learning_system.record_feedback(
            query=query,
            intent=intent or "GENERAL",
            response=response or "",
            feedback_type="neutral",
            session_id=session_id
        )

        logger.info("Feedback recorded for learning")

        return state

    @traceable(name="MilhenaHandleError")
    async def handle_error(self, state: MilhenaState) -> MilhenaState:
        """Handle errors and technical queries"""
        state["response"] = "Per informazioni tecniche, contatta il team IT."
        state["error"] = "Technical query deflected"

        logger.info("Technical query handled")

        return state

    # ============================================================================
    # ROUTING FUNCTIONS
    # ============================================================================

    def route_from_supervisor(self, state: MilhenaState) -> str:
        """
        Route based on Supervisor ACTION decision.
        Best Practice 2025: Action-based routing (respond/tool/route)

        IMPORTANTE: TUTTI i path passano SEMPRE per mask_response prima di END
        """
        decision = state.get("supervisor_decision")

        logger.error(f"🚦 [DEBUG] ROUTING - decision={decision}")

        if not decision:
            logger.warning("[ROUTING] No supervisor decision, defaulting to full pipeline")
            return "apply_patterns"

        action = decision.get("action", "route")  # Default: route (conservative)
        category = decision["category"]

        logger.error(f"🚦 [DEBUG] ROUTING - action={action}, category={category}")

        # ACTION: respond
        # Supervisor ha già generato direct_response, vai direttamente a Mask
        if action == "respond":
            logger.info(f"[ROUTING] action=respond (category={category}) → mask_response")
            return "mask_response"

        # ACTION: tool
        # Serve DB query per dati, poi genera risposta e va a Mask
        if action == "tool":
            logger.error(f"🚀 [DEBUG] ROUTING TO DATABASE_QUERY NODE")
            logger.info(f"[ROUTING] action=tool (category={category}) → database_query → generate_response → mask_response")
            return "database_query"

        # ACTION: route
        # Full pipeline: Disambiguate → RAG → Generate → Mask
        if action == "route":
            logger.info(f"[ROUTING] action=route (category={category}) → apply_patterns (full pipeline)")
            return "apply_patterns"

        # Fallback (non dovrebbe mai succedere)
        logger.warning(f"[ROUTING] Unknown action '{action}', defaulting to full pipeline")
        return "apply_patterns"

    def route_from_complexity(self, state: MilhenaState) -> str:
        """
        Route based on query complexity for fast-path optimization.
        Simple queries skip disambiguation/RAG and go directly to response generation.
        """
        is_simple = state.get("context", {}).get("is_simple_query", False)

        if is_simple:
            logger.info("[OPTIMIZATION] Taking FAST PATH - skipping disambiguation and RAG")
            return "simple"
        else:
            logger.info("[OPTIMIZATION] Taking FULL PATH - complex query needs full pipeline")
            return "complex"

    def route_from_intent(self, state: MilhenaState) -> str:
        """Route based on intent"""
        intent = state.get("intent", "GENERAL")

        if intent == "TECHNICAL":
            return "technical"
        elif intent in ["METRIC", "STATUS", "DATA", "COUNT"]:
            # These intents need database data - go through RAG first
            return "needs_data"
        else:
            return "business"

    def route_after_rag(self, state: MilhenaState) -> str:
        """Route after RAG retrieval - decide if we need DB data or can answer directly"""
        rag_context = state.get("rag_context", [])
        intent = state.get("intent", "GENERAL")

        # If RAG found high-quality docs, we might have the answer
        if rag_context and len(rag_context) > 0:
            # Check if top result has high relevance (relevance_score: 1.0 = perfect)
            top_relevance = rag_context[0].get("relevance_score", 0.0)
            if top_relevance > 0.8:
                logger.info(f"High-quality RAG result (relevance: {top_relevance:.3f}), skipping DB query")
                return "has_answer"

        # For data-heavy intents, always query DB even if RAG found something
        if intent in ["METRIC", "STATUS", "DATA", "COUNT"]:
            return "needs_db"

        # Default: if we have some RAG context, use it
        if rag_context:
            return "has_answer"

        return "needs_db"

    def _assess_complexity(self, query: str) -> str:
        """Assess query complexity"""
        word_count = len(query.split())

        if word_count < 10:
            return "simple"
        elif word_count < 30:
            return "medium"
        else:
            return "complex"

    # ============================================================================
    # PUBLIC INTERFACE
    # ============================================================================

    async def process(
        self,
        query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the Milhena workflow

        Args:
            query: User query
            session_id: Session identifier
            context: Optional context

        Returns:
            Response dictionary
        """
        try:
            # Config with thread_id for conversation memory (Best Practice: LangGraph Checkpointer)
            # thread_id = session_id ensures each user has their own conversation history
            config = {
                "configurable": {
                    "thread_id": session_id
                }
            }

            # CRITICAL FIX: Load conversation history BEFORE invoking graph
            # So supervisor can access it in state["messages"]
            previous_messages = []
            try:
                # Get last checkpoint for this thread
                state_snapshot = self.compiled_graph.get_state(config)
                if state_snapshot and hasattr(state_snapshot, 'values') and state_snapshot.values:
                    # Extract messages from previous state
                    prev_msgs = state_snapshot.values.get("messages", [])
                    # Keep last 10 messages max (5 turns) to avoid context explosion
                    previous_messages = prev_msgs[-10:] if len(prev_msgs) > 10 else prev_msgs
                    logger.info(f"[MEMORY] Loaded {len(previous_messages)} previous messages from session {session_id}")
            except Exception as e:
                logger.warning(f"[MEMORY] Could not load previous state: {e}")
                # Continue without history if loading fails

            # Initialize state WITH conversation history
            initial_state = MilhenaState(
                messages=previous_messages + [HumanMessage(content=query)],  # History + new message
                query=query,
                intent=None,
                session_id=session_id,
                context=context or {},
                disambiguated=False,
                response=None,
                feedback=None,
                cached=False,
                masked=False,
                error=None,
                rag_context=None,
                learned_patterns=None,
                supervisor_decision=None,
                waiting_clarification=False,
                original_query=None
            )

            # Run the graph with config (checkpointer saves NEW state after execution)
            final_state = await self.compiled_graph.ainvoke(initial_state, config)

            # Extract supervisor decision for metadata
            supervisor_decision = final_state.get("supervisor_decision")

            # Return the result
            return {
                "success": True,
                "response": final_state.get("response"),
                "intent": final_state.get("intent"),
                "cached": final_state.get("cached", False),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "supervisor_decision": supervisor_decision,
                    "supervisor_category": supervisor_decision.get("category") if supervisor_decision else None,
                    "supervisor_action": supervisor_decision.get("action") if supervisor_decision else None,
                    "supervisor_confidence": supervisor_decision.get("confidence") if supervisor_decision else None
                }
            }

        except Exception as e:
            logger.error(f"Error in MilhenaGraph: {e}")
            return {
                "success": False,
                "response": "Si è verificato un problema temporaneo. Riprova.",
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }

    async def process_with_feedback(
        self,
        query: str,
        session_id: str,
        feedback_type: str,  # "positive" or "negative"
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process query and record feedback

        Args:
            query: User query
            session_id: Session identifier
            feedback_type: Type of feedback
            context: Optional context

        Returns:
            Response dictionary
        """
        # Process the query
        result = await self.process(query, session_id, context)

        # Record the feedback
        if result["success"]:
            await self.learning_system.record_feedback(
                query=query,
                intent=result.get("intent", "GENERAL"),
                response=result.get("response", ""),
                feedback_type=feedback_type,
                session_id=session_id
            )

        return result

    async def process_query(
        self,
        query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process query with enhanced metadata for API compatibility.
        Alias for process() with additional metadata extraction.

        Args:
            query: User query
            session_id: Session identifier
            context: Optional context

        Returns:
            Response dictionary with metadata (supervisor_decision, processing_time, etc.)
        """
        import time
        start_time = time.time()

        # Call the base process method
        result = await self.process(query, session_id, context)

        # Add processing time
        processing_time = time.time() - start_time

        # Enhance metadata with supervisor decision if available
        # (extract from final state if needed)
        metadata = result.get("metadata", {})
        metadata["processing_time"] = processing_time

        # Return enhanced result
        return {
            "success": result.get("success", False),
            "response": result.get("response", "Come posso aiutarti?"),
            "metadata": metadata,
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", 0.95)
        }

# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

# Create a singleton instance
_milhena_instance = None

def get_milhena_graph() -> MilhenaGraph:
    """Get or create the Milhena graph singleton"""
    global _milhena_instance
    if _milhena_instance is None:
        _milhena_instance = MilhenaGraph()
    return _milhena_instance

# ============================================================================
# LANGGRAPH STUDIO EXPORT
# ============================================================================

# Export the compiled graph for LangGraph Studio
# This is what langgraph.json references
milhena_graph = get_milhena_graph().compiled_graph