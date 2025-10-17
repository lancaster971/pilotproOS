"""
Fast-Path v3.5 - Instant Safety Classification

ONLY safety checks (DANGER + GREETING) - everything else → Classifier

Reference: CONTEXT-SYSTEM.md v3.5.0 Phase 1
"""
from typing import Optional, Dict, Any
from langsmith import traceable
import logging

from app.agents.v3_5.utils.state import SupervisorDecision, AgentState

logger = logging.getLogger(__name__)


class FastPath:
    """
    Fast-Path Component - First step in agent pipeline

    Purpose: Instant classification for safety-critical queries
    - DANGER keywords → block immediately (security-first)
    - GREETING queries → quick response
    - Everything else → pass to Classifier (LLM)

    Latency: <1ms (keyword matching only)
    """

    def __init__(self):
        # DANGER keywords (expanded for comprehensive security coverage)
        self.danger_keywords = [
            # Credentials & Secrets
            "password", "credenziali", "credential", "api key", "token",
            "secret", "chiave", "accesso admin", "root password",
            "connection string", "dsn", "db url", "database url",
            "api_key", "access_token", "bearer", "auth token",
            "passwd", "pwd", "private key", "refresh token",

            # Tech Stack & Architecture (prevent technical leaks)
            "flowwise", "langflow", "langgraph", "langchain",
            "flowise", "n8n", "postgresql", "postgres", "mysql",
            "redis", "chromadb", "docker", "kubernetes", "k8s",
            "architettura", "struttura sistema", "stack tecnologico",
            "tech stack", "tecnologie", "framework", "librerie",
            "che database", "quale database", "usate database",
            "che sistema", "quale sistema", "sistema usa",
            "come funziona sistema", "come è fatto", "strutturato il sistema",

            # Infrastructure terms
            "nginx", "apache", "server", "hosting", "cloud provider",
            "aws", "azure", "gcp", "digitalocean", "heroku",

            # Development tools
            "git", "github", "gitlab", "jenkins", "ci/cd", "pipeline"
        ]

        # GREETING exact matches (case-insensitive)
        self.greeting_exact = {
            "ciao", "buongiorno", "buonasera", "hello", "hi", "salve",
            "grazie", "arrivederci", "buonanotte", "hey"
        }

    @traceable(name="FastPath", run_type="chain", metadata={"version": "3.5.6"})
    async def check(self, state: AgentState) -> AgentState:
        """
        Check if query matches fast-path patterns (DANGER or GREETING).

        Returns:
            state: Modified state with supervisor_decision if match found,
                   or unmodified state if no match (pass to Classifier)
        """
        query = state["query"]
        query_lower = query.lower().strip()

        # ============================================================================
        # SAFETY CHECK 1: DANGER Keywords (Security-First)
        # ============================================================================
        if any(kw in query_lower for kw in self.danger_keywords):
            logger.warning(f"[FAST-PATH] DANGER keyword detected: '{query[:50]}...'")

            decision = SupervisorDecision(
                action="respond",
                category="DANGER",
                confidence=1.0,
                reasoning="Blocco sicurezza immediato (fast-path)",
                direct_response="⚠️ Non posso fornire informazioni sull'architettura tecnica o dati sensibili. Per assistenza contatta l'amministratore.",
                needs_rag=False,
                needs_database=False,
                clarification_options=None,
                llm_used="fast-path"
            )

            state["supervisor_decision"] = decision.model_dump()
            state["waiting_clarification"] = False
            state["response"] = decision.direct_response
            state["intent"] = "SECURITY"

            logger.info(f"[FAST-PATH] Blocked DANGER query with direct response")
            return state

        # ============================================================================
        # GREETING: Quick Response for Common Greetings
        # ============================================================================
        if query_lower in self.greeting_exact:
            logger.info(f"[FAST-PATH] GREETING detected: '{query}'")

            decision = SupervisorDecision(
                action="respond",
                category="GREETING",
                confidence=1.0,
                reasoning="Saluto comune (fast-path)",
                direct_response="Ciao! Come posso aiutarti?",
                needs_rag=False,
                needs_database=False,
                clarification_options=None,
                llm_used="fast-path"
            )

            state["supervisor_decision"] = decision.model_dump()
            state["waiting_clarification"] = False
            state["response"] = decision.direct_response
            state["intent"] = "GENERAL"

            logger.info(f"[FAST-PATH] Responded to greeting with quick message")
            return state

        # ============================================================================
        # PASS TO CLASSIFIER (Everything else)
        # ============================================================================
        # No match → LLM Classifier will handle intelligence
        logger.info(f"[FAST-PATH] No match, passing to Classifier: '{query[:50]}...'")
        return state
